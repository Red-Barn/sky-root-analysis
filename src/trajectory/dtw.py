import numpy as np
from src.trajectory.haversine import haversine_dtw

EARTH_R = 6371000.0

def coords_to_rad(coords):
    arr = np.asarray(coords, dtype=np.float32)
    lat = np.deg2rad(arr[:, 0]).astype(np.float32, copy=False)
    lon = np.deg2rad(arr[:, 1]).astype(np.float32, copy=False)
    return lat, lon


def dtw_cost_haversine(actual_coords, route_coords, cutoff=np.inf):
    latA, lonA = coords_to_rad(actual_coords)
    latR, lonR = coords_to_rad(route_coords)

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

        row = haversine_dtw(
            latA[i - 1], lonA[i - 1], cos_latA[i - 1],
            latR, lonR, cos_latR
        )

        row_min = np.inf
        for j in range(1, M + 1):
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

        if row_min > cutoff:
            return float("inf")

        prev, curr = curr, prev

    return float(prev[M])


def dtw_path_haversine(actual_coords, route_coords):
    latA, lonA = coords_to_rad(actual_coords)
    latR, lonR = coords_to_rad(route_coords)

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

        row = haversine_dtw(
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