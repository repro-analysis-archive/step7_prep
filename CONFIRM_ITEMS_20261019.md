# Repository-based [TO CONFIRM] items of the evaluator record (task v2)

Written 2026-10-20, read only (task `CC_TASK_SS_confirm_items_v2.md`). Nothing was modified in the main repository
(`/home/user/projects/medical_video_causal_gate`, HEAD `2880d73`), `/srv/ss_exploratory` (HEAD `1c8e628`),
`/srv/ss_exploratory_B` (HEAD `458341f`) or on LaCie. Line numbers refer to the file at the commit named. The quoted
excerpts, with line numbers, are in the audit bundle (`excerpts/`); the recomputation script and its output are
`recompute_item1_item4.py` / `.out`.

| item | answer | discrepancy |
|---|---|---|
| 1. D definition vs implementation | Numerator, P1/P2 orientation, denominator, averaging and bootstrap in the locked code match §12.3. D̄ recomputed from `report_cells.csv`: P1b-SITE 2.1976168635785953, P2-SITE 0.05210508364589429; reported 2.198 and 0.052 (`families.json` 2.197616863578595 and 0.052105083645894015). | None in definition or value. The code also resamples the truths with the same indices, so Ψ̄_j is recomputed on each resample; §12.3 neither states nor excludes this. REPORT.md names D_j "oriented relative difference (positive = as predicted)" without writing out the formula. |
| 2. Mask check | ρ_c: centre 2 0.5625, 3 0.703125, 4 0.703125, 5 0.703125; min_c ρ_c 0.5625; r 0.45; valid ("r = 0.45 stands"); fallback r = 0.98 × min_c ρ_c not used. | Per-centre profiles are recorded in the step-4 record (`mask_check.json`) but not reported in `RESULTS_20261019` (REPORT.md, figures, tables); `METHODS_DRAFT.md` line 81 still has "[TO FILL: r …]". §3.1 line 147 says "The profiles are reported." |
| 3. Execution order | 0ebf2cf 2026-10-12 14:26:41 +0900; 7adaf13 2026-10-12 14:26:41 +0900 (0ebf2cf → 0667430 → 7adaf13 by ancestry). Step-6 grid start 14:26:42 with 0 shards; first completed unit 14:27:03.80 +0900. The first unit follows 0ebf2cf. | None. The three commits share one second; their order is given by ancestry, not by time. |
| 4. X1/X2 Δ vs protocol D | Denominator (per-cell mean truth, identical to step 6 in 1278/1278 rows), numerator form (|mean(Ψ̂ − Ψ)|) and paired bootstrap (B = 2,000, cells fixed, same indices for both arms) match. Recomputed group mean 0.5609627059097283 = recorded 0.5609627059097283 (reported 0.561). | Δ is A − B (X arm minus step-6 arm), not oriented by family prediction: for P2 cells against step-6 FM-k it is the negative of the §12.3 P2 orientation. Bootstrap seed names differ from step 6 ("exploratory:…" vs "family:<F>"), and Δ has a per-cell interval with no §12.3 counterpart. |

## 1. D definition vs implementation

**Sources.**
* Protocol: `docs/SS_PROTOCOL_DS203.md` at `4c86dc5`, §11 lines 639–656 and §12.2–12.3 lines 705–737.
* Locked aggregation code: `ss_benchmark/grid.py` (`_d_values`, lines 88–95; `family_verdict`, lines 98–132), called
  by `ss_benchmark/grid_driver.py` `aggregate` (lines 117–159, call at line 149). The git blob of `grid.py` is
  `77abcd611ce2995188d172375321164578cd00c1` and that of `grid_driver.py`
  `fcebb451cda10e3b1155a4b70896d31eb3058314`. Both are identical at `98cba1e` (code lock), `af56777` (SDR commit),
  `7adaf13` (step-6 launch) and `2880d73`, and in the step-6 code snapshot on LaCie
  (`/media/user/LaCie/medvideo_gate/ss_step6/code_snapshot/ss_benchmark/`).
