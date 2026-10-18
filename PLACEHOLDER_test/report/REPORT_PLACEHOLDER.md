# PLACEHOLDER report (test of make_report.py)

> **PLACEHOLDER — synthetic test output, not results. No DS203 data.**

Inputs (SHA-256):

* `PLACEHOLDER_test/grid/families.json` `a9047ae162c81634ac9589493e2f2bdad3922405ca730d687d2b626ace2e60a2`
* `PLACEHOLDER_test/grid/cell_metrics.csv` `b41c9e5505c89f68bf498ff7544b8e1d097241591585e3976bdb44ac3d045bc1`
* `PLACEHOLDER_test/step5/checks.json` `36e197b7f089ce43bde219af38ad6c8124c81e19b7e99257437c1bee822798d5`
* `PLACEHOLDER_test/step5/section13.json` `cd8b7e9579b4c4e30035fcd6cfb43f23bd6f00d9c04557667f63eb76702ba89f`
* `PLACEHOLDER_test/step5/reps_report.json` `224acc52be534de7931f1ab02b2f6bd2dee2fa0ba4fb92d42562b16a6e9bfc49`
* `PLACEHOLDER_test/step5/gsite_record.json` `26a538012bce89538141d29e9c944b54e79e6ddd8532c8a31167aea62314522a`

## 1. Family verdicts (§12.3)

Primary set. D_j = oriented relative difference per cell (positive = as predicted); D̄_F = mean over the family's cells; 95 % percentile bootstrap over replicates within cells (B = 2,000, seed 20261008). SUPPORTED: lower bound > 0 and D_j > 0 in ≥ 75 % of cells; CONTRADICTED: upper bound < 0 or D_j > 0 in ≤ 25 %; INCONCLUSIVE otherwise.

| family | comparison | cells | D̄_F | 95 % CI | share D_j > 0 | rule verdict | conditions failed | reported verdict |
|---|---|---:|---:|---|---:|---|---|---|
| P1a | ORACLE vs ORACLE-C | 2 | 0.665 | [0.409, 0.893] | 1.00 | SUPPORTED | none | SUPPORTED: consistent with the theory-motivated direction |
| P1b-SITE | SITE vs NV | 7 | 2.999 | [2.362, 3.604] | 1.00 | SUPPORTED | none | SUPPORTED: consistent with the theory-motivated direction |
| P1b-FM | FM-P vs FM-P-C | 7 | 0.978 | [0.765, 1.177] | 1.00 | SUPPORTED | none | SUPPORTED: consistent with the theory-motivated direction |
| P2-SITE | SITE vs NV | 3 | 0.107 | [0.053, 0.109] | 0.67 | INCONCLUSIVE | none | INCONCLUSIVE: inconclusive (no directional claim) |
| P2-FM | FM-P vs FM-P-C | 3 | -0.059 | [-0.209, 0.060] | 0.33 | INCONCLUSIVE | none | INCONCLUSIVE: inconclusive (no directional claim) |
| P2-ORACLE | ORACLE vs ORACLE-C | 3 | 0.058 | [0.013, 0.097] | 1.00 | SUPPORTED | none | SUPPORTED: consistent with the theory-motivated direction |

**§10.3 sensitivity sets — named families** (reported separately; never family verdicts). *Locked aggregation*: the locked `aggregate` verdict, which applies the primary-set E1 / E3 conditions to every set. *Protocol-consistent ceiling*: the §13 / §12.2 conditions evaluated on the set's own step-5 E1–E3 (single-file: E1 and E3-site on the 278-case set and on the single-file set, E3-state on the single-file set); per-W P2 results are instrument-like only if that set's G-SITE ≤ 0.01.

