# SS-DS203: project record for the evaluator (status as of 2026-10-20) — v5

**Status of this document: provisional factual handover.** It compiles
results and events as recorded in the project's repositories. Items
confirmed against the repositories are marked as such (confirmation record
`CONFIRM_ITEMS_20261019.md`, step7_prep commit fa2b8c7; audit zip SHA-256
57307b87…1251a). This is not an independent replication.

Changes from v4: the §9 hypothesis restricted to the subsets where it is
observed (S2 contradicts the general form); swap commands and times sourced
to the system journal.

Changes from v3 (after a read-only check of v3 against the repositories):
E2 wording for X1 corrected; "held-out folds" added; B subsampling values
given without a boundary judgement and the explanatory sentence labelled a
hypothesis; literature sources reconciled with the search records; OOM
statement sourced to the kernel log and the swap off/on added to the
register; step-7 commit wording restricted to what the repository shows.

## 1. Scientific question

When site-associated information is included in, or linearly removed from,
the adjustment set of a sequential causal analysis, how do bias and interval
validity change as a function of intervention duration (K), post-window
actions (P), pre-window history (W) and unmeasured confounding (α)?
Semi-synthetic design: real video and real centre heterogeneity; treatments,
outcomes, truth and the site loading c(C) (permuted per replicate) are
**synthetic**. No result here is a real-patient effect estimate.

## 2. Data and analysis sets

278 full-length cases (centres 2–5: 49/41/71/117); primary causal set
n = 158 (28/34/44/52); sensitivity sets W = 0 (n = 204), W = 5 (n = 201),
single-file (n = 123). Content state S: binary switch (appendix visible).

## 3. Protocol and review process

- Protocol frozen: 4c86dc5 (2026-10-05 12:22 +0900); freeze record 8f63e43.
- Until 2026-10-07, stages were reviewed in written audit documents from a
  review process separate from the implementation sessions.
  **[TO CONFIRM — investigator]** whether that review was human or
  AI-assisted. From 2026-10-07 the investigator is the sole approver.

## 4. Code lock and model selection

- Estimator gate PASS (6/6 cells, PLACEHOLDER design); projection 5.99 days
  at 20 workers; G-SITE η² 0.0014 / 0.0037 / 0.0045; 0 small-truth flags.
  SDR implementation af56777; final code lock 98cba1e.
- Models: primary SurgeNetCholec; secondary LeanVAE-4ch; reference
  Cosmos-1.0-Tokenizer-CV8x8x8. Post-lock SurgeNet adapter correction
  (ad8833a; reselection ba73820). Equivalence with official code: max
  difference 0.0 (four models) and 3.7e-7 (Cosmos).

## 5. Steps 4–5

- Runner 9e1aa71 from 2026-10-06 08:04. Memory-guard false-positive STOP
  16:35:27 (≈80 GiB available; the kernel log shows no OOM line between
  16:00 and 17:30); swappiness set to 10 and swap disabled/re-enabled at
  17:28:14–17:28:17 (system journal, sudo entries); resumed 17:28:48;
  the mask check restarted from case 1. Watchdog from 2026-10-07 09:37:15,
  never relaunched.
- **Mask check (confirmed, 8d4c61a):** ρ_c = 0.5625 (centre 2), 0.703125
  (centres 3, 4, 5; last grid point); min ρ_c = 0.5625 ≥ 0.45, so
  r = 0.45 stands; fallback not used. **Deviation:** §3.1 requires the
  per-centre profiles to be reported; they exist in `mask_check.json` but
  are not yet in the results report. To be added as a supplementary
  figure.
- dts QC: no frame loss; ≈50 grid frames shifted by one frame interval
  (extrapolated from a sample); no step-boundary crossing in examined files.
- Step-4 record 8d4c61a; step-5 record 0ebf2cf.

## 6. Step-5 results and §13

