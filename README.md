# sky-root-analysis-clean

실제 이동 궤적 데이터와 버스 기반 후보 경로를 비교해, 공항 접근 경로의 개선 필요 구간과 우선 검토 지역을 찾는 Python 분석 파이프라인입니다.

이 저장소는 단순 시각화가 아니라 다음 흐름을 하나로 묶습니다.

- 원본 이동 데이터 압축
- 이상 이동(spike) 제거
- 공항버스/시내버스 정류장 매핑
- 읍면동(EMD) 코드 부여
- 이상치 경로 제거
- Google Directions API 기반 버스 후보 경로 캐시 생성
- 실제 경로와 후보 경로의 DTW 비교
- trip 단위 개선 필요 판정
- region 단위 우선순위 산정
- 차트/지도/사례 시각화 생성

핵심 오케스트레이션은 `src/main.py`에서 수행됩니다.

## 저장소 구조

```text
sky-root-analysis-clean/
|-- README.md
|-- src/
|   |-- main.py
|   |-- config/
|   |   |-- settings.py
|   |   |-- runtime.py
|   |   `-- policy.py
|   |-- data/
|   |   `-- loader.py
|   |-- preprocess/
|   |   |-- compress.py
|   |   |-- cleaning.py
|   |   |-- makeEMD.py
|   |   `-- boxplot.py
|   |-- mapping/
|   |   |-- main.py
|   |   `-- bus/
|   |       |-- builder.py
|   |       |-- airport_bus.py
|   |       |-- city_bus.py
|   |       |-- intersection.py
|   |       `-- updater.py
|   |-- trajectory/
|   |   |-- haversine.py
|   |   `-- dtw.py
|   |-- analysis/
|   |   |-- main.py
|   |   |-- extraction/
|   |   |   |-- api_info_bulider.py
|   |   |   |-- generation.py
|   |   |   |-- extractor.py
|   |   |   `-- similarity.py
|   |   |-- route/
|   |   |   |-- analyzer.py
|   |   |   `-- improvement.py
|   |   `-- region/
|   |       `-- region_analysis.py
|   |-- visualization/
|   |   `-- visualize.py
|   `-- prediction/
|       `-- GRU.ipynb
`-- .gitignore
```

`.gitignore` 기준으로 `data/`, `result/`, `.env`는 버전 관리 대상이 아닙니다. 즉, 실행에 필요한 데이터와 결과물은 저장소 외부에서 준비되어야 합니다.

## 프로젝트 목적

이 프로젝트의 목적은 "실제 공항 이동 경로가 대중교통 버스 후보 경로와 얼마나 다르게 움직였는가"를 측정하여 기존 공항 접근 경로의 개선 필요성을 구하는 것 입니다.

- 실제 이동 경로는 LGU+의 유동인구 데이터의 셀 단위 위치 로그 CSV에서 읽습니다.
- 버스 후보 경로는 Google Directions API의 `mode=transit`, `transit_mode=bus` 응답에서 생성합니다.
- 실제 경로와 후보 경로의 차이는 Haversine 기반 DTW로 계산합니다.
- 차이 패턴은 GMM으로 정상/이탈 구간을 분리해 개선 필요 여부를 판정합니다.
- 최종적으로 EMD_CODE 단위로 묶어 우선 검토해야 할 지역을 랭킹화합니다.

## 엔드 투 엔드 파이프라인

`src/main.py`의 순서는 아래와 같습니다.

1. `compress_folder(RAW_DATA_DIR, COMPRESSED_DATA_DIR)`
2. `cleaning_folder(COMPRESSED_DATA_DIR, CLEANING_DATA_DIR)`
3. `run_mapping()`
4. `makeEMD_folder(MAPPING_DATA_DIR, PROCESSED_DATA_DIR)`
5. `delete_outlier()`
6. `run_build_candidate_total_info_cache()`
7. `run_extract_best_routes()`
8. `run_analysis_routes()`
9. `run_analysis_regions()`
10. `run_visualization()`

### 1) 압축

`src/preprocess/compress.py`는 같은 `TRIP_NO` 안에서:

- 시간 순으로 정렬한 뒤, 속도와 셀id가 같은 연속 구간을 하나의 행으로 압축합니다.

입력:

- `data/raw/*.csv`