| set:family | cells | D̄_F | 95 % CI | share D_j > 0 | locked aggregation | own-set conditions | protocol-consistent ceiling |
|---|---:|---:|---|---:|---|---|---|
| W0:P1b-FM | 7 | 1.275 | [1.003, 1.514] | 1.00 | SUPPORTED (conditions applied: primary set) | no set-specific E1–E3 for W0 in the step-5 record | descriptive only: no set-specific E1–E3 for W0 in the step-5 record |
| W0:P1b-SITE | 7 | 3.720 | [3.499, 3.935] | 1.00 | SUPPORTED (conditions applied: primary set) | no E1–E3 condition | SUPPORTED |
| W0:P2-FM | 1 | -0.002 | [-0.020, 0.016] | 0.00 | CONTRADICTED (conditions applied: primary set) | no set-specific E1–E3 for W0 in the step-5 record; G-SITE (own set) ≤ 0.01: instrument-like | descriptive only: no set-specific E1–E3 for W0 in the step-5 record |
| W0:P2-ORACLE | 1 | 0.113 | [0.069, 0.159] | 1.00 | SUPPORTED (conditions applied: primary set) | no E1–E3 condition; G-SITE (own set) ≤ 0.01: instrument-like | SUPPORTED |
| W0:P2-SITE | 1 | 0.163 | [0.096, 0.234] | 1.00 | SUPPORTED (conditions applied: primary set) | no E1–E3 condition; G-SITE (own set) ≤ 0.01: instrument-like | SUPPORTED |
| W5:P2-FM | 1 | 0.099 | [0.013, 0.207] | 1.00 | SUPPORTED (conditions applied: primary set) | no set-specific E1–E3 for W5 in the step-5 record; G-SITE (own set) ≤ 0.01: instrument-like | descriptive only: no set-specific E1–E3 for W5 in the step-5 record |
| W5:P2-ORACLE | 1 | 0.072 | [0.038, 0.105] | 1.00 | SUPPORTED (conditions applied: primary set) | no E1–E3 condition; G-SITE (own set) ≤ 0.01: instrument-like | SUPPORTED |
| W5:P2-SITE | 1 | 0.063 | [-0.035, 0.166] | 1.00 | INCONCLUSIVE (conditions applied: primary set) | no E1–E3 condition; G-SITE (own set) ≤ 0.01: instrument-like | INCONCLUSIVE |
| single_file:P1b-FM | 7 | 1.304 | [0.537, 2.135] | 0.71 | INCONCLUSIVE (conditions applied: primary set) | E1 pass, E3-site pass, E3-state pass | INCONCLUSIVE: inconclusive (no directional claim); E2 fails on this set: FM-vs-NV comparisons cannot be read as confounder recovery; E3-state-retention not applicable on this set (E2 fails): FM−C interpretation rests on E3-site |
| single_file:P1b-SITE | 7 | 3.689 | [3.207, 4.192] | 1.00 | SUPPORTED (conditions applied: primary set) | no E1–E3 condition | SUPPORTED |
| single_file:P2-FM | 3 | 0.013 | [-0.052, 0.082] | 0.67 | INCONCLUSIVE (conditions applied: primary set) | E1 pass, E3-site pass, E3-state pass; G-SITE: no single-file value at code lock (primary value used by the locked code) | INCONCLUSIVE: inconclusive (no directional claim); E2 fails on this set: FM-vs-NV comparisons cannot be read as confounder recovery; E3-state-retention not applicable on this set (E2 fails): FM−C interpretation rests on E3-site |
| single_file:P2-SITE | 3 | 0.123 | [0.108, 0.134] | 1.00 | SUPPORTED (conditions applied: primary set) | no E1–E3 condition; G-SITE: no single-file value at code lock (primary value used by the locked code) | SUPPORTED |

**Exploratory — families outside the §10.3 scope** (computed by the locked aggregation because both arms exist in the set; not verdicts, not claims):

| set:family | cells | D̄_F | 95 % CI | share D_j > 0 |
|---|---:|---:|---|---:|
| W0:P1a | 1 | 1.784 | [1.558, 2.022] | 1.00 |

## 2. §13 claim ceilings (applied mechanically)

**(a) Fixed at step 5** by the committed §13 record (rules triggered):

