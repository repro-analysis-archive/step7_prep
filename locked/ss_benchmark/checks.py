"""Pre-causal checks (§5): E1, E2, E3-site / E3-state-retention, the fixed MLP probe, and G-SITE (§5.4).

Shared settings (§5): folds of §2 (restricted to the set); fold-v probes are trained on the set's training-fold cases
and predict its held-out fold, both transformed by the fold-v PCA / LEACE maps (reduce.py). Site probes are per step;
a case's prediction is the mean predicted probability over its steps (argmax); balanced accuracy over cases. CIs:
case bootstrap stratified by site, 2,000 resamples, seed 20261008 (named child stream per check; N10 for the bounds).
Learners: linear site probe = multinomial L2 logistic, penalty by inner 5-fold group CV over {1e-4..1e2} (N9); E2 =
binary L2 logistic, same grid; MLP probe = 256-unit one-hidden-layer MLP (§5.3, N1-N2). Inner-CV splits and MLP
initialisation use streams of SeedSequence(20261006) child "probe" (check, set, arm, fold).
E2 base: natural cubic spline of elapsed time (step index; spline span is invariant to the affine map to seconds), 4 df:
boundary knots at the training-fold min / max and interior knots at the training-fold 25 / 50 / 75 % quantiles
(truncated-power basis of Hastie et al., ESL eq. 5.4-5.5, without the constant).

Reporting-only quantities (never used by a pass / fail rule, model selection, nuisance fitting or family verdict):
* pre-removal MLP site probe (§4.3 "site decodability before and after (linear probe and 2-layer MLP probe)");
* E2 secondary on all steps of the 278 videos (§5.2), with S_t = 1{t ≥ s_i};
* E2 secondary with past synthetic actions in the baseline (§5.2): reference DGP cell K = 5, P = 0, W = 5,
  α = 0.5, γ = 1, φ_A = 0, "replicate 1" = the first replicate (spawn index 0) of that grid cell; rows = the K window
  steps of the primary set; H_t = the past actions as lags 1..W+K−1 (lag ℓ = A at window-relative step t − ℓ),
  lags before the trajectory start set to the DGP's initial value 0 (§6); base = spline(elapsed time) + H_t,
  full = base + R_t;
* the normalised-time stricter reference (§5.2): the E2 comparison with elapsed time replaced by t / n_i (n_i = the
  case's number of steps; uses future information, not a valid baseline);
* near-uniform frames (§3.1 step 4): proportion of flagged grid frames by centre, by S and by centre × S.
"""
import numpy as np
import pandas as pd

from . import seeds
from .constants import (E1_BA, E1_LOWER, E2_DELTA_AUC, E3_RETENTION, E3_UPPER, GSITE_MAX_ETA2, MLP_PROBE, N_BOOTSTRAP,
                        PENALTY_GRID_E2, SEED_BOOTSTRAP, SEED_FOLDS)
from .learners import MLP, fit_logistic_cv, fit_multinomial_cv


# ---------------------------------------------------------------------------------------------------------------------
# metrics and bootstrap
# ---------------------------------------------------------------------------------------------------------------------
def balanced_accuracy(y, pred, weights=None, classes=None):
    y, pred = np.asarray(y), np.asarray(pred)
    w = np.ones(len(y)) if weights is None else np.asarray(weights, float)
    classes = np.unique(y) if classes is None else classes
    rec = [np.sum(w * ((y == k) & (pred == k))) / np.sum(w * (y == k)) for k in classes if np.sum(w * (y == k)) > 0]
    return float(np.mean(rec))


def weighted_auc(y, s, w=None):
    y = np.asarray(y, float); s = np.asarray(s, float)
    w = np.ones(len(y)) if w is None else np.asarray(w, float)
    order = np.argsort(s, kind="mergesort")
    s, y, w = s[order], y[order], w[order]
    _, start = np.unique(s, return_index=True)
    wp = np.add.reduceat(w * y, start)
    wn = np.add.reduceat(w * (1 - y), start)
    below = np.cumsum(wn) - wn
    return float(np.sum(wp * (below + 0.5 * wn)) / (wp.sum() * wn.sum()))


def bootstrap_case_weights(case_sites, n_boot, rng):
    """(n_boot, n_cases) multiplicity matrix of a case bootstrap stratified by site."""
    case_sites = np.asarray(case_sites)
    Wt = np.zeros((n_boot, len(case_sites)))
    for site in np.unique(case_sites):
        idx = np.flatnonzero(case_sites == site)
        draws = rng.integers(0, len(idx), size=(n_boot, len(idx)))
        for b in range(n_boot):
            Wt[b] += np.bincount(idx[draws[b]], minlength=len(case_sites))
    return Wt


