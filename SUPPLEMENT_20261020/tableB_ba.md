**Table B. Exploratory B: case-level site balanced accuracy per key × analysis × probe × set** (`results_B/b_main.csv`, `/srv/ss_exploratory_B` `458341f`)

(a) transport: the S1 probe (fitted as in E3) evaluated on each set; (b) within-set refit. Reported separately; never pooled or contrasted. S1 = 278 cases, all steps; S2 = 158 cases, all steps; S3 = 158 cases, analysis region (75 steps per case).

| key | analysis | probe | set | cases | rows | BA | 95 % interval | one-sided 95 % upper | exceeds 0.35 |
|---|---|---|---|---|---|---|---|---|---|
| P | (a) | linear | S1 | 278 | 104662 | 0.250 | [0.250, 0.250] | 0.250 | no |
| P | (a) | linear | S2 | 158 | 70763 | 0.250 | [0.250, 0.250] | 0.250 | no |
| P | (a) | linear | S3 | 158 | 11850 | 0.250 | [0.250, 0.250] | 0.250 | no |
| P | (a) | mlp | S1 | 278 | 104662 | 0.957 | [0.927, 0.982] | 0.979 | yes |
| P | (a) | mlp | S2 | 158 | 70763 | 0.969 | [0.936, 0.994] | 0.991 | yes |
| P | (a) | mlp | S3 | 158 | 11850 | 0.884 | [0.827, 0.933] | 0.926 | yes |
| P | (b) | linear | S1 | 278 | 104662 | 0.250 | [0.250, 0.250] | 0.250 | no |
| P | (b) | linear | S2 | 158 | 70763 | 0.231 | [0.182, 0.282] | 0.273 | no |
| P | (b) | linear | S3 | 158 | 11850 | 0.416 | [0.352, 0.481] | 0.472 | yes |
| P | (b) | mlp | S1 | 278 | 104662 | 0.957 | [0.927, 0.982] | 0.979 | yes |
| P | (b) | mlp | S2 | 158 | 70763 | 0.948 | [0.907, 0.982] | 0.982 | yes |
| P | (b) | mlp | S3 | 158 | 11850 | 0.702 | [0.640, 0.763] | 0.755 | yes |
| S | (a) | linear | S1 | 278 | 104662 | 0.250 | [0.250, 0.250] | 0.250 | no |
| S | (a) | linear | S2 | 158 | 70763 | 0.250 | [0.250, 0.250] | 0.250 | no |
| S | (a) | linear | S3 | 158 | 11850 | 0.250 | [0.250, 0.250] | 0.250 | no |
| S | (a) | mlp | S1 | 278 | 104662 | 0.495 | [0.456, 0.535] | 0.531 | yes |
| S | (a) | mlp | S2 | 158 | 70763 | 0.479 | [0.433, 0.523] | 0.517 | yes |
| S | (a) | mlp | S3 | 158 | 11850 | 0.501 | [0.443, 0.562] | 0.550 | yes |
| S | (b) | linear | S1 | 278 | 104662 | 0.250 | [0.250, 0.250] | 0.250 | no |
| S | (b) | linear | S2 | 158 | 70763 | 0.239 | [0.188, 0.290] | 0.282 | no |
| S | (b) | linear | S3 | 158 | 11850 | 0.393 | [0.346, 0.444] | 0.435 | yes |
| S | (b) | mlp | S1 | 278 | 104662 | 0.495 | [0.456, 0.535] | 0.531 | yes |
| S | (b) | mlp | S2 | 158 | 70763 | 0.520 | [0.475, 0.566] | 0.559 | yes |
| S | (b) | mlp | S3 | 158 | 11850 | 0.428 | [0.368, 0.489] | 0.476 | yes |
| REF | (a) | linear | S1 | 278 | 104662 | 0.250 | [0.250, 0.250] | 0.250 | no |
| REF | (a) | linear | S2 | 158 | 70763 | 0.250 | [0.250, 0.250] | 0.250 | no |
| REF | (a) | linear | S3 | 158 | 11850 | 0.250 | [0.250, 0.250] | 0.250 | no |
| REF | (a) | mlp | S1 | 278 | 104662 | 0.863 | [0.818, 0.904] | 0.900 | yes |
| REF | (a) | mlp | S2 | 158 | 70763 | 0.875 | [0.822, 0.924] | 0.916 | yes |
| REF | (a) | mlp | S3 | 158 | 11850 | 0.788 | [0.724, 0.848] | 0.839 | yes |
| REF | (b) | linear | S1 | 278 | 104662 | 0.250 | [0.250, 0.250] | 0.250 | no |
| REF | (b) | linear | S2 | 158 | 70763 | 0.208 | [0.158, 0.257] | 0.251 | no |
| REF | (b) | linear | S3 | 158 | 11850 | 0.448 | [0.387, 0.518] | 0.505 | yes |
| REF | (b) | mlp | S1 | 278 | 104662 | 0.863 | [0.818, 0.904] | 0.900 | yes |
| REF | (b) | mlp | S2 | 158 | 70763 | 0.871 | [0.815, 0.924] | 0.918 | yes |
| REF | (b) | mlp | S3 | 158 | 11850 | 0.620 | [0.543, 0.687] | 0.680 | yes |

