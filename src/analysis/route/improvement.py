import numpy as np
from sklearn.mixture import GaussianMixture

def gmm_deviation_clusters(distances):
    X = distances.reshape(-1, 1)  # (N, 1)
    
    gmm = GaussianMixture(
        n_components=2,     # normal / deviation
        covariance_type='full',
        random_state=0)
    gmm.fit(X)
    
    labels = gmm.predict(X)  # (N,)
    means = gmm.means_.flatten()  # (2,)
    
    normal_label = np.argmin(means)
    dev_label = np.argmax(means)
    
    return labels, normal_label, dev_label, gmm

def longest_run(mask):
    max_run, cur = 0, 0
    for v in mask:
        if v:
            cur += 1
            max_run = max(max_run, cur)
        else:
            cur = 0
    return max_run

def is_improvement_required(distances, policy):
    labels, normal_label, dev_label, gmm = gmm_deviation_clusters(distances)
    is_deviated = (labels == dev_label)
    
    probs = gmm.predict_proba(distances.reshape(-1, 1))
    mean_conf = probs[:, dev_label][is_deviated].mean() if is_deviated.any() else 0.0
    
    deviation_ratio = is_deviated.mean()
    deviation_score = deviation_ratio * mean_conf
    
    point_count = len(distances)
    longest_deviation = longest_run(is_deviated)
    longest_deviation_ratio = longest_deviation / point_count
    
    mu = gmm.means_.flatten()
    sigma = np.sqrt(gmm.covariances_.flatten())
    separation = abs(mu[0] - mu[1]) / (sigma[0] + sigma[1] + 1e-12)
    
    need_improvement = (
        deviation_score >= policy.deviation_score_threshold and
        longest_deviation >= policy.longest_deviation_threshold and
        separation >= policy.separation_threshold
    )
    
    return {
        "need_improvement": need_improvement,
        "deviation_ratio": deviation_ratio,
        "mean_confidence": mean_conf,
        "longest_deviation": longest_deviation,
        "longest_deviation_ratio": longest_deviation_ratio,
        "separation": separation,
        "is_deviated": is_deviated.tolist(),
    }