def boot_rng(name, root=SEED_BOOTSTRAP):
    return seeds.rng(np.random.SeedSequence(root), name)


def probe_rng(*names, root=SEED_FOLDS):
    return seeds.rng(np.random.SeedSequence(root), "probe", *names)


# ---------------------------------------------------------------------------------------------------------------------
# site probes (E1, E3-site)
# ---------------------------------------------------------------------------------------------------------------------
def site_probe_case_predictions(rep_by_fold, case_idx, case_sites, case_folds, steps_of, kind, tag, root=SEED_FOLDS):
    """Out-of-fold case-level site predictions.

    rep_by_fold[v][i]: (n_steps_i, d) features of case i under the fold-v maps; case_idx: cases of the set;
    steps_of(i): row indices of case i's steps used by the set (e.g. the analysis region); kind: 'linear' | 'mlp'.
    """
    case_idx = np.asarray(case_idx)
    sites = np.asarray(case_sites)[case_idx]
    classes = np.unique(np.asarray(case_sites))
    folds = np.asarray(case_folds)[case_idx]
    pred = np.empty(len(case_idx), dtype=classes.dtype)
    for v in np.unique(folds):
        tr = case_idx[folds != v]
        te_pos = np.flatnonzero(folds == v)
        X = np.concatenate([rep_by_fold[v][i][steps_of(i)] for i in tr])
        y = np.concatenate([np.full(len(steps_of(i)), case_sites[i]) for i in tr])
        g = np.concatenate([np.full(len(steps_of(i)), i) for i in tr])
        rng = probe_rng(tag, kind, int(v), root=root)
        if kind == "linear":
            model = fit_multinomial_cv(X, y, g, rng, PENALTY_GRID_E2)
            model_classes = model.classes
        else:
            yk = np.searchsorted(classes, y)
            model = MLP("multi", **MLP_PROBE).fit(X, yk, rng, g, n_classes=len(classes))
            model_classes = classes
        for p in te_pos:
            i = case_idx[p]
            prob = model.predict_proba(rep_by_fold[v][i][steps_of(i)]).mean(0)
            pred[p] = model_classes[int(np.argmax(prob))]
    return sites, pred


def ba_with_ci(sites, pred, boot_name, n_boot=N_BOOTSTRAP, root=SEED_BOOTSTRAP):
    classes = np.unique(sites)
    ba = balanced_accuracy(sites, pred, classes=classes)
    Wt = bootstrap_case_weights(sites, n_boot, boot_rng(boot_name, root))
    boots = np.array([balanced_accuracy(sites, pred, Wt[b], classes) for b in range(n_boot)])
    return dict(ba=ba, lo_2p5=float(np.percentile(boots, 2.5)), hi_97p5=float(np.percentile(boots, 97.5)),
                upper_one_sided_95=float(np.percentile(boots, 95.0)), n_cases=int(len(sites)))


def e1(rep_by_fold, case_idx, case_sites, case_folds, steps_of, tag, roots=(SEED_FOLDS, SEED_BOOTSTRAP)):
    s, p = site_probe_case_predictions(rep_by_fold, case_idx, case_sites, case_folds, steps_of, "linear", tag, roots[0])
    r = ba_with_ci(s, p, f"E1:{tag}", root=roots[1])
    r["pass"] = bool(r["ba"] >= E1_BA and r["lo_2p5"] > E1_LOWER)
    return r


def e3_site(repC_by_fold, case_idx, case_sites, case_folds, steps_of, tag, roots=(SEED_FOLDS, SEED_BOOTSTRAP)):
    out = {}
    for kind in ("linear", "mlp"):
        s, p = site_probe_case_predictions(repC_by_fold, case_idx, case_sites, case_folds, steps_of, kind,
                                           f"E3:{tag}", roots[0])
        out[kind] = ba_with_ci(s, p, f"E3:{tag}:{kind}", root=roots[1])
    out["pass"] = bool(out["linear"]["upper_one_sided_95"] <= E3_UPPER)
    out["mlp_exceeds_margin"] = bool(out["mlp"]["upper_one_sided_95"] > E3_UPPER)
    return out


