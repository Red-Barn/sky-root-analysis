import pandas as pd

def time_to_datatime(df):
    df['DPR_MT1_UNIT_TM'] = pd.to_datetime(df['DPR_MT1_UNIT_TM'])
    return df

def transport_nan_to_none(df):
    df['TRANSPORT_TYPE'] = df['TRANSPORT_TYPE'].apply(lambda x: None if pd.isna(x) else x)
    return df

def group_py_NO(df):
    grouped = df.groupby('TRIP_NO')
    return grouped

def normal_create_trajectory(group):
    return group.sort_values('DPR_MT1_UNIT_TM')[['DYNA_DYN_KD_CD', 'DPR_MT1_UNIT_TM', 'DPR_CELL_XCRD', 'DPR_CELL_YCRD']].to_numpy()

def transport_create_trajectory(group):
    return group.sort_values('DPR_MT1_UNIT_TM')[['DYNA_DYN_KD_CD', 'DPR_MT1_UNIT_TM', 'DPR_CELL_XCRD', 'DPR_CELL_YCRD', 'TRANSPORT_TYPE']].to_numpy()

def normal_paths(df):
    """
    데이터프레임을 {TRIP_NO: trajectory} 형태의 딕셔너리로 변환합니다.
    trajectory는 시간순으로 정렬된 [DYNA_DYN_KD_CD, DPR_MT1_UNIT_TM, DPR_CELL_XCRD, DPR_CELL_YCRD]의 numpy 배열입니다.
    """
    df = time_to_datatime(df)
    grouped = group_py_NO(df)
    trajectories = {no: normal_create_trajectory(group) for no, group in grouped}
    return trajectories

def transport_path(df):
    """
    데이터프레임을 {TRIP_NO: trajectory} 형태의 딕셔너리로 변환합니다.
    trajectory는 시간순으로 정렬된 [DYNA_DYN_KD_CD, DPR_MT1_UNIT_TM, DPR_CELL_XCRD, DPR_CELL_YCRD, TRANSPORT_TYPE]의 numpy 배열입니다.
    단, 공항버스 이전의 경로를 구하기 위해 TRANSPORT_TYPE이 None이 아닌 첫 번째 지점 이전의 지점들로만 구성됩니다.
    """
    df = time_to_datatime(df)
    df = transport_nan_to_none(df)
    grouped = group_py_NO(df)
    trajectories = {no: transport_create_trajectory(group) for no, group in grouped}
    
    peopletraj = {}
    for key, values in trajectories.items():
        temp = []
        for value in values:
            if value[4] is not None:
                break
            temp.append(value)
        if temp:
            peopletraj[key] = temp
    return peopletraj