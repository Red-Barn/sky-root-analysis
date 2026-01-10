import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt

from src.config.settings import RESULT_REGION_DIR
from src.data.loader import load_emd

# 1. 데이터 로드
region_df = pd.read_csv("result/region/2024-08-19.csv")
emd = gpd.read_file("data/open/emd_WGS84.json")

# 2. 코드 타입 통일
region_df["EMD_CODE"] = region_df["EMD_CODE"].astype(str)
emd["EMD_CD"] = emd["EMD_CD"].astype(str)

# 3. 조인
gdf = emd.merge(region_df, left_on="EMD_CD", right_on="EMD_CODE", how="left")

# 4. 시각화
fig, ax = plt.subplots(1, 1, figsize=(10, 10))
gdf.plot(
    column="severity_score",
    cmap="Reds",
    legend=True,
    ax=ax,
    missing_kwds={"color": "lightgrey"}
)

ax.set_title("지역별 개선 필요도 (Severity Score)")
ax.axis("off")
plt.show()

# 2️⃣ 개선 필요 상위 3개 지역 선정

top3 = (
    region_df[region_df["improve_trips"] == True]
    .sort_values("severity_score", ascending=False)
    .head(3)
)

top3_codes = top3["EMD_CODE"].astype(str).tolist()


# 🗺️ Folium 기반 시각화 (추천 ⭐)

import folium
from shapely.geometry import LineString

# 기준 지역
emd_target = gdf[gdf["EMD_CODE"] == top3_codes[0]]

# 지도 중심
center = emd_target.geometry.centroid.iloc[0]
m = folium.Map(location=[center.y, center.x], zoom_start=14)

# 1. EMD 경계
folium.GeoJson(
    emd_target.geometry,
    name="EMD Boundary",
    style_function=lambda x: {"fillColor": "none", "color": "black", "weight": 2}
).add_to(m)


# 🧍 실제 이동 경로 (파란 선)
trip_df = pd.read_csv("data/processed/bus_mapping.csv")

# 예: 해당 EMD의 trip만
trip_df = trip_df[trip_df["EMD_CODE"] == top3_codes[0]]

for trip_id, group in trip_df.groupby("TRIP_ID"):
    coords = list(zip(group["LON"], group["LAT"]))
    folium.PolyLine(
        coords,
        color="blue",
        weight=2,
        opacity=0.6
    ).add_to(m)


# 🚌 버스 탑승 구간 (빨간 선)
bus_segments = trip_df[trip_df["BUS_TYPE"].notna()]

for trip_id, group in bus_segments.groupby("TRIP_ID"):
    coords = list(zip(group["LON"], group["LAT"]))
    folium.PolyLine(
        coords,
        color="red",
        weight=4,
        opacity=0.8,
        tooltip=group["BUS_NAME"].iloc[0]
    ).add_to(m)

m.save("output/top3_region_route.html")
