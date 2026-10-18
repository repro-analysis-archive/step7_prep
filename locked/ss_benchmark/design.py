"""Case sets, folds and the window design (§2, §7.2), for the real path and the PLACEHOLDER path.

Real path (supported; during code lock only the case IDs (fold test) and centre + offset (G-SITE) are read):
  * 278-case representation set: centres 2-5 of out/DS203_d8_cases.csv (Center3_020 is not in that file);
  * primary causal set (158): out/ss_window_offsets.csv (dbd5984);
  * per-W sets W0 (204) / W5 (201): out/ss_window_offsets_perW.csv (adf9160);
  * single-file set (123): primary cases with n_files == 1.
Folds (§2): case-level 5-fold stratified by site, seed 20261006, defined once on the 278 cases; every analysis set
uses the same labels restricted to its cases. Implementation: cases sorted by ID; sites in increasing order; within a
site a seeded permutation of its cases is dealt round-robin to folds 0-4, the deal continuing across sites.

PLACEHOLDER path: synthetic centres (101-104), synthetic switch steps, video lengths and offsets, all from streams of
seed 99990001, with the same set sizes (278 / 158 / 204 / 201 / 123) and the same fold rule (placeholder fold seed).
"""
import os
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import seeds
from .constants import (N_FOLDS, N_PRIMARY_CASES, N_REPRESENTATION_CASES, PLACEHOLDER_LABEL, REPRESENTATION_CENTRES,
                        SEED_FOLDS)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "data_audit", "lead", "out")
D8_CASES = os.path.join(OUT, "DS203_d8_cases.csv")
OFFSETS = os.path.join(OUT, "ss_window_offsets.csv")
OFFSETS_PERW = os.path.join(OUT, "ss_window_offsets_perW.csv")
SET_SIZES = {"primary": 158, "W0": 204, "W5": 201, "single_file": 123}


def case_id(center, op) -> str:
    return f"C{int(center)}_{int(op):03d}"


def make_folds(ids, sites, seed: int, n_folds: int = N_FOLDS) -> np.ndarray:
    ids = np.asarray(ids, dtype=object)
    sites = np.asarray(sites)
    order = np.argsort(ids, kind="stable")
    folds = np.full(len(ids), -1, dtype=np.int64)
    rng = np.random.default_rng(seed)
    dealt = 0
    for site in np.unique(sites):
        idx = order[sites[order] == site]
        perm = rng.permutation(len(idx))
        folds[idx[perm]] = (dealt + np.arange(len(idx))) % n_folds
        dealt += len(idx)
    assert (folds >= 0).all()
    return folds


def representation_cases() -> pd.DataFrame:
    """The 278 real case IDs and centres (reads only the centre and op columns)."""
    d = pd.read_csv(D8_CASES, usecols=["center", "op"])
    d = d[d.center.isin(REPRESENTATION_CENTRES)].copy()
    d["case_id"] = [case_id(c, o) for c, o in zip(d.center, d.op)]
    d = d.sort_values("case_id").reset_index(drop=True)
    assert len(d) == N_REPRESENTATION_CASES and d.case_id.is_unique, len(d)
    assert "C3_020" not in set(d.case_id)
    return d[["case_id", "center"]]


def representation_switch_steps() -> pd.Series:
    """Real switch steps s_i = max(ceil(T_i / 5) − 1, 0) of the 278 cases (§2; used from §14 step 5 on)."""
    d = pd.read_csv(D8_CASES, usecols=["center", "op", "timestamp_s"])
    d = d[d.center.isin(REPRESENTATION_CENTRES)]
    ids = [case_id(c, o) for c, o in zip(d.center, d.op)]
    s = np.maximum(np.ceil(d.timestamp_s.to_numpy() / 5.0) - 1, 0).astype(np.int64)
    out = pd.Series(s, index=ids, name="s").sort_index()
    assert len(out) == N_REPRESENTATION_CASES
    return out


