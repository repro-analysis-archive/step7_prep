"""Fully synthetic PLACEHOLDER representations for the dry run, the estimator gate and the compute projection.

No DS203 frame or representation is involved. For each of the 278 PLACEHOLDER cases (design.placeholder_
representation_set) and each placeholder model key (P, S, REF, P-nat), a raw d-dimensional "representation" per step
is drawn from a 99990001 stream:
    x_t = b_S · S_t + B_C[centre] + b_T · (t / n) + σ · N(0, I_d),  S_t = 1{t ≥ s_i}
with random loading vectors (P-nat: a stronger centre loading, mimicking acquisition cues). The pipeline then runs the
real code path: fold-wise PCA (64 PCs) and LEACE (reduce.foldwise_reduce) on the 278 cases with the placeholder fold
labels, and window-step features (window-relative steps 0..14, absolute step w_i + t) are cut for every analysis set.
"""
import numpy as np

from . import seeds
from .design import placeholder_design, placeholder_representation_set
from .reduce import foldwise_reduce

PLACEHOLDER_MODELS = {"P": dict(d=128, site=0.6, state=1.0), "S": dict(d=96, site=0.4, state=0.7),
                      "REF": dict(d=160, site=0.8, state=0.5), "P-nat": dict(d=128, site=1.5, state=1.0)}
K_MAX = 15


def raw_representations(rep_set, key):
    spec = PLACEHOLDER_MODELS[key]
    rng = seeds.rng(seeds.placeholder_seq("features", key))
    d = spec["d"]
    b_S = rng.standard_normal(d) * spec["state"] / np.sqrt(d) * 4
    B_C = {c: rng.standard_normal(d) * spec["site"] / np.sqrt(d) * 4 for c in sorted(set(rep_set.centre))}
    b_T = rng.standard_normal(d) / np.sqrt(d) * 2
    out = []
    for _, r in rep_set.iterrows():
        t = np.arange(r.n)
        S = (t >= r.s).astype(float)
        x = S[:, None] * b_S + B_C[r.centre] + (t / r.n)[:, None] * b_T + rng.standard_normal((r.n, d))
        out.append(x)
    return out


def build(set_names=("primary", "W0", "W5", "single_file"), keys=("P", "S", "REF", "P-nat")):
    """Return (rep_set, designs, reps, reports): reps[set][key] has shape (5, n_set, K_MAX, 64)."""
    rep_set = placeholder_representation_set()
    designs = {s: placeholder_design(s, rep_set) for s in set_names}
    reps = {s: {} for s in set_names}
    reports = {}
    full = {}
    for key in keys:
        raw = raw_representations(rep_set, key)
        red = foldwise_reduce(raw, rep_set.fold.to_numpy(), rep_set.centre.to_numpy(), with_leace=key != "P-nat")
        reports[key] = red["report"]
        full[key] = red
        pos = {cid: i for i, cid in enumerate(rep_set.case_id)}
        for s in set_names:
            D = designs[s]
            idx = np.array([pos[c] for c in D.ids])
            w = D.window_start()
            for out_key, src in ((key, "R"), (f"{key}-C", "R-C")):
                if not red[src]:
                    continue
                arr = np.empty((len(red[src]), D.n, K_MAX, red[src][0][0].shape[1]))
                for v, per_case in enumerate(red[src]):
                    for k, (i, wi) in enumerate(zip(idx, w)):
                        arr[v, k] = per_case[i][wi:wi + K_MAX]
                reps[s][out_key] = arr
    return rep_set, designs, reps, reports, full
