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
                ])
            )
            
    i, j = N, M
    alignment = []

    while i > 0 and j > 0:
        alignment.append((i - 1, j - 1))

        candidates = torch.stack([
            R[i - 1, j - 1],  # diagonal
            R[i - 1, j],      # up
            R[i, j - 1]       # left
        ])

        move = torch.argmin(candidates).item()

        if move == 0:
            i -= 1
            j -= 1
        elif move == 1:
            i -= 1
        else:
            j -= 1

    alignment.reverse()
    
    distances = torch.tensor([
        D[i, j] for i, j in alignment
    ])

    return R[N, M], alignment, distances
