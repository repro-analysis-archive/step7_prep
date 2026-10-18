# §14 step 7: procedure (draft, 2026-10-09)

**Sources.**
* Frozen protocol `docs/SS_PROTOCOL_DS203.md` (`4c86dc5`): §11, §12, §13, §14 step 7.
* The locked grid driver (`ss_benchmark/grid_driver.py`, SDR commit `af56777`): `main`, `aggregate`.
* `ss_benchmark/grid.py`: `family_verdict`, `cell_metrics`.
* The step-6 runner (`scripts/run_step6.sh`, `scripts/step6_orchestrate.py`, `scripts/step6_grid_units.py`; committed by the chain).

Everything here is orchestration; no analysis code changes.

## 0. What step 7 is

* §14 says only "7. Report". The investigator defines step 7 as the **final aggregation and the family verdicts**, followed by the report.
* In the locked code, the aggregation is the last call of `grid_driver.main` (`aggregate`). It reads every unit shard and writes three files:

| output | contents | protocol |
|---|---|---|
| `replicates.csv` | one row per (set, cell, arm, replicate): estimate, SE, CI, truth, covered, diagnostics | — |
| `cell_metrics.csv` | per (set, cell, arm): mean truth, bias, \|bias\|, relative bias, coverage, bias / MC-SD, RMSE, CI width, support-failure rate, ESS and density-ratio range, small-truth flag | §11 |
| `families.json` | per set and family: D_j per cell, D̄_F, its 95 % percentile bootstrap CI (B = 2,000, seed 20261008, replicates resampled within cells, cells fixed), share of D_j > 0, the rule verdict, the conditions required and failed, and the reported verdict | §12.3 |

* In `families.json`, a family whose conditions fail is reported as "NOT TESTED (reported as P3 / descriptive)". The §10.3 sets carry `enters_verdicts: false`. Per-W P2 entries carry `instrument_like` (G-SITE ≤ 0.01).
* The step-6 runner deliberately suppressed `aggregate`. Step 7 reruns the locked `main` with **exactly the step-6 arguments**. Every unit's shard exists, so `_unit` returns immediately (`if os.path.exists(path): return path`), and `main` then calls `aggregate`.

## 1. Preconditions

All of these are checked by `run_step7.sh`, which refuses with exit 3 and changes nothing otherwise.

1. **Step 6 complete** (`<out6>/state.json`: `"status": "complete"`):
   * `step6_record/run_record.json` is present;
   * the number of shards equals `run_plan.json` `n_units` (73,200 for the real grid);
   * the SHA-256 digest recomputed over all shards equals the recorded `shard_digest`;
   * no step-6 process is alive.
2. **Provenance:**
   * HEAD = `--expect-commit`, the commit that adds the step-7 scripts;
   * the tree is clean;
   * the step-6 launch commit is an ancestor of HEAD;
   * between the two, **no file under `ss_benchmark/` and no step-6 runner file changed**.
3. **SDR commit check (§14 step 6, repeated):**
   * `ss_benchmark/` at HEAD is byte-identical to `af56777`, except the CODELOCK_CORRECTION_001 extraction adapter `ss_benchmark/models/prim_caformer.py`, which the grid does not import;
   * the step-6 code snapshot is unchanged (`code_snapshot.json` hashes).
4. Step 7 has not already completed for this step-6 output.

## 2. Exact command (what `run_step7.sh` runs)

```
cd /media/user/LaCie/medvideo_gate/ss_step6/code_snapshot
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONHASHSEED=0 \
PYTHONDONTWRITEBYTECODE=1 /home/user/miniconda3/bin/python3 -m ss_benchmark.grid_driver \
  --out /media/user/LaCie/medvideo_gate/ss_step6/grid \
  --reps /media/user/LaCie/medvideo_gate/ss_step4_5/step5/reps.npz \
  --conditions /media/user/LaCie/medvideo_gate/ss_step6/code_snapshot/results/step5/grid_conditions.json \
  --gsite /media/user/LaCie/medvideo_gate/ss_step6/code_snapshot/results/codelock_gate/gsite_record.json \
  --projection /media/user/LaCie/medvideo_gate/ss_step6/code_snapshot/results/codelock_gate/projection_PLACEHOLDER.json \
  --workers 1
```