* E3-state-retention not applicable (E2 primary fails) — FM-P / FM-P−C: the report states that retention of state information could not be assessed. FM−C interpretation then rests on E3-site alone (§5.3).
* E3-state-retention not applicable (E2 primary fails) — FM-S / FM-S−C: the report states that retention of state information could not be assessed. FM−C interpretation then rests on E3-site alone (§5.3).
* E3-state-retention not applicable (E2 primary fails) — REF / REF−C: the report states that retention of state information could not be assessed. FM−C interpretation then rests on E3-site alone (§5.3).
* E2 fails — FM-P / FM-P−C: "video representations recover the confounding state" is not established. FM-vs-NV comparisons cannot be read as confounder recovery.
* E2 fails — FM-P-nat: "video representations recover the confounding state" is not established. FM-vs-NV comparisons cannot be read as confounder recovery.
* E2 fails — FM-S / FM-S−C: "video representations recover the confounding state" is not established. FM-vs-NV comparisons cannot be read as confounder recovery.
* E2 fails — REF / REF−C: "video representations recover the confounding state" is not established. FM-vs-NV comparisons cannot be read as confounder recovery.
* E3-site passes (FM-P / FM-P−C, 278-case set; FM-P / FM-P−C, 158-case set; FM-S / FM-S−C, 278-case set; FM-S / FM-S−C, 158-case set; REF / REF−C, 278-case set; REF / REF−C, 158-case set): the wording is "no longer exceeds the prespecified linear site-encoding boundary", never "equivalent to chance" or "eliminated".

**(b) Rules deferred to step 7, evaluated now:**

* "E1 and E3 (both components) pass but P1b-FM and P2-FM are INCONCLUSIVE": conditions E1 = True, E3-site = True, E3-state = True, G-SITE = True; P1b-FM = SUPPORTED, P2-FM = INCONCLUSIVE → not triggered.
* P1a: SUPPORTED → stated as "consistent with the theory-motivated direction"; not a confirmation of the theory maps.
* P1b-SITE: SUPPORTED → stated as "consistent with the theory-motivated direction"; not a confirmation of the theory maps.
* P1b-FM: SUPPORTED → stated as "consistent with the theory-motivated direction"; not a confirmation of the theory maps.
* P2-ORACLE: SUPPORTED → stated as "consistent with the theory-motivated direction"; not a confirmation of the theory maps.

**(c) Standing rules:**

* Headline directional claims come only from primary-set family verdicts; single cells are descriptive; all cells are reported (§12.3). P3 cells and comparisons carry no directional prediction (§12.2).
* A family whose conditions fail is NOT TESTED and reported as P3 / descriptive (§12.2, §5.4).
* §10.3 sets are reported separately and never enter family verdicts (§10.3).
* Representation wording ("video-derived representations", arm-specific wording of §1)
* Native arm differs from standardized: attributed to acquisition shortcuts, not to image content
* REF arm: not a fair model comparison, not a pixel-level replication of K4, may retain frame-rate-derived information
* FULL arm: an exchangeability oracle / implementation sanity reference; its finite-sample bias is reported
* All claims describe a deliberately constructed orthogonal benchmark (§1, §7.2)
* No causal effect in DS203 is estimated (§1).

## 3. Pre-causal checks (§5) and G-SITE (§5.4)

Balanced accuracy (BA) of the case-level site probe [95 % bootstrap bounds]; E2 = ΔAUC of base + R_t over base (elapsed-time spline) [95 % CI]; E3-site upper = one-sided 95 % upper bound after removal (boundary 0.35); retention = post / pre ΔAUC (≥ 0.50).

