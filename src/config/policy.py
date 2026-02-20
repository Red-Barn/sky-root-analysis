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
    improve_ratio_weight: float = 0.5
    deviation_ratio_weight: float = 0.3
    longest_deviation_weight: float = 0.2
    min_total_trips: int = 5

    # Backward-compatible aliases
    @property
    def improve_ratio_threshold(self) -> float:
        return self.improve_ratio_weight

    @property
    def median_norm_threshold(self) -> float:
        return self.deviation_ratio_weight

    @property
    def cluster_norm_threshold(self) -> float:
        return self.longest_deviation_weight
