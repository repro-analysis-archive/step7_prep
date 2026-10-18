"""Causal-grid driver (§10, §11, §12; §14 step 6). Real path supported, not exercised during code lock.

    python -m ss_benchmark.grid_driver --out DIR --reps REPS.npz --conditions COND.json --gsite GSITE.json \
        --projection PROJ.json [--workers N]                       (real design, replicate root 20261007)
    python -m ss_benchmark.grid_driver --out DIR --placeholder [--max-reps M] [--cells i,j,...]   (dry run)

* Units are (set, cell, replicate); one unit draws the replicate's DGP once (§10.2: all arms share it) and runs every
  arm of that set. Primary set: the 240 cells × all available arms; M = 200 (reduction (a): 100 in P3-only cells),
  learner mode "select" (reduction (b): linear learners in P3-only cells), reduction (c): FM-S−C and REF−C dropped in
  P3-only cells; reductions are read from the projection record. §10.3 sets: single-file (P1b ∪ P2 cells; NV, SITE,
  FM-P, FM-P−C), W0 (P1b cells and P2 cells with W = 0) and W5 (P2 cells with W = 5) (NV, SITE, FM-P, FM-P−C, ORACLE,
  ORACLE−C); M = 200; never reduced. An arm whose representation is absent from REPS (arm dropped, §4.1.4) is skipped.
* Replicate seeds: SeedSequence(20261007, spawn_key=(cell index, replicate)) for every set (placeholder: a
  99990001-derived root).
* Outputs: shards work/<set>/c<cell>_r<rep>.json; replicates.csv; cell_metrics.csv (§11 per set, cell, arm);
  families.json: primary-set family verdicts (§12.3) with their conditions (G-SITE from GSITE.json; E1 / E3 from
  COND.json); sensitivity-set families are reported separately and never enter verdicts; per-W P2 results are
  instrument-like only if that set's G-SITE ≤ 0.01 (§10.3).
"""
import argparse
import json
import multiprocessing as mp
import os
import sys
import time

import numpy as np
import pandas as pd

from . import arms as arms_mod
from . import design as design_mod
from . import dgp, grid, placeholder, sdr, seeds
from .constants import M_REPLICATES, SEED_REPLICATES

_S = {}


def sensitivity_cells():
    p1b = grid.family_cells("P1b-SITE")
    p2 = grid.family_cells("P2-SITE")
    return {"single_file": p1b + p2, "W0": p1b + [c for c in p2 if c.W == 0], "W5": [c for c in p2 if c.W == 5]}


def build_units(reductions, available_arms, max_reps=None, cells_subset=None):
    fam = set(grid.family_cell_indices())
    units = []
    for c in grid.all_cells():
        if cells_subset is not None and c.index not in cells_subset:
            continue
        p3 = c.index not in fam
        M = 100 if (p3 and "a" in reductions) else M_REPLICATES
        mode = "linear" if (p3 and "b" in reductions) else "select"
        arm_list = [a for a in arms_mod.ARMS if a in available_arms["primary"]
                    and not (p3 and "c" in reductions and a in ("FM-S-C", "REF-C"))]
        for r in range(M if max_reps is None else min(M, max_reps)):
            units.append(("primary", c.index, r, tuple(arm_list), mode))
    for s, cells in sensitivity_cells().items():
        if s not in available_arms:
            continue
        for c in cells:
            if cells_subset is not None and c.index not in cells_subset:
                continue
            arm_list = [a for a in arms_mod.SENSITIVITY_ARMS[s] if a in available_arms[s]]
            for r in range(M_REPLICATES if max_reps is None else min(M_REPLICATES, max_reps)):
                units.append((s, c.index, r, tuple(arm_list), "select"))
    return units


def _shard(out, u):
    s, ci, r = u[:3]
    return os.path.join(out, "work", s, f"c{ci:03d}_r{r:04d}.json")


def _unit(args):
    out, u = args
    path = _shard(out, u)
    if os.path.exists(path):
        return path
    s, ci, r, arm_list, mode = u
    D = _S["designs"][s]
    cell = grid.all_cells()[ci]
    seq = seeds.replicate_seq(ci, r, _S["root"])
    d = dgp.draw(D, cell, seq)
    A, Y = dgp.simulate(D, cell, d)
    truth = dgp.truth(D, cell, d)
    recs = []
    for arm in arm_list:
        X = arms_mod.arm_covariates(arm, D, cell, d, _S["reps"][s])
        e = sdr.sdr_mtp(A, Y, X, cell.W, cell.K, D.folds, seeds.child(seq, "learners"), mode)
        recs.append(dict(set=s, design=D.label, cell=ci, rep=r, arm=arm, mode=mode, truth=truth,
                         covered=bool(e["ci_lo"] <= truth <= e["ci_hi"]), **e))
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(recs, f, sort_keys=True)
    os.replace(tmp, path)
    return path


def load_reps(path, sets):
    z = np.load(path, allow_pickle=False)
    reps = {s: {} for s in sets}
    for k in z.files:
        s, key = k.split("/", 1)
        if s in reps and key != "ids":
            reps[s][key] = z[k]
    ids = {s: z[f"{s}/ids"] for s in sets if f"{s}/ids" in z.files}
    return reps, ids


