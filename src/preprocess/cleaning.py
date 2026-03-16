from typing import List

import numpy as np
import pandas as pd
from tqdm import tqdm

from src.config.settings import DATA_DIR
from src.config.runtime import create_runtime_context
from src.data.loader import load_filtered_trips
from src.trajectory.haversine import harversine_numpy

def _speed_kmh(distance_m: float, start_tm, end_tm) -> float:
    seconds = (pd.Timestamp(end_tm) - pd.Timestamp(start_tm)).total_seconds()
    return float(distance_m / seconds * 3.6)


def prepare_input():
    df = load_filtered_trips().copy()
    
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


def remove_spike_points(trip_df, ctx):
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

        if _is_spike_pair(prev_row, cur_row, next_row, policy=ctx.preprocess):
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


def trim_destination_tail(trip_df, policy):
    """
    마지막 도착점 근처(그리고 가능하면 같은 EMD_CODE)에서 오래 머문 tail 을 제거.
    마지막 행은 목적지 도착점으로 보고, 그 근처에 계속 머무는 마지막 streak 를 잘라낸다.
    """
    trip_df = trip_df.reset_index(drop=True).copy()
    final_x = trip_df.iloc[-1]["DPR_CELL_XCRD"]
    final_y = trip_df.iloc[-1]["DPR_CELL_YCRD"]
    final_emd = trip_df.iloc[-1].get("EMD_CODE")

    start = len(trip_df) - 1
    while start - 1 >= 0:
        row = trip_df.iloc[start - 1]
        dist_to_final = harversine_numpy(
            row["DPR_CELL_XCRD"],
            row["DPR_CELL_YCRD"],
            final_x,
            final_y,
        )
        same_emd = row.get("EMD_CODE") == final_emd

        if dist_to_final <= policy.dest_radius_m and same_emd:
            start -= 1
        else:
            break

    streak_len = len(trip_df) - start
    dwell_seconds = (
        trip_df.iloc[-1]["DPR_MT1_UNIT_TM"] - trip_df.iloc[start]["DPR_MT1_UNIT_TM"]
    ).total_seconds()

    if streak_len >= policy.dest_consecutive_rows or dwell_seconds >= policy.dest_min_dwell_seconds:
        trimmed_count = len(trip_df) - (start + 1)
        return trip_df.iloc[: start + 1].reset_index(drop=True), trimmed_count

    return trip_df, 0


def clean_trip_points():
    ctx = create_runtime_context(verbose=True)
    df = prepare_input()
    original_columns = df.columns.tolist()

    cleaned_groups = []
    summary_rows = []
    grouped = df.groupby("TRIP_NO", sort=False)

    for trip_no, trip_df in tqdm(grouped, total=grouped.ngroups, desc="Cleaning trip points"):
        trip_df = trip_df.sort_values(["DPR_MT1_UNIT_TM", "ARV_MT1_UNIT_TM"]).reset_index(drop=True)
        original_len = len(trip_df)

        trip_df, spike_removed = remove_spike_points(trip_df, ctx)
        trip_df, tail_removed = trim_destination_tail(trip_df, policy=ctx.preprocess)

        # Check if the cleaned trip has enough points
        if len(trip_df) < ctx.preprocess.min_trip_points:
            continue

        cleaned_groups.append(trip_df[original_columns])
        summary_rows.append(
            {
                "TRIP_NO": trip_no,
                "original_rows": original_len,
                "spike_rows_removed": spike_removed,
                "tail_rows_removed": tail_removed,
                "final_rows": len(trip_df),
            }
        )

    cleaned_df = pd.concat(cleaned_groups, ignore_index=True)
    cleaned_df = cleaned_df[original_columns]
    cleaned_df.to_csv(DATA_DIR / "processed_all_trips.csv", index=False)

    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(DATA_DIR / "summary.csv", index=False)


if __name__ == "__main__":
    clean_trip_points()