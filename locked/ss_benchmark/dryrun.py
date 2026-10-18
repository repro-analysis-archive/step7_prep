"""PLACEHOLDER dry run of the representation-level checks and the family aggregation (§14 step 2: "a dry run on fully
synthetic placeholder features (no DS203 frames)").

Runs, on the PLACEHOLDER 278-case set and its 158-case primary / 123-case single-file sets, through the step-5 code
path (pipeline.run_checks on PLACEHOLDER files written to a temporary directory): fold-wise PCA / LEACE, E1, E2,
E3-site (linear and MLP), E3-state-retention, the FM conditions and the reporting-only paths (pre-removal MLP probe,
E2 on all 278 videos, E2 with past actions, normalised-time reference); the near-uniform summary (pipeline.
near_uniform) on synthetic flags; and a small causal run (two family cells, six arms, three replicates, linear
learners) followed by the §12.3 aggregation code. All seeds derive from 99990001. Output: one JSON file.

    python -m ss_benchmark.dryrun --out FILE [--n-boot B]
"""
import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

from . import arms as arms_mod
from . import checks, dgp, grid, placeholder, sdr, seeds
from .constants import PLACEHOLDER_LABEL


def _roots():
    return (int(seeds.placeholder_seq("dryrun", "probe").generate_state(1)[0]),
            int(seeds.placeholder_seq("dryrun", "bootstrap").generate_state(1)[0]))


def run(n_boot=2000):
    import tempfile
    from . import pipeline
    rep_set, designs, reps, reports, full = placeholder.build()
    roots = _roots()
    out = dict(label=PLACEHOLDER_LABEL, reduction_reports={k: v for k, v in reports.items()})
    cases = pd.DataFrame(dict(case_id=rep_set.case_id, center=rep_set.centre, s=rep_set.s))
    with tempfile.TemporaryDirectory() as tmp:
        f = full["P"]
        lens = np.array([len(x) for x in f["R"][0]])
        path = os.path.join(tmp, "reps_full_P.npz")
        np.savez(path, lengths=lens, **{f"R_{v}": np.concatenate(f["R"][v]) for v in range(5)},
                 **{f"RC_{v}": np.concatenate(f["R-C"][v]) for v in range(5)})
        chk = pipeline.run_checks({"P": path}, os.path.join(tmp, "checks.json"), cases=cases,
                                  folds=rep_set.fold.to_numpy(), designs=designs, roots=roots, n_boot=n_boot,
                                  replicate_root=int(seeds.placeholder_seq("dryrun", "e2-history").generate_state(1)[0]))
        out["checks"] = chk["P"]
        frng = seeds.rng(seeds.placeholder_seq("dryrun", "near-uniform"))
        for cid, n in zip(rep_set.case_id, rep_set.n):
            np.save(os.path.join(tmp, f"{cid}.near_uniform.npy"), frng.random(10 * int(n)) < 0.02)
        out["near_uniform"] = pipeline.near_uniform(tmp, os.path.join(tmp, "nu.json"), cases=cases)

    # small causal run + aggregation (exercise path only)
    D = designs["primary"]
    root = int(seeds.placeholder_seq("dryrun", "replicates").generate_state(1)[0])
    cells = [grid.find_cell(1, 0, 0, 0.5, 1.0), grid.find_cell(2, 5, 0, 0.5, 1.0)]
    arm_list = ("NV", "SITE", "FM-P", "FM-P-C", "ORACLE-C", "ORACLE")
    res = {}
    for c in cells:
        for r in range(3):
            seq = seeds.replicate_seq(c.index, r, root)
            d = dgp.draw(D, c, seq)
            A, Y = dgp.simulate(D, c, d)
            tr = dgp.truth(D, c, d)
            for arm in arm_list:
                X = arms_mod.arm_covariates(arm, D, c, d, reps["primary"])
                e = sdr.sdr_mtp(A, Y, X, c.W, c.K, D.folds, seeds.child(seq, "learners"), "linear")
                res.setdefault((c.index, arm), []).append((e["est"], tr))
    fam = {}
    for f, cells_f in (("P1b-SITE", [cells[1]]), ("P2-SITE", [cells[0]])):
        w_arm, wo_arm = grid.FAMILIES[f][:2]
        per = {c.index: ([x[0] for x in res[(c.index, w_arm)]], [x[0] for x in res[(c.index, wo_arm)]],
                         [x[1] for x in res[(c.index, w_arm)]]) for c in cells_f}
        fam[f] = grid.family_verdict(f, per, n_boot=n_boot, conditions={"G-SITE": True})
    out["causal_dryrun"] = {f"{k[0]}:{k[1]}": v for k, v in sorted(res.items())}
    out["family_dryrun"] = fam
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--n-boot", type=int, default=2000)
    a = ap.parse_args(argv)
    res = run(a.n_boot)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as f:
        json.dump(res, f, indent=1, sort_keys=True, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))
        f.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
