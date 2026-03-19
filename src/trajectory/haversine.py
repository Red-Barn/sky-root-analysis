import torch
import numpy as np

EARTH_R = 6371000.0

def harversine_torch(coords1, coords2):
    lon1, lat1 = torch.deg2rad(coords1[:, 0]), torch.deg2rad(coords1[:, 1])
    lon2, lat2 = torch.deg2rad(coords2[:, 0]), torch.deg2rad(coords2[:, 1])
    dlon = lon2.unsqueeze(0) - lon1.unsqueeze(1)
    dlat = lat2.unsqueeze(0) - lat1.unsqueeze(1)
    a = torch.sin(dlat / 2)**2 + torch.cos(lat1.unsqueeze(1)) * torch.cos(lat2.unsqueeze(0)) * torch.sin(dlon / 2)**2
    c = 2 * torch.atan2(torch.sqrt(a), torch.sqrt(1 - a))
    
    distance = EARTH_R * c
    return distance


def harversine_numpy(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0) ** 2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a))
    
    distance = EARTH_R * c
    return distance


def haversine_dtw(lat1, lon1, cos_lat1, lat2, lon2, cos_lat2):
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    sin_dlat = np.sin(dlat * 0.5)
    sin_dlon = np.sin(dlon * 0.5)
    a = sin_dlat * sin_dlat + cos_lat1 * cos_lat2 * (sin_dlon * sin_dlon)
    c = 2.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a))
    
    distance = (EARTH_R * c).astype(np.float32, copy=False)
    return distance


def haversine_pairs_rad(lat1, lon1, lat2, lon2):
    cos1 = np.cos(lat1)
    cos2 = np.cos(lat2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    sin_dlat = np.sin(dlat * 0.5)
    sin_dlon = np.sin(dlon * 0.5)
    a = sin_dlat * sin_dlat + cos1 * cos2 * (sin_dlon * sin_dlon)
    a = np.clip(a, 0.0, 1.0)
    c = 2.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a))
    return (EARTH_R * c).astype(np.float32, copy=False)


def haversine_pair_rad(lat1, lon1, cos1, lat2, lon2, cos2):
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    sin_dlat = np.sin(dlat * 0.5)
    sin_dlon = np.sin(dlon * 0.5)
    a = sin_dlat * sin_dlat + cos1 * cos2 * (sin_dlon * sin_dlon)
    a = np.clip(a, 0.0, 1.0)
    c = 2.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a))
    return np.float32(EARTH_R * c)