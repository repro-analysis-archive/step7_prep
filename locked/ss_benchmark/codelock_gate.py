"""Code-lock runner stages (§9 estimator gate, §10.4 compute projection, §5.4 G-SITE, pass/fail record).

    python -m ss_benchmark.codelock_gate --out DIR [--smoke] [--workers N] [--stage all|gate|projection|gsite|smalltruth|record]
    python -m ss_benchmark.codelock_gate --out DIR --status

(a) Estimator gate (§9): FULL arm only; cells K ∈ {1,5,15} × P ∈ {0,5}, W = 5, α = 0.5, γ = 1, φ_A = 0; M = 200;
    the fully synthetic PLACEHOLDER design (n = 158) with known truth; replicate SeedSequences from a 99990001-derived
    root spawned by (grid cell index, replicate). Pass: in every cell, coverage of the 95 % Wald interval in
    [0.90, 0.99], |bias| < 5 % of the mean true contrast, and every replicate finite.
(b) Compute projection (§10.4): times SDR fits on the PLACEHOLDER design for every K, W, arm and learner mode (select =
    ridge/MLP and logistic/MLP by CV; linear = reduction (b)), plus the §10.3 sensitivity configurations at their set
    sizes (PLACEHOLDER sets of 123 / 204 / 201 cases); projects full-grid wall time = Σ_cells,arms M × mean fit time /
    workers; applies reductions (a) P3 cells M = 100, (b) P3 cells linear learners only, (c) P3 cells without FM-S−C
    and REF−C, cumulatively, until the projection is ≤ 7 days.
(c) G-SITE (§5.4) from the real design metadata (centre and offset only).
(c2) Small-truth design check (§11, "flagged at code lock"): exact DGP truth for every cell of every analysis set over
    the 24 site-loading permutations, from the real centre and offset only; a cell is flagged if min |truth| < 0.025.
    Public output small_truth_flags.json (cell, flag, number flagged); the truth values are kept only in
    provenance_small_truth_values.json. Truth only: no action, outcome, estimator or arm is involved.
(d) Machine-readable record of (a)-(c2).
No stage reads a DS203 frame or representation; no estimator or arm quantity is computed on the real design.
"""
import argparse
import json
import multiprocessing as mp
import os
import platform
import sys
import time

import numpy as np
import pandas as pd

from . import arms as arms_mod
from . import checks, design, dgp, grid, placeholder, sdr, seeds
from .constants import (BUDGET_DAYS, GATE_ALPHA, GATE_COVERAGE, GATE_GAMMA, GATE_K, GATE_P, GATE_REL_BIAS, GATE_W,
                        GRID_K, GRID_W, IMPLEMENTATION_NOTES, M_REPLICATES, PLACEHOLDER_LABEL)

TIMING_REPS = 3
TIMING_REP_OFFSET = 10000          # timing replicates use indices 10000+ of the placeholder root (not gate replicates)
_STATE = {}


# ---------------------------------------------------------------------------------------------------------------------
# io helpers
# ---------------------------------------------------------------------------------------------------------------------
def _write_json(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=1, sort_keys=True)
        f.write("\n")
    os.replace(tmp, path)


def _log(out, msg):
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}"
    with open(os.path.join(out, "progress.log"), "a") as f:
        f.write(line + "\n")
    print(line, flush=True)


def _plan(smoke):
    gate_reps = 2 if smoke else M_REPLICATES
    gate_cells = [grid.find_cell(K, P, GATE_W, GATE_ALPHA, GATE_GAMMA) for K in GATE_K for P in GATE_P]
    gate_units = [("gate", c.index, r) for c in gate_cells for r in range(gate_reps)]
    tk = (1, 2) if smoke else GRID_K
    tw = (0, 5) if smoke else GRID_W
    nrep = 1 if smoke else TIMING_REPS
    tim = []
    for K in tk:
        for W in tw:
            for arm in arms_mod.ARMS:
                for mode in ("select", "linear"):
                    for r in range(nrep):
                        tim.append(("main", K, W, arm, mode, r))
    sens_kw = {"single_file": [(K, 0) for K in tk] + [(1, W) for W in tw if W != 0],
               "W0": [(K, 0) for K in tk], "W5": [(1, 5)]}
    for s, kws in sens_kw.items():
        for K, W in kws:
            for arm in arms_mod.SENSITIVITY_ARMS[s]:
                for r in range(nrep):
                    tim.append((s, K, W, arm, "select", r))
    return dict(smoke=smoke, gate_reps=gate_reps, gate_cells=[c.index for c in gate_cells], gate_units=gate_units,
                timing_units=tim)


