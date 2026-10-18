"""§14 step 7 orchestrator behind scripts/run_step7.sh (orchestration only; never changes analysis code).

Step 7 = the locked final aggregation of the causal grid (§12.3 family verdicts, §11 cell metrics): the locked
`ss_benchmark.grid_driver.main`, run from the step-6 code snapshot with exactly the step-6 arguments. Every unit's
shard already exists, so `_unit` returns at once and `aggregate` writes replicates.csv, cell_metrics.csv and
families.json. No unit is recomputed; this is verified (shard count and SHA-256 digest before and after, run_plan.json
unchanged).

Preconditions (refused, exit 3, nothing changed):
* step 6 complete: <out6>/state.json status "complete"; step6_record/run_record.json present; shard count = planned
  units; the recomputed shard digest equals the recorded one; no step-6 process alive;
* HEAD == --expect-commit; clean tree; the step-6 launch commit is an ancestor of HEAD; between them nothing under
  ss_benchmark/ and no step-6 runner file changed; ss_benchmark/ = the SDR commit af56777 (CODELOCK_CORRECTION_001
  adapter excepted); the step-6 code snapshot is unchanged (code_snapshot.json hashes).
Records (committed automatically, records only, before anyone reads them; parent and file set verified):
  results/step6/run_record.json, results/step6/shard_sha256.txt.gz,
  results/step7/families.json, results/step7/cell_metrics.csv, results/step7/step7_manifest.json,
  results/step7/STEP7_RECORD.md
replicates.csv stays with the step-6 output (its SHA-256 is in step7_manifest.json); it is too large for git.
The report and figures (make_report.py, make_figures.py) are separate commands, run after this commit.

    python step7_orchestrate.py run --repo REPO --out6 DIR --expect-commit SHA
    python step7_orchestrate.py status --out6 DIR
"""
import argparse
import datetime
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import sys

PY = "/home/user/miniconda3/bin/python3"
SDR_COMMIT = "af56777e0f52b5c350dd7ba557d55b2394cbd4bf"
SDR_EXEMPT = frozenset({"ss_benchmark/models/prim_caformer.py"})
STEP6_FILES = ("scripts/run_step6.sh", "scripts/step6_orchestrate.py", "scripts/step6_grid_units.py")
PREFIX = "SS §14 step 7 record (automated, scripts/run_step7.sh)"
RECORDS = ("results/step6/run_record.json", "results/step6/shard_sha256.txt.gz", "results/step7/families.json",
           "results/step7/cell_metrics.csv", "results/step7/step7_manifest.json", "results/step7/STEP7_RECORD.md")
CODELOCK_ENV = dict(OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", NUMEXPR_NUM_THREADS="1",
                    PYTHONHASHSEED="0", PYTHONDONTWRITEBYTECODE="1")


class Refuse(Exception):
    pass


def now():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(16 << 20), b""):
            h.update(b)
    return h.hexdigest()


def jread(p, default=None):
    try:
        with open(p) as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def git(repo, *args, check=True):
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True,
                       env=dict(os.environ, GIT_OPTIONAL_LOCKS="0"))
    if check and r.returncode:
        raise Refuse(f"git {' '.join(args)} failed: {r.stderr.strip()[:200]}")
    return r.stdout.strip()


def shard_lines(grid):
    w = os.path.join(grid, "work")
    lines = []
    for s in sorted(os.listdir(w)):
        for f in sorted(os.listdir(os.path.join(w, s))):
            if f.endswith(".json"):
                lines.append(f"{s}/{f} {sha(os.path.join(w, s, f))}")
    return lines