* These are the step-6 arguments, taken from `<out6>/state.json` `settings`.
* `--workers` does not enter the unit list or `run_plan.json`, and no unit is computed, so 1 worker is used.
* The same thread settings as code lock and step 6.
* `run_step7.sh` verifies afterwards that the shard digest and `run_plan.json` are unchanged, i.e. that nothing was recomputed.

**Operator commands:**

```
cd /home/user/projects/medical_video_causal_gate
scripts/run_step7.sh --expect-commit <commit adding the step-7 scripts>    # or: setsid nohup … &
scripts/run_step7.sh --status
```

* **Logs:** `<out6>/logs/step7.log`, `step7_driver.log` and `step7_stdout.log`.
* **State:** `<out6>/step7_state.json`.

## 3. Expected runtime: about 10–30 min (estimate)

* 73,200 shard files (700,800 SDR records) on LaCie, read three times:
  * the digest before;
  * the aggregation (`json.load` of every shard into one DataFrame of 700,800 rows);
  * the digest after.
* Small-file reads on the rotational disk dominate (page cache helps on the second and third pass).
* The family bootstraps are cheap: B = 2,000 × at most 66 cells × M = 200 replicate indices per family.
* Memory: a few hundred MB.
* The PLACEHOLDER test (§6) measures only the plumbing, not this runtime.

## 4. What is committed

1. **By `run_step7.sh`, automatically, records only, before anyone reads them** (the same safeguard as the step-4 record). The commit is verified for parent, exact file set and a clean tree. Files:
   * `results/step6/run_record.json` (step-6 settings, run plan, shard counts, shard digest);
   * `results/step6/shard_sha256.txt.gz` (per-shard SHA-256 list; deterministic gzip);
   * `results/step7/families.json`;
   * `results/step7/cell_metrics.csv`;
   * `results/step7/step7_manifest.json` (SHA-256 and size of `replicates.csv`, `cell_metrics.csv` and `families.json`; the exact command; the thread settings);
   * `results/step7/STEP7_RECORD.md`.

   `replicates.csv` (700,800 rows) stays with the step-6 output on LaCie. It is too large for git; its SHA-256 is committed.
2. **By the investigator, after review:**
   * the report (`make_report.py` → `results/step7/REPORT.md` and `report_cells.csv`);
   * the figures and tables (`make_figures.py` → `results/step7/figures/*.pdf`, `tables/*.csv`);
   * the step-7 scripts themselves, committed before `run_step7.sh` runs (they are part of `--expect-commit`).

```
/home/user/miniconda3/bin/python3 scripts/make_report.py --step7 results/step7 --step5 results/step5 \
    --gsite results/codelock_gate/gsite_record.json --out results/step7/REPORT.md
/home/user/miniconda3/bin/python3 scripts/make_figures.py --step7 results/step7 --step5 results/step5 \
    --out results/step7/figures      # main slice W = 30, α = 0.5, γ = 1 (defaults)
```

## 5. §13 claim ceilings that apply after step 7

**(a) Pre-grid ceilings,** fixed at step 5 by the committed §13 record (`results/step5/section13.json`). These are E1 / E2 / E3-site / MLP margin / E3-state / G-SITE.
* Each triggered rule limits what may be said about FM-vs-FM−C, FM-vs-NV, or the FM−C arms.

**(b) Rules evaluable only now** (deferred at step 5):
* **Negative result.** If E1 and E3 (both components) pass but P1b-FM and P2-FM are INCONCLUSIVE, the statement is "encoded site information did not change causal behaviour here" (§13). Mechanically:
  * `fm_conditions_primary` (key P) all true;
  * G-SITE passed;
  * `families.json` `primary:P1b-FM` and `primary:P2-FM` both have verdict INCONCLUSIVE.
* **Verdict wording** (§12.3, §13). SUPPORTED → "consistent with the theory-motivated direction". CONTRADICTED → "inconsistent with the theory-motivated direction". No family result is stated as a confirmation of the theory maps.

**(c) Standing rules:**
* Headline directional claims come only from family verdicts (primary set). Single cells are descriptive, and all cells are reported (§12.3).
* P3 cells and comparisons: no directional prediction; reported against the maps (§12.2).
* A family whose conditions fail is "NOT TESTED", reported as P3 / descriptive (§12.2, §5.4).
* §10.3 sets are reported separately and never enter family verdicts. Per-W P2 results are instrument-like only if that set's G-SITE ≤ 0.01 (code lock: W0 0.0037, W5 0.0045); otherwise they are descriptive.
* Cells with small truth (|truth| < 0.025) are flagged (§11); 0 cells were flagged at code lock.
* Fixed wording:
  * E3-site wording, "no longer exceeds the prespecified linear site-encoding boundary";
  * the native arm is attributed to acquisition shortcuts;
  * the REF caveats;
  * the FULL arm is an exchangeability oracle / implementation sanity reference, and its finite-sample bias is reported;
  * "video-derived representations" wording;
  * all claims describe a deliberately constructed orthogonal benchmark.
