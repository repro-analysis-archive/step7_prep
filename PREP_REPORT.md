# Step-7 / paper preparation: report (2026-10-09)

**Task.** `CC_TASK_SS_step7_paper_prep_v1.md`. All work is in `/srv/ss_step6_prep/step7_prep/`.

**Hard limits kept:**
* no write and no git command in the repository (files read with `cat` / `cp` only);
* A, the chain, `repo_files/`, the watchdog and LaCie untouched;
* nothing installed; the base Python was used only to run scripts;
* at most 2 CPUs (18–19) and under 4 GB (peak PSS 1.3 GB for the grid, 2.0 GB for the checks);
* no real-design computation; PLACEHOLDER only.

## Files

| file | purpose |
|---|---|
| `STEP7_PROCEDURE.md` | §1: preconditions, exact command, runtime, outputs, claim ceilings, what is committed, open points |
| `run_step7.sh`, `step7_orchestrate.py` | §1: orchestration-only step-7 runner (to be copied to `scripts/`) |
| `make_report.py` | §2: results report (Markdown plus `report_cells.csv`) |
| `make_figures.py` | §3: figures 1–4 (vector PDF) and Tables 1–3 (CSV + Markdown) |
| `METHODS_DRAFT.md` | §4: Methods, results-independent; 15 `[REF: …]` and 11 `[TO FILL: …]` placeholders |
| `make_placeholder_inputs.py` | PLACEHOLDER test inputs from the locked code (a `cp` of `ss_benchmark/` in `locked/`) |
| `PLACEHOLDER_test/` | every PLACEHOLDER output: grid, step 5, report, figures, PNG previews, `run_step7` test log |
| `apply_section13_copy.py`, `memguard.sh` | test helpers: a copy of the staged §13 applicator; a PSS memory guard |

## PLACEHOLDER test results

* **Grid.** The locked `grid_driver --placeholder`, aggregation on, as at step 7:
  * 70 units: 24 primary cells over K ∈ {1, 2, 5} × P ∈ {0, 5, 30} at W = 0, plus W ∈ {5, 30}, two α = 0 cells and one φ_A cell; M = 2; the §10.3 sets;
  * output: `families.json` (19 entries), `cell_metrics.csv` (286 rows), `replicates.csv`.
  * K = 15 was left out. Its units took 15–20 min each on 2 CPUs; the first run was stopped and rerun without it, reusing the 30 finished shards.
* **Step 5.** The locked `pipeline.run_checks` on PLACEHOLDER representations of all four keys (n_boot = 200): 65 min on 2 CPUs.
  * Outputs: `checks.json`, `reps_report.json`, and the §13 record via the staged applicator (32 rule evaluations).
* **`make_report.py`** produced `PLACEHOLDER_test/report/REPORT_PLACEHOLDER.md`, bannered PLACEHOLDER, with:
  * the family verdicts and the §10.3 tables;
  * the pre-grid ceilings and the two deferred rules, evaluated mechanically;
  * the E1–E3 / LEACE / G-SITE tables;
  * per-cell relative-bias and coverage pivots by arm.
* **`make_figures.py`** produced four PDFs with embedded TrueType fonts and a PLACEHOLDER watermark, plus Tables 1–3.
  * After looking at the PNG previews, three layout defects were fixed: a clipped label, overlapping titles, and markers in empty heatmap cells.
* **`run_step7.sh`** (throwaway repository copy; tiny step-6 PLACEHOLDER run):
  * R1–R5 refused correctly: step 6 incomplete, wrong commit, dirty tree, altered shard, analysis code changed;
  * R6 full run: 11 s, no unit recomputed, records-only commit verified;
  * R7 relaunch refused;
  * R8 report and figures ran on the committed records.
  * An initial false refusal (the substring `step6_` in the staging path) was found and fixed before the final tests.

## Ambiguities to confirm

Details: `STEP7_PROCEDURE.md` §7.

1. The protocol does not assign the aggregation (`families.json`) to step 6 or 7. Treated as step 7, per the investigator.
2. Who commits step-6 / step-7 outputs is unspecified. Here: an automatic records-only commit before anyone reads them; report and figures by hand. `replicates.csv` is not committed (size); its SHA-256 is.
3. The locked aggregation computes sensitivity-set families beyond §10.3's stated P1b / P2 scope (e.g. `W0:P1a`). They are reported separately and never enter verdicts.
4. Single-file families use the primary-set E1 / E3 conditions in the locked code, not the single-file E1–E3 that step 5 computes.
5. The figure slice (W = 5, α = 0.5, γ = 1) is a presentation choice; it is not fixed by the protocol. **Decided 2026-10-09:** W = 30, α = 0.5, γ = 1, plus all-cell supplementary heatmaps (`PRESENTATION_DECISIONS.md`).
6. Methods inputs not in the records:
   * single-file counts per centre (other than centre 2: 13);
   * the watchdog's existence and log location: not found on the machine on 2026-10-07;
   * the chain's actual launch time: its process started on 2026-10-07 09:36, not on Friday;
   * the final step-4 / chain / step-7 commits.
7. Runtime: step 7 should take about 10–30 min (an estimate dominated by reading 73,200 shard files on the rotational disk three times; the PLACEHOLDER run cannot measure it).

## Follow-up fixes (2026-10-09, `CC_TASK_SS_step7_prep_fixes_v1.md`)

1. **Background shells stopped.** Two of my waiting loops from the PLACEHOLDER grid test were still running: pid 1120791 (task `bpw1k9yvz`) and pid 2079585 (task `bl7jxh8wp`).
   * Each was `until grep … || ! pgrep -f "ss_benchmark.grid_driver --out …step7_prep"; do sleep …`, at 0.0 % CPU and about 3.7 MB RSS.
   * They never ended because the `pgrep -f` pattern matched their own command line.
   * Both were stopped; `ps` then showed nothing from `step7_prep` running. A, the watchdog and the chain were not signalled.
2. **Figure slice** fixed in `PRESENTATION_DECISIONS.md`:
   * main text: W = 30, α = 0.5, γ = 1, primary set;
   * supplementary: heatmaps of every cell (S1 contrasts, S2 relative bias, S3 coverage).
   * `make_figures.py` was updated, and the PLACEHOLDER figures were regenerated from the existing outputs. The supplementary PDFs have 10, 24 and 24 pages. The main-slice panels are sparse because the PLACEHOLDER grid has W = 30 cells only for K ∈ {1, 5} at P = 0.
3. **Sensitivity sets.** `make_report.py` now shows, per named §10.3 family:
   * the locked verdict, labelled "locked aggregation";
   * the protocol-consistent ceiling from the set's own step-5 E1–E3. For the per-W sets, which have no own E1–E3, FM comparisons are descriptive only.

   Families outside §10.3 (e.g. W0:P1a) appear only in an exploratory section. Re-tested on the PLACEHOLDER outputs, plus two failure paths: own-set E1 failing makes the single-file FM families NOT TESTED; a per-W G-SITE failure makes per-W P2 descriptive.
4. **Methods.**
   * Watchdog and chain launch facts added.
   * Single-file per-centre counts filled from `ss_window_offsets.csv` (13 / 34 / 44 / 32). The per-W counts were confirmed from `ss_window_offsets_perW.csv` (37 / 40 / 57 / 70; 37 / 40 / 56 / 68), with set sizes from `ss_gsite_perW.json`.
   * Sensitivity-ceiling and presentation sentences added; Table 1 updated.
   * `OPERATIONS_LOG_ADDENDUM.md` written; the chain's staged copy was not edited.
