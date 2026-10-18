"""PCA (64 PCs, §4.2) and LEACE linear site removal (§4.3).

Both are fitted, for each fold v of the §2 split, on all steps of the 278-case set's training-fold cases (fold ≠ v)
and applied to the held-out fold. A fold-v nuisance or probe is trained on training cases transformed by the fold-v
maps (in-sample) and predicts held-out cases transformed by the same maps, so training and held-out features share one
coordinate system (PCs fitted on different folds are not comparable across folds). Output arrays are therefore indexed
by fold: rep[v] is every case transformed by the fold-v maps.

PCA: centred (not scaled); exact eigendecomposition of the covariance (chunked accumulation) when d ≤ 8192, otherwise
randomized SVD (scikit-learn randomized_svd, n_oversamples=64, n_iter=7, random_state from SeedSequence(20261006)
child "pca-randomized-svd", fold v); component signs fixed so that each component's largest-|loading| entry is
positive.

LEACE (Belrose et al. 2023, closed form): with Σ_XX, Σ_XZ the covariance of X and of X with the one-hot site
indicator Z, W = Σ_XX^{-1/2} (pseudo-inverse square root; eigenvalues ≤ 1e-12·max treated as zero), U an orthonormal
basis of col(W Σ_XZ), the eraser is r(x) = x − P (x − μ), P = W⁺ U Uᵀ W (an oblique projection, P² = P, and
(I − P) Σ_XZ = 0 on the fitting data).
"""
import numpy as np

from . import seeds
from .constants import N_PCS, SEED_FOLDS

EXACT_PCA_MAX_DIM = 8192


class PCA:
    def __init__(self, mean, components, explained_variance, total_variance):
        self.mean, self.components = mean, components
        self.explained_variance, self.total_variance = explained_variance, total_variance

    def transform(self, X):
        return (np.asarray(X, np.float64) - self.mean) @ self.components.T


def _sign_fix(V):
    idx = np.argmax(np.abs(V), axis=1)
    s = np.sign(V[np.arange(V.shape[0]), idx])
    s[s == 0] = 1.0
    return V * s[:, None]


def fit_pca(X, n_components=N_PCS, fold=0, chunk=20000):
    X = np.asarray(X)
    n, d = X.shape
    mean = np.zeros(d)
    for s in range(0, n, chunk):
        mean += X[s:s + chunk].sum(0, dtype=np.float64)
    mean /= n
    if d <= EXACT_PCA_MAX_DIM:
        C = np.zeros((d, d))
        for s in range(0, n, chunk):
            B = X[s:s + chunk].astype(np.float64) - mean
            C += B.T @ B
        C /= n - 1
        evals, evecs = np.linalg.eigh(C)
        order = np.argsort(evals)[::-1][:n_components]
        comps = _sign_fix(evecs[:, order].T)
        return PCA(mean, comps, evals[order], float(np.trace(C)))
    from sklearn.utils.extmath import randomized_svd
    rs = int(seeds.child(np.random.SeedSequence(SEED_FOLDS), "pca-randomized-svd", int(fold)).generate_state(1)[0])
    Xc = (X - mean.astype(X.dtype))
    _, S, Vt = randomized_svd(Xc, n_components, n_oversamples=64, n_iter=7, random_state=rs)
    total = float(sum(((X[s:s + chunk].astype(np.float64) - mean) ** 2).sum() for s in range(0, n, chunk)) / (n - 1))
    return PCA(mean, _sign_fix(Vt), S ** 2 / (n - 1), total)


class LEACE:
    def __init__(self, mean, P, rank):
        self.mean, self.P, self.rank = mean, P, rank

    def transform(self, X):
        X = np.asarray(X, np.float64)
        return X - (X - self.mean) @ self.P.T


def fit_leace(X, z):
    X = np.asarray(X, np.float64)
    levels, codes = np.unique(z, return_inverse=True)
    Z = np.zeros((len(z), len(levels))); Z[np.arange(len(z)), codes] = 1.0
    mean = X.mean(0)
    Xc = X - mean
    Zc = Z - Z.mean(0)
    n = len(X)
    Sxx = Xc.T @ Xc / n
    Sxz = Xc.T @ Zc / n
    evals, evecs = np.linalg.eigh(Sxx)
    keep = evals > 1e-12 * evals.max()
    W = (evecs[:, keep] / np.sqrt(evals[keep])) @ evecs[:, keep].T
    W_pinv = (evecs[:, keep] * np.sqrt(evals[keep])) @ evecs[:, keep].T
    M = W @ Sxz
    u, s, _ = np.linalg.svd(M, full_matrices=False)
    r = int((s > 1e-12 * max(s.max(), 1e-300)).sum())
    U = u[:, :r]
    P = W_pinv @ U @ U.T @ W
    return LEACE(mean, P, r), dict(Sxx=Sxx, Sxz=Sxz)


def leace_identities(leace, X, z):
    """Max-abs residuals of P² = P, (I − P) Σ_XZ = 0 and Cov(r(X), Z) = 0 on (X, z)."""
    X = np.asarray(X, np.float64)
    levels, codes = np.unique(z, return_inverse=True)
    Z = np.zeros((len(z), len(levels))); Z[np.arange(len(z)), codes] = 1.0
    Xc = X - X.mean(0)
    Sxz = Xc.T @ (Z - Z.mean(0)) / len(X)
    P = leace.P
    Xe = leace.transform(X)
    cov_e = (Xe - Xe.mean(0)).T @ (Z - Z.mean(0)) / len(X)
    return dict(idempotence=float(np.abs(P @ P - P).max()),
                erases_cross_cov=float(np.abs(Sxz - P @ Sxz).max()),
                erased_cov_with_site=float(np.abs(cov_e).max()))


def foldwise_reduce(case_reps, case_folds, case_sites, n_folds=5, n_components=N_PCS, with_leace=True):
    """case_reps: list (278) of (n_steps_i, d) arrays. Returns per-fold transformed lists and fit reports.

    out["R"][v][i] = PCA_v(case_reps[i]); out["R-C"][v][i] = LEACE_v(PCA_v(case_reps[i])).
    """
    case_folds = np.asarray(case_folds)
    out = {"R": [], "R-C": [], "report": []}
    for v in range(n_folds):
        train = np.flatnonzero(case_folds != v)
        Xtr = np.concatenate([case_reps[i] for i in train])
        pca = fit_pca(Xtr, n_components, fold=v)
        R = [pca.transform(x) for x in case_reps]
        rep = dict(fold=v, n_train_steps=int(len(Xtr)), pca_var_retained=float(pca.explained_variance.sum()
                                                                               / pca.total_variance))
        out["R"].append(R)
        if with_leace:
            ztr = np.concatenate([np.full(len(case_reps[i]), case_sites[i]) for i in train])
            Rtr = np.concatenate([R[i] for i in train])
            le, _ = fit_leace(Rtr, ztr)
            RC = [le.transform(r) for r in R]
            Rtr_e = np.concatenate([RC[i] for i in train])
            rep.update(leace_rank=le.rank, leace_dim_retained=int(n_components - le.rank),
                       leace_var_retained=float(np.trace(np.cov(Rtr_e.T)) / np.trace(np.cov(Rtr.T))),
                       leace_identities=leace_identities(le, Rtr, ztr))
            out["R-C"].append(RC)
        out["report"].append(rep)
    return out