def available(reps):
    out = {}
    for s, r in reps.items():
        out[s] = {a for a in arms_mod.ARMS if a not in arms_mod.REP_KEY or arms_mod.REP_KEY[a] in r}
    return out


def aggregate(out, units, conditions, gsite):
    recs = []
    for u in units:
        recs.extend(json.load(open(_shard(out, u))))
    df = pd.DataFrame(recs).sort_values(["set", "cell", "arm", "rep"]).reset_index(drop=True)
    df.to_csv(os.path.join(out, "replicates.csv"), index=False)
    rows = []
    for (s, ci, arm), g in df.groupby(["set", "cell", "arm"], sort=True):
        m = grid.cell_metrics(g.est, g.se, g.ci_lo, g.ci_hi, g.truth)
        rows.append(dict(set=s, cell=int(ci), arm=arm, **grid.all_cells()[int(ci)].as_dict(), **m,
                         support_failure_rate=float(g.support_failure.mean()), ess_min=float(g.ess_min.min()),
                         ratio_min=float(g.ratio_min.min()), ratio_max=float(g.ratio_max.max())))
    pd.DataFrame(rows).to_csv(os.path.join(out, "cell_metrics.csv"), index=False)
    fams = {}
    for s in sorted(df.set.unique()):
        sub = df[df.set == s]
        cond = dict(conditions.get(s, conditions.get("primary", {})))
        g_ok = gsite.get(s, {}).get("gate_pass", False) if s != "single_file" else gsite.get("primary", {}).get(
            "gate_pass", False)
        cond["G-SITE"] = bool(g_ok)
        for f, (w_arm, wo_arm, kind, pred, needs) in grid.FAMILIES.items():
            if not {w_arm, wo_arm} <= set(sub.arm):
                continue
            per = {}
            for c in grid.family_cells(f):
                a = sub[(sub.cell == c.index) & (sub.arm == w_arm)].sort_values("rep")
                b = sub[(sub.cell == c.index) & (sub.arm == wo_arm)].sort_values("rep")
                if len(a) and len(b):
                    assert (a.rep.values == b.rep.values).all()
                    per[c.index] = (a.est.values, b.est.values, a.truth.values)
            if not per:
                continue
            v = grid.family_verdict(f, per, conditions=cond)
            v["set"] = s
            v["enters_verdicts"] = s == "primary"
            if s != "primary":
                v["note"] = "§10.3 sensitivity run: reported separately; does not enter family verdicts"
                if f.startswith("P2") and s in ("W0", "W5"):
                    v["instrument_like"] = bool(gsite.get(s, {}).get("gate_pass", False))
            fams[f"{s}:{f}"] = v
    with open(os.path.join(out, "families.json"), "w") as fh:
        json.dump(fams, fh, indent=1, sort_keys=True)
    return fams


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--reps")
    ap.add_argument("--conditions")
    ap.add_argument("--gsite")
    ap.add_argument("--projection")
    ap.add_argument("--placeholder", action="store_true")
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    ap.add_argument("--max-reps", type=int)
    ap.add_argument("--cells")
    a = ap.parse_args(argv)
    sets = ("primary", "single_file", "W0", "W5")
    if a.placeholder:
        _, designs, reps, _, _ = placeholder.build()
        root = int(seeds.placeholder_seq("grid-driver", "replicates").generate_state(1)[0])
        conditions = {"primary": {"E1": True, "E3-site": True, "E3-state": True}}
        gsite = {s: {"gate_pass": True} for s in sets}
        reductions = ""
    else:
        designs = {s: design_mod.load_real_design(s) for s in sets}
        reps, ids = load_reps(a.reps, sets)
        for s in sets:
            if s in ids:
                assert list(ids[s]) == list(designs[s].ids), f"representation / design case order differs ({s})"
        root = SEED_REPLICATES
        conditions = json.load(open(a.conditions))
        gsite = json.load(open(a.gsite))["sets"]
        proj = json.load(open(a.projection))
        assert proj["projection_pass"], "compute projection did not pass"
        reductions = "".join(proj["reductions_applied"])
    _S.update(designs=designs, reps=reps, root=root)
    cells_subset = {int(x) for x in a.cells.split(",")} if a.cells else None
    units = build_units(reductions, available(reps), a.max_reps, cells_subset)
    os.makedirs(a.out, exist_ok=True)
    for s in sets:
        os.makedirs(os.path.join(a.out, "work", s), exist_ok=True)
    with open(os.path.join(a.out, "run_plan.json"), "w") as f:
        json.dump(dict(placeholder=a.placeholder, root=root, reductions=reductions, n_units=len(units),
                       sets={s: designs[s].label for s in sets}), f, indent=1, sort_keys=True)
    t0 = time.time()
    with mp.get_context("fork").Pool(a.workers) as pool:
        for k, _ in enumerate(pool.imap_unordered(_unit, [(a.out, u) for u in units], chunksize=1)):
            if (k + 1) % max(1, len(units) // 100) == 0 or k + 1 == len(units):
                print(f"{time.strftime('%F %T')} {k + 1}/{len(units)} units; elapsed {time.time() - t0:.0f} s",
                      flush=True)
    aggregate(a.out, units, conditions, gsite)
    return 0


if __name__ == "__main__":
    sys.exit(main())
