from typing import List

import pandas as pd
from tqdm import tqdm
from pathlib import Path

from src.config.runtime import create_runtime_context
from src.trajectory.haversine import harversine_numpy


def _speed_kmh(distance_m: float, start_tm, end_tm) -> float:
    seconds = (pd.Timestamp(end_tm) - pd.Timestamp(start_tm)).total_seconds()
    return float(distance_m / seconds * 3.6)


def prepare_input(df):
    df = df.copy()
    
    for col in ["DPR_MT1_UNIT_TM", "ARV_MT1_UNIT_TM"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")
        
    for col in ["DPR_CELL_XCRD", "DPR_CELL_YCRD", "ARV_CELL_XCRD", "ARV_CELL_YCRD", "DYNA_MVMT_SPED"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        
    return df


def _recalc_row_speed(row):
    dist_m = harversine_numpy(
        row["DPR_CELL_XCRD"],
        row["DPR_CELL_YCRD"],
        row["ARV_CELL_XCRD"],
        row["ARV_CELL_YCRD"],
    )
    return _speed_kmh(dist_m, row["DPR_MT1_UNIT_TM"], row["ARV_MT1_UNIT_TM"])


def _is_spike_pair(prev_row, cur_row, next_row, policy):
    d_in = harversine_numpy(
        prev_row["DPR_CELL_XCRD"],
        prev_row["DPR_CELL_YCRD"],
        cur_row["DPR_CELL_XCRD"],
        cur_row["DPR_CELL_YCRD"],
    )
    d_out = harversine_numpy(
        cur_row["DPR_CELL_XCRD"],
        cur_row["DPR_CELL_YCRD"],
        next_row["DPR_CELL_XCRD"],
        next_row["DPR_CELL_YCRD"],
    )
    d_skip = harversine_numpy(
        prev_row["DPR_CELL_XCRD"],
        prev_row["DPR_CELL_YCRD"],
        next_row["DPR_CELL_XCRD"],
        next_row["DPR_CELL_YCRD"],
    )

    v_in = _speed_kmh(d_in, prev_row["DPR_MT1_UNIT_TM"], cur_row["DPR_MT1_UNIT_TM"])
    v_out = _speed_kmh(d_out, cur_row["DPR_MT1_UNIT_TM"], next_row["DPR_MT1_UNIT_TM"])
    v_skip = _speed_kmh(d_skip, prev_row["DPR_MT1_UNIT_TM"], next_row["DPR_MT1_UNIT_TM"])

    bad_in = (d_in >= policy.max_spike_distance_m) or (v_in >= policy.max_speed_kmh)
    bad_out = (d_out >= policy.max_spike_distance_m) or (v_out >= policy.max_speed_kmh)
    recover_skip = (d_skip < policy.max_spike_distance_m) or (v_skip < policy.max_speed_kmh)

    return bool(bad_in and bad_out and recover_skip)


def _merge_two_rows(prev_row, next_row):
    """중간 point 하나를 제거한 것처럼 prev_row 를 next_row 도착점까지 확장."""
    merged = prev_row.copy()
    merged["ARV_MT1_UNIT_TM"] = next_row["DPR_MT1_UNIT_TM"]
    merged["ARV_CELL_ID"] = next_row["DPR_CELL_ID"]
    merged["ARV_CELL_XCRD"] = next_row["DPR_CELL_XCRD"]
    merged["ARV_CELL_YCRD"] = next_row["DPR_CELL_YCRD"]
    merged["DYNA_MVMT_SPED"] = _recalc_row_speed(merged)

    return merged


def remove_spike_points(trip_df, policy):
    """
    중간에 한 점이 튄 경우,
    [이전 row] + [다음 row] 를 합쳐서 점 하나를 삭제한 효과를 만든다.
    """
    rows: List[pd.Series] = [row.copy() for _, row in trip_df.iterrows()]
    removed_count = 0
    i = 1

    while i < len(rows) - 1:
        prev_row = rows[i - 1]
        cur_row = rows[i]
        next_row = rows[i + 1]

        if _is_spike_pair(prev_row, cur_row, next_row, policy):
            rows[i - 1] = _merge_two_rows(prev_row, next_row)
            del rows[i]
            removed_count += 1
            if i > 1:
                i -= 1  # 이전 점과도 spike 여부 재검사
            continue
        i += 1

    cleaned = pd.DataFrame(rows)
    cleaned = cleaned.reset_index(drop=True)
    return cleaned, removed_count


def clean_trip_points(df, policy):
    df = prepare_input(df)
    original_columns = df.columns.tolist()

    cleaned_groups = []
    summary_rows = []
    grouped = df.groupby("TRIP_NO", sort=False)

    for trip_no, trip_df in tqdm(grouped, total=grouped.ngroups, desc="Cleaning trip points", position=1, leave=False):
        trip_df = trip_df.sort_values(["DPR_MT1_UNIT_TM", "ARV_MT1_UNIT_TM"]).reset_index(drop=True)
        original_len = len(trip_df)
        
        trip_df, spike_removed = remove_spike_points(trip_df, policy)

        # Check if the cleaned trip has enough points
        if len(trip_df) < policy.min_trip_points:
            continue

        cleaned_groups.append(trip_df[original_columns])
        summary_rows.append(
            {
                "TRIP_NO": trip_no,
                "original_rows": original_len,
                "spike_rows_removed": spike_removed,
                "final_rows": len(trip_df),
            }
        )

    cleaned_df = pd.concat(cleaned_groups, ignore_index=True)
    cleaned_df = cleaned_df[original_columns]
    
    return cleaned_df, summary_rows

    
def cleaning_folder(input_dir: Path, output_dir: Path):
    ctx = create_runtime_context(verbose=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = []
    
    for file_path in tqdm(list(input_dir.glob("*.csv")), desc="Cleaning files", position=0):
        df = pd.read_csv(file_path)
        cleaned_df, summary_rows = clean_trip_points(df, policy=ctx.preprocess)
        summary.extend(summary_rows)
        output_path = output_dir / file_path.name
        cleaned_df.to_csv(output_path, index=False)
        
    summary_df = pd.DataFrame(summary)
    summary_df.to_csv(output_dir / "cleaning_summary.csv", index=False)
    