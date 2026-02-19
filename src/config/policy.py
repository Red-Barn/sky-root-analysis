from dataclasses import dataclass


@dataclass(frozen=True)
# similarity.select_best_route_gpu
class RouteSimilarityPolicy:
    near_threshold: float = 100 # 100m 이내를 근접으로 간주하여 유사도 평가


@dataclass(frozen=True)
class ImprovementPolicy:
    deviation_score_threshold: float = 0.2
    longest_deviation_threshold: int = 10
    separation_threshold: float = 1.0
    
    
@dataclass(frozen=True)
class BusDistancePolicy:
    bus_threshold_m = 100   # 기본값 50
    
    
@dataclass(frozen=True)
class SeverityScorePolicy:
    improve_ratio_threshold = 0.5
    median_norm_threshold = 0.3
    cluster_norm_threshold = 0.2
    min_total_trips = 5