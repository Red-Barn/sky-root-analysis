import torch

def cdtw(D, gamma=1.0):
    N, M = D.shape
    device = D.device

    R = torch.full((N + 1, M + 1), float('inf'), device=device)
    R[0, 0] = 0

    for i in range(1, N + 1):
        for j in range(1, M + 1):
            R[i, j] = D[i - 1, j - 1] + torch.min(
                torch.stack([
                    R[i - 1, j - 1],
                    R[i - 1, j],
                    R[i, j - 1]
                ]))

    return R[N, M]