E1 pass (P, S, REF). E2: P pass; P-nat, S, REF fail. E3-site: 278-case set
pass (linear BA 0.25), MLP exceeds margin (P 0.96, S 0.49, REF 0.86);
158-case primary set **fail** (linear BA P 0.42, S 0.39, REF 0.45).
E3-state: P pass. §13 (0667430): FM vs FM−C descriptive only; P1b-FM and
P2-FM not tested.

## 7. Steps 6–7

- **Execution order (confirmed):** 0ebf2cf → 0667430 → 7adaf13 by ancestry
  (all committed 14:26:41); step 6 started 14:26:42 with no shards; first
  completed unit 14:27:03.80 (file mtime), 22.8 s after 0ebf2cf; one
  attempt only.
- Step 6 completed 2026-10-18 20:20:34 (last unit 20:17:38; 73,200 units,
  18 workers). Step 7: records committed automatically by the step-7
  runner, which does not display results before committing (2880d73).

### D (confirmed)

Locked `grid.py` (`_d_values`, `family_verdict`) matches §12.3: numerator
|mean(Ψ̂ − Ψ)| per arm; P1 = without C − with C, P2 = with C − without C;
denominator mean truth per cell; unweighted mean over fixed cells;
bootstrap B = 2,000, seed 20261008, shared indices, cells not resampled.
Not stated in §12.3: the bootstrap also resamples the truths (mean truth
recomputed per resample). Recomputed D̄: P1b-SITE 2.1976 and P2-SITE 0.0521,
identical to the records. D is dimensionless.

### Verdicts (primary set)

| Family | Comparison | Cells | D̄ | Lower 95 % | Share D > 0 | Verdict |
|---|---|---|---|---|---|---|
| P1a | ORACLE vs ORACLE−C | 66 | 1.925 | 1.909 | 0.98 | SUPPORTED |
| P1b-SITE | SITE vs NV | 48 | 2.198 | 2.167 | 1.00 | SUPPORTED |
| P2-SITE | SITE vs NV | 18 | 0.052 | 0.048 | 1.00 | SUPPORTED |
| P2-ORACLE | ORACLE vs ORACLE−C | 12 | 0.042 | 0.036 | 0.92 | SUPPORTED |
| P1b-FM | FM-P vs FM-P−C | 48 | 0.594 | 0.582 | 1.00 | not tested (§13) |
| P2-FM | FM-P vs FM-P−C | 12 | 0.005 | −0.000 | 0.50 | not tested (§13) |

Sensitivity sets: all SITE/ORACLE families in the same direction. Intervals
are Monte Carlo uncertainty over 200 paired replicates per cell.

**Ceiling.** Supported within the constructed DGP with an explicit site
covariate. The direction is partly implied by the DGP: site acts on
subsequent actions (K ≥ 2 or P > 0) that enter the outcome, so it becomes a
confounder rather than an instrument. Not evidence about real clinical
interventions, nor a confirmatory result for learned representations.

## 8. Exploratory X1/X2 (outside the protocol)

- Plan b6d1cf7 (2026-10-13 08:21 +0900), OSF https://osf.io/5c627 (embargo
  to 2028-10-13): written after the step-5 E3 failure was known and while
  step 6 was running, before access to step-6 results.
- Run: launch 015595d; C0 reproduced step-6 records exactly; 28,400 truths
  identical; records 1c8e628 (2026-10-19 20:18).
- **Δ definition (confirmed):** same form as D, same per-cell mean truth as
  step 6 (1,278/1,278 rows), §12.3 bootstrap scheme. Differences: Δ is
  always (X arm − step-6 arm), not oriented by family; bootstrap seed names
  differ from step 6; per-cell intervals are added. Negative Δ = X arm has
  smaller |bias|.
- **X1 erasure (refitted on the 158-case analysis region):** linear E3 on
  that set 0.25 (a procedural check: fitted on training folds and evaluated
  on held-out folds of the same population); MLP still decodes site (P 0.58,
  REF 0.46, S 0.31). E2 for P: ΔAUC 0.050 [0.019, 0.080] before removal
  (pass); 0.044 [0.012, 0.074] after the step-5 protocol removal (not met);
  0.051 [0.019, 0.083] after the X1 removal (met). State-retention fraction
  1.019 (X1) vs 0.868 (step 5).
