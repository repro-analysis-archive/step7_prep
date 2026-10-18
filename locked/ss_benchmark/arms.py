"""Adjustment arms (§8): step-t covariates of each arm (H_t is added by the estimator).

ASCII arm names: "FM-P-C" = FM-P−C, "ORACLE-C" = ORACLE−C, etc. C enters as three centre dummies (lowest label is
the reference level). Representation arms read R_t (64 PCs) or R_t^(−C) at window step t from ``reps[key]``, an array
(n_folds, n, K_max, 64) over window steps 0..K_max-1, where reps[key][v] holds the fold-v PCA / LEACE features
(reduce.py); the same for every replicate (same videos and representations, §10.2). Representation arms therefore
return {fold: list of K arrays}; the other arms return one list of K arrays.
"""
import numpy as np

ARMS = ("NV", "SITE", "FM-P", "FM-P-C", "FM-S", "FM-S-C", "REF", "REF-C", "FM-P-nat", "ORACLE-C", "ORACLE", "FULL")
REP_KEY = {"FM-P": "P", "FM-P-C": "P-C", "FM-S": "S", "FM-S-C": "S-C", "REF": "REF", "REF-C": "REF-C",
           "FM-P-nat": "P-nat"}
SENSITIVITY_ARMS = {"single_file": ("NV", "SITE", "FM-P", "FM-P-C"),
                    "W0": ("NV", "SITE", "FM-P", "FM-P-C", "ORACLE", "ORACLE-C"),
                    "W5": ("NV", "SITE", "FM-P", "FM-P-C", "ORACLE", "ORACLE-C")}


def centre_dummies(design) -> np.ndarray:
    levels, codes = design.centre_codes()
    D = np.zeros((design.n, len(levels) - 1))
    for k in range(1, len(levels)):
        D[:, k - 1] = codes == k
    return D


def arm_covariates(arm, design, cell, draws, reps=None):
    """List of K arrays (n, p_arm) with the arm's step-t covariates; p_arm may be 0."""
    K, n = cell.K, design.n
    if arm in REP_KEY:
        R = reps[REP_KEY[arm]]
        return {v: [np.ascontiguousarray(R[v][:, t, :], dtype=np.float64) for t in range(K)] for v in range(len(R))}
    S = design.state(np.arange(K))
    C = centre_dummies(design)
    out = []
    for t in range(K):
        if arm == "NV":
            X = np.zeros((n, 0))
        elif arm == "SITE":
            X = C
        elif arm == "ORACLE-C":
            X = S[:, t:t + 1]
        elif arm == "ORACLE":
            X = np.hstack([S[:, t:t + 1], C])
        elif arm == "FULL":
            X = np.hstack([S[:, t:t + 1], C, draws["U"][:, None]])
        else:
            raise ValueError(arm)
        out.append(np.ascontiguousarray(X, dtype=np.float64))
    return out