# ---------------------------------------------------------------------------------------------------------------------
# workers
# ---------------------------------------------------------------------------------------------------------------------
def _init_state():
    if "designs" not in _STATE:
        _, designs, reps, reports, _ = placeholder.build()
        _STATE.update(designs=designs, reps=reps, reports=reports, root=seeds.placeholder_replicate_root())


def _run_sdr(set_name, cell, rep, arm, mode):
    D = _STATE["designs"][set_name]
    seq = seeds.replicate_seq(cell.index, rep, _STATE["root"])
    d = dgp.draw(D, cell, seq)
    A, Y = dgp.simulate(D, cell, d)
    truth = dgp.truth(D, cell, d)
    X = arms_mod.arm_covariates(arm, D, cell, d, _STATE["reps"][set_name])
    t0, c0 = time.perf_counter(), time.process_time()
    res = sdr.sdr_mtp(A, Y, X, cell.W, cell.K, D.folds, seeds.child(seq, "learners"), mode)
    return truth, res, time.perf_counter() - t0, time.process_time() - c0


def _gate_unit(args):
    out, _, cell_index, rep = args
    path = os.path.join(out, "work", "gate", f"c{cell_index:03d}_r{rep:04d}.json")
    if os.path.exists(path):
        return path
    cell = grid.all_cells()[cell_index]
    truth, res, _, _ = _run_sdr("primary", cell, rep, "FULL", "select")
    rec = dict(label=PLACEHOLDER_LABEL, design=_STATE["designs"]["primary"].label, cell=cell_index, K=cell.K,
               P=cell.P, W=cell.W, alpha=cell.alpha, gamma=cell.gamma, phi=cell.phi, rep=rep, arm="FULL",
               mode="select", truth=truth,
               covered=bool(res["ci_lo"] <= truth <= res["ci_hi"]), **res)
    _write_json(path, rec)
    return path


def _timing_unit(args):
    out, (comp, K, W, arm, mode, r) = args
    path = os.path.join(out, "work", "timing", f"{comp}_K{K}_W{W}_{arm}_{mode}_r{r}.json")
    if os.path.exists(path):
        return path
    set_name = "primary" if comp == "main" else comp
    cell = grid.find_cell(K, 5 if comp == "main" or K != 1 else 0, W, 0.5, 1.0)
    truth, res, wall, cpu = _run_sdr(set_name, cell, TIMING_REP_OFFSET + r, arm, mode)
    rec = dict(label=PLACEHOLDER_LABEL, component=comp, set=set_name, n=_STATE["designs"][set_name].n, K=K, W=W,
               arm=arm, mode=mode, rep=r, cell=cell.index, wall_seconds=wall, cpu_seconds=cpu,
               finite=not res["support_failure"])
    _write_json(path, rec)
    return path