| representation | E1 278 BA | E1 158 BA | E1 single-file BA | MLP probe 278 (pre-removal) | E2 158 ΔAUC | E2 158 after removal | E3-site 278 linear / MLP upper | E3-site 158 linear / MLP upper | E3-state |
|---|---|---|---|---|---|---|---|---|---|
| primary (FM-P) | 1.000 [1.000, 1.000] pass | 1.000 [1.000, 1.000] pass | 1.000 [1.000, 1.000] pass | 1.000 | +0.049 [+0.042, +0.056] FAIL | +0.049 [+0.043, +0.055] FAIL | 0.250 / 0.271 pass | 0.250 / 0.250 pass | not applicable |
| secondary (FM-S) | 1.000 [1.000, 1.000] pass | 1.000 [1.000, 1.000] pass | 1.000 [1.000, 1.000] pass | 1.000 | +0.044 [+0.037, +0.049] FAIL | +0.044 [+0.037, +0.050] FAIL | 0.250 / 0.276 pass | 0.250 / 0.250 pass | not applicable |
| reference (REF) | 1.000 [1.000, 1.000] pass | 1.000 [1.000, 1.000] pass | 1.000 [1.000, 1.000] pass | 1.000 | +0.035 [+0.030, +0.041] FAIL | +0.036 [+0.030, +0.042] FAIL | 0.250 / 0.276 pass | 0.250 / 0.270 pass | not applicable |
| primary, native (FM-P-nat) | 1.000 [1.000, 1.000] pass | 1.000 [1.000, 1.000] pass | 1.000 [1.000, 1.000] pass | 1.000 | +0.049 [+0.042, +0.055] FAIL | — | — | — | — |

Reporting-only E2 paths (no pass field): ΔAUC on all 278 videos, normalised-time reference, and with past synthetic actions (reference cell K = 5, P = 0, W = 5, α = 0.5, γ = 1).

| representation | E2 278 | E2 278 normalised time | E2 158 normalised time | E2 158 with history |
|---|---|---|---|---|
| primary (FM-P) | +0.010 [+0.009, +0.011] | +0.007 [+0.006, +0.008] | +0.036 [+0.030, +0.041] | +0.159 [+0.102, +0.215] |
| secondary (FM-S) | +0.009 [+0.008, +0.010] | +0.006 [+0.005, +0.007] | +0.032 [+0.026, +0.037] | +0.135 [+0.087, +0.185] |
| reference (REF) | +0.007 [+0.006, +0.008] | +0.005 [+0.004, +0.006] | +0.025 [+0.020, +0.029] | +0.114 [+0.075, +0.155] |
| primary, native (FM-P-nat) | +0.010 [+0.009, +0.011] | +0.007 [+0.006, +0.008] | +0.036 [+0.029, +0.041] | +0.161 [+0.103, +0.214] |

**G-SITE** (η² of S at the window start on C; gate ≤ 0.01; code lock): primary 0.0000 (pass), W0 0.0000 (pass), W5 0.0000 (pass).

**PCA / LEACE** (fold-wise, 64 PCs; step-5 reduction report `reps_report.json`):

| representation | folds | training steps (fold 0) | PCA variance retained (mean) | LEACE rank per fold | dimensions retained | LEACE variance retained (mean) |
|---|---:|---:|---:|---|---|---:|
| primary (FM-P) | 5 | 36711 | 0.558 | [3, 3, 3, 3, 3] | [61, 61, 61, 61, 61] | 0.892 |
| secondary (FM-S) | 5 | 36711 | 0.698 | [3, 3, 3, 3, 3] | [61, 61, 61, 61, 61] | 0.928 |
| reference (REF) | 5 | 36711 | 0.455 | [3, 3, 3, 3, 3] | [61, 61, 61, 61, 61] | 0.867 |
| primary, native (FM-P-nat) | 5 | 36711 | 0.616 | [None, None, None, None, None] | [None, None, None, None, None] | — |

**P3 (descriptive):** 5 primary-set cells belong to no family; they carry no directional prediction and are reported in the tables below.

## 4. Relative bias and interval coverage per cell and arm (§11)

Relative bias = mean(Ψ̂ − Ψ) / mean Ψ; coverage = share of replicates whose 95 % Wald interval contains Ψ. All metrics per cell and arm: `report_cells.csv`.

**primary: relative bias** (16 cells; M per cell 2–2)