* §1: no causal effect in DS203 is estimated.
* **`make_report.py`** applies (a)–(c) mechanically from `section13.json`, `checks.json`, `gsite_record.json` and `families.json`.

## 6. PLACEHOLDER test of this procedure (2026-10-09)

Results are in `PLACEHOLDER_test/run_step7_tests_PLACEHOLDER.log`.
* **Setup.** A throwaway copy of the repository (`cp -a`; no git command in the original) with:
  * PLACEHOLDER step-5 / §13 records;
  * the staged step-6 runner;
  * a tiny PLACEHOLDER step-6 run (1 cell, 1 replicate, 3 units);
  * a commit adding the step-7 scripts.

| # | test | result |
|---|---|---|
| R1 | step 6 not complete | refused, exit 3 |
| R2 | `--expect-commit` ≠ HEAD | refused, exit 3 |
| R3 | untracked file | refused, exit 3 |
| R4 | one shard altered after step 6 | refused (digest mismatch), exit 3 |
| R5 | `ss_benchmark/` changed since the step-6 launch commit | refused, exit 3 |
| R6 | full run | locked aggregation in 11 s; no unit recomputed (digest and run plan unchanged); records-only commit of exactly the 6 files, parent = HEAD, repository identity, clean tree |
| R7 | relaunch after completion | refused, exit 3 |
| R8 | `make_report.py` / `make_figures.py` on the committed 1-cell records | written |

* The copy was deleted afterwards.
* `make_report.py` and `make_figures.py` were also run on a larger PLACEHOLDER grid: 70 units (24 primary cells, all six families, the §10.3 sets), with aggregation on and PLACEHOLDER step-5 checks for all four representation keys (`PLACEHOLDER_test/`).

## 7. Points the protocol leaves open (decided here, for the investigator to confirm)

1. **Aggregation step.** §14 step 6 says "run the causal grid … and commit", and step 7 says "Report". The protocol does not assign the aggregation (`families.json`) to either. Following the investigator, it is step 7.
2. **Who commits the step-6 / step-7 outputs.** The protocol does not say. Here the aggregation records are committed automatically, records only, before anyone reads them; report and figures follow by hand.
3. **Large outputs.** `replicates.csv` is not committed (size); its SHA-256 is.
4. **§13 "fail on the 158-case set"** is read as "E1 and E3-site do not both pass on the 158-case set". This matches the §12.2 conditions and the locked `fm_conditions`; it is already fixed in the §13 record.
5. **Sensitivity-set families beyond §10.3's stated scope.** §10.3 names the P1b and P2 families for the per-W sets. For every set, the locked `aggregate` computes every family whose two arms exist, over the family cells present in that set. `families.json` therefore also holds, for example, `W0:P1a` over the α = 0 P1b cells. These entries never enter verdicts. **Resolved 2026-10-09:** `make_report.py` lists them only in an exploratory section, never as verdicts.
6. **Single-file family conditions.** §10.3 runs E1–E3 on the single-file set, and step 5 computes them (`E1_single_file`, `E3_site_single_file`, `E3_state_single_file`). The locked `aggregate`, however, applies the primary-set conditions to the single-file families (`conditions.get(s, conditions["primary"])`), and `grid_conditions.json` holds only `primary`. This affects sensitivity entries only.
   **Resolved 2026-10-09 (report layer; locked code unchanged):** the locked verdict is kept and labelled "locked aggregation". Next to it, the report states the "protocol-consistent ceiling" from each set's own step-5 E1–E3. The per-W sets have no own E1–E3, so their FM comparisons are descriptive only.
7. **Figure slice.** Figures 1–2 show one (W, α, γ) slice, φ_A = 0. **Decided by the investigator 2026-10-09** (`PRESENTATION_DECISIONS.md`): the main-text slice is W = 30, α = 0.5, γ = 1, primary set, and the supplementary heatmaps cover every cell. The earlier W = 5 default and the averaged heatmap were dropped.