def _pool_run(out, fn, units, workers, stage):
    todo = [u for u in units]
    done0 = sum(os.path.exists(p) for p in _unit_paths(out, stage, units))
    _log(out, f"[{stage}] start: {done0}/{len(units)} units already done; workers={workers}")
    t0 = time.time()
    ctx = mp.get_context("fork")
    n_done = done0
    step = max(1, len(units) // 50)
    with ctx.Pool(workers, initializer=_init_state) as pool:
        for k, _ in enumerate(pool.imap_unordered(fn, todo, chunksize=1)):
            n_now = k + 1
            if n_now % step == 0 or n_now == len(todo):
                n_done = sum(os.path.exists(p) for p in _unit_paths(out, stage, units))
                _log(out, f"[{stage}] {n_done}/{len(units)} units done; elapsed {time.time() - t0:.0f} s")
    return time.time() - t0


def _unit_paths(out, stage, units):
    if stage == "gate":
        return [os.path.join(out, "work", "gate", f"c{c:03d}_r{r:04d}.json") for _, _, c, r in units]
    return [os.path.join(out, "work", "timing", f"{c}_K{K}_W{W}_{a}_{m}_r{r}.json") for _, (c, K, W, a, m, r) in units]


# ---------------------------------------------------------------------------------------------------------------------
# stages
# ---------------------------------------------------------------------------------------------------------------------
def stage_gate(out, plan, workers):
    os.makedirs(os.path.join(out, "work", "gate"), exist_ok=True)
    units = [(out,) + u for u in plan["gate_units"]]
    _pool_run(out, _gate_unit, units, workers, "gate")
    recs = [json.load(open(p)) for p in _unit_paths(out, "gate", units)]
    df = pd.DataFrame(recs).sort_values(["cell", "rep"]).reset_index(drop=True)
    df.to_csv(os.path.join(out, "gate_PLACEHOLDER_replicates.csv"), index=False)
    cells = []
    for ci, g in df.groupby("cell", sort=True):
        m = grid.cell_metrics(g.est, g.se, g.ci_lo, g.ci_hi, g.truth)
        cov_ok = GATE_COVERAGE[0] <= m["coverage"] <= GATE_COVERAGE[1]
        bias_ok = abs(m["bias"]) < GATE_REL_BIAS * abs(m["mean_truth"])
        c = grid.all_cells()[int(ci)]
        cells.append(dict(cell=int(ci), K=c.K, P=c.P, W=c.W, alpha=c.alpha, gamma=c.gamma, phi=c.phi, **m,
                          support_failures=int(g.support_failure.sum()), coverage_in_range=bool(cov_ok),
                          abs_bias_below_5pct=bool(bias_ok), all_finite=bool(m["M_finite"] == m["M"]),
                          cell_pass=bool(cov_ok and bias_ok and m["M_finite"] == m["M"])))
    res = dict(label=PLACEHOLDER_LABEL, design=f"{PLACEHOLDER_LABEL}:primary (n=158, synthetic centres/offsets)",
               arm="FULL", learner_mode="select", M=plan["gate_reps"], criteria=dict(
                   coverage=list(GATE_COVERAGE), rel_bias_below=GATE_REL_BIAS, all_replicates_finite=True),
               cells=cells, gate_pass=bool(all(c["cell_pass"] for c in cells)))
    _write_json(os.path.join(out, "gate_PLACEHOLDER_cells.json"), res)
    _log(out, "[gate] complete")
    return res


def _project(times, reductions, n_workers):
    """Projected wall seconds for the full grid + §10.3 given mean fit times (dict keyed by comp, K, W, arm, mode)."""
    fam = set(grid.family_cell_indices())
    total = 0.0
    dropped = {"FM-S-C", "REF-C"} if "c" in reductions else set()
    for c in grid.all_cells():
        p3 = c.index not in fam
        M = 100 if (p3 and "a" in reductions) else M_REPLICATES
        mode = "linear" if (p3 and "b" in reductions) else "select"
        for arm in arms_mod.ARMS:
            if p3 and arm in dropped:
                continue
            total += M * times[("main", c.K, c.W, arm, mode)]
    p1b = grid.family_cells("P1b-SITE")
    p2 = grid.family_cells("P2-SITE")
    sens = {"single_file": p1b + p2, "W0": p1b + [c for c in p2 if c.W == 0], "W5": [c for c in p2 if c.W == 5]}
    for s, cells in sens.items():
        for c in cells:
            for arm in arms_mod.SENSITIVITY_ARMS[s]:
                total += M_REPLICATES * times[(s, c.K, c.W, arm, "select")]
    return total / n_workers


def stage_projection(out, plan, workers):
    os.makedirs(os.path.join(out, "work", "timing"), exist_ok=True)
    units = [(out, u) for u in plan["timing_units"]]
    wall = _pool_run(out, _timing_unit, units, workers, "projection")
    recs = pd.DataFrame([json.load(open(p)) for p in _unit_paths(out, "projection", units)])
    recs = recs.sort_values(["component", "K", "W", "arm", "mode", "rep"]).reset_index(drop=True)
    recs.to_csv(os.path.join(out, "projection_PLACEHOLDER_timings.csv"), index=False)
    mean_t = recs.groupby(["component", "K", "W", "arm", "mode"]).wall_seconds.mean().to_dict()
    times = dict(mean_t)
    if plan["smoke"]:            # smoke: fill untimed K / W by the largest timed configuration (exercise path only)
        for comp in ("main", "single_file", "W0", "W5"):
            for K in GRID_K:
                for W in GRID_W:
                    for arm in arms_mod.ARMS:
                        for mode in ("select", "linear"):
                            if (comp, K, W, arm, mode) not in times:
                                cand = [v for k, v in mean_t.items() if k[0] == comp and k[3] == arm and k[4] == mode]
                                cand = cand or [max(mean_t.values())]
                                times[(comp, K, W, arm, mode)] = max(cand)
    n_workers = workers
    steps = []
    for red in ("", "a", "ab", "abc"):
        sec = _project(times, red, n_workers)
        steps.append(dict(reductions=list(red), projected_wall_seconds=sec, projected_days=sec / 86400))
    fits = next((s for s in steps if s["projected_days"] <= BUDGET_DAYS), None)
    res = dict(label=PLACEHOLDER_LABEL, n_workers=n_workers, budget_days=BUDGET_DAYS, timing_units=len(recs),
               timing_reps_per_config=TIMING_REPS if not plan["smoke"] else 1, timing_stage_wall_seconds=wall,
               sum_fit_wall_seconds=float(recs.wall_seconds.sum()), all_timing_fits_finite=bool(recs.finite.all()),
               projection_steps=steps, reductions_applied=fits["reductions"] if fits else None,
               projection_pass=bool(fits is not None),
               method="Σ over cells, arms and §10.3 runs of M × mean measured wall time per SDR fit (PLACEHOLDER, "
                      "same K, W, arm, learner mode and set size), divided by the number of worker processes; fit "
                      "times measured with all workers busy.",
               smoke_extrapolated=bool(plan["smoke"]))
    _write_json(os.path.join(out, "projection_PLACEHOLDER.json"), res)
    _log(out, "[projection] complete")
    return res


def stage_gsite(out):
    cells = grid.all_cells()
    res = {}
    for s in ("primary", "W0", "W5"):
        centre, offset = design.gsite_inputs(s)
        res[s] = checks.gsite(centre, offset, [c for c in cells if c.phi == 0])
    rec = dict(label="REAL DESIGN METADATA (centre, offset only; G-SITE design check, §5.4)", sets=res,
               gate_pass_primary=res["primary"]["gate_pass"],
               per_W_instrument_like={s: res[s]["gate_pass"] for s in ("W0", "W5")},
               eta2_primary_4dp=round(res["primary"]["eta2_S_window_start"], 4))
    _write_json(os.path.join(out, "gsite_record.json"), rec)
    _log(out, "[gsite] complete")
    return rec


def stage_smalltruth(out):
    from .grid_driver import sensitivity_cells
    sets = {"primary": grid.all_cells(), **sensitivity_cells()}
    public, internal = {}, {}
    for s, cells in sets.items():
        D = design.truth_check_design(s)
        res = dgp.small_truth_check(D, cells)
        public[s] = dict(n_cells=len(res), n_flagged=int(sum(r["flag"] for r in res)),
                         cells=[dict(cell=r["cell"], flag=r["flag"]) for r in res])
        internal[s] = res
    rule = "flag if min over the 24 site-loading permutations of |Psi(delta) - Psi(1)| < 0.025 (§11)"
    _write_json(os.path.join(out, "small_truth_flags.json"), dict(
        label="REAL DESIGN METADATA (centre, offset only); truth-only design check (§11)", rule=rule, sets=public,
        n_flagged_total=int(sum(v["n_flagged"] for v in public.values()))))
    _write_json(os.path.join(out, "provenance_small_truth_values.json"), dict(
        label="INTERNAL PROVENANCE: exact truth values (no estimate exists)", rule=rule, sets=internal))
    _log(out, "[smalltruth] complete")


def stage_record(out, plan):
    g = json.load(open(os.path.join(out, "gate_PLACEHOLDER_cells.json")))
    p = json.load(open(os.path.join(out, "projection_PLACEHOLDER.json")))
    s = json.load(open(os.path.join(out, "gsite_record.json")))
    st = json.load(open(os.path.join(out, "small_truth_flags.json")))
    prov = json.load(open(os.path.join(out, "provenance.json"))) if os.path.exists(
        os.path.join(out, "provenance.json")) else {}
    rec = dict(smoke=plan["smoke"],
               a_estimator_gate=dict(pass_=g["gate_pass"], design=g["design"], cells=[
                   dict(cell=c["cell"], K=c["K"], P=c["P"], cell_pass=c["cell_pass"]) for c in g["cells"]]),
               b_compute_projection=dict(pass_=p["projection_pass"], reductions_applied=p["reductions_applied"],
                                         budget_days=p["budget_days"]),
               c_gsite=dict(pass_primary=s["gate_pass_primary"], per_W=s["per_W_instrument_like"]),
               c2_small_truth=dict(n_flagged_total=st["n_flagged_total"],
                                   n_flagged={k: v["n_flagged"] for k, v in st["sets"].items()},
                                   note="flags are reported (§11); they do not stop code lock"),
               code_lock_may_proceed=bool(g["gate_pass"] and p["projection_pass"]),
               note="G-SITE does not stop code lock; if it fails, P2-SITE and P2-ORACLE are reported as P3 (§5.4).",
               provenance=prov)
    _write_json(os.path.join(out, "codelock_passfail_record.json"), rec)
    _log(out, "[record] complete")
    return rec


# ---------------------------------------------------------------------------------------------------------------------
# status (no estimates)
# ---------------------------------------------------------------------------------------------------------------------
def status(out):
    plan_p = os.path.join(out, "plan.json")
    if not os.path.exists(plan_p):
        print(f"no run found in {out}")
        return
    plan = json.load(open(plan_p))
    n_gate = len(plan["gate_units"])
    n_tim = len(plan["timing_units"])
    d_gate = len(os.listdir(os.path.join(out, "work", "gate"))) if os.path.isdir(os.path.join(out, "work", "gate")) else 0
    d_tim = len(os.listdir(os.path.join(out, "work", "timing"))) if os.path.isdir(
        os.path.join(out, "work", "timing")) else 0
    pid_p = os.path.join(out, "runner.pid")
    alive = False
    if os.path.exists(pid_p):
        try:
            os.kill(int(open(pid_p).read().split()[0]), 0)
            alive = True
        except (OSError, ValueError):
            alive = False
    stages = {k: os.path.exists(os.path.join(out, f)) for k, f in (
        ("a_gate", "gate_PLACEHOLDER_cells.json"), ("b_projection", "projection_PLACEHOLDER.json"),
        ("c_gsite", "gsite_record.json"), ("c2_smalltruth", "small_truth_flags.json"),
        ("d_record", "codelock_passfail_record.json"))}
    print(f"run directory : {out}")
    print(f"runner alive  : {alive}")
    print(f"(a) gate      : {min(d_gate, n_gate)}/{n_gate} replicate units; complete={stages['a_gate']}")
    print(f"(b) projection: {min(d_tim, n_tim)}/{n_tim} timing units; complete={stages['b_projection']}")
    print(f"(c) G-SITE    : complete={stages['c_gsite']}")
    print(f"(c2) small-truth design check: complete={stages['c2_smalltruth']}")
    print(f"(d) record    : written={stages['d_record']}")
    logp = os.path.join(out, "progress.log")
    if os.path.exists(logp):
        last = open(logp).read().strip().splitlines()[-1:]
        print("last log line :", last[0] if last else "")
    print("(status shows progress only; no estimate or verdict is printed)")


# ---------------------------------------------------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    ap.add_argument("--stage", default="all", choices=["all", "gate", "projection", "gsite", "smalltruth", "record"])
    ap.add_argument("--status", action="store_true")
    a = ap.parse_args(argv)
    if a.status:
        status(a.out)
        return 0
    os.makedirs(a.out, exist_ok=True)
    plan = _plan(a.smoke)
    plan_p = os.path.join(a.out, "plan.json")
    if os.path.exists(plan_p) and json.load(open(plan_p))["smoke"] != a.smoke:
        raise SystemExit("existing run directory has a different smoke setting")
    _write_json(plan_p, plan)
    if not os.path.exists(os.path.join(a.out, "provenance.json")):
        _write_json(os.path.join(a.out, "provenance.json"), dict(
            code_commit=os.environ.get("SS_CODE_COMMIT"), code_snapshot=os.environ.get("SS_CODE_SNAPSHOT"),
            python=sys.version, numpy=np.__version__, pandas=pd.__version__,
            scipy=__import__("scipy").__version__, platform=platform.platform(), cpu_count=os.cpu_count(),
            workers=a.workers, start=time.strftime("%Y-%m-%d %H:%M:%S %z"),
            implementation_notes=IMPLEMENTATION_NOTES, code_dir=os.path.dirname(os.path.abspath(__file__))))
    _init_state()                         # build PLACEHOLDER designs/representations once; inherited by fork
    if a.stage in ("all", "gate"):
        stage_gate(a.out, plan, a.workers)
    if a.stage in ("all", "projection"):
        stage_projection(a.out, plan, a.workers)
    if a.stage in ("all", "gsite"):
        stage_gsite(a.out)
    if a.stage in ("all", "smalltruth"):
        stage_smalltruth(a.out)
    if a.stage in ("all", "record"):
        stage_record(a.out, plan)
    return 0


if __name__ == "__main__":
    sys.exit(main())