class Step7:
    def __init__(self, a):
        self.a = a
        self.repo, self.out6 = os.path.abspath(a.repo), os.path.abspath(a.out6)
        self.grid = os.path.join(self.out6, "grid")
        self.snap = os.path.join(self.out6, "code_snapshot")
        self.state_p = os.path.join(self.out6, "step7_state.json")
        self.state = jread(self.state_p, {}) or {}

    def log(self, msg):
        line = f"{now()} {msg}"
        os.makedirs(os.path.join(self.out6, "logs"), exist_ok=True)
        with open(os.path.join(self.out6, "logs", "step7.log"), "a") as f:
            f.write(line + "\n")
        print(line, flush=True)

    def save(self, **kw):
        self.state.update(kw, updated=now())
        tmp = self.state_p + ".tmp"
        with open(tmp, "w") as f:
            json.dump(self.state, f, indent=1, sort_keys=True)
        os.replace(tmp, self.state_p)

    def preflight(self):
        if self.state.get("status") == "complete":
            raise Refuse("refused: step 7 is already complete for this step-6 output")
        st6 = jread(os.path.join(self.out6, "state.json"), {}) or {}
        if st6.get("status") != "complete":
            raise Refuse(f"refused: step 6 is not complete (state: {st6.get('status', 'absent')})")
        rr = jread(os.path.join(self.out6, "step6_record", "run_record.json"))
        plan = jread(os.path.join(self.grid, "run_plan.json"))
        if not rr or not plan:
            raise Refuse("refused: step-6 run record or run plan missing")
        for d in os.listdir("/proc"):
            if d.isdigit() and int(d) != os.getpid():
                try:
                    argv = open(f"/proc/{d}/cmdline", "rb").read().decode(errors="replace").split("\0")
                except OSError:
                    continue
                prog = any(x.endswith(("step6_orchestrate.py", "step6_grid_units.py")) or x == "ss_benchmark.grid_driver"
                           for x in argv)
                if prog and any(x.startswith(self.out6) for x in argv):
                    raise Refuse(f"refused: a step-6 process is still alive (pid {d})")
        lines = shard_lines(self.grid)
        if len(lines) != plan["n_units"]:
            raise Refuse(f"refused: {len(lines)} shards != {plan['n_units']} planned units")
        if hashlib.sha256("\n".join(lines).encode()).hexdigest() != rr["shard_digest"]:
            raise Refuse("refused: the shards differ from the step-6 record (digest mismatch)")
        launch, exp = st6["launch_commit"], self.a.expect_commit
        head = git(self.repo, "rev-parse", "HEAD")
        if head != exp:
            raise Refuse(f"refused: HEAD {head[:12]} is not --expect-commit {exp[:12]}")
        if git(self.repo, "status", "--porcelain", "--untracked-files=all"):
            raise Refuse("refused: working tree not clean")
        if subprocess.run(["git", "-C", self.repo, "merge-base", "--is-ancestor", launch, head],
                          env=dict(os.environ, GIT_OPTIONAL_LOCKS="0")).returncode:
            raise Refuse(f"refused: the step-6 launch commit {launch[:12]} is not an ancestor of HEAD")
        moved = [f for f in git(self.repo, "diff", "--name-only", launch, head).splitlines()
                 if f.startswith("ss_benchmark/") or f in STEP6_FILES]
        if moved:
            raise Refuse(f"refused: analysis or step-6 runner files changed since step 6: {moved[:5]}")
        sdr = set(git(self.repo, "diff", "--name-only", SDR_COMMIT, head, "--", "ss_benchmark").splitlines())
        if sdr - SDR_EXEMPT:
            raise Refuse(f"refused: ss_benchmark differs from the SDR commit: {sorted(sdr - SDR_EXEMPT)[:5]}")
        meta = jread(os.path.join(self.out6, "code_snapshot.json"), {}) or {}
        if meta.get("commit") != launch or any(sha(os.path.join(self.snap, r)) != h for r, h in
                                                meta.get("files", {}).items()):
            raise Refuse("refused: the step-6 code snapshot changed or belongs to another commit")
        return st6, rr, plan, lines

    def driver_args(self, st6):
        s = st6["settings"]
        args = ["--out", self.grid, "--workers", "1"]
        if st6.get("placeholder"):
            ph = s.get("placeholder") or {}
            args += ["--placeholder"] + (["--cells", ph["cells"]] if ph.get("cells") else []) + \
                    (["--max-reps", str(ph["max_reps"])] if ph.get("max_reps") else [])
        else:
            args += ["--reps", s["reps"], "--conditions", os.path.join(self.snap, "results/step5/grid_conditions.json"),
                     "--gsite", os.path.join(self.snap, "results/codelock_gate/gsite_record.json"),
                     "--projection", os.path.join(self.snap, "results/codelock_gate/projection_PLACEHOLDER.json")]
        return args

    def run(self):
        st6, rr, plan, lines = self.preflight()
        head = git(self.repo, "rev-parse", "HEAD")
        self.save(status="running", pid=os.getpid(), started=now(), expect_commit=head,
                  step6_launch_commit=st6["launch_commit"])
        plan_sha = sha(os.path.join(self.grid, "run_plan.json"))
        cmd = [PY, "-m", "ss_benchmark.grid_driver", *self.driver_args(st6)]
        self.log(f"step 7: preconditions passed (step 6 complete, {len(lines)} shards = plan, digest verified, HEAD "
                 f"{head[:12]}, ss_benchmark = SDR commit); aggregation: {' '.join(cmd)}")
        with open(os.path.join(self.out6, "logs", "step7_driver.log"), "a") as lf:
            rc = subprocess.run(cmd, cwd=self.snap, env=dict(os.environ, **CODELOCK_ENV), stdout=lf,
                                stderr=subprocess.STDOUT).returncode
        if rc:
            self.save(status="failed", exit=rc)
            raise SystemExit(f"STOP: the locked aggregation exited {rc}; see logs/step7_driver.log")
        after = shard_lines(self.grid)
        if after != lines or sha(os.path.join(self.grid, "run_plan.json")) != plan_sha:
            self.save(status="failed")
            raise SystemExit("STOP: shards or run plan changed during the aggregation")
        for f in ("replicates.csv", "cell_metrics.csv", "families.json"):
            if not os.path.exists(os.path.join(self.grid, f)):
                raise SystemExit(f"STOP: {f} not written")
        self.log("aggregation done; no unit recomputed (shard digest and run plan unchanged)")
        self.write_records(st6, rr, lines)
        self.commit(head)
        self.save(status="complete", finished=now())
        self.log("step 7 complete: records committed; run make_report.py / make_figures.py next")

    def write_records(self, st6, rr, lines):
        r6, r7 = os.path.join(self.repo, "results", "step6"), os.path.join(self.repo, "results", "step7")
        os.makedirs(r6, exist_ok=True)
        os.makedirs(r7, exist_ok=True)
        shutil.copy2(os.path.join(self.out6, "step6_record", "run_record.json"), os.path.join(r6, "run_record.json"))
        with gzip.GzipFile(os.path.join(r6, "shard_sha256.txt.gz"), "wb", mtime=0) as g:
            g.write(("\n".join(lines) + "\n").encode())
        for f in ("families.json", "cell_metrics.csv"):
            shutil.copy2(os.path.join(self.grid, f), os.path.join(r7, f))
        man = dict(step6_launch_commit=st6["launch_commit"], step6_shard_digest=rr["shard_digest"],
                   n_units=len(lines), placeholder=bool(st6.get("placeholder")),
                   outputs={f: dict(path=os.path.join(self.grid, f), bytes=os.path.getsize(os.path.join(self.grid, f)),
                                    sha256=sha(os.path.join(self.grid, f)))
                            for f in ("replicates.csv", "cell_metrics.csv", "families.json")},
                   command=f"{PY} -m ss_benchmark.grid_driver {' '.join(self.driver_args(st6))} (cwd {self.snap})",
                   thread_env=CODELOCK_ENV)
        with open(os.path.join(r7, "step7_manifest.json"), "w") as f:
            json.dump(man, f, indent=1, sort_keys=True)
        with open(os.path.join(r7, "STEP7_RECORD.md"), "w") as f:
            f.write(f"""# §14 step 7 record (written by scripts/run_step7.sh)

* Step 6: launch commit `{st6['launch_commit']}`; {len(lines)} unit shards, digest `{rr['shard_digest']}`
  (`results/step6/shard_sha256.txt.gz`, `results/step6/run_record.json`).
* Aggregation: the locked `ss_benchmark.grid_driver.main` from the step-6 code snapshot with the step-6 arguments
  (`step7_manifest.json`); every shard existed, none was recomputed (digest and run plan unchanged).
* `families.json`: §12.3 family verdicts (primary set; §10.3 sets reported separately, never entering verdicts).
* `cell_metrics.csv`: §11 metrics per set, cell and arm. `replicates.csv` stays with the step-6 output (SHA-256 in
  `step7_manifest.json`).
* Committed automatically, records only, before the report is written. §13 claim ceilings: `results/step5/section13.json`
  and the deferred rules, applied by `make_report.py`.
{'* PLACEHOLDER: this record comes from a PLACEHOLDER test run, not from DS203.' if st6.get('placeholder') else ''}
""")

    def commit(self, head):
        got = {l[3:] for l in git(self.repo, "status", "--porcelain", "--untracked-files=all").splitlines()}
        if got != set(RECORDS):
            raise SystemExit(f"STOP: untracked files {sorted(got)[:8]} are not exactly the step-7 records")
        git(self.repo, "add", "--", *RECORDS)
        git(self.repo, "commit", "-q", "-m", f"{PREFIX}: family verdicts, cell metrics, step-6 shard digest; "
                                             f"records only")
        new = git(self.repo, "rev-parse", "HEAD")
        changed = set(git(self.repo, "diff-tree", "--no-commit-id", "--name-only", "-r", new).splitlines())
        if git(self.repo, "rev-parse", f"{new}^") != head or changed != set(RECORDS) or \
                git(self.repo, "status", "--porcelain", "--untracked-files=all"):
            raise SystemExit("STOP: step-7 commit verification failed")
        self.save(record_commit=new)
        self.log(f"step-7 records committed: {new} (parent {head[:12]}; exactly {len(RECORDS)} files)")


def status(out6):
    st = jread(os.path.join(out6, "step7_state.json"), {}) or {}
    print(f"step 7: {st.get('status', 'not started')}" + (f"; record commit {st['record_commit']}"
                                                         if st.get("record_commit") else ""))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("run", "status"))
    ap.add_argument("--repo")
    ap.add_argument("--out6", required=True)
    ap.add_argument("--expect-commit")
    a = ap.parse_args(argv)
    if a.cmd == "status":
        return status(a.out6)
    try:
        Step7(a).run()
        return 0
    except Refuse as e:
        print(f"{now()} {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
