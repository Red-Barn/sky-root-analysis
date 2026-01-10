import pandas as pd
from tqdm import tqdm

from src.config.settings import MAPPING_DATA_DIR, RESULT_REGION_DIR
from src.visualization.utils import plot_region_severity_map, select_top_regions, plot_region_case

def run_visualization():
    for file_path in tqdm(list(RESULT_REGION_DIR.glob("*.csv")), desc="visualizing files", position=0):   
        # 1. 지역 분석
        region_df = pd.read_csv(file_path)

        # 2. 전체 지도
        plot_region_severity_map(region_df, "emd.geojson")

        # 3. Top 3 지역
        top_regions = select_top_regions(region_df, top_n=3)

        # 4. mapping 결과 로드
        mapping_df = pd.concat([
            pd.read_csv(p) for p in MAPPING_DATA_DIR.glob("*.csv")
        ])

        # 5. 지역별 상세 시각화
        for emd in top_regions:
            plot_region_case(mapping_df, "emd.geojson", emd)
            
if __name__ == "__main__":
    run_visualization()
