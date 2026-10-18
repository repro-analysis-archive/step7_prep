"""PLACEHOLDER test inputs for make_report.py / make_figures.py (no DS203 data, no real design; seeds 99990001-derived).

Runs the locked code (a cp of the repository's ss_benchmark in ./locked, unchanged) on the PLACEHOLDER design:
  step5  pipeline.run_checks on placeholder.build() representations for the keys P, S, REF (with -C) and P-nat,
         n_boot = 200 (PLACEHOLDER only), placeholder roots -> PLACEHOLDER_test/step5/checks.json, reps_report.json;
         a PLACEHOLDER G-SITE record; the §13 record via a copy of apply_section13.py
  grid   grid_driver.main --placeholder on a small cell subset, M = 2, aggregation ON (as at §14 step 7)
         -> PLACEHOLDER_test/grid/{replicates.csv, cell_metrics.csv, families.json, run_plan.json}
Every output lives under PLACEHOLDER_test/ and every JSON written here carries "label": "PLACEHOLDER".

    python make_placeholder_inputs.py step5|grid [--workers 2]
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "PLACEHOLDER_test")
sys.path.insert(0, os.path.join(HERE, "locked"))

# cells: (K, P, W, alpha, gamma); K x P at W = 0 (alpha 0.5, gamma 1), W in {5, 30} at P = 0 for K in {1, 5},
# two alpha = 0 cells (P1a), one phi_A = 0.5 cell. K = 15 is left out: its units took 15-20 min each with 2 CPU
# threads (the first run was stopped after the 30 K <= 5 primary units; those shards are reused unchanged).
CELLS = [(K, P, 0, 0.5, 1.0) for K in (1, 2, 5) for P in (0, 5, 30)] + \
        [(K, 0, W, 0.5, 1.0) for K in (1, 5) for W in (5, 30)] + [(2, 5, 0, 0.0, 1.0), (5, 0, 5, 0.0, 1.0)]


def step5(n_boot):
    import numpy as np
    import pandas as pd
    from ss_benchmark import pipeline, placeholder, seeds
    d = os.path.join(OUT, "step5")
    os.makedirs(d, exist_ok=True)
    rep_set, designs, reps, reports, full = placeholder.build()
    cases = pd.DataFrame(dict(case_id=rep_set.case_id, center=rep_set.centre, s=rep_set.s))
    paths = {}
    for key, f in full.items():
        lens = np.array([len(x) for x in f["R"][0]])
        p = os.path.join(d, f"reps_full_{key}.npz")
        extra = {f"RC_{v}": np.concatenate(f["R-C"][v]) for v in range(5)} if f.get("R-C") else {}
        np.savez(p, lengths=lens, **{f"R_{v}": np.concatenate(f["R"][v]) for v in range(5)}, **extra)
        paths[key] = p
    roots = (int(seeds.placeholder_seq("step7prep", "probe").generate_state(1)[0]),
             int(seeds.placeholder_seq("step7prep", "bootstrap").generate_state(1)[0]))
    chk = pipeline.run_checks(paths, os.path.join(d, "checks.json"), cases=cases, folds=rep_set.fold.to_numpy(),
                              designs=designs, roots=roots, n_boot=n_boot,
                              replicate_root=int(seeds.placeholder_seq("step7prep", "e2-history").generate_state(1)[0]))
    chk["label"] = "PLACEHOLDER"
    json.dump(chk, open(os.path.join(d, "checks.json"), "w"), indent=1, sort_keys=True, default=float)
    json.dump(dict(reports, label="PLACEHOLDER"), open(os.path.join(d, "reps_report.json"), "w"), indent=1,
              sort_keys=True, default=float)
    gs = dict(label="PLACEHOLDER", gate_pass_primary=True, eta2_primary_4dp=0.0,
              sets={s: dict(gate_pass=True, eta2_S_window_start=0.0) for s in ("primary", "W0", "W5")})
    json.dump(gs, open(os.path.join(d, "gsite_record.json"), "w"), indent=1, sort_keys=True)
    gen = os.path.join(HERE, "apply_section13_copy.py")
    subprocess.run([sys.executable, gen, "--checks", os.path.join(d, "checks.json"), "--gsite",
                    os.path.join(d, "gsite_record.json"), "--out-dir", d], check=True)
    for f in ("section13.json", "grid_conditions.json"):
        j = json.load(open(os.path.join(d, f)))
        j["label"] = "PLACEHOLDER"
        json.dump(j, open(os.path.join(d, f), "w"), indent=1, sort_keys=True)


def grid(workers):
    from ss_benchmark import grid as g
    idx = [g.find_cell(*c).index for c in CELLS] + [g.find_cell(1, 0, 5, 0.5, 1.0, 0.5).index]
    gd = os.path.join(OUT, "grid")
    os.makedirs(gd, exist_ok=True)
    env = dict(os.environ, OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1",
               NUMEXPR_NUM_THREADS="1", PYTHONHASHSEED="0", PYTHONDONTWRITEBYTECODE="1")
    subprocess.run([sys.executable, "-m", "ss_benchmark.grid_driver", "--out", gd, "--placeholder", "--cells",
                    ",".join(map(str, sorted(idx))), "--max-reps", "2", "--workers", str(workers)],
                   cwd=os.path.join(HERE, "locked"), env=env, check=True)
    json.dump(dict(label="PLACEHOLDER", cells=sorted(idx), max_reps=2, note="tiny PLACEHOLDER grid for testing the "
                   "report and figure scripts; not results"), open(os.path.join(gd, "PLACEHOLDER_LABEL.json"), "w"),
              indent=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("part", choices=("step5", "grid"))
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--n-boot", type=int, default=200)
    a = ap.parse_args()
    step5(a.n_boot) if a.part == "step5" else grid(a.workers)