| cell | K | P | W | α | γ | φ_A | family | NV | SITE | FM-P | FM-P-C | FM-S | FM-S-C | REF | REF-C | FM-P-nat | ORACLE-C | ORACLE | FULL |
|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 3 | 1 | 0 | 0 | 0.5 | 1 | 0 | P2-SITE,P2-FM,P2-ORACLE | +30.6% | +39.7% | +11.4% | +10.7% | +14.4% | +11.6% | +20.3% | +18.8% | +4.8% | +16.2% | +27.7% | +15.5% |
| 9 | 1 | 0 | 5 | 0.5 | 1 | 0 | P2-SITE,P2-FM,P2-ORACLE | +10.5% | +35.7% | +13.6% | +25.8% | +33.3% | -4.1% | +22.7% | +15.6% | +14.3% | +23.9% | +29.8% | +18.5% |
| 15 | 1 | 0 | 30 | 0.5 | 1 | 0 | P2-SITE,P2-FM,P2-ORACLE | +14.9% | +12.8% | +7.0% | -13.1% | -18.1% | +13.0% | -23.9% | -30.9% | -11.1% | -1.1% | +1.3% | -0.6% |
| 21 | 1 | 5 | 0 | 0.5 | 1 | 0 | P1b-SITE,P1b-FM | +333.6% | +224.7% | +196.5% | +215.1% | +214.7% | +256.5% | +192.6% | +250.9% | +215.0% | +294.4% | +52.5% | -11.9% |
| 39 | 1 | 30 | 0 | 0.5 | 1 | 0 | P1b-SITE,P1b-FM | +1512.7% | +884.6% | +907.2% | +1126.9% | +1236.4% | +1144.6% | +945.0% | +1181.0% | +984.5% | +1527.1% | +362.7% | +7.1% |
| 57 | 2 | 0 | 0 | 0.5 | 1 | 0 | P3 | +53.0% | +55.5% | +17.5% | +20.7% | +16.8% | +16.7% | +14.2% | +25.7% | +22.9% | +27.3% | +5.1% | -11.5% |
| 73 | 2 | 5 | 0 | 0 | 1 | 0 | P1a,P1b-SITE,P1b-FM | +280.6% | +130.3% | +132.8% | +172.5% | +133.1% | +159.1% | +138.2% | +172.4% | +74.2% | +166.6% | -60.8% | -21.6% |
| 75 | 2 | 5 | 0 | 0.5 | 1 | 0 | P1b-SITE,P1b-FM | +318.7% | +216.5% | +183.4% | +205.6% | +183.6% | +206.5% | +208.8% | +204.1% | +144.1% | +223.2% | +103.9% | -11.5% |
| 93 | 2 | 30 | 0 | 0.5 | 1 | 0 | P1b-SITE,P1b-FM | +1290.4% | +790.7% | +893.1% | +1072.3% | +876.5% | +1010.7% | +851.6% | +1095.4% | +786.2% | +1677.0% | +562.5% | +38.0% |
| 111 | 5 | 0 | 0 | 0.5 | 1 | 0 | P3 | +119.6% | +85.4% | +70.7% | +78.5% | +69.8% | +82.9% | +76.0% | +80.6% | +57.7% | +97.5% | +39.1% | -2.9% |
| 115 | 5 | 0 | 5 | 0 | 1 | 0 | P1a | +61.8% | +80.6% | +16.6% | +17.2% | +33.0% | +24.0% | +26.1% | +31.2% | +17.0% | +27.4% | -0.2% | +0.7% |
| 117 | 5 | 0 | 5 | 0.5 | 1 | 0 | P3 | +46.9% | +80.5% | +18.2% | +22.1% | +31.5% | +23.7% | +39.3% | +37.0% | +25.1% | +19.9% | +18.8% | -3.0% |
| 123 | 5 | 0 | 30 | 0.5 | 1 | 0 | P3 | +55.7% | +56.2% | +3.1% | +13.0% | +14.7% | +24.3% | +16.0% | +19.1% | +8.0% | +4.2% | +7.7% | +6.2% |
| 129 | 5 | 5 | 0 | 0.5 | 1 | 0 | P1b-SITE,P1b-FM | +298.3% | +275.4% | +231.9% | +245.5% | +219.2% | +233.6% | +219.7% | +236.1% | +197.8% | +220.3% | +118.5% | -22.1% |
| 147 | 5 | 30 | 0 | 0.5 | 1 | 0 | P1b-SITE,P1b-FM | +1191.1% | +604.1% | +825.0% | +1016.3% | +891.8% | +1008.1% | +773.2% | +988.0% | +709.0% | +1126.9% | +649.7% | -8.0% |
| 219 | 1 | 0 | 5 | 0.5 | 1 | 0.5 | P3 | +1.9% | +14.7% | -0.7% | -13.0% | -6.0% | -5.7% | -4.2% | -15.8% | -4.6% | +8.0% | +20.4% | +13.9% |

