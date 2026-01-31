import pandas as pd
import numpy as np
from shapely.geometry import Point, Polygon, MultiPolygon
from tqdm import tqdm
from pathlib import Path

from src.data.loader import load_emd

def makeEMD_folder(input_dir: Path, output_dir: Path):
    emdDF = load_emd()["features"]
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for file_path in tqdm(list(input_dir.glob("*.csv")), desc="Making EMD files", position=0):
        df = pd.read_csv(file_path)
        makeEMD_df = makeEMD_dataframe(df, emdDF)
        output_path = output_dir / file_path.name
        makeEMD_df.to_csv(output_path, index=False)

def makeEMD_dataframe(df: pd.DataFrame, emdDF) -> pd.DataFrame:
    result = []
    df = df.copy()
    
    for data in emdDF:
        name = data['properties']['EMD_KOR_NM']
        code = data['properties']['EMD_CD']
        if data['geometry']:
            if data['geometry']['type'] == "Polygon":
                polygon = Polygon(np.round(np.float64(data['geometry']['coordinates'][0]), decimals = 9))
            else:
                polygons = [Polygon(np.round(np.float64(coords[0]), decimals = 9)) for coords in data['geometry']['coordinates']]
                polygon = MultiPolygon(polygons)
                
        result.append([name, code, polygon])
        
    df['EMD_CODE'] = None
    
    for index, row in tqdm(df.iterrows(), total=len(df), desc="Checking EMD", position=1, leave=False):
        point = Point(np.round(np.float64(row['DPR_CELL_XCRD']), decimals = 9), np.round(np.float64(row['DPR_CELL_YCRD']), decimals = 9))

        for name, code, polygon in result:
            if polygon.contains(point):
                df.at[index, 'DPR_ADNG_NM'] = name
                df.at[index, 'EMD_CODE'] = code
                break
            
    df = df.dropna(subset=['EMD_CODE']).reset_index(drop=True)
    return df