def truth_check_design(set_name: str) -> "Design":
    """Centre + offset only design for the small-truth check (§11); no other field is read."""
    centre, offset = gsite_inputs(set_name)
    return Design(label=f"REAL:{set_name} (centre and offset only)", ids=np.arange(len(centre)), centre=centre,
                  offset=offset, folds=np.zeros(len(centre), dtype=np.int64))


def representation_folds() -> pd.Series:
    d = representation_cases()
    return pd.Series(make_folds(d.case_id.values, d.center.values, SEED_FOLDS), index=d.case_id.values, name="fold")


def restrict_folds(folds: pd.Series, ids) -> np.ndarray:
    return folds.loc[list(ids)].to_numpy()


def analysis_set_folds(set_name: str) -> pd.Series:
    """Fold labels of a real analysis set: the 278-case labels restricted to its case IDs (§2)."""
    ids = analysis_set_ids(set_name)
    return pd.Series(restrict_folds(representation_folds(), ids), index=ids, name="fold")


def analysis_set_ids(set_name: str) -> list:
    """Real analysis-set case IDs (reads only the ID columns)."""
    if set_name in ("primary", "single_file"):
        d = pd.read_csv(OFFSETS, usecols=["center", "op", "n_files"])
        if set_name == "single_file":
            d = d[d.n_files == 1]
    else:
        d = pd.read_csv(OFFSETS_PERW, usecols=["set", "center", "op"])
        d = d[d["set"] == set_name]
    ids = sorted(case_id(c, o) for c, o in zip(d.center, d.op))
    assert len(ids) == SET_SIZES[set_name], (set_name, len(ids))
    return ids


@dataclass
class Design:
    label: str                      # "REAL:<set>" or "PLACEHOLDER:<set>"
    ids: np.ndarray
    centre: np.ndarray              # site label per case
    offset: np.ndarray              # O_i in {-15..15}
    folds: np.ndarray               # §2 fold label per case
    switch_step: np.ndarray = None  # s_i (absolute step); needed only to locate representations
    n_steps: np.ndarray = None      # n_i
    extra: dict = field(default_factory=dict)

    @property
    def n(self) -> int:
        return len(self.ids)

    @property
    def is_placeholder(self) -> bool:
        return self.label.startswith(PLACEHOLDER_LABEL)

    def state(self, rel_steps) -> np.ndarray:
        """S at window-relative steps j: 1{O_i + j >= 0} (§7.2); shape (n, len(rel_steps))."""
        j = np.asarray(rel_steps)[None, :]
        return (self.offset[:, None] + j >= 0).astype(np.float64)

    def window_start(self) -> np.ndarray:
        return self.switch_step + self.offset

    def centre_codes(self):
        levels = np.unique(self.centre)
        return levels, np.searchsorted(levels, self.centre)


def load_real_design(set_name: str) -> Design:
    """Real causal design (supported; not exercised during code lock, except centre and offset for G-SITE)."""
    if set_name in ("primary", "single_file"):
        d = pd.read_csv(OFFSETS)
        if set_name == "single_file":
            d = d[d.n_files == 1]
    else:
        d = pd.read_csv(OFFSETS_PERW)
        d = d[d["set"] == set_name]
    d = d.assign(case_id=[case_id(c, o) for c, o in zip(d.center, d.op)]).sort_values("case_id")
    assert len(d) == SET_SIZES[set_name]
    folds = analysis_set_folds(set_name).loc[d.case_id].to_numpy()
    return Design(label=f"REAL:{set_name}", ids=d.case_id.to_numpy(), centre=d.center.to_numpy(),
                  offset=d.O.to_numpy().astype(np.int64), folds=folds, switch_step=d.s.to_numpy().astype(np.int64),
                  n_steps=d.n.to_numpy().astype(np.int64))


