import torch

def cdist(coords1, coords2):
    # 지구 반지름 (미터)
    R = 6371000.0

    lon1, lat1 = torch.deg2rad(coords1[:, 0]), torch.deg2rad(coords1[:, 1])
    lon2, lat2 = torch.deg2rad(coords2[:, 0]), torch.deg2rad(coords2[:, 1])
    
    dlon = lon2.unsqueeze(0) - lon1.unsqueeze(1)
    dlat = lat2.unsqueeze(0) - lat1.unsqueeze(1)
    
    # Haversine 공식 적용
    a = torch.sin(dlat / 2)**2 + torch.cos(lat1.unsqueeze(1)) * torch.cos(lat2.unsqueeze(0)) * torch.sin(dlon / 2)**2
    c = 2 * torch.atan2(torch.sqrt(a), torch.sqrt(1 - a))
    
    distance = R * c
    
    return distance