from dataclasses import dataclass

@dataclass(frozen=True)
class BusDistancePolicy:
    bus_threshold_m = 100
    
    
@dataclass(frozen=True)
class PreprocessPolicy:
    max_speed_kmh: float = 120.0
    max_spike_distance_m: float = 2000.0
    dest_radius_m: float = 300.0
    dest_consecutive_rows: int = 3
    dest_min_dwell_seconds: int = 180
    min_trip_points: int = 20
    
    
@dataclass(frozen=True)
class ImprovementPolicy:
    deviation_score_threshold: float = 0.2
    longest_deviation_threshold: int = 10
    longest_deviation_ratio_threshold: float = 0.1
    separation_threshold: float = 1.1
    
    
@dataclass(frozen=True)
class SeverityScorePolicy:
    min_total_trips: int = 5
    min_improve_ratio_lower_bound: float = 0.3
    min_avg_deviation_ratio: float = 0.15
    min_avg_longest_deviation: float = 10.0
    min_avg_longest_deviation_ratio: float = 0.05
    wilson_z: float = 1.96

    improve_ratio_weight: float = 0.5
    deviation_ratio_weight: float = 0.3
    longest_deviation_weight: float = 0.2