def gsite_inputs(set_name: str):
    """Centre and offset only (G-SITE, §5.4; small-truth design check, §11)."""
    if set_name in ("primary", "single_file"):
        d = pd.read_csv(OFFSETS, usecols=["center", "op", "n_files", "O"])
        if set_name == "single_file":
            d = d[d.n_files == 1]
    else:
        d = pd.read_csv(OFFSETS_PERW, usecols=["set", "center", "op", "O"])
        d = d[d["set"] == set_name]
    assert len(d) == SET_SIZES[set_name]
    return d.center.to_numpy(), d.O.to_numpy().astype(np.int64)


# ---------------------------------------------------------------------------------------------------------------------
# PLACEHOLDER design
# ---------------------------------------------------------------------------------------------------------------------
PLACEHOLDER_CENTRES = (101, 102, 103, 104)


def placeholder_representation_set() -> pd.DataFrame:
    """278 synthetic cases: centre, switch step s, length n, offset O, membership of the four analysis sets, fold."""
    rng = seeds.rng(seeds.placeholder_seq("design", "representation-set"))
    while True:
        sizes = rng.multinomial(N_REPRESENTATION_CASES, [0.25] * 4)
        if sizes.min() >= 40:
            break
    centre = np.repeat(PLACEHOLDER_CENTRES, sizes)
    ids = np.array([f"PH{c}_{k:03d}" for c, sz in zip(PLACEHOLDER_CENTRES, sizes) for k in range(sz)], dtype=object)
    s = rng.integers(50, 91, size=len(ids))
    n = s + 60 + rng.integers(5, 61, size=len(ids))
    offset = rng.integers(-15, 16, size=len(ids))
    while True:
        primary = np.zeros(len(ids), bool)
        primary[rng.choice(len(ids), N_PRIMARY_CASES, replace=False)] = True
        if min((primary & (centre == c)).sum() for c in PLACEHOLDER_CENTRES) >= 20:
            break
    rest = np.flatnonzero(~primary)
    rest = rest[rng.permutation(len(rest))]
    w0 = primary.copy(); w0[rest[:SET_SIZES["W0"] - N_PRIMARY_CASES]] = True
    w5 = primary.copy(); w5[rest[:SET_SIZES["W5"] - N_PRIMARY_CASES]] = True
    single = np.zeros(len(ids), bool)
    prim_idx = np.flatnonzero(primary)
    single[rng.choice(prim_idx, SET_SIZES["single_file"], replace=False)] = True
    fold_seed = int(seeds.placeholder_seq("design", "folds").generate_state(1)[0])
    folds = make_folds(ids, centre, fold_seed)
    return pd.DataFrame(dict(case_id=ids, centre=centre, s=s, n=n, O=offset, primary=primary, W0=w0, W5=w5,
                             single_file=single, fold=folds)).sort_values("case_id").reset_index(drop=True)


def placeholder_design(set_name: str = "primary", rep_set: pd.DataFrame = None) -> Design:
    d = placeholder_representation_set() if rep_set is None else rep_set
    d = d[d[set_name]]
    assert len(d) == SET_SIZES[set_name]
    return Design(label=f"{PLACEHOLDER_LABEL}:{set_name}", ids=d.case_id.to_numpy(), centre=d.centre.to_numpy(),
                  offset=d.O.to_numpy().astype(np.int64), folds=d.fold.to_numpy(),
                  switch_step=d.s.to_numpy().astype(np.int64), n_steps=d.n.to_numpy().astype(np.int64))


def placeholder_large_design(n: int, name: str) -> Design:
    """A large synthetic design (fast tests 1-2): centres, offsets and folds from a 99990001 stream."""
    rng = seeds.rng(seeds.placeholder_seq("design", "large", name))
    centre = rng.choice(PLACEHOLDER_CENTRES, size=n)
    offset = rng.integers(-15, 16, size=n)
    ids = np.array([f"PHL_{k:07d}" for k in range(n)], dtype=object)
    folds = make_folds(ids, centre, int(seeds.placeholder_seq("design", "large-folds", name).generate_state(1)[0]))
    return Design(label=f"{PLACEHOLDER_LABEL}:large-{name}", ids=ids, centre=centre, offset=offset, folds=folds)