* Step 7 ran the locked `ss_benchmark.grid_driver` from that snapshot (`scripts/step7_orchestrate.py` lines 1–8 and
  177 at `2880d73`).
* Report: `/srv/ss_step6_prep/step7_prep/RESULTS_20261019/REPORT.md` (step7_prep `a6c8880`), lines 12–22.

| component | protocol (4c86dc5) | locked code (grid.py at 2880d73) | REPORT.md | finding |
|---|---|---|---|---|
| bias | §11 line 642: "absolute bias \|mean_r(Ψ̂_r − Ψ_r)\|" | lines 90–91: `b_w = (est_w - truth).mean(0)`, `b_wo = (est_wo - truth).mean(0)` | line 120: "Relative bias = mean(Ψ̂ − Ψ) / mean Ψ" | same |
| with / without C | §12.2 lines 712, 714: P1b-SITE "SITE < NV", P2-SITE "SITE ≥ NV" | lines 63, 65: `"P1b-SITE": ("SITE", "NV", "P1", …)`, `"P2-SITE": ("SITE", "NV", "P2", …)` (with-C arm, without-C arm) | lines 19, 21: "SITE vs NV" | same |
| P1 orientation | line 722: "P1: D_j = (\|b_without C\| − \|b_with C\|) / Ψ̄_j" | lines 93–94: `if kind == "P1": return (np.abs(b_wo) - np.abs(b_w)) / psi` | line 14: "oriented relative difference per cell (positive = as predicted)" | same |
| P2 orientation | line 723: "P2: D_j = (\|b_with C\| − \|b_without C\|) / Ψ̄_j" | line 95: `return (np.abs(b_w) - np.abs(b_wo)) / psi` | line 14 (as above) | same |
| denominator | line 721: "Ψ̄_j the mean truth" | line 92: `psi = truth.mean(0)`, over the cell's replicates with finite estimates in both arms and finite truth (lines 109–111) | not stated beyond "relative" | same; `dropped_nonfinite` = 0 in every P1b-SITE and P2-SITE cell, so Ψ̄_j is over all 200 replicates |
| averaging | line 724: "D̄_F = mean_j D_j" | lines 116–117: `D = np.asarray(D)`, `Dbar = float(D.mean())` (unweighted, over the family's cells) | line 14: "D̄_F = mean over the family's cells" | same |
| cells | lines 712, 714: 48 cells (W = 0, P ∈ {5, 30}); 18 cells (K = 1, P = 0) | lines 63, 65, 70: predicates `c.W == 0 and c.P in (5, 30)`, `c.K == 1 and c.P == 0`; sizes 48, 18 | lines 19, 21: 48, 18 | same |
| bootstrap | lines 725–729: replicates resampled within each cell, same indices for both arms; B = 2,000; seed 20261008; cells not resampled | line 105: `seeds.rng(np.random.SeedSequence(SEED_BOOTSTRAP), f"family:{name}")`; line 114: `rng.integers(0, M, size=(n_boot, M))` per cell in increasing index (line 103); line 115: the same indices for `ew`, `ewo` and `tr`; `n_boot = N_BOOTSTRAP` = 2000 and `SEED_BOOTSTRAP` = 20261008 (`constants.py` lines 73, 17); lines 118–119: 2.5 / 97.5 percentiles of D̄*; cells not resampled | line 14: "95 % percentile bootstrap over replicates within cells (B = 2,000, seed 20261008)" | same. The truths are resampled with the same indices, so Ψ̄_j is recomputed on each resample (`grid.py` lines 9–10: "D̄_F is recomputed on each resample (biases and mean truth of every cell)"); §12.3 does not state this |
| verdict rule | lines 731–733 | lines 121–126 | line 14 | same |

**Recomputation from `report_cells.csv`.**
* Inputs: primary set, arms SITE and NV, columns `abs_bias` and `mean_truth`. There are 2,880 primary rows, with
  `M` = `M_finite` = 200 in every row. `mean_truth` is identical between SITE and NV in every cell used.
* Formulas: P1 D_j = (abs_bias_NV − abs_bias_SITE) / mean_truth; P2 D_j = (abs_bias_SITE − abs_bias_NV) /
  mean_truth.

| family | cells | recomputed D̄ | `families.json` (2880d73) D_bar | difference | REPORT.md D̄_F | max \|D_j − `D_cells`\| | share D_j > 0 (recomputed / recorded) |
|---|---:|---:|---:|---:|---:|---:|---|
| P1b-SITE | 48 (18 … 203) | 2.1976168635785953 | 2.197616863578595 | 4.4e-16 | 2.198 | 8.9e-15 | 1.0 / 1.0 |
| P2-SITE | 18 (0 … 17) | 0.05210508364589429 | 0.052105083645894015 | 2.8e-16 | 0.052 | 1.1e-15 | 1.0 / 1.0 |

Recorded intervals (`families.json`): P1b-SITE [2.1672177596777806, 2.2258719276527437], P2-SITE [0.04765917337663384,
0.056192079000649306]; REPORT.md lines 19 and 21: [2.167, 2.226] and [0.048, 0.056]. The intervals were not
recomputed: they need the per-replicate estimates, which `report_cells.csv` does not contain.

## 2. Mask check (step-4 record at 8d4c61a)

**Rule:** `docs/SS_PROTOCOL_DS203.md` at `4c86dc5`, §3.1 step 3, lines 142–147:
> "The visible radius ρ_c is the largest ρ with m_c(ρ′) ≥ 0.25 × median{m_c(ρ″): ρ″ ≤ 0.1} for all ρ′ ≤ ρ." /
> "If min_c ρ_c ≥ 0.45, r = 0.45 stands. Otherwise r = 0.98 × min_c ρ_c. No other value is permitted." / "The
> profiles are reported."

**Record:** `results/step4/mask_check.json` at `8d4c61a`. Its SHA-256 is
`81c8eb46fa7abba4cb5024e073e30cc838c011d2d62488abbde72d73434d58d5`, identical to
`/media/user/LaCie/medvideo_gate/ss_step4_5/step4/mask_check.json`.

| centre | ρ_c (`visible_radius`, lines 1475–1478) | frames (`profiles.<c>.n_frames`) | profile points (ρ from 0.00390625 to 0.703125) |
|---|---:|---:|---:|
| 2 | 0.5625 | 2820 | 180 |
| 3 | 0.703125 | 2797 | 180 |
| 4 | 0.703125 | 4850 | 180 |
| 5 | 0.703125 | 7093 | 180 |

* min_c ρ_c: `"min_visible_radius": 0.5625` (line 2).
* Final r: `"r": 0.45` (line 1473).
* Pass / fail: `mask_check.json` has no pass/fail field. The validity check is recorded in two places:
  * `results/step4/run_meta.json` at `8d4c61a`, line 5: `"mask_check_valid": true`;
  * `/media/user/LaCie/medvideo_gate/ss_step4_5/logs/progress.log`, line 234:
    "2026-10-07T21:33:51+09:00 mask check valid (r = 0.45 stands)".
* Validation code: `scripts/step4_5_orchestrate.py` at `8d4c61a`, lines 192–206 and 604–609. Its message is
  "r = 0.45 stands" when r = 0.45 and "single frozen fallback applied (r = 0.98 x min_c rho_c)" otherwise.
* Fallback: not used. min_c ρ_c = 0.5625 ≥ 0.45, so r = 0.45 (`ss_benchmark/preprocess.py` at `8d4c61a`, lines
  182–183; constants `MASK_RADIUS = 0.45`, `MASK_CHECK_THRESHOLD = 0.25`, `MASK_CHECK_CENTRAL_RHO = 0.1`,
  `MASK_CHECK_SHRINK = 0.98`, `constants.py` lines 36–39).
* For centres 3–5, ρ_c equals the last profile point, 0.703125. `preprocess.py` lines 173–174 return `rho[-1]` when
  no point falls below the threshold.
* Per-centre profiles:
  * They are recorded in the committed step-4 record (`profiles.<c>.rho` and `.m`, 180 values per centre;
    `mask_check.json` lines 3–1472).
  * They are not reported in `RESULTS_20261019` (no mask, profile or ρ_c entry in REPORT.md; the figure and table
    files are fig1–fig4, figS1–figS3 and table1–table3).
  * `METHODS_DRAFT.md` line 81 (step7_prep): "Value used: [TO FILL: r from `results/step4/mask_check.json`]".
* Log note, not assessed:
  * `/media/user/LaCie/medvideo_gate/ss_step4_5/logs/mask_check.log` has 1,087 lines; 842 of them contain the ffmpeg
    message "Broken pipe". The log also contains "non monotonically increasing dts" messages.
  * The unit's last log line is "===== 2026-10-07T21:33:51+09:00 exit 0".

## 3. Execution order

| commit | author / committer time | parent | subject |
|---|---|---|---|
| `8d4c61a` | 2026-10-12 13:34:22 +0900 | `9e1aa71` | SS §14 step 4 record |
| `0ebf2cf632d752cdf5136473a3b6e368c0e5094c` | 2026-10-12 14:26:41 +0900 | `8d4c61a` | SS §14 step 5 record (automated, chain_5_to_6.sh) |
| `066743094ebc0d74b283fee4b6fb4afd282709ba` | 2026-10-12 14:26:41 +0900 | `0ebf2cf` | SS §13 applied mechanically |
| `7adaf133f8eaac9cf790d5320c2dd4b48d0b05cc` | 2026-10-12 14:26:41 +0900 | `0667430` | SS §14 step 6 runner and records |

* Git commit times have one-second resolution. The three commits share 14:26:41, and their order follows from
  ancestry: 0ebf2cf → 0667430 → 7adaf13.
* Step-6 log: `/media/user/LaCie/medvideo_gate/ss_step6/logs/progress.log`, lines 1–3:
  * "2026-10-12T14:26:42+09:00 preflight passed: HEAD 7adaf133f8ea; clean tree; step-5 and §13 records committed; …"
  * "… code snapshot of 7adaf133f8ea created (46 files)"
  * "2026-10-12T14:26:42+09:00 grid: start (attempt 1); 0 shards present"
  * This is the only "attempt" line in the log.
* First completed step-6 unit:
  * The unit files carry no timestamp field, so the file modification time is used.
  * The earliest mtime among the 73,200 unit files in `/media/user/LaCie/medvideo_gate/ss_step6/grid/work/` is
    `primary/c000_r0015.json`, **2026-10-12 14:27:03.80 +0900**. The next are c000_r0002 and c000_r0003 at
    14:27:04.11.
  * `grid.log` line 2, the first progress line, reads "2026-10-12 14:44:26 732/73200 units".
  * Step 7 did not rewrite the shards: `scripts/step7_orchestrate.py` at `2880d73`, lines 4–5, says "Every unit's
    shard already exists, so `_unit` returns at once".
* **The first unit follows 0ebf2cf:**
  * the first unit file is dated 14:27:03.80, 22.8 s after the 0ebf2cf commit time (14:26:41) and after 7adaf13;
  * the runner recorded 0 shards present when it started at 14:26:42.

## 4. X1/X2 Δ vs protocol D

**Sources.**
* `xplore/x_compare.py` at `015595d`: docstring lines 1–13, `_delta` lines 106–108, `paired_arrays` lines 111–118,
  `compare` lines 125–170, pairing check lines 66–85.
* `xplore/common.py` at `015595d`, line 30 (comparator mapping).
* `results_X/X_REPORT.md` at `1c8e628`: line 5 (definition) and line 64 (group row).
* Protocol §12.3 as in item 1.

| component | X (015595d / 1c8e628) | protocol D (§12.3) / step 6 | finding |
|---|---|---|---|
| definition | X_REPORT.md line 5: "Δ = (\|bias_A\| − \|bias_B\|) / mean truth, with A the X arm and B the step-6 comparator; negative Δ means the X arm had the smaller \|bias\|"; `_delta` line 108: `(np.abs((eA - tr).mean(-1)) - np.abs((eB - tr).mean(-1))) / tr.mean(-1)` | `grid._d_values` lines 90–95 | same form: \|mean(Ψ̂ − Ψ)\| differences over mean truth |
| denominator | `tr.mean(-1)`, with `tr` the X arm's truths (line 115) over the cell's 200 paired replicates. The pairing check (lines 66–85) requires the X truths to equal the step-6 truths exactly: 28,400 pairs checked, passed (`x_pairing_c0.json`) | Ψ̄_j = mean truth of the cell (grid.py line 92) | same. `mean_truth` in `x_comparisons_cells.csv` equals the step-6 `mean_truth` in `report_cells.csv` (primary, same cell, comparator arm) exactly in 1278 / 1278 rows. `abs_bias_B` equals the step-6 `abs_bias` in 1276 / 1278 rows; the other 2 differ by ≤ 4.4e-16 |
| sign | A − B, A = X arm (k−C), B = step-6 k−C, FM-k or NV (`comparator_arm`, line 37; `SITE_RETAINED`, common.py line 30); not oriented by family prediction | oriented: P1 = without C − with C, P2 = with C − without C | **differs by definition.** Against step-6 FM-k (the with-C arm), Δ = (\|b_X k−C\| − \|b_FM-k\|)/Ψ̄ has the P1 orientation with the X arm in the without-C position. For P2 cells, the §12.3 orientation would be −Δ. The comparators step-6 k−C and NV have no §12.3 counterpart |
| non-finite | `paired_arrays` line 117: finite `eA`, `eB`, `tr`; count reported as `dropped_nonfinite` | grid.py lines 109–111 (same filter) | same; 0 dropped in all 1,278 rows |
| bootstrap | per cell (lines 136–138): `rng.integers(0, M, size=(n_boot, M))`, same indices for `eA`, `eB`, `tr`. Per group (lines 153–162): one generator per comparison and group; a (B, M) index matrix per cell in increasing index; mean over the group's cells; cells fixed. 2.5 / 97.5 percentiles. `N_BOOTSTRAP`, `SEED_BOOTSTRAP` from the locked constants (line 23): 2,000; 20261008 | §12.3 lines 725–729; grid.py lines 103–119 | same scheme. Differences: (i) seed children are named "exploratory:<X>:<arm>:step6-<B arm>:<cell \| group>" instead of "family:<F>", so the resample indices differ from the step-6 family bootstrap; (ii) Δ also has a per-cell interval, which §12.3 does not define |

**Recomputation (X1, FM-P-C vs step-6 FM-P, P1b-FM cells), from `x_comparisons_cells.csv`.**
* 48 cells; mean of `delta` = **0.5609627059097283**.
  * `x_comparisons_groups.csv` `mean_delta` = 0.5609627059097283 (difference 0.0).
  * X_REPORT.md line 64: "| X1 | FM-P-C | step6 FM-P | P1b-FM | 48 | 0.561 | [0.549, 0.573] | 0 |".
* The same mean from `(abs_bias_A − abs_bias_B) / mean_truth` = 0.5609627059097284. Over all 1,278 rows, `delta`
  equals `(abs_bias_A − abs_bias_B) / mean_truth` to within 6.2e-15.
* Cells with Δ < 0: 0. `dropped_nonfinite` = 0; M = 200.
* Recorded interval (`x_comparisons_groups.csv`): [0.5494309963021069, 0.5731958014130013]; not recomputed (needs the
  per-replicate estimates).
