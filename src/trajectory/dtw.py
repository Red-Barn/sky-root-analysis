import numpy as np

EARTH_R = 6371000.0  # 기존 cdist와 동일 (미터)


def _coords_to_rad(coords):
    """
    coords: [(lat, lon), ...] in degrees
    return: lat_rad(float32), lon_rad(float32)
    """
    arr = np.asarray(coords, dtype=np.float32)
    lat = np.deg2rad(arr[:, 0]).astype(np.float32, copy=False)
    lon = np.deg2rad(arr[:, 1]).astype(np.float32, copy=False)
    return lat, lon


def _haversine_row(lat1, lon1, cos_lat1, lat2, lon2, cos_lat2):
    """
    lat1, lon1: scalar radians (float32)
    lat2, lon2: vectors radians (float32)
    cos_lat1: scalar, cos(lat1)
    cos_lat2: vector, cos(lat2)
    return: distances (M,) float32 in meters
    """
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    sin_dlat = np.sin(dlat * 0.5)
    sin_dlon = np.sin(dlon * 0.5)

    a = sin_dlat * sin_dlat + cos_lat1 * cos_lat2 * (sin_dlon * sin_dlon)
    c = 2.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a))
    return (EARTH_R * c).astype(np.float32, copy=False)


def dtw_cost_haversine(actual_coords, route_coords, cutoff=np.inf):
    """
    exact DTW cost만 계산 (alignment/distances 없음)
    cutoff: 현재 best보다 커질 게 확실하면 조기 중단(정답 불변)
    """
    latA, lonA = _coords_to_rad(actual_coords)
    latR, lonR = _coords_to_rad(route_coords)

    N = latA.shape[0]
    M = latR.shape[0]
    if N == 0 or M == 0:
        return float("inf")

    cos_latA = np.cos(latA)
    cos_latR = np.cos(latR)

    prev = np.full(M + 1, np.inf, dtype=np.float32)
    curr = np.full(M + 1, np.inf, dtype=np.float32)
    prev[0] = 0.0

    for i in range(1, N + 1):
        curr[0] = np.inf

        row = _haversine_row(
            latA[i - 1], lonA[i - 1], cos_latA[i - 1],
            latR, lonR, cos_latR
        )

        row_min = np.inf
        for j in range(1, M + 1):
            # tie-breaking: diag -> up -> left (기존 torch.argmin과 동일한 우선순위)
            diag = prev[j - 1]
            up = prev[j]
            left = curr[j - 1]

            m = diag
            if up < m:
                m = up
            if left < m:
                m = left

            v = row[j - 1] + m
            curr[j] = v
            if v < row_min:
                row_min = v

        # exact pruning: 비용은 누적합(>=0)이라 row_min이 cutoff보다 크면 더 좋아질 수 없음
        if row_min > cutoff:
            return float("inf")

        prev, curr = curr, prev

    return float(prev[M])


def dtw_path_haversine(actual_coords, route_coords):
    """
    exact DTW cost + alignment + (alignment 경로의 거리들) 반환
    distances는 기존 improvement.py 호환 위해 CPU torch tensor로 반환
    """
    latA, lonA = _coords_to_rad(actual_coords)
    latR, lonR = _coords_to_rad(route_coords)

    N = latA.shape[0]
    M = latR.shape[0]
    if N == 0 or M == 0:
        return float("inf"), [], np.empty((0,), dtype=np.float32)

    cos_latA = np.cos(latA)
    cos_latR = np.cos(latR)

    prev = np.full(M + 1, np.inf, dtype=np.float32)
    curr = np.full(M + 1, np.inf, dtype=np.float32)

    # backpointer (0:diag, 1:up, 2:left)
    steps = np.empty((N, M), dtype=np.int8)

    prev[0] = 0.0

    for i in range(1, N + 1):
        curr[0] = np.inf

        row = _haversine_row(
            latA[i - 1], lonA[i - 1], cos_latA[i - 1],
            latR, lonR, cos_latR
        )

        for j in range(1, M + 1):
            diag = prev[j - 1]
            up = prev[j]
            left = curr[j - 1]

            # tie-breaking: diag -> up -> left
            if diag <= up and diag <= left:
                m = diag
                step = 0
            elif up <= left:
                m = up
                step = 1
            else:
                m = left
                step = 2

            curr[j] = row[j - 1] + m
            steps[i - 1, j - 1] = step

        prev, curr = curr, prev

    cost = float(prev[M])

    # backtrack
    i = N - 1
    j = M - 1
    alignment = []
    while True:
        alignment.append((i, j))
        if i == 0 and j == 0:
            break
        step = steps[i, j]
        if step == 0:
            i -= 1
            j -= 1
        elif step == 1:
            i -= 1
        else:
            j -= 1
    alignment.reverse()

    # distances along alignment (vectorized)
    ii = np.fromiter((p[0] for p in alignment), dtype=np.int64, count=len(alignment))
    jj = np.fromiter((p[1] for p in alignment), dtype=np.int64, count=len(alignment))

    lat1 = latA[ii]; lon1 = lonA[ii]
    lat2 = latR[jj]; lon2 = lonR[jj]
    cos1 = np.cos(lat1); cos2 = np.cos(lat2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1
    sin_dlat = np.sin(dlat * 0.5)
    sin_dlon = np.sin(dlon * 0.5)

    a = sin_dlat * sin_dlat + cos1 * cos2 * (sin_dlon * sin_dlon)
    c = 2.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a))
    distances = (EARTH_R * c).astype(np.float32, copy=False)

    return cost, alignment, distances