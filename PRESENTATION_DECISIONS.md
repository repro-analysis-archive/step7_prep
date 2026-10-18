# Presentation decisions (fixed before any result exists)

* **Recorded:** 2026-10-09 10:31 +0900.
* **Authority:** investigator decision in `CC_TASK_SS_step7_prep_fixes_v1.md` §2.
* **No step-6 result exists yet.** Checked at 2026-10-09 10:30:54 +0900:
  * no step-6 process exists (`ps`);
  * the chain (pid 4003618, started 2026-10-07 09:36:40) is still waiting for computation A, which is running (runner pid 2098753);
  * the step-6 output directory `/media/user/LaCie/medvideo_gate/ss_step6` does not exist (one read-only existence test).
* **Data seen so far:** no step-5 result has been read in this work either. The only grid outputs seen are PLACEHOLDER test outputs.

## Decision

1. **Main-text figures: slice W = 30, α = 0.5, γ = 1, φ_A = 0, primary set (158 cases).**
   * Figure 1: relative bias and 95 % interval coverage against K, by arm, one column per P ∈ {0, 5, 30}.
   * Figure 2: role-switch view. Δ|bias| / mean truth (|bias| without C − |bias| with C) against K, one line per P, one panel per with/without-C pair (SITE/NV, FM-P/FM-P−C, FM-S/FM-S−C, REF/REF−C, ORACLE/ORACLE−C).
   * Figure 3: the same contrast as K × P heatmaps at this slice, one panel per pair.
   * Figure 4: E1–E3 and PCA / LEACE summaries. These do not depend on the slice.
2. **Supplementary: heatmaps covering every cell of the grid** (primary set, all 240 cells: the 216 φ_A = 0 cells and the 24 φ_A = 0.5 cells). Rows are α × γ; columns are W; each panel is K × P; φ_A = 0.5 is on its own page. No averaging over any factor.
   * S1: the contrast Δ|bias| / mean truth, one page per pair.
   * S2: relative bias, one page per arm.
   * S3: coverage, one page per arm.

Implemented in `make_figures.py` (defaults `--W 30 --alpha 0.5 --gamma 1`). The earlier draft default (W = 5) and the averaged (K, P, W) heatmap were replaced.
