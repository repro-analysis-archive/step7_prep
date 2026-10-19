**Table S4. Mask check (protocol §3.1 step 3; step-4 record `8d4c61a`, `results/step4/mask_check.json` and `run_meta.json`)**

| centre | frames in the mean frame | visible radius ρ_c (× side) | profile points |
|---|---|---|---|
| 2 | 2820 | 0.5625 | 180 |
| 3 | 2797 | 0.703125 | 180 |
| 4 | 4850 | 0.703125 | 180 |
| 5 | 7093 | 0.703125 | 180 |

* min_c ρ_c = 0.5625; final r = 0.45 (× side).
* Rule (§3.1): r = 0.45 if min_c ρ_c ≥ 0.45, otherwise r = 0.98 × min_c ρ_c. Recorded: r = 0.45; the fallback r = 0.98 × min_c ρ_c was not used.
* Validity: `run_meta.json` `mask_check_valid` = true; runner log (LaCie `ss_step4_5/logs/progress.log` line 234): "mask check valid (r = 0.45 stands)".
* For centres 3–5, ρ_c equals the last profile point (0.703125).