# ---------------------------------------------------------------------------------------------------------------------
# E2 state recovery beyond time
# ---------------------------------------------------------------------------------------------------------------------
def ns_basis(x, knots):
    x = np.asarray(x, float)
    k = np.unique(np.asarray(knots, float))
    K = len(k)

    def d(j):
        return (np.maximum(x - k[j], 0) ** 3 - np.maximum(x - k[K - 1], 0) ** 3) / (k[K - 1] - k[j])

    return np.column_stack([x] + [d(j) - d(K - 2) for j in range(K - 2)])


def spline_knots(x_train):
    x = np.asarray(x_train, float)
    return [x.min(), *np.quantile(x, [0.25, 0.5, 0.75]), x.max()]


def e2_auc(rows, rep_by_fold, case_folds, case_sites, tag, extra=None, roots=(SEED_FOLDS, SEED_BOOTSTRAP),
           n_boot=N_BOOTSTRAP):
    """rows: DataFrame with columns case (index into rep arrays), step (row index into the case's rep), time, S.

    extra: optional (n_rows, q) array added to the base (E2 secondary with H). Returns AUCs, ΔAUC and its CI.
    """
    case = rows.case.to_numpy()
    folds = np.asarray(case_folds)[case]
    y = rows.S.to_numpy().astype(float)
    p_base = np.empty(len(rows)); p_full = np.empty(len(rows))
    for v in np.unique(folds):
        tr = np.flatnonzero(folds != v); te = np.flatnonzero(folds == v)
        knots = spline_knots(rows.time.to_numpy()[tr])
        B = ns_basis(rows.time.to_numpy(), knots)
        if extra is not None:
            B = np.hstack([B, extra])
        R = np.vstack([rep_by_fold[v][c][s] for c, s in zip(case, rows.step.to_numpy())])
        F = np.hstack([B, R])
        rng = probe_rng(tag, "E2", int(v), root=roots[0])
        mb = fit_logistic_cv(B[tr], y[tr], case[tr], rng, PENALTY_GRID_E2)
        mf = fit_logistic_cv(F[tr], y[tr], case[tr], rng, PENALTY_GRID_E2)
        p_base[te] = mb.logit(B[te]); p_full[te] = mf.logit(F[te])
    auc_b, auc_f = weighted_auc(y, p_base), weighted_auc(y, p_full)
    ucase, inv = np.unique(case, return_inverse=True)
    Wt = bootstrap_case_weights(np.asarray(case_sites)[ucase], n_boot, boot_rng(f"E2:{tag}", roots[1]))
    d = np.array([weighted_auc(y, p_full, Wt[b][inv]) - weighted_auc(y, p_base, Wt[b][inv]) for b in range(n_boot)])
    lo, hi = np.percentile(d, [2.5, 97.5])
    delta = auc_f - auc_b
    return dict(auc_base=auc_b, auc_full=auc_f, delta_auc=delta, ci_lo=float(lo), ci_hi=float(hi),
                n_rows=int(len(rows)), n_cases=int(len(ucase)),
                **{"pass": bool(delta >= E2_DELTA_AUC and (lo > 0 or hi < 0))})


def e3_state_retention(e2_pre, e2_post):
    if not e2_pre["pass"]:
        return dict(applicable=False, pass_=None, note="E2 primary failed: retention of state information could not "
                                                        "be assessed")
    ratio = e2_post["delta_auc"] / e2_pre["delta_auc"]
    return dict(applicable=True, retained_fraction=float(ratio), pass_=bool(ratio >= E3_RETENTION))


def fm_conditions(e1_278, e1_158, e3_278, e3_158, e3_state):
    """Conditions of P1b-FM / P2-FM (§5.3, §12.2)."""
    return {"E1": bool(e1_278["pass"] and e1_158["pass"]), "E3-site": bool(e3_278["pass"] and e3_158["pass"]),
            "E3-state": bool((not e3_state["applicable"]) or e3_state["pass_"])}


# ---------------------------------------------------------------------------------------------------------------------
# reporting-only paths
# ---------------------------------------------------------------------------------------------------------------------
def mlp_site_probe(rep_by_fold, case_idx, case_sites, case_folds, steps_of, tag, roots=(SEED_FOLDS, SEED_BOOTSTRAP)):
    """Pre-removal 2-layer MLP site probe (reporting only; §4.3)."""
    s, p = site_probe_case_predictions(rep_by_fold, case_idx, case_sites, case_folds, steps_of, "mlp",
                                       f"E1-MLP:{tag}", roots[0])
    out = ba_with_ci(s, p, f"E1-MLP:{tag}", root=roots[1])
    out["reporting_only"] = True
    return out