출력:

- `data/interim/compressed/*.csv`

### 2) 정제

`src/preprocess/cleaning.py`는 Haversine 거리와 시간 차이를 이용해 spike를 제거합니다.

정제 정책은 `src/config/policy.py`에 정의되어 있습니다.

- `max_speed_kmh = 120.0`
- `max_spike_distance_m = 2000.0`
- `min_trip_points = 20`

출력:

- `data/interim/cleaning/*.csv`
- `data/interim/cleaning/cleaning_summary.csv`

### 3) 버스 매핑

`src/mapping/main.py`는 정제된 이동 궤적을 공항버스/시내버스 정류장과 매핑합니다.

세부 로직:

- `src/mapping/bus/builder.py`: `TRIP_NO`별 trajectory 생성
- `src/mapping/bus/airport_bus.py`: 공항버스 정류장 매핑
- `src/mapping/bus/city_bus.py`: 시내버스 정류장 매핑
- `src/mapping/bus/intersection.py`: 교집합 기반 시내버스 노선 정제
- `src/mapping/bus/updater.py`: `BUS_ID`, `STATION`, `TRANSPORT_TYPE` 컬럼 반영

거리 기준은 `bus_threshold_m = 100`입니다.

출력:

- `data/mapping/*.csv`

### 4) EMD 코드 부여

`src/preprocess/makeEMD.py`는 `emd_WGS84.json`의 폴리곤과 경도와 위도를 비교해 각 행에 `EMD_CODE`를 부여합니다.

출력:

- `data/processed/*.csv`

### 5) 이상치 경로 제거

`src/preprocess/boxplot.py`는 공항 접근 시간 분포를 기반으로 outlier를 제거합니다.

중요 포인트:

- 공항 EMD 상수: `28110147`
- 지역별 body time 상한과 전체 tail time 상한을 IQR 방식으로 계산
- 조건을 넘는 trip을 제거한 뒤 전체 분석용 CSV 생성

출력:

- `data/access_time_boxplot.csv`
- `data/tail_access_time_boxplot.png`
- `data/filtered_all_trips.csv`

### 6) Google Directions API 후보 경로 캐시 생성

`src/analysis/extraction/api_info_bulider.py`와 `src/analysis/extraction/generation.py`가 후보 경로를 생성합니다.

API 설정:

- `mode=transit`
- `transit_mode=bus`
- `transit_routing_preference=fewer_transfers`
- `alternatives=true`
- `language=ko`

특이점:

- 오래된 경로는 추출이 불가함에 따라 실제 과거 시각을 그대로 넣지 않고, "내일 같은 시각"으로 출발 시각을 맞춰 API를 호출합니다.
- 응답 step 단위에서 거리, 시간, 시작/종료 좌표, polyline, 교통수단 정보를 펼쳐 저장합니다.

출력:

- `data/total_api_info.csv`

### 7) 최적 후보 경로 추출

`src/analysis/extraction/extractor.py`와 `src/analysis/extraction/similarity.py`는 실제 경로와 후보 경로를 비교해 최적 경로를 고릅니다.

핵심 알고리즘:

- 실제 경로 좌표 추출
- 후보 route별 polyline decode
- Haversine 기반 DTW cost 계산
- 최소 DTW route 선택
- 선택된 route에 대해 alignment, pointwise distance 저장

출력:

- `result/extraction/extracted_best_routes.csv`

주요 컬럼:

- `TRIP_NO`
- `EMD_CODE`
- `best_route_idx`
- `dtw`
- `alignment`
- `distances`

### 8) trip 단위 개선 필요 판정

`src/analysis/route/improvement.py`는 DTW 거리 시계열을 2개 군집 GMM으로 분리하고, 개선 필요 여부를 판단합니다.

기본 기준:

- `deviation_score_threshold = 0.2`
- `longest_deviation_threshold = 10`
- `longest_deviation_ratio_threshold = 0.1`
- `separation_threshold = 1.1`

`src/analysis/route/analyzer.py`는 각 trip에 대해 다음 지표를 저장합니다.

- `improve_required`
- `deviation_ratio`
- `mean_confidence`
- `longest_deviation`
- `longest_deviation_ratio`
- `separation`
- `is_deviated`

출력:

- `result/trip/routes_analysis_all_trips.csv`

