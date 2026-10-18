#!/usr/bin/env bash
# Peak summed PSS (KiB) of processes whose command line mentions $1; kills them above 3.8 GiB (hard limit 4 GB).
pat="$1"; peakf="$2"; peak=0
while true; do
  tot=0; pids=()
  for p in /proc/[0-9]*; do
    c=$(tr '\0' ' ' < $p/cmdline 2>/dev/null)
    case "$c" in *"$pat"*) case "$c" in *memguard*) ;; *) r=$(awk "/^Pss:/{print \$2}" $p/smaps_rollup 2>/dev/null); tot=$((tot + ${r:-0})); pids+=("${p#/proc/}");; esac;; esac
  done
  (( tot > peak )) && peak=$tot && echo $peak > "$peakf"
  if (( tot > 3984588 )); then kill -KILL "${pids[@]}" 2>/dev/null; echo "KILLED at $tot KiB" >> "$peakf"; fi
  sleep 1
done
