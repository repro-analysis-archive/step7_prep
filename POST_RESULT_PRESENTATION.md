# Post-result presentation choices (made after the results were known)

* **Recorded:** 2026-10-20 (task `CC_TASK_SS_reporting_completion_v1.md`).
* **Separate from** `PRESENTATION_DECISIONS.md`, which was fixed on 2026-10-09 before any step-6 result existed and is
  unchanged. Nothing here alters those decisions or the main-text figures 1–4 and supplementary figures S1–S3.
* **Results known when these choices were made:**
  * all step-5, step-6 and step-7 records;
  * the X1/X2 records (`1c8e628`) and the B records (`458341f`);
  * the readout `X_B_READOUT_20261020.md`, the confirmation record `CONFIRM_ITEMS_20261019.md` and the evaluator
    record v5.
* **Fact base:** `SS_DS203_PROJECT_RECORD_for_evaluator_20261020_v5.md`, SHA-256
  `c1d8d651535136907b461e2666b4671d4fc58c736a78e6bb61fbcac54dc27684`.

## Rules applied to every new output

1. **No number changed.** Every value is read with `git show <commit>:<path>` from a committed record (`SUPPLEMENT_20261020/SOURCES.md`). Nothing is recomputed except plotting.
2. **Nothing selected.** Every new table or figure shows all cells, sets and keys that the plans define:
   * the mask check: 4 centres × 180 profile points;
   * X: 2 analyses × 3 arms × 3 comparators × 3 groups (54 group rows) and all 71 cells per panel;
   * X1 E3/E2: 3 keys × 2 probes, and 3 E2 conditions per key;
   * B: 3 keys × 2 analyses × 2 probes × 3 sets (36 rows), 36 judgement statements and 36 sensitivity rows.
3. **CSV tables are verbatim.** `tableX_group_summaries.csv`, `tableB_ba.csv`, `tableB_judgements.csv` and `tableB_sens.csv` are byte copies of the record files (same SHA-256). `tableS4_mask_check.csv` and `tableX_E3.csv` give each recorded value as its JSON text.
4. **Markdown tables show 3 decimals**, the rounding of the committed reports.
   * `make_supplement.py` asserts that each rounded row of Tables X, B and B-sens equals the corresponding row of the committed `X_REPORT.md` / `B_REPORT.md`.
   * For Table X-E3 it asserts that the X1 linear / MLP BA and upper bounds and the step-5 linear upper bounds equal the committed `X_REPORT.md` E3 table.
5. **Row order** follows the record files.
6. **Captions** (`CAPTIONS.md`) label every X / B output "EXPLORATORY". They quote the ceilings and the Δ definition verbatim from the fact base, §8–9, and the mask-check deviation from §5.

## Choices per output

| output | choice made after the results |
|---|---|
| Figure S4 (mask profiles) | 2 × 2 panels, one per centre. The recorded profile m_c(ρ) as stored (no normalisation, no smoothing). Vertical lines at the recorded ρ_c (orange) and at r = 0.45 (dashed black); x-axis 0–0.72 so that ρ_c = 0.703125 is visible. The 0.25 × central-median threshold of §3.1 is not drawn, because it is not a recorded value and drawing it would require a computation. |
| Table S4 | Per-centre frames, ρ_c and number of profile points; min_c ρ_c, r and "fallback not used". The validity is cited from `run_meta.json` (committed) and from the runner log line on LaCie (not committed; quoted). |
| Table X | The 54 group rows in record order; the columns of the committed X_REPORT.md group table. Seed names and full precision are in the CSV only. |
| Table X-E3 | Built after the results to set X1 next to step 5 on the 158-case analysis region (the only set on which X1 is defined): E3-site (linear and MLP: BA, 95 % interval, one-sided upper); E2 primary in three conditions (step 5 before removal, step 5 after protocol removal, X1 after X1 removal) with "met / not met" for the §5.2 criterion as recorded in the `pass` field; E3-state retention. |
| Figure X | One page per analysis (X1, X2) × comparison (step-6 k−C, FM-k, NV); one panel per arm. All 71 cells, grouped in the order P1b-FM, P2-FM, main-figure slice, by cell index within each group. Cell 15 belongs to both P2-FM and the slice and appears in both. Point = Δ; vertical bar = recorded 95 % interval (drawn from the recorded bounds, not as ± errors). Zero line. Colours by group (matplotlib defaults C0–C2). The y-axis is independent per panel, because the Δ ranges of the three comparators differ widely. |
| Table B | The 36 BA rows with the columns of the committed B_REPORT.md; the 36 judgement statements as a second table copied unchanged from `b_judgements.csv`, not merged into the BA rows. |
| Table B-sens | The 36 rows in record order (P, REF, S, as in the record and B_REPORT.md). |
| Figure B | 3 × 2 panels: rows = keys (P, S, REF), columns = (a) transport and (b) within-set refit, never pooled. x = S1, S2, S3; linear (blue circles) and MLP (orange squares) offset by ±0.08. Points = BA with the recorded 95 % interval; horizontal tick = recorded one-sided 95 % upper bound. Dashed line at the 0.35 boundary (the judgement applies to the upper bound); dotted line at chance 0.25 (a reference line added here). Shared y-axis 0.1–1.02. |
| Names | Supplementary Figure S4 / Table S4 continue the existing S1–S3 numbering. X and B outputs are labelled X, X-E3, B and B-sens; their final numbering is left to the manuscript. |
| Location | All new outputs are in `SUPPLEMENT_20261020/`, generated by `make_supplement.py` (log `SUPPLEMENT_20261020/generate.log`). |
