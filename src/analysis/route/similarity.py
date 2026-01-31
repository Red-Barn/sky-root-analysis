import numpy as np
import torch
from src.trajectory.haversine import cdist
from src.trajectory.dtw import cdtw

def to_tensor(coords, device):
    """
    coords: [(lat, lon), ...]
    return: torch tensor [[lon, lat], ...]
    """
    return torch.tensor(
        [[lon, lat] for lat, lon in coords],
        dtype=torch.float32,
        device=device
    )
    
def evaluate_route_gpu(actual_coords, route_coords, near_threshold=100, device=torch.device("cpu")):
    A = to_tensor(actual_coords, device)
    R = to_tensor(route_coords, device)
    
    dist_matrix = cdist(A, R)   # (lon x lat)
    min_distances = torch.min(dist_matrix, dim=1).values
    distances = min_distances.cpu().numpy()
    dtw = cdtw(dist_matrix)
    
    return {
        "mean": distances.mean(),
        "median": float(torch.median(min_distances).cpu()),
        "max": distances.max(),
        "near_ratio": (distances <= near_threshold).sum() / len(distances),
        "distances" : distances,
        "dtw": float(dtw.cpu())
    }
    
def select_best_route_gpu(actual_coords, candidate_routes, policy, device):
    best_idx = None
    best_score = float("inf")
    best_result = None
    
    for route in candidate_routes:
        route_no = route["ROUTE_NO"]
        route_coords = route["POINTS"]  # [(lat, lon), ...]
        
        if len(actual_coords) == 0 or len(route_coords) == 0:
            return None
        
        res = evaluate_route_gpu(actual_coords, route_coords, near_threshold = policy.near_threshold, device=device)
        score = res["dtw"]
        
        if score < best_score:
            best_score = score
            best_idx = route_no
            best_result = res
            
    return best_idx, best_result