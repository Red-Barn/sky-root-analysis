import pandas as pd


def normalize(series):
    return (series - series.min()) / (series.max() - series.min() + 1e-6)


def region_level_analysis(df, policy):
    required_cols = {
        "TRIP_NO",
        "EMD_CODE",
        "has_candidate",
        "improve_required",
        "deviation_ratio",
        "mean_confidence",
        "longest_deviation",
        "separation",
    }
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"region_level_analysis: missing required columns: {sorted(missing)}")

    df = df[df["has_candidate"] == True].copy()
    df = df[df["EMD_CODE"].notna()].copy()

    # Handle values loaded back from CSV where dtypes may shift.
    df["improve_required"] = df["improve_required"].astype(bool)
    for col in ["deviation_ratio", "mean_confidence", "longest_deviation", "separation"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    grouped = df.groupby("EMD_CODE").agg(
        total_trips=("TRIP_NO", "count"),
        improve_trips=("improve_required", "sum"),
        avg_deviation_ratio=("deviation_ratio", "mean"),
        avg_mean_confidence=("mean_confidence", "mean"),
        avg_longest_deviation=("longest_deviation", "mean"),
        avg_separation=("separation", "mean"),
    ).reset_index()

    grouped = grouped[grouped["total_trips"] >= policy.min_total_trips]
    grouped["improve_ratio"] = grouped["improve_trips"] / grouped["total_trips"]

    # Keep existing policy weights and map them to new trip-level metrics.
    grouped["deviation_norm"] = normalize(grouped["avg_deviation_ratio"])
    grouped["longest_dev_norm"] = normalize(grouped["avg_longest_deviation"])

    grouped["severity_score"] = (
        policy.improve_ratio_weight * grouped["improve_ratio"]
        + policy.deviation_ratio_weight * grouped["deviation_norm"]
        + policy.longest_deviation_weight * grouped["longest_dev_norm"]
    )

    grouped["improve_ratio_pct"] = grouped["improve_ratio"] * 100
    grouped = grouped.sort_values("severity_score", ascending=False).reset_index(drop=True)
    grouped["priority_rank"] = grouped.index + 1

    return grouped
