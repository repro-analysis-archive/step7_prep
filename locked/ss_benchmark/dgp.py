"""Semi-synthetic DGP (§6) and the exact truth (§7.1).

Trajectory steps are window-relative j = -W, ..., K+P-1 (array column j + W); window j = 0..K-1; post j = K..K+P-1.
  A_ij = μ + γ c(C_i) + κ S_ij + α U_i + φ A_i,j-1 + ε_ij,  A_i,-W-1 = 0
  Y_i  = τ Σ_{j=0}^{K+P-1} A_ij + λ Σ_{j=0}^{K+P-1} S_ij + β U_i + ε_Y,  β = α
  S_ij = 1{O_i + j >= 0} (§7.2)
Replicate draws (§10.2): named child streams of the replicate SeedSequence: "c-permutation" (§6), "U",
"epsilon-A", "epsilon-Y". c(C): (-3,-1,1,3)/√5 assigned to the four centres (sorted labels) as values[perm[k]].
Truth Ψ(δ) − Ψ(1) for d(a) = δa on the K window steps (pre- and post-window natural), conditional on the design's
(C_i, S_i·) and averaged over cases: closed form for φ = 0, exact mean recursion for φ ≠ 0.

Small-truth design check (§11, at code lock): the truth depends on a replicate only through its c permutation, so it
is computed exactly for all 24 permutations of the site loadings (no seed drawn); a cell is flagged if
min over permutations |Ψ(δ) − Ψ(1)| < 0.025, which bounds every replicate. Truth only: no action, outcome or estimate.
"""
import itertools

import numpy as np

from . import seeds
from .constants import DELTA, KAPPA, LAMBDA, MU, SITE_LOADINGS, TAU


def rel_steps(cell) -> np.ndarray:
    return np.arange(-cell.W, cell.K + cell.P)


def site_loadings(design, seq) -> np.ndarray:
    levels, codes = design.centre_codes()
    assert len(levels) == 4, levels
    perm = seeds.rng(seq, "c-permutation").permutation(4)
    values = np.asarray(SITE_LOADINGS)[perm]
    return values[codes]


def draw(design, cell, seq) -> dict:
    n, L = design.n, cell.W + cell.K + cell.P
    return dict(c=site_loadings(design, seq),
                U=seeds.rng(seq, "U").standard_normal(n),
                eps_A=seeds.rng(seq, "epsilon-A").standard_normal((n, L)),
                eps_Y=seeds.rng(seq, "epsilon-Y").standard_normal(n))


def simulate(design, cell, d, delta=None, S=None):
    """Natural trajectory (A, Y); with ``delta`` also the intervened (A_d, Y_d) under the same draws."""
    steps = rel_steps(cell)
    S = design.state(steps) if S is None else S
    beta = cell.alpha
    base = MU + cell.gamma * d["c"][:, None] + KAPPA * S + cell.alpha * d["U"][:, None] + d["eps_A"]
    L = len(steps)
    A = np.empty_like(base)
    prev = np.zeros(design.n if S is None else S.shape[0])
    for j in range(L):
        A[:, j] = base[:, j] + cell.phi * prev
        prev = A[:, j]
    out_cols = slice(cell.W, L)
    Y = TAU * A[:, out_cols].sum(1) + LAMBDA * S[:, out_cols].sum(1) + beta * d["U"] + d["eps_Y"]
    if delta is None:
        return A, Y
    A_d = np.empty_like(base)
    prev = np.zeros_like(prev)
    for j in range(L):
        nat = base[:, j] + cell.phi * prev               # natural value given the intervened past
        A_d[:, j] = delta * nat if 0 <= steps[j] < cell.K else nat
        prev = A_d[:, j]
    Y_d = TAU * A_d[:, out_cols].sum(1) + LAMBDA * S[:, out_cols].sum(1) + beta * d["U"] + d["eps_Y"]
    return A, Y, A_d, Y_d


def truth_closed_form(c, S_window, cell, delta=DELTA) -> float:
    """φ = 0: Ψ(δ) − Ψ(1) = τ (δ − 1) mean_i Σ_{j=0}^{K-1} (μ + γ c_i + κ S_ij)."""
    assert cell.phi == 0
    assert S_window.shape[1] == cell.K
    return float(TAU * (delta - 1.0) * np.mean(cell.K * MU + cell.K * cell.gamma * c + KAPPA * S_window.sum(1)))


def truth_recursion(c, S, cell, delta=DELTA) -> float:
    """Exact mean recursion over the trajectory (any φ); S has columns j = -W..K+P-1."""
    steps = rel_steps(cell)
    m = np.zeros(len(c))
    md = np.zeros(len(c))
    diff = np.zeros(len(c))
    for j, rel in enumerate(steps):
        drift = MU + cell.gamma * c + KAPPA * S[:, j]
        m_new = drift + cell.phi * m
        md_new = delta * (drift + cell.phi * md) if 0 <= rel < cell.K else drift + cell.phi * md
        m, md = m_new, md_new
        if rel >= 0:
            diff += md - m
    return float(TAU * diff.mean())


def truth(design, cell, d, delta=DELTA) -> float:
    S = design.state(rel_steps(cell))
    if cell.phi == 0:
        return truth_closed_form(d["c"], S[:, cell.W:cell.W + cell.K], cell, delta)
    return truth_recursion(d["c"], S, cell, delta)


def truth_for_permutation(design, cell, perm, delta=DELTA) -> float:
    """Exact truth when the four sorted centres receive SITE_LOADINGS[perm[k]]."""
    _, codes = design.centre_codes()
    c = np.asarray(SITE_LOADINGS)[np.asarray(perm)][codes]
    S = design.state(rel_steps(cell))
    if cell.phi == 0:
        return truth_closed_form(c, S[:, cell.W:cell.W + cell.K], cell, delta)
    return truth_recursion(c, S, cell, delta)


SMALL_TRUTH = 0.025


def small_truth_check(design, cells, threshold=SMALL_TRUTH):
    """Per cell: exact truth over the 24 site-loading permutations; flag = min |truth| < threshold."""
    perms = list(itertools.permutations(range(4)))
    out = []
    for c in cells:
        vals = np.array([truth_for_permutation(design, c, p) for p in perms])
        out.append(dict(cell=int(c.index), flag=bool(np.abs(vals).min() < threshold),
                        min_abs=float(np.abs(vals).min()), min=float(vals.min()), max=float(vals.max()),
                        mean=float(vals.mean())))
    return out