**primary: coverage** (16 cells; M per cell 2–2)

| cell | K | P | W | α | γ | φ_A | family | NV | SITE | FM-P | FM-P-C | FM-S | FM-S-C | REF | REF-C | FM-P-nat | ORACLE-C | ORACLE | FULL |
|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 3 | 1 | 0 | 0 | 0.5 | 1 | 0 | P2-SITE,P2-FM,P2-ORACLE | 0.500 | 0.000 | 0.500 | 0.500 | 1.000 | 1.000 | 0.500 | 0.500 | 1.000 | 1.000 | 0.500 | 0.500 |
| 9 | 1 | 0 | 5 | 0.5 | 1 | 0 | P2-SITE,P2-FM,P2-ORACLE | 0.500 | 0.000 | 1.000 | 0.500 | 0.500 | 0.500 | 1.000 | 1.000 | 1.000 | 0.500 | 0.500 | 1.000 |
| 15 | 1 | 0 | 30 | 0.5 | 1 | 0 | P2-SITE,P2-FM,P2-ORACLE | 1.000 | 1.000 | 1.000 | 0.500 | 0.500 | 1.000 | 0.500 | 0.500 | 0.500 | 1.000 | 1.000 | 1.000 |
| 21 | 1 | 5 | 0 | 0.5 | 1 | 0 | P1b-SITE,P1b-FM | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.500 | 1.000 |
| 39 | 1 | 30 | 0 | 0.5 | 1 | 0 | P1b-SITE,P1b-FM | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.500 | 1.000 |
| 57 | 2 | 0 | 0 | 0.5 | 1 | 0 | P3 | 0.000 | 0.000 | 0.500 | 0.500 | 0.500 | 0.500 | 0.500 | 0.500 | 0.500 | 0.500 | 1.000 | 1.000 |
| 73 | 2 | 5 | 0 | 0 | 1 | 0 | P1a,P1b-SITE,P1b-FM | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.500 | 1.000 |
| 75 | 2 | 5 | 0 | 0.5 | 1 | 0 | P1b-SITE,P1b-FM | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| 93 | 2 | 30 | 0 | 0.5 | 1 | 0 | P1b-SITE,P1b-FM | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| 111 | 5 | 0 | 0 | 0.5 | 1 | 0 | P3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| 115 | 5 | 0 | 5 | 0 | 1 | 0 | P1a | 0.000 | 0.000 | 0.500 | 0.500 | 0.000 | 0.000 | 0.000 | 0.000 | 0.500 | 0.000 | 1.000 | 1.000 |
| 117 | 5 | 0 | 5 | 0.5 | 1 | 0 | P3 | 0.000 | 0.000 | 0.500 | 0.500 | 0.000 | 0.500 | 0.000 | 0.000 | 0.500 | 0.500 | 0.500 | 1.000 |
| 123 | 5 | 0 | 30 | 0.5 | 1 | 0 | P3 | 0.000 | 0.000 | 1.000 | 1.000 | 0.500 | 0.000 | 0.500 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| 129 | 5 | 5 | 0 | 0.5 | 1 | 0 | P1b-SITE,P1b-FM | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| 147 | 5 | 30 | 0 | 0.5 | 1 | 0 | P1b-SITE,P1b-FM | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| 219 | 1 | 0 | 5 | 0.5 | 1 | 0.5 | P3 | 1.000 | 1.000 | 1.000 | 0.500 | 1.000 | 1.000 | 1.000 | 0.500 | 0.500 | 1.000 | 1.000 | 1.000 |

Flags (primary): small-truth cells 0; cell–arm pairs with non-finite replicates 0.

**single_file: relative bias** (10 cells; M per cell 2–2)

