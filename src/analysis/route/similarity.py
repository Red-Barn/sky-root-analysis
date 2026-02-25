# src/analysis/route/similarity.py
from src.trajectory.dtw import dtw_cost_haversine, dtw_path_haversine

def select_best_route_gpu(actual_coords, candidate_routes, policy, device):
    # device는 더 이상 의미 없음(CPU로 계산)
    if not actual_coords or not candidate_routes:
        return None, None

    best_idx = None
    best_score = float("inf")
    best_route_coords = None

    # 1) 후보들은 DTW cost만 계산 (cutoff로 pruning)
    for route in candidate_routes:
        route_no = route["ROUTE_NO"]
        route_coords = route["POINTS"]
        if not route_coords:
            continue

        score = dtw_cost_haversine(actual_coords, route_coords, cutoff=best_score)
        if score < best_score:
            best_score = score
            best_idx = route_no
            best_route_coords = route_coords

    if best_idx is None:
        return None, None

    # 2) best 1개만 alignment/distances 생성
    dtw, alignment, distances = dtw_path_haversine(actual_coords, best_route_coords)
    return best_idx, {
        "dtw": dtw,
        "aligment": alignment,
        "distances": distances,
    }