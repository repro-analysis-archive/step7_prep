# Captions (supplementary figures and tables, 2026-10-20)

Ceilings and definitions are quoted verbatim from the fact base `SS_DS203_PROJECT_RECORD_for_evaluator_20261020_v5.md` (SHA-256 `c1d8d651535136907b461e2666b4671d4fc58c736a78e6bb61fbcac54dc27684`), §5, §8 and §9. Every number is from the committed records listed in `SOURCES.md`.

## Supplementary Figure S4 and Table S4. Mask check (protocol §3.1)

Per-centre radial profiles m_c(ρ) of the grayscale mean standardized frame (protocol §3.1: 256 × 256, every 60th grid frame of every case), 180 points per centre, from the step-4 record (`8d4c61a`, `mask_check.json`). Orange: the visible radius ρ_c; dashed black: the mask radius r = 0.45. min_c ρ_c = 0.5625 ≥ 0.45, so r = 0.45 stands and the fallback r = 0.98 × min_c ρ_c was not used. Reported here to close the deviation recorded in the fact base:

> - **Mask check (confirmed, 8d4c61a):** ρ_c = 0.5625 (centre 2), 0.703125 (centres 3, 4, 5; last grid point); min ρ_c = 0.5625 ≥ 0.45, so r = 0.45 stands; fallback not used. **Deviation:** §3.1 requires the per-centre profiles to be reported; they exist in `mask_check.json` but are not yet in the results report. To be added as a supplementary figure.

## Table X. Exploratory X1/X2: group summaries

EXPLORATORY (outside the frozen protocol; plan `b6d1cf7`, OSF https://osf.io/5c627). All 2 analyses × 3 arms × 3 comparators × 3 groups (54 rows).

> - **Δ definition (confirmed):** same form as D, same per-cell mean truth as step 6 (1,278/1,278 rows), §12.3 bootstrap scheme. Differences: Δ is always (X arm − step-6 arm), not oriented by family; bootstrap seed names differ from step 6; per-cell intervals are added. Negative Δ = X arm has smaller |bias|.

> - **Ceiling:** exploratory; no verdict; cannot restore P1b-FM/P2-FM; nonlinear site information remains after X1; X2 changes do not show that erasure caused a difference.

## Table X-E3. Exploratory X1: E3-site, E2 and E3-state retention next to step 5

EXPLORATORY. X1 refits the LEACE eraser on the 158-case analysis region (training folds) and evaluates on held-out folds of the same population; step-5 values are the protocol LEACE (fitted on the 278-case set). Keys P, S, REF; probes linear and MLP.

> - **Ceiling:** exploratory; no verdict; cannot restore P1b-FM/P2-FM; nonlinear site information remains after X1; X2 changes do not show that erasure caused a difference.

## Supplementary Figure X. Exploratory X1/X2: per-cell Δ

EXPLORATORY. One page per analysis (X1, X2) × comparator (step-6 k−C, step-6 FM-k, step-6 NV); one panel per arm (FM-P−C, FM-S−C, REF−C); all 71 cells, grouped as P1b-FM (48), P2-FM (12) and the main-figure slice (12); cell 15 belongs to both P2-FM and the slice and is shown in both. Points: Δ; bars: 95 % paired bootstrap percentile intervals (B = 2,000). y-axes differ between panels.

> - **Δ definition (confirmed):** same form as D, same per-cell mean truth as step 6 (1,278/1,278 rows), §12.3 bootstrap scheme. Differences: Δ is always (X arm − step-6 arm), not oriented by family; bootstrap seed names differ from step 6; per-cell intervals are added. Negative Δ = X arm has smaller |bias|.

> - **Ceiling:** exploratory; no verdict; cannot restore P1b-FM/P2-FM; nonlinear site information remains after X1; X2 changes do not show that erasure caused a difference.

## Table B and Supplementary Figure B. Exploratory B: balanced accuracy by evaluation set

EXPLORATORY (outside the frozen protocol; plan `e1c27b4`, OSF https://osf.io/g9ymw). All 3 keys × 2 analyses × 2 probes × 3 sets (36 cells) with the generated judgement statements. In the figure, (a) transport and (b) within-set refit are separate panels (never pooled); points: BA with 95 % interval; horizontal ticks: one-sided 95 % upper bound; dashed line: the 0.35 boundary, which applies to the upper bound; dotted line: chance 0.25.

> - **Ceiling:** B locates where the judgement changes; it does not identify why. The subsampling changes centre balance, case set and steps per case at the same time. *Hypothesis (not tested):* linear guardedness is exact only on the fitting population, so within-set refits on some subsets (S3 and the equal-size subsamples, but not S2, whose within-set linear BA is 0.231 / 0.239 / 0.208 for P / S / REF, upper bounds 0.251–0.282) recover some linear site information; whether window selection adds to this is not determined by B.

## Table B-sens. Exploratory B: equal-size subsampling

EXPLORATORY. 28 cases per centre, 75 steps per case, 20 draws; median, 2.5–97.5 % across draws and range of the point BA; descriptive point estimates, no bootstrap, no judgement.

> - **Ceiling:** B locates where the judgement changes; it does not identify why. The subsampling changes centre balance, case set and steps per case at the same time. *Hypothesis (not tested):* linear guardedness is exact only on the fitting population, so within-set refits on some subsets (S3 and the equal-size subsamples, but not S2, whose within-set linear BA is 0.231 / 0.239 / 0.208 for P / S / REF, upper bounds 0.251–0.282) recover some linear site information; whether window selection adds to this is not determined by B.