| cell | K | P | W | α | γ | φ_A | family | NV | SITE | FM-P | FM-P-C |
|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|
| 3 | 1 | 0 | 0 | 0.5 | 1 | 0 | P2-SITE,P2-FM,P2-ORACLE | +44.7% | +65.2% | +7.5% | -7.0% |
| 9 | 1 | 0 | 5 | 0.5 | 1 | 0 | P2-SITE,P2-FM,P2-ORACLE | +27.8% | +40.8% | +59.7% | +43.4% |
| 15 | 1 | 0 | 30 | 0.5 | 1 | 0 | P2-SITE,P2-FM,P2-ORACLE | +2.9% | +6.2% | -4.9% | -17.9% |
| 21 | 1 | 5 | 0 | 0.5 | 1 | 0 | P1b-SITE,P1b-FM | +348.1% | +299.5% | +198.6% | +242.5% |
| 39 | 1 | 30 | 0 | 0.5 | 1 | 0 | P1b-SITE,P1b-FM | +1519.2% | +465.2% | +831.3% | +1364.8% |
| 73 | 2 | 5 | 0 | 0 | 1 | 0 | P1a,P1b-SITE,P1b-FM | +256.0% | +109.0% | +97.2% | +169.8% |
| 75 | 2 | 5 | 0 | 0.5 | 1 | 0 | P1b-SITE,P1b-FM | +343.5% | +246.9% | +221.4% | +162.8% |
| 93 | 2 | 30 | 0 | 0.5 | 1 | 0 | P1b-SITE,P1b-FM | +1382.9% | +556.9% | +917.3% | +1091.2% |
| 129 | 5 | 5 | 0 | 0.5 | 1 | 0 | P1b-SITE,P1b-FM | +293.2% | +233.7% | +220.1% | +202.5% |
| 147 | 5 | 30 | 0 | 0.5 | 1 | 0 | P1b-SITE,P1b-FM | +1017.3% | +666.7% | +808.9% | +973.9% |

**single_file: coverage** (10 cells; M per cell 2–2)

| cell | K | P | W | α | γ | φ_A | family | NV | SITE | FM-P | FM-P-C |
|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|
| 3 | 1 | 0 | 0 | 0.5 | 1 | 0 | P2-SITE,P2-FM,P2-ORACLE | 0.000 | 0.000 | 1.000 | 1.000 |
| 9 | 1 | 0 | 5 | 0.5 | 1 | 0 | P2-SITE,P2-FM,P2-ORACLE | 1.000 | 0.000 | 0.000 | 0.000 |
| 15 | 1 | 0 | 30 | 0.5 | 1 | 0 | P2-SITE,P2-FM,P2-ORACLE | 1.000 | 1.000 | 1.000 | 1.000 |
| 21 | 1 | 5 | 0 | 0.5 | 1 | 0 | P1b-SITE,P1b-FM | 0.000 | 0.000 | 0.000 | 0.000 |
| 39 | 1 | 30 | 0 | 0.5 | 1 | 0 | P1b-SITE,P1b-FM | 0.000 | 0.500 | 0.000 | 0.000 |
| 73 | 2 | 5 | 0 | 0 | 1 | 0 | P1a,P1b-SITE,P1b-FM | 0.000 | 0.500 | 0.500 | 0.000 |
| 75 | 2 | 5 | 0 | 0.5 | 1 | 0 | P1b-SITE,P1b-FM | 0.000 | 0.000 | 0.000 | 0.000 |
| 93 | 2 | 30 | 0 | 0.5 | 1 | 0 | P1b-SITE,P1b-FM | 0.000 | 0.500 | 0.000 | 0.000 |
| 129 | 5 | 5 | 0 | 0.5 | 1 | 0 | P1b-SITE,P1b-FM | 0.000 | 0.000 | 0.000 | 0.000 |
| 147 | 5 | 30 | 0 | 0.5 | 1 | 0 | P1b-SITE,P1b-FM | 0.000 | 0.000 | 0.000 | 0.000 |

Flags (single_file): small-truth cells 0; cell–arm pairs with non-finite replicates 0.

**W0: relative bias** (8 cells; M per cell 2–2)