### 9) region 단위 우선순위 분석

`src/analysis/region/region_analysis.py`는 `EMD_CODE`별로 trip 결과를 집계합니다.

핵심 방식:

- 최소 trip 수: `min_total_trips = 5`
- 개선 필요 비율의 Wilson lower bound 계산
- deviation 관련 지표 정규화
- 가중합으로 `severity_score` 계산

가중치:

- 개선 필요 비율 하한: `0.5`
- 평균 deviation ratio: `0.3`
- 평균 longest deviation ratio: `0.2`

출력:

- `result/region/region_analysis_all_trips.csv`

주요 컬럼:

- `total_trips`
- `improve_trips`
- `improve_ratio`
- `improve_ratio_lower_bound`
- `needs_attention`
- `severity_score`
- `priority_rank`

### 10) 시각화 리포트 생성

`src/visualization/visualize.py`는 지역 우선순위와 대표 사례를 시각화합니다.

생성 파일:

- `result/report_figures/top_regions_summary.csv`
- `result/report_figures/selected_case_trips.csv`
- `result/report_figures/01_top_regions_bar.png`
- `result/report_figures/02_region_priority_scatter.png`
- `result/report_figures/03_region_severity_map.png`
- `result/report_figures/04_top_region_trip_boxplot.png`
- `result/report_figures/05_policy_scatter.png`
- `result/report_figures/case_maps/<rank>_<EMD_NAME>/*_map.html`
- `result/report_figures/case_maps/<rank>_<EMD_NAME>/*_distance_profile.png`

## 설정 모듈

`src/config/settings.py`는 루트 경로와 데이터/결과 디렉터리를 정의합니다.

기준 경로:

- `BASE_DIR / data`
- `BASE_DIR / result`
- `BASE_DIR / .env`

필수 환경 변수:

```env
GOOGLE_MAPS_API_KEY=YOUR_API_KEY
```

`src/config/runtime.py`는 `torch.cuda.is_available()`로 실행 디바이스를 고릅니다.

- GPU가 있으면 `cuda`
- 없으면 `cpu`

## 데이터 로더

`src/data/loader.py` 기준으로 런타임에 필요한 주요 파일은 다음과 같습니다.

공개 데이터:

- `data/open/emd_WGS84.json`
- `data/open/` 아래의 시내버스 정류장/노선 정보 파일
- `data/open/` 아래의 공항버스 정류장/노선 정보 파일

파이프라인 산출물:

- `data/filtered_all_trips.csv`
- `data/total_api_info.csv`
- `result/extraction/extracted_best_routes.csv`
- `result/trip/routes_analysis_all_trips.csv`
- `result/region/region_analysis_all_trips.csv`

가공 중 추가되는 대표 컬럼:

- `BUS_ID`
- `STATION`
- `TRANSPORT_TYPE`
- `DPR_ADNG_NM`
- `EMD_CODE`

## 주요 의존 라이브러리

코드 import 기준 주요 패키지는 아래와 같습니다.

- pandas
- geopandas
- numpy
- matplotlib
- folium
- torch
- requests
- polyline
- python-dotenv
- tqdm
- shapely
- scikit-learn
- jupyter

## 예측 노트북

`src/prediction/GRU.ipynb`은 메인 파이프라인과 별도로 존재하는 실험성 예측 노트북입니다.

코드상 확인되는 흐름:

- `data/interim/compressed/*.csv`를 모아 trip 요약 피처 생성
- GRU 모델 학습
- 예측 결과와 잔차 시각화 저장
- 전체 시계열 예측 CSV 저장

생성 파일:

- `result/prediction/actual_vs_predicted.png`
- `result/prediction/residual_vs_predicted.png`
- `result/prediction/all_time_series_prediction.png`
- `result/prediction/gru_prediction.csv`

현재 `src/main.py`에서는 이 노트북을 호출하지 않습니다.

## 현재 저장소 기준 유의사항

- 보안상 `data/`와 `result/`는 커밋되지 않으므로, 저장소만 clone해서는 바로 실행되지 않습니다.
- Google Directions API 키가 없으면 후보 경로 생성 단계가 실패합니다.
- 시각화는 `Malgun Gothic` 폰트를 전제로 한 그래프 설정을 사용합니다.