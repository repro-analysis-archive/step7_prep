#!/usr/bin/env bash
# §14 step 7 (orchestration only): the locked final aggregation of the causal grid (family verdicts, cell metrics),
# run from the step-6 code snapshot with the step-6 arguments; no unit is recomputed; records committed automatically
# (records only). Refuses (exit 3, nothing changed) unless step 6 is complete and verified, HEAD == --expect-commit,
# the tree is clean and no analysis code changed since step 6. Logic: scripts/step7_orchestrate.py.
#
#   scripts/run_step7.sh --expect-commit <SHA>          (about 10-30 min; may be run detached with setsid nohup)
#   scripts/run_step7.sh --status
#
# Options: --out6 DIR (default /media/user/LaCie/medvideo_gate/ss_step6).
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY=/home/user/miniconda3/bin/python3
OUT6=/media/user/LaCie/medvideo_gate/ss_step6
EXPECT=""
MODE=run
while [[ $# -gt 0 ]]; do
  case "$1" in
    --expect-commit) EXPECT="$2"; shift 2 ;;
    --out6) OUT6="$2"; shift 2 ;;
    --status) MODE=status; shift ;;
    *) echo "unknown argument: $1" >&2; exit 64 ;;
  esac
done
if [[ $MODE == status ]]; then exec "$PY" "$REPO/scripts/step7_orchestrate.py" status --out6 "$OUT6"; fi
[[ -n $EXPECT ]] || { echo "$(date -Is) refused: --expect-commit is required" >&2; exit 3; }
export GIT_OPTIONAL_LOCKS=0
EXP="$(git -C "$REPO" rev-parse --verify --quiet "${EXPECT}^{commit}")" || { echo "refused: unknown commit" >&2; exit 3; }
[[ "$(git -C "$REPO" rev-parse --verify --quiet HEAD:scripts/run_step7.sh)" == \
   "$(git -C "$REPO" hash-object "${BASH_SOURCE[0]}")" ]] || { echo "refused: this script is not the one in HEAD" >&2; exit 3; }
mkdir -p "$OUT6/logs"
exec 9>"$OUT6/step7.lock"
flock -n 9 || { echo "refused: another step-7 run holds $OUT6/step7.lock" >&2; exit 3; }
cd "$REPO"
export PYTHONDONTWRITEBYTECODE=1
"$PY" "$REPO/scripts/step7_orchestrate.py" run --repo "$REPO" --out6 "$OUT6" --expect-commit "$EXP" \
  2>&1 | tee -a "$OUT6/logs/step7_stdout.log"
