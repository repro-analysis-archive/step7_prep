**Table 1. Data and analysis sets**

| set | cases | centres_2_3_4_5 | definition | source |
|---|---|---|---|---|
| representation set (E1, E3-site, PCA / LEACE) | 278 | all 278 full-length cases of centres 2–5 | 279 counted cases minus Center3_020 (timestamp beyond video end); centre 1 excluded (mostly 5-min clips) | protocol §2 |
| primary causal set | 158 | 28 / 34 / 44 / 52 | s − 45 ≥ 0 and s + 60 ≤ n (n = ⌊duration / 5⌋); offsets O ∈ {−15…15} (seed 20261005) | protocol §2, §7.2; dbd5984 |
| per-W set W = 0 | 204 | 37 / 40 / 57 / 70 | primary offsets kept; 46 new offsets, same rule and seed | protocol §10.3; adf9160 |
| per-W set W = 5 | 201 | 37 / 40 / 56 / 68 | primary offsets kept; 43 new offsets | protocol §10.3; adf9160 |
| single-file set | 123 | 13 / 34 / 44 / 32 | primary cases with one video file | protocol §2; ss_window_offsets.csv (dbd5984) |
| excluded from the primary set | 120 | 21 / 7 / 27 / 65 | mainly early switches (46 of 117 centre-5 cases show the appendix within 75 s) | protocol §7.2 |