| cell | K | P | W | α | γ | φ_A | family | NV | SITE | FM-P | FM-P-C | ORACLE-C | ORACLE |
|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|
| 3 | 1 | 0 | 0 | 0.5 | 1 | 0 | P2-SITE,P2-FM,P2-ORACLE | +26.1% | +42.4% | +16.3% | +16.6% | +22.4% | +33.7% |
| 21 | 1 | 5 | 0 | 0.5 | 1 | 0 | P1b-SITE,P1b-FM | +348.0% | +229.6% | +188.8% | +262.1% | +309.1% | +101.1% |
| 39 | 1 | 30 | 0 | 0.5 | 1 | 0 | P1b-SITE,P1b-FM | +1707.9% | +767.3% | +1072.3% | +1326.0% | +1781.2% | +618.0% |
| 73 | 2 | 5 | 0 | 0 | 1 | 0 | P1a,P1b-SITE,P1b-FM | +238.4% | +135.4% | +124.9% | +195.9% | +220.8% | -42.5% |
| 75 | 2 | 5 | 0 | 0.5 | 1 | 0 | P1b-SITE,P1b-FM | +280.9% | +210.8% | +167.3% | +215.3% | +249.1% | +84.5% |
| 93 | 2 | 30 | 0 | 0.5 | 1 | 0 | P1b-SITE,P1b-FM | +1536.8% | +681.3% | +1004.1% | +1183.4% | +1459.6% | +597.7% |
| 129 | 5 | 5 | 0 | 0.5 | 1 | 0 | P1b-SITE,P1b-FM | +299.8% | +237.9% | +198.8% | +226.0% | +246.0% | +110.5% |
| 147 | 5 | 30 | 0 | 0.5 | 1 | 0 | P1b-SITE,P1b-FM | +1014.5% | +560.0% | +742.6% | +982.6% | +1053.0% | +506.7% |

**W0: coverage** (8 cells; M per cell 2–2)

| cell | K | P | W | α | γ | φ_A | family | NV | SITE | FM-P | FM-P-C | ORACLE-C | ORACLE |
|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|
| 3 | 1 | 0 | 0 | 0.5 | 1 | 0 | P2-SITE,P2-FM,P2-ORACLE | 0.000 | 0.000 | 0.500 | 0.500 | 0.000 | 0.000 |
| 21 | 1 | 5 | 0 | 0.5 | 1 | 0 | P1b-SITE,P1b-FM | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 39 | 1 | 30 | 0 | 0.5 | 1 | 0 | P1b-SITE,P1b-FM | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 73 | 2 | 5 | 0 | 0 | 1 | 0 | P1a,P1b-SITE,P1b-FM | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.500 |
| 75 | 2 | 5 | 0 | 0.5 | 1 | 0 | P1b-SITE,P1b-FM | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 93 | 2 | 30 | 0 | 0.5 | 1 | 0 | P1b-SITE,P1b-FM | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 129 | 5 | 5 | 0 | 0.5 | 1 | 0 | P1b-SITE,P1b-FM | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 147 | 5 | 30 | 0 | 0.5 | 1 | 0 | P1b-SITE,P1b-FM | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

Flags (W0): small-truth cells 0; cell–arm pairs with non-finite replicates 0.

**W5: relative bias** (1 cells; M per cell 2–2)

| cell | K | P | W | α | γ | φ_A | family | NV | SITE | FM-P | FM-P-C | ORACLE-C | ORACLE |
|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|
| 9 | 1 | 0 | 5 | 0.5 | 1 | 0 | P2-SITE,P2-FM,P2-ORACLE | +22.5% | +28.8% | +23.7% | +13.8% | +14.8% | +22.0% |

**W5: coverage** (1 cells; M per cell 2–2)

| cell | K | P | W | α | γ | φ_A | family | NV | SITE | FM-P | FM-P-C | ORACLE-C | ORACLE |
|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|
| 9 | 1 | 0 | 5 | 0.5 | 1 | 0 | P2-SITE,P2-FM,P2-ORACLE | 0.500 | 0.000 | 0.500 | 0.500 | 0.500 | 0.500 |

Flags (W5): small-truth cells 0; cell–arm pairs with non-finite replicates 0.

> **PLACEHOLDER — synthetic test output, not results.**