- **X1 vs step-6 FM−C:** P1b-FM cells P −0.033 [−0.042, −0.023], S +0.023,
  REF +0.004; P2-FM cells ≈ 0.
- **X1 FM−C vs step-6 FM (site retained), P1b-FM cells:** P +0.561
  [0.549, 0.573] (48/48 cells same sign), S +0.343, REF +0.496; P2-FM cells
  P −0.007, S −0.004, REF −0.006.
- **X2 (linear-only nuisance) vs step-6 FM−C:** |mean Δ| ≤ 0.011 in all
  groups.
- **Ceiling:** exploratory; no verdict; cannot restore P1b-FM/P2-FM;
  nonlinear site information remains after X1; X2 changes do not show that
  erasure caused a difference.

## 9. Exploratory B (outside the protocol)

- Plan e1c27b4 (2026-10-19 10:00 +0900), OSF https://osf.io/g9ymw (embargo
  to 2028-10-13), written after the step-7 verdicts were generated in the
  same working session (disclosed); B uses no step-6/7 or X quantity.
- Run: launch c7354ed; C-B0 reproduced the step-5 E3 numbers for all keys;
  records 458341f (2026-10-20 00:29).
- Transport (S1-fitted probe): linear BA 0.25 in S1, S2, S3; MLP exceeds the
  boundary everywhere.
- Within-set refit, linear: S1 0.25, S2 0.21–0.24, S3 0.39–0.45; the
  judgement changes between S2 and S3 (all keys), not between S1 and S2.
- Equal-size subsampling (28 cases per centre, 75 steps per case, 20
  draws; descriptive point estimates, no bootstrap, no judgement): refit
  linear median BA, P 0.339 / 0.290 / 0.362, REF 0.308 / 0.286 / 0.379,
  S 0.259 / 0.214 / 0.357 (S1 / S2 / S3).
- **Ceiling:** B locates where the judgement changes; it does not identify
  why. The subsampling changes centre balance, case set and steps per case
  at the same time. *Hypothesis (not tested):* linear guardedness is exact
  only on the fitting population, so within-set refits on some subsets (S3
  and the equal-size subsamples, but not S2, whose within-set linear BA is
  0.231 / 0.239 / 0.208 for P / S / REF, upper bounds 0.251–0.282) recover
  some linear site information; whether window selection adds to this is
  not determined by B.

## 10. Literature check (scoped to the reported search)

As in v2: window-subset erasure failure not found in the search (now
qualified by §9); nonlinear residual site information reported in prior
work; residual-site effects on causal estimates not found; one directly
relevant longitudinal instrument-amplification study
(DOI 10.1186/s12874-022-01563-3; Q4-a). Sources named by the evaluator:
arXiv 2607.06126 is already in the search records (Q3-e, PARTIAL; author
list not recorded there); LEACE (Belrose et al. 2023) is in the
related-work notes; Spindler et al. (CLeaR 2026, PMLR 323) is not among the
2,501 records and is to be added after checking the primary source.

## 11. Deviation and operations register

As in v2 (source retrievals 1–7, including the VISSL retrieval beyond the
SurgeNet-only wording; operational decisions), plus: mask-check profiles
not yet reported (§5); swap disabled and re-enabled at 17:28:14–17:28:17 before
the 6 Oct resume (system journal), not recorded in the operations log, which
also gives the swappiness change without a time (§5); bootstrap resampling of truths not stated in §12.3
(§7); X Δ orientation and seeds differ from §12.3 (§8).

## 12. Next steps

1. Investigator: state the nature of the earlier review (§3).
2. Reporting fixes without changing any number: mask-check profiles as a
   supplementary figure; Methods filled (r = 0.45, commits); X/B tables.
3. Figures, tables, text and title, with the claim ceilings above; target
   journals compared on IF, APC and scope.
