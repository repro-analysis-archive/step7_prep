"""Cross-fitted sequentially doubly robust (SDR) estimator of Ψ(δ) − Ψ(1) for the multiplicative MTP d(a) = δa (§9).

Implementation note N6/N7. Treatment times are the K window steps t = 0..K-1 (trajectory column W + t). At step t the
nuisances condition on H_t = all past synthetic actions of the trajectory (columns 0..W+t-1: pre-window and earlier
window steps) and on the arm's step-t covariates X_t only (§8). Post-window actions are not intervened on and are not
conditioned on (they lie after the last treatment time and are part of the outcome process).
``X_steps`` is a list of K arrays (n, p_t), or a dict {fold: list} for representation arms, whose fold-v features come
from the fold-v PCA / LEACE maps (reduce.py).

For each outer fold v (the fixed §2 fold labels of the analysis set):
  1. density ratios r_t = g^d(A_t | F_t) / g(A_t | F_t) by probabilistic classification of the stacked rows
     (A_t, F_t; Λ = 0) and (δA_t, F_t; Λ = 1) fitted on the training cases; r_t = exp(logit) (no trimming);
  2. backward sequential regression with V_K = Y and, for t = K-1..0, m_t = E[V_{t+1} | A_t, F_t] fitted on the
     training cases, then V_t = m_t(δA_t, F_t) + r_t (V_{t+1} − m_t(A_t, F_t)), evaluated for the training cases
     (in-sample, for the next regression) and the held-out cases.
Ψ̂(δ) = mean V_0 (held-out); Ψ̂(1) = mean Y; contrast influence function IF_i = V_0,i − Y_i; SE = sd(IF)/sqrt(n);
95 % Wald interval.
"""
import numpy as np

from . import seeds
from .constants import DELTA, Z_975
from .learners import fit_classifier, fit_outcome


def _features(A, X_steps, W, t):
    H = A[:, :W + t]
    X = X_steps[t]
    return np.hstack([H, X]) if X is not None and X.shape[1] else H


def sdr_mtp(A, Y, X_steps, W, K, folds, seq, mode="select", delta=DELTA):
    n = len(Y)
    V0 = np.full(n, np.nan)
    R = np.full((n, K), np.nan)
    chosen = {"outcome_mlp": 0, "ratio_mlp": 0, "fits": 0}
    for v in np.unique(folds):
        tr = np.flatnonzero(folds != v)
        te = np.flatnonzero(folds == v)
        ntr = len(tr)
        r_tr = np.empty((ntr, K))
        r_te = np.empty((len(te), K))
        Xv = X_steps[int(v)] if isinstance(X_steps, dict) else X_steps
        feats = [_features(A, Xv, W, t) for t in range(K)]
        for t in range(K):
            a, F = A[:, W + t], feats[t]
            Xs = np.vstack([np.column_stack([a[tr], F[tr]]), np.column_stack([delta * a[tr], F[tr]])])
            lab = np.r_[np.zeros(ntr), np.ones(ntr)]
            grp = np.r_[np.arange(ntr), np.arange(ntr)]
            clf, info = fit_classifier(Xs, lab, grp, seeds.rng(seq, "ratio", t, int(v)), mode)
            chosen["ratio_mlp"] += info["learner"] == "mlp"
            r_tr[:, t] = np.exp(clf.logit(np.column_stack([a[tr], F[tr]])))
            r_te[:, t] = np.exp(clf.logit(np.column_stack([a[te], F[te]])))
        V_tr = Y[tr].astype(np.float64).copy()
        V_te = Y[te].astype(np.float64).copy()
        for t in reversed(range(K)):
            a, F = A[:, W + t], feats[t]
            X_tr = np.column_stack([a[tr], F[tr]])
            reg, info = fit_outcome(X_tr, V_tr, np.arange(ntr), seeds.rng(seq, "outcome", t, int(v)), mode)
            chosen["outcome_mlp"] += info["learner"] == "mlp"
            chosen["fits"] += 1
            m_tr = reg.predict(X_tr)
            md_tr = reg.predict(np.column_stack([delta * a[tr], F[tr]]))
            m_te = reg.predict(np.column_stack([a[te], F[te]]))
            md_te = reg.predict(np.column_stack([delta * a[te], F[te]]))
            V_tr = md_tr + r_tr[:, t] * (V_tr - m_tr)
            V_te = md_te + r_te[:, t] * (V_te - m_te)
        V0[te] = V_te
        R[te] = r_te
    IF = V0 - Y
    est = float(IF.mean())
    se = float(IF.std(ddof=1) / np.sqrt(n))
    cum = np.cumprod(R, axis=1)
    with np.errstate(all="ignore"):
        ess = (cum.sum(0) ** 2 / (cum ** 2).sum(0)) / n
    finite = bool(np.isfinite(R).all() and np.isfinite(V0).all() and np.isfinite(se))
    return dict(est=est, se=se, ci_lo=est - Z_975 * se, ci_hi=est + Z_975 * se, psi_delta=float(V0.mean()),
                psi_one=float(Y.mean()), ratio_min=float(np.nanmin(R)), ratio_max=float(np.nanmax(R)),
                ratio_all_finite_positive=bool(np.isfinite(R).all() and (R > 0).all()),
                ess_min=float(np.nanmin(ess)), cumratio_max=float(np.nanmax(cum)),
                support_failure=not (finite and (R > 0).all()), n_outcome_fits=chosen["fits"],
                n_outcome_mlp=int(chosen["outcome_mlp"]), n_ratio_mlp=int(chosen["ratio_mlp"]))
