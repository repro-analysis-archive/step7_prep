**Table X-E3. Exploratory X1: E3-site, E2 and E3-state retention on the 158-case analysis region, next to step 5** (X1: `results_X/x1_e3.json`, `1c8e628`; step 5: `results/step5/checks.json`, `0ebf2cf`)

*E3-site: case-level site balanced accuracy after removal [95 % interval]; one-sided 95 % upper bound (boundary 0.35).*

| key | probe | step-5 BA | step-5 95 % interval | step-5 upper | X1 BA | X1 95 % interval | X1 upper |
|---|---|---|---|---|---|---|---|
| P | linear | 0.416 | [0.352, 0.481] | 0.472 | 0.250 | [0.250, 0.250] | 0.250 |
| P | mlp | 0.702 | [0.640, 0.763] | 0.755 | 0.577 | [0.506, 0.647] | 0.637 |
| S | linear | 0.393 | [0.346, 0.444] | 0.435 | 0.250 | [0.250, 0.250] | 0.250 |
| S | mlp | 0.428 | [0.368, 0.489] | 0.476 | 0.309 | [0.255, 0.366] | 0.357 |
| REF | linear | 0.448 | [0.387, 0.518] | 0.505 | 0.250 | [0.250, 0.250] | 0.250 |
| REF | mlp | 0.620 | [0.543, 0.687] | 0.680 | 0.458 | [0.392, 0.530] | 0.517 |

*E2 primary: ΔAUC for S_t of base + R_t over base [95 % CI]; criterion ΔAUC ≥ 0.05 and CI excluding 0.*

| key | condition | ΔAUC | 95 % CI | E2 criterion |
|---|---|---|---|---|
| P | step 5, before removal | 0.050 | [0.019, 0.080] | met |
| P | step 5, after protocol removal | 0.044 | [0.012, 0.074] | not met |
| P | X1, after X1 removal | 0.051 | [0.019, 0.083] | met |
| S | step 5, before removal | 0.002 | [-0.017, 0.024] | not met |
| S | step 5, after protocol removal | 0.003 | [-0.018, 0.025] | not met |
| S | X1, after X1 removal | -0.000 | [-0.022, 0.021] | not met |
| REF | step 5, before removal | 0.024 | [-0.000, 0.049] | not met |
| REF | step 5, after protocol removal | 0.024 | [-0.000, 0.051] | not met |
| REF | X1, after X1 removal | 0.024 | [-0.002, 0.052] | not met |

*E3-state retention (post / pre ΔAUC ≥ 0.50):*

| key | step 5 | X1 |
|---|---|---|
| P | retained fraction 0.868 | retained fraction 1.019 |
| S | not applicable (E2 primary failed) | not applicable (E2 primary failed) |
| REF | not applicable (E2 primary failed) | not applicable (E2 primary failed) |

* The X1 eraser is fitted on training folds and evaluated on held-out folds of the same population (the 158-case analysis region); its linear E3-site value is a check of the procedure and does not gate X1 (X_REPORT.md).
* All values as recorded; the CSV gives every field as its JSON text.
