import ast
import numpy as np
import pandas as pd
from src.analysis.route.improvement import is_improvement_required


# Trip 단위 분석
def analyze_trip(trip, ctx):
    trip_no = trip["TRIP_NO"]
    emd_code = trip["EMD_CODE"]
    best_idx = trip["best_route_idx"]
    dtw = trip["dtw"]
    alignment = ast.literal_eval(trip["alignment"])
    distances = np.array(ast.literal_eval(trip["distances"]), dtype=np.float32)

    # Step 3: 경로 개선 필요 판별
    improvement = is_improvement_required(distances, policy=ctx.improvement)

    return {
        "TRIP_NO": trip_no,
        "EMD_CODE": emd_code,
        "best_route_idx": best_idx,
        "dtw": dtw,
        "alignment": alignment,
        "distances": distances.tolist(),
        "improve_required": improvement["need_improvement"],
        "deviation_ratio": improvement["deviation_ratio"],
        "mean_confidence": improvement["mean_confidence"],
        "longest_deviation": improvement["longest_deviation"],
        "longest_deviation_ratio": improvement["longest_deviation_ratio"],
        "separation": improvement["separation"],
        "is_deviated": improvement["is_deviated"],
    }
    
def analyze_trips(df, ctx):
    results = []

    for _, trip in df.iterrows():
        res = analyze_trip(trip, ctx)
        
        if res:
            results.append(res)
                

    return pd.DataFrame(results)