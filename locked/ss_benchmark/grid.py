"""Design grid (§10.1), families (§12.2) and the aggregation rule (§12.3).

Cell indices: the 216 primary cells (φ_A = 0) in lexicographic order of (K, P, W, α, γ) over the §10.1 value lists,
indices 0-215; then the 24 φ_A = 0.5 cells (K ∈ {1,5}, P ∈ {0,5}, W = 5, all α, γ) in the same order, 216-239. The
cell index is the first spawn-key element of the replicate SeedSequence (§10.2).

Family cells (P1a, P1b, P2) are drawn from the 216 primary cells; every other cell (including the 24 φ_A cells) is a
P3-only cell. Bootstrap (§12.3): for family F, a Generator from SeedSequence(20261008) child "family:<F>" draws, for
each family cell in increasing cell index, a (B, M) matrix of replicate indices used for both arms of the pair; D̄_F is
recomputed on each resample (biases and mean truth of every cell); 95 % percentile interval.
"""
from dataclasses import asdict, dataclass

import numpy as np

from . import seeds
from .constants import (GRID_ALPHA, GRID_GAMMA, GRID_K, GRID_P, GRID_W, N_BOOTSTRAP, PHI_K, PHI_P, PHI_PRIMARY,
                        PHI_SENSITIVITY, PHI_W, SEED_BOOTSTRAP)


@dataclass(frozen=True)
class Cell:
    index: int
    K: int
    P: int
    W: int
    alpha: float
    gamma: float
    phi: float

    def as_dict(self):
        return asdict(self)


def all_cells():
    cells = []
    for K in GRID_K:
        for P in GRID_P:
            for W in GRID_W:
                for a in GRID_ALPHA:
                    for g in GRID_GAMMA:
                        cells.append(Cell(len(cells), K, P, W, a, g, PHI_PRIMARY))
    for K in PHI_K:
        for P in PHI_P:
            for W in PHI_W:
                for a in GRID_ALPHA:
                    for g in GRID_GAMMA:
                        cells.append(Cell(len(cells), K, P, W, a, g, PHI_SENSITIVITY))
    assert len(cells) == 240
    return cells


def find_cell(K, P, W, alpha, gamma, phi=PHI_PRIMARY):
    for c in all_cells():
        if (c.K, c.P, c.W, c.alpha, c.gamma, c.phi) == (K, P, W, alpha, gamma, phi):
            return c
    raise KeyError((K, P, W, alpha, gamma, phi))


# family: (with-C arm, without-C arm, kind, cell predicate, conditions)
FAMILIES = {
    "P1a": ("ORACLE", "ORACLE-C", "P1", lambda c: c.alpha == 0 and not (c.K == 1 and c.P == 0), ()),
    "P1b-SITE": ("SITE", "NV", "P1", lambda c: c.W == 0 and c.P in (5, 30), ()),
    "P1b-FM": ("FM-P", "FM-P-C", "P1", lambda c: c.W == 0 and c.P in (5, 30), ("E1", "E3-site", "E3-state")),
    "P2-SITE": ("SITE", "NV", "P2", lambda c: c.K == 1 and c.P == 0, ("G-SITE",)),
    "P2-FM": ("FM-P", "FM-P-C", "P2", lambda c: c.K == 1 and c.P == 0 and c.alpha > 0,
              ("G-SITE", "E1", "E3-site", "E3-state")),
    "P2-ORACLE": ("ORACLE", "ORACLE-C", "P2", lambda c: c.K == 1 and c.P == 0 and c.alpha > 0, ("G-SITE",)),
}
FAMILY_SIZES = {"P1a": 66, "P1b-SITE": 48, "P1b-FM": 48, "P2-SITE": 18, "P2-FM": 12, "P2-ORACLE": 12}


def family_cells(name):
    pred = FAMILIES[name][3]
    cells = [c for c in all_cells() if c.phi == PHI_PRIMARY and pred(c)]
    assert len(cells) == FAMILY_SIZES[name], (name, len(cells))
    return cells


def family_cell_indices():
    return sorted({c.index for f in FAMILIES for c in family_cells(f)})


def is_family_cell(cell) -> bool:
    return cell.index in set(family_cell_indices())


def _d_values(est_w, est_wo, truth, kind):
    """Per-cell D_j from (M, J) arrays (NaN-free)."""
    b_w = (est_w - truth).mean(0)
    b_wo = (est_wo - truth).mean(0)
    psi = truth.mean(0)
    if kind == "P1":
        return (np.abs(b_wo) - np.abs(b_w)) / psi
    return (np.abs(b_w) - np.abs(b_wo)) / psi


def family_verdict(name, per_cell, n_boot=N_BOOTSTRAP, conditions=None):
    """per_cell: {cell_index: (est_with[M], est_without[M], truth[M])}. conditions: {"G-SITE": bool, ...}."""
    w_arm, wo_arm, kind, _, needs = FAMILIES[name]
    conditions = conditions or {}
    failed = [c for c in needs if not conditions.get(c, False)]
    idx = sorted(per_cell)
    D, Dstar, dropped = [], [], {}
    rng = seeds.rng(np.random.SeedSequence(SEED_BOOTSTRAP), f"family:{name}")
    boot_sum = np.zeros(n_boot)
    for j in idx:
        ew, ewo, tr = (np.asarray(x, float) for x in per_cell[j])
        ok = np.isfinite(ew) & np.isfinite(ewo) & np.isfinite(tr)
        dropped[j] = int((~ok).sum())
        ew, ewo, tr = ew[ok], ewo[ok], tr[ok]
        M = len(tr)
        D.append(float(_d_values(ew[:, None], ewo[:, None], tr[:, None], kind)[0]))
        b = rng.integers(0, M, size=(n_boot, M))
        boot_sum += _d_values(ew[b].T, ewo[b].T, tr[b].T, kind)
    D = np.asarray(D)
    Dbar = float(D.mean())
    Dstar = boot_sum / len(idx)
    lo, hi = (float(x) for x in np.percentile(Dstar, [2.5, 97.5]))
    share = float((D > 0).mean())
    if lo > 0 and share >= 0.75:
        verdict = "SUPPORTED"
    elif hi < 0 or share <= 0.25:
        verdict = "CONTRADICTED"
    else:
        verdict = "INCONCLUSIVE"
    tested = not failed
    return dict(family=name, with_arm=w_arm, without_arm=wo_arm, kind=kind, n_cells=len(idx), D_bar=Dbar,
                ci_lo=lo, ci_hi=hi, share_positive=share, rule_verdict=verdict,
                verdict=verdict if tested else "NOT TESTED (reported as P3 / descriptive)",
                conditions_required=list(needs), conditions_failed=failed, D_cells=dict(zip(map(int, idx), D.tolist())),
                dropped_nonfinite=dropped)


def cell_metrics(est, se, lo, hi, truth):
    """§11 per-arm, per-cell metrics from per-replicate arrays."""
    est, se, lo, hi, truth = (np.asarray(x, float) for x in (est, se, lo, hi, truth))
    ok = np.isfinite(est) & np.isfinite(se)
    err = est[ok] - truth[ok]
    psi = float(truth.mean())
    bias = float(err.mean()) if ok.any() else float("nan")
    sd = float(est[ok].std(ddof=1)) if ok.sum() > 1 else float("nan")
    return dict(M=int(len(est)), M_finite=int(ok.sum()), mean_truth=psi, bias=bias, abs_bias=abs(bias),
                rel_bias=bias / psi if psi else float("nan"),
                coverage=float(((lo <= truth) & (truth <= hi) & ok).mean()),
                bias_to_mcsd=abs(bias) / sd if sd and np.isfinite(sd) else float("nan"),
                rmse=float(np.sqrt(np.mean(err ** 2))) if ok.any() else float("nan"),
                ci_width=float(np.mean(hi[ok] - lo[ok])) if ok.any() else float("nan"),
                small_truth_flag=bool(abs(psi) < 0.025))
