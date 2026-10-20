# Evidence preserved from non-committed logs (2026-10-20)

Saved for task `CC_TASK_SS_manuscript_package_SSD_v3.md` §0 because the Methods draft cites facts that rest on logs
outside any repository, which may be rotated. Every file is the unchanged output of the command shown (no line edited);
commands were run on 2026-10-20 as user `user` (groups include `adm`, so no elevated rights were needed).

| file | what it is | command | SHA-256 |
|---|---|---|---|
| `journal_20261006_1720-1735_sudo_swap.txt` | System journal 2026-10-06 17:20–17:35: the sudo entries for `sysctl vm.swappiness=10` (17:28:14.344), `swapoff -a` (17:28:14.358) and `swapon -a` (17:28:17.029), each from TTY pts/4 in `/home/user/projects/medical_video_causal_gate`, with their session open/close lines; the systemd lines for the swap deactivation (17:28:17.023); the kernel line for the swap activation (17:28:17.034). The kernel logs no line for the deactivation; systemd does. | `journalctl --since "2026-10-06 17:20:00" --until "2026-10-06 17:35:00" -o short-iso-precise \| grep -E 'sudo\[[0-9]+\]\|systemd\[1\]: .*\.swap: \|kernel: .*swap'` | `2721e76bb4d1c6a98dd52ccc6e67db4c4de1d9c9b9501f016f4663b1bb655fe6` |
| `kernel_20261006_1600-1730.txt` | Kernel log 2026-10-06 16:00–17:30, complete (one line: the swap activation at 17:28:17). | `journalctl -k --since "2026-10-06 16:00:00" --until "2026-10-06 17:30:00" -o short-iso-precise` | `34c41729cd9291960b0f3fc3cd7df41269d098f349ca6257bdb7ea04bec778fe` |
| `kernel_20261006_1600-1730_oom_search.txt` | OOM search in that excerpt: 0 matching lines. | shown in the file | `08416e77750cb87dbe7b7408bc7056178f5fbf21445b9be0a9333d11bf039087` |
| `runner_watchdog.log` | `~/ops/runner_watchdog.log`, complete (2 lines: start 2026-10-07 09:37:15; exit without action 2026-10-12 14:28:06, runner state complete). No relaunch line. | `cp -p /home/user/ops/runner_watchdog.log .` | `9e4f1b18acd42d74caa67b1498b276a3718a85fad8bf4f9db47d23435a50598d` |
| `step4_5_progress_log_lines_43_57-63_234.txt` | Step 4–5 runner log on LaCie (`/media/user/LaCie/medvideo_gate/ss_step4_5/logs/progress.log`, read only), lines 43, 57–63 and 234: the first mask-check start (14:20:15); the memory-pressure strikes and STOP (16:34:57–16:35:27); the resume preflight (17:28:49) and the mask-check restart (17:28:52, attempt 1); "mask check valid (r = 0.45 stands)" (2026-10-07 21:33:51). The same lines are in `runner_stdout.log`. | `sed -n '43p;57,63p;234p' /media/user/LaCie/medvideo_gate/ss_step4_5/logs/progress.log` | `bf576e11ee3a138c55184d6ed47a65aaa0def5457f44b7d632e74de93cefa355` |
| `SS_DS203_PROJECT_RECORD_for_evaluator_20261020_v5.md` | The evaluator record v5 (fact base quoted by `SUPPLEMENT_20261020/CAPTIONS.md` and the Methods draft), copied unchanged from `~/Downloads/`. | `cp -p ~/Downloads/SS_DS203_PROJECT_RECORD_for_evaluator_20261020_v5.md .` | `c1d8d651535136907b461e2666b4671d4fc58c736a78e6bb61fbcac54dc27684` |

**Journal coverage.**
* `journalctl --list-boots`: boot 0 (`1f3eaff7…`) runs from 2026-09-27 22:29:42 JST to the present, so 2026-10-06 lies within one boot.
* The full journal holds 1,161 entries for 2026-10-06 16:00–17:30 (`journalctl --since … --until … \| grep -c ""`), so it was recording throughout the window.
* The kernel logged 7 lines on 2026-10-06; one of them falls in the window.
