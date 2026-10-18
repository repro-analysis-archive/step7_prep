# OPERATIONS_LOG_STEP4_5: addendum (corrections, 2026-10-09)

* **Recorded:** 2026-10-09, under `CC_TASK_SS_step7_prep_fixes_v1.md` §4.
* **To be committed:** separately, after step 6 has started.
* **Scope:** this addendum corrects `decisions/OPERATIONS_LOG_STEP4_5.md`. The chain commits that file from its staged copy, which was deliberately not edited while the chain runs, because changing the chain's inputs could make it stop.

## 1. Watchdog (corrects §1, last row, and the appendix line "not present at this path")

* **Started:** 2026-10-07 09:37:15 +0900.
* **Process:** `~/ops/runner_watchdog_v1.sh`, pid 4004380.
* **Log:** `~/ops/runner_watchdog.log`.
* **Relaunches:** none logged as of the morning of 2026-10-09 (investigator).
* **Consistency:** `ps` on 2026-10-09 10:30 showed pid 4004380 running for 2 days 00:52:55, which matches the start time.
* **Why the draft said otherwise.** The staged log's statement that the watchdog was absent comes from a read-only check at about 08:15 on 2026-10-07, before the watchdog was started. The chain's automatic appendix reports the file's state at commit time.

## 2. Chain launch (corrects §2, decision 1, and `STEP6_RUNNER.md` §6, which assumed a Friday launch)

* **Launched:** 2026-10-07 09:36 +0900 (process start 09:36:40).
* **Process:** `/srv/ss_step6_prep/chain_5_to_6.py run`, pid 4003618, on the base conda Python (`/home/user/miniconda3/bin/python3`).
* **Launch day:** 7 October, not the Friday initially planned.