def e2_rows(case_idx, steps_of, switch_step, n_steps=None):
    """E2 rows (case, step, time, S) with S = 1{step ≥ s_i}; with n_steps also ntime = step / n_i."""
    recs = [(int(i), int(t), int(t), int(t >= switch_step[i])) for i in case_idx for t in steps_of(i)]
    rows = pd.DataFrame(recs, columns=["case", "step", "time", "S"])
    if n_steps is not None:
        rows["ntime"] = rows.step / np.asarray(n_steps)[rows.case.to_numpy()]
    return rows


def normalized_time_rows(rows):
    """The same rows with elapsed time replaced by t / n_i (stricter reference; §5.2)."""
    return rows.assign(time=rows["ntime"])


def history_rows(rep_case_idx, design, A, W, K):
    """E2-with-H rows on the K window steps and the lag matrix H (zero before the trajectory start; §6 initial 0)."""
    w = design.window_start()
    n_lags = W + K - 1
    recs, H = [], []
    for k, i in enumerate(rep_case_idx):
        for t in range(K):
            step = int(w[k] + t)
            recs.append((int(i), step, step, int(design.offset[k] + t >= 0)))
            lags = np.zeros(n_lags)
            for ell in range(1, n_lags + 1):
                col = W + t - ell
                if col >= 0:
                    lags[ell - 1] = A[k, col]
            H.append(lags)
    return pd.DataFrame(recs, columns=["case", "step", "time", "S"]), np.asarray(H)


def near_uniform_summary(flags_by_case, centres, switch_steps):
    """Proportion of near-uniform grid frames by centre, by S and by centre × S (§3.1 step 4; reporting only).

    flags_by_case[i]: bool array over the case's grid frames 0..; frame k belongs to step k // 10, S = 1{step ≥ s_i}.
    """
    rows = []
    for f, c, s in zip(flags_by_case, centres, switch_steps):
        f = np.asarray(f, bool)
        S = (np.arange(len(f)) // 10 >= s).astype(int)
        for sv in (0, 1):
            m = S == sv
            rows.append((c, sv, int(m.sum()), int(f[m].sum())))
    d = pd.DataFrame(rows, columns=["centre", "S", "n_frames", "n_near_uniform"])

    def table(by):
        g = d.groupby(by, sort=True)[["n_frames", "n_near_uniform"]].sum()
        g["proportion"] = g.n_near_uniform / g.n_frames.where(g.n_frames > 0)
        return [dict(zip(([by] if isinstance(by, str) else by), (k if isinstance(k, tuple) else (k,))),
                     n_frames=int(r.n_frames), n_near_uniform=int(r.n_near_uniform),
                     proportion=None if pd.isna(r.proportion) else float(r.proportion)) for k, r in g.iterrows()]

    tot = d[["n_frames", "n_near_uniform"]].sum()
    return dict(by_centre=table("centre"), by_S=table("S"), by_centre_S=table(["centre", "S"]),
                overall=dict(n_frames=int(tot.n_frames), n_near_uniform=int(tot.n_near_uniform),
                             proportion=float(tot.n_near_uniform / tot.n_frames) if tot.n_frames else None),
                reporting_only=True)


# ---------------------------------------------------------------------------------------------------------------------
# G-SITE (§5.4)
# ---------------------------------------------------------------------------------------------------------------------
def eta2(groups, y):
    """One-way η² (between-group SS / total SS); identical to data_audit/lead/ss_gsite_perW.py."""
    y = np.asarray(y, float)
    m = y.mean()
    tot = ((y - m) ** 2).sum()
    if not tot:
        return 0.0
    return float(sum(len(g) * (g.mean() - m) ** 2 for _, g in pd.Series(y).groupby(np.asarray(groups)))) / tot


def gsite(centre, offset, cells):
    """η² of S at the window start on C (gate), and of Σ_{window∪post} S on C for every (K, P) in ``cells``."""
    centre, offset = np.asarray(centre), np.asarray(offset)
    s0 = (offset >= 0).astype(float)
    g = eta2(centre, s0)
    per_kp = {}
    for c in cells:
        key = f"K{c.K}_P{c.P}"
        if key not in per_kp:
            j = np.arange(0, c.K + c.P)
            per_kp[key] = eta2(centre, (offset[:, None] + j[None, :] >= 0).sum(1))
    return dict(n=int(len(centre)), eta2_S_window_start=g, gate_pass=bool(g <= GSITE_MAX_ETA2),
                P_S1_window_start=float(s0.mean()), eta2_sum_S_window_post=per_kp)