**Judgement statements as generated** (`results_B/b_judgements.csv`; judgement = whether the one-sided 95 % upper bound exceeds 0.35)

| key | analysis | probe | pair | exceeds_x | exceeds_y | statement |
|---|---|---|---|---|---|---|
| P | a | linear | S1->S2 | False | False | the judgement does not change between S1 and S2 |
| P | a | linear | S2->S3 | False | False | the judgement does not change between S2 and S3 |
| P | a | linear | S1->S3 | False | False | the judgement does not change between S1 and S3 |
| P | a | mlp | S1->S2 | True | True | the judgement does not change between S1 and S2 |
| P | a | mlp | S2->S3 | True | True | the judgement does not change between S2 and S3 |
| P | a | mlp | S1->S3 | True | True | the judgement does not change between S1 and S3 |
| P | b | linear | S1->S2 | False | False | the judgement does not change between S1 and S2 |
| P | b | linear | S2->S3 | False | True | the judgement changes between S2 and S3 |
| P | b | linear | S1->S3 | False | True | the judgement changes between S1 and S3 |
| P | b | mlp | S1->S2 | True | True | the judgement does not change between S1 and S2 |
| P | b | mlp | S2->S3 | True | True | the judgement does not change between S2 and S3 |
| P | b | mlp | S1->S3 | True | True | the judgement does not change between S1 and S3 |
| S | a | linear | S1->S2 | False | False | the judgement does not change between S1 and S2 |
| S | a | linear | S2->S3 | False | False | the judgement does not change between S2 and S3 |
| S | a | linear | S1->S3 | False | False | the judgement does not change between S1 and S3 |
| S | a | mlp | S1->S2 | True | True | the judgement does not change between S1 and S2 |
| S | a | mlp | S2->S3 | True | True | the judgement does not change between S2 and S3 |
| S | a | mlp | S1->S3 | True | True | the judgement does not change between S1 and S3 |
| S | b | linear | S1->S2 | False | False | the judgement does not change between S1 and S2 |
| S | b | linear | S2->S3 | False | True | the judgement changes between S2 and S3 |
| S | b | linear | S1->S3 | False | True | the judgement changes between S1 and S3 |
| S | b | mlp | S1->S2 | True | True | the judgement does not change between S1 and S2 |
| S | b | mlp | S2->S3 | True | True | the judgement does not change between S2 and S3 |
| S | b | mlp | S1->S3 | True | True | the judgement does not change between S1 and S3 |
| REF | a | linear | S1->S2 | False | False | the judgement does not change between S1 and S2 |
| REF | a | linear | S2->S3 | False | False | the judgement does not change between S2 and S3 |
| REF | a | linear | S1->S3 | False | False | the judgement does not change between S1 and S3 |
| REF | a | mlp | S1->S2 | True | True | the judgement does not change between S1 and S2 |
| REF | a | mlp | S2->S3 | True | True | the judgement does not change between S2 and S3 |
| REF | a | mlp | S1->S3 | True | True | the judgement does not change between S1 and S3 |
| REF | b | linear | S1->S2 | False | False | the judgement does not change between S1 and S2 |
| REF | b | linear | S2->S3 | False | True | the judgement changes between S2 and S3 |
| REF | b | linear | S1->S3 | False | True | the judgement changes between S1 and S3 |
| REF | b | mlp | S1->S2 | True | True | the judgement does not change between S1 and S2 |
| REF | b | mlp | S2->S3 | True | True | the judgement does not change between S2 and S3 |
| REF | b | mlp | S1->S3 | True | True | the judgement does not change between S1 and S3 |

* Rows of the first table identical, at 3 decimals, to the committed `B_REPORT.md`; the judgement statements are copied unchanged.
