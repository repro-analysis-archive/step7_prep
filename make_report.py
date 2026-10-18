"""§14 step 7 results report (one Markdown file plus a per-cell CSV), from the committed step-5 / step-7 records.

Inputs (read only):
* <step7>/families.json, <step7>/cell_metrics.csv     locked grid_driver.aggregate output (§11, §12.3)
* <step5>/checks.json, <step5>/section13.json, <step5>/reps_report.json (optional)
* gsite_record.json (code lock)
Output: <out> (REPORT.md) and report_cells.csv next to it.

Sections: 1 family verdicts (primary set; §10.3 sets separately; P3 descriptive); 2 §13 claim ceilings, applied
mechanically (the step-5 §13 record, the rules deferred to step 7, the standing rules); 3 E1-E3, LEACE and G-SITE
summaries; 4 relative bias and interval coverage per cell and arm. No statistic is computed here beyond formatting and
counting: every number comes from the locked outputs. If any input is labelled PLACEHOLDER (or --placeholder is
given), every page carries a PLACEHOLDER banner.

    python make_report.py --step7 DIR --step5 DIR --gsite FILE --out REPORT.md [--code REPO_ROOT] [--placeholder]
"""
import argparse
import hashlib
import json
import math
import os
import sys

import pandas as pd

ARMS = ("NV", "SITE", "FM-P", "FM-P-C", "FM-S", "FM-S-C", "REF", "REF-C", "FM-P-nat", "ORACLE-C", "ORACLE", "FULL")
FAMILY_ORDER = ("P1a", "P1b-SITE", "P1b-FM", "P2-SITE", "P2-FM", "P2-ORACLE")
KEYS = ("P", "S", "REF", "P-nat")
KEY_NAMES = {"P": "primary (FM-P)", "S": "secondary (FM-S)", "REF": "reference (REF)", "P-nat": "primary, native (FM-P-nat)"}
WORDING = {"SUPPORTED": "consistent with the theory-motivated direction",
           "CONTRADICTED": "inconsistent with the theory-motivated direction",
           "INCONCLUSIVE": "inconclusive (no directional claim)"}


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def jload(p, required=True):
    if not os.path.exists(p):
        if required:
            raise SystemExit(f"STOP: missing input {p}")
        return None
    return json.load(open(p))


def f3(x, pct=False):
    if x is None or (isinstance(x, float) and not math.isfinite(x)):
        return "—"
    return f"{100 * x:+.1f}%" if pct else f"{x:.3f}"


def yn(x):
    return "—" if x is None else ("pass" if x else "FAIL")


def is_placeholder(*objs):
    def walk(o):
        if isinstance(o, dict):
            return o.get("label") == "PLACEHOLDER" or o.get("placeholder") is True or any(walk(v) for v in o.values())
        if isinstance(o, list):
            return any(walk(v) for v in o)
        return isinstance(o, str) and o.startswith("PLACEHOLDER")
    return any(walk(o) for o in objs if o is not None)

# §10.3: the families named for each sensitivity set (arms: single-file NV, SITE, FM-P, FM-P-C; per-W sets also
# ORACLE, ORACLE-C). Anything else the locked aggregation computes for these sets is exploratory.
NAMED_SENSITIVITY = {"single_file": ("P1b-SITE", "P1b-FM", "P2-SITE", "P2-FM"),
                     "W0": ("P1b-SITE", "P1b-FM", "P2-SITE", "P2-FM", "P2-ORACLE"),
                     "W5": ("P2-SITE", "P2-FM", "P2-ORACLE")}
FM_FAMILIES = ("P1b-FM", "P2-FM")


def own_set_conditions(checks, s):
    """P1b-FM / P2-FM conditions from the set's own step-5 checks (key P; the FM arms of §10.3 are FM-P / FM-P-C).

    Read as §12.2 with "both sets" = the 278-case set and this set. Returns (dict or None, explanation)."""
    c = checks.get("P") or {}
    e1, e3, st = c.get(f"E1_{s}"), c.get(f"E3_site_{s}"), c.get(f"E3_state_{s}")
    if not (e1 and e3 and st and c.get("E1_278") and c.get("E3_site_278")):
        return None, f"no set-specific E1–E3 for {s} in the step-5 record"
    cond = {"E1": bool(c["E1_278"]["pass"] and e1["pass"]), "E3-site": bool(c["E3_site_278"]["pass"] and e3["pass"]),
            "E3-state": bool((not st["applicable"]) or st["pass_"])}
    return cond, ", ".join(f"{k} {'pass' if v else 'FAIL'}" for k, v in cond.items())


def own_set_ceilings(checks, s):
    """§13 ceilings for FM-P / FM-P-C in set s from the set's own E2 / E3 results (statements only)."""
    c = checks.get("P") or {}
    out = []
    e2, e3, st = c.get(f"E2_{s}"), c.get(f"E3_site_{s}"), c.get(f"E3_state_{s}")
    if e2 is not None and not e2.get("pass"):
        out.append("E2 fails on this set: FM-vs-NV comparisons cannot be read as confounder recovery")
    if e3 is not None and e3.get("pass") and e3.get("mlp_exceeds_margin"):
        out.append("E3-site passes but the MLP probe exceeds the margin: \"linear site information removed; "
                   "nonlinear site information remains\"")
    if st is not None and st.get("applicable") and not st.get("pass_"):
        out.append("E3-state-retention fails on this set: FM−C differences not attributed to site removal alone")
    if st is not None and not st.get("applicable"):
        out.append("E3-state-retention not applicable on this set (E2 fails): FM−C interpretation rests on E3-site")
    return out


def sensitivity_section(fams, checks, gsite):
    sets = gsite.get("sets", {})
    L = ["", "**§10.3 sensitivity sets — named families** (reported separately; never family verdicts). "
         "*Locked aggregation*: the locked `aggregate` verdict, which applies the primary-set E1 / E3 conditions to "
         "every set. *Protocol-consistent ceiling*: the §13 / §12.2 conditions evaluated on the set's own step-5 "
         "E1–E3 (single-file: E1 and E3-site on the 278-case set and on the single-file set, E3-state on the "
         "single-file set); per-W P2 results are instrument-like only if that set's G-SITE ≤ 0.01.", "",
         "| set:family | cells | D̄_F | 95 % CI | share D_j > 0 | locked aggregation | own-set conditions | "
         "protocol-consistent ceiling |", "|---|---:|---:|---|---:|---|---|---|"]
    explor = []
    for k in sorted(k for k in fams if not k.startswith("primary:")):
        v = fams[k]
        s, f = k.split(":", 1)
        if f not in NAMED_SENSITIVITY.get(s, ()):
            explor.append((k, v))
            continue
        locked = f"{v['verdict']} (conditions applied: primary set)"
        if f in FM_FAMILIES:
            cond, why = own_set_conditions(checks, s)
            if cond is None:
                ceil = "descriptive only: " + why
            elif all(cond.values()):
                ceil = (f"{v['rule_verdict']}: {WORDING.get(v['rule_verdict'], v['rule_verdict'])}"
                        if v["rule_verdict"] in WORDING else v["rule_verdict"])
            else:
                ceil = "NOT TESTED on own checks: FM vs FM−C reported descriptively only"
            extra = own_set_ceilings(checks, s)
            if extra:
                ceil += "; " + "; ".join(extra)
        else:
            why = "no E1–E3 condition"
            ceil = v["rule_verdict"]
        if f.startswith("P2"):
            g = sets.get(s, {}).get("gate_pass") if s in ("W0", "W5") else None
            gtxt = ("G-SITE (own set) " + ("≤ 0.01: instrument-like" if g else "> 0.01: descriptive")) if g is not None \
                else "G-SITE: no single-file value at code lock (primary value used by the locked code)"
            why = f"{why}; {gtxt}"
            if g is False:
                ceil = "descriptive only (per-W G-SITE > 0.01)"
        L.append(f"| {k} | {v['n_cells']} | {f3(v['D_bar'])} | [{f3(v['ci_lo'])}, {f3(v['ci_hi'])}] | "
                 f"{v['share_positive']:.2f} | {locked} | {why} | {ceil} |")
    if explor:
        L += ["", "**Exploratory — families outside the §10.3 scope** (computed by the locked aggregation because both "
              "arms exist in the set; not verdicts, not claims):", "",
              "| set:family | cells | D̄_F | 95 % CI | share D_j > 0 |", "|---|---:|---:|---|---:|"]
        L += [f"| {k} | {v['n_cells']} | {f3(v['D_bar'])} | [{f3(v['ci_lo'])}, {f3(v['ci_hi'])}] | "
              f"{v['share_positive']:.2f} |" for k, v in explor]
    return L


def family_section(fams, checks, gsite):
    L = ["## 1. Family verdicts (§12.3)", "",
         "Primary set. D_j = oriented relative difference per cell (positive = as predicted); D̄_F = mean over the "
         "family's cells; 95 % percentile bootstrap over replicates within cells (B = 2,000, seed 20261008). "
         "SUPPORTED: lower bound > 0 and D_j > 0 in ≥ 75 % of cells; CONTRADICTED: upper bound < 0 or D_j > 0 in "
         "≤ 25 %; INCONCLUSIVE otherwise.", "",
         "| family | comparison | cells | D̄_F | 95 % CI | share D_j > 0 | rule verdict | conditions failed | "
         "reported verdict |", "|---|---|---:|---:|---|---:|---|---|---|"]
    for f in FAMILY_ORDER:
        v = fams.get(f"primary:{f}")
        if v is None:
            L.append(f"| {f} | — | 0 | — | — | — | — | — | not computed (no cells in this output) |")
            continue
        rep = v["verdict"]
        rep = f"{rep}: {WORDING[rep]}" if rep in WORDING else rep
        L.append(f"| {f} | {v['with_arm']} vs {v['without_arm']} | {v['n_cells']} | {f3(v['D_bar'])} | "
                 f"[{f3(v['ci_lo'])}, {f3(v['ci_hi'])}] | {v['share_positive']:.2f} | {v['rule_verdict']} | "
                 f"{', '.join(v['conditions_failed']) or 'none'} | {rep} |")
    L += sensitivity_section(fams, checks, gsite)
    return L


def ceilings_section(s13, fams, gsite_pass):
    L = ["## 2. §13 claim ceilings (applied mechanically)", "",
         "**(a) Fixed at step 5** by the committed §13 record (rules triggered):", ""]
    trig = [r for r in s13["rules"] if r["triggered"] and r["rule"] != "E3site_passes_wording"]
    L += [f"* {r['condition']} — {r['scope']}: {r['consequence']}" for r in trig] or ["* none"]
    wording = [r["scope"] for r in s13["rules"] if r["triggered"] and r["rule"] == "E3site_passes_wording"]
    if wording:
        L.append("* E3-site passes (" + "; ".join(wording) + "): the wording is \"no longer exceeds the prespecified "
                 "linear site-encoding boundary\", never \"equivalent to chance\" or \"eliminated\".")
    cond = s13["family_conditions_primary"]
    p1b, p2 = fams.get("primary:P1b-FM"), fams.get("primary:P2-FM")
    neg = (all(cond.values()) and gsite_pass and p1b is not None and p2 is not None
           and p1b["verdict"] == "INCONCLUSIVE" and p2["verdict"] == "INCONCLUSIVE")
    L += ["", "**(b) Rules deferred to step 7, evaluated now:**", "",
          f"* \"E1 and E3 (both components) pass but P1b-FM and P2-FM are INCONCLUSIVE\": conditions E1 = "
          f"{cond['E1']}, E3-site = {cond['E3-site']}, E3-state = {cond['E3-state']}, G-SITE = {gsite_pass}; "
          f"P1b-FM = {p1b['verdict'] if p1b else 'absent'}, P2-FM = {p2['verdict'] if p2 else 'absent'} → "
          + ("**triggered**: \"encoded site information did not change causal behaviour here\"." if neg
             else "not triggered.")]
    for f in FAMILY_ORDER:
        v = fams.get(f"primary:{f}")
        if v and v["verdict"] in ("SUPPORTED", "CONTRADICTED"):
            L.append(f"* {f}: {v['verdict']} → stated as \"{WORDING[v['verdict']]}\"; not a confirmation of the "
                     f"theory maps.")
    L += ["", "**(c) Standing rules:**", "",
          "* Headline directional claims come only from primary-set family verdicts; single cells are descriptive; "
          "all cells are reported (§12.3). P3 cells and comparisons carry no directional prediction (§12.2).",
          "* A family whose conditions fail is NOT TESTED and reported as P3 / descriptive (§12.2, §5.4).",
          "* §10.3 sets are reported separately and never enter family verdicts (§10.3)."]
    L += [f"* {s}" for s in s13.get("standing_rules", [])]
    L.append("* No causal effect in DS203 is estimated (§1).")
    return L


def checks_section(checks, gsite, reps_report):
    L = ["## 3. Pre-causal checks (§5) and G-SITE (§5.4)", "",
         "Balanced accuracy (BA) of the case-level site probe [95 % bootstrap bounds]; E2 = ΔAUC of base + R_t over "
         "base (elapsed-time spline) [95 % CI]; E3-site upper = one-sided 95 % upper bound after removal "
         "(boundary 0.35); retention = post / pre ΔAUC (≥ 0.50).", "",
         "| representation | E1 278 BA | E1 158 BA | E1 single-file BA | MLP probe 278 (pre-removal) | E2 158 ΔAUC | "
         "E2 158 after removal | E3-site 278 linear / MLP upper | E3-site 158 linear / MLP upper | E3-state |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for k in KEYS:
        c = checks.get(k)
        if not c:
            L.append(f"| {KEY_NAMES[k]} | not in checks.json | | | | | | | | |")
            continue

        def ba(e):
            return "—" if not e else f"{e['ba']:.3f} [{e['lo_2p5']:.3f}, {e['hi_97p5']:.3f}] {yn(e.get('pass'))}"

        def e2(e):
            return "—" if not e else f"{e['delta_auc']:+.3f} [{e['ci_lo']:+.3f}, {e['ci_hi']:+.3f}] {yn(e.get('pass'))}"

        def e3(e):
            return "—" if not e else (f"{e['linear']['upper_one_sided_95']:.3f} / {e['mlp']['upper_one_sided_95']:.3f} "
                                      f"{yn(e['pass'])}{' (MLP > margin)' if e['mlp_exceeds_margin'] else ''}")
        st = c.get("E3_state_primary")
        sts = "—" if not st else ("not applicable" if not st["applicable"] else
                                  f"{st['retained_fraction']:.2f} {yn(st['pass_'])}")
        mlp = c.get("E1_MLP_278")
        mlps = "—" if not mlp else f"{mlp['ba']:.3f}"
        L.append(f"| {KEY_NAMES[k]} | {ba(c.get('E1_278'))} | {ba(c.get('E1_primary'))} | "
                 f"{ba(c.get('E1_single_file'))} | {mlps} | "
                 f"{e2(c.get('E2_primary'))} | {e2(c.get('E2_primary_after_removal'))} | {e3(c.get('E3_site_278'))} | "
                 f"{e3(c.get('E3_site_primary'))} | {sts} |")
    L += ["", "Reporting-only E2 paths (no pass field): ΔAUC on all 278 videos, normalised-time reference, and with "
          "past synthetic actions (reference cell K = 5, P = 0, W = 5, α = 0.5, γ = 1).", "",
          "| representation | E2 278 | E2 278 normalised time | E2 158 normalised time | E2 158 with history |",
          "|---|---|---|---|---|"]
    for k in KEYS:
        c = checks.get(k) or {}

        def d(e):
            return "—" if not e else f"{e['delta_auc']:+.3f} [{e['ci_lo']:+.3f}, {e['ci_hi']:+.3f}]"
        if c:
            L.append(f"| {KEY_NAMES[k]} | {d(c.get('E2_278'))} | {d(c.get('E2_278_normtime'))} | "
                     f"{d(c.get('E2_primary_normtime'))} | {d(c.get('E2_primary_history'))} |")
    sets = gsite.get("sets", {})
    L += ["", "**G-SITE** (η² of S at the window start on C; gate ≤ 0.01; code lock): "
          + ", ".join(f"{s} {sets[s]['eta2_S_window_start']:.4f} ({'pass' if sets[s]['gate_pass'] else 'FAIL'})"
                      for s in ("primary", "W0", "W5") if s in sets) + "."]
    if reps_report:
        L += ["", "**PCA / LEACE** (fold-wise, 64 PCs; step-5 reduction report `reps_report.json`):", "",
              "| representation | folds | training steps (fold 0) | PCA variance retained (mean) | LEACE rank per fold "
              "| dimensions retained | LEACE variance retained (mean) |", "|---|---:|---:|---:|---|---|---:|"]
        for k in KEYS:
            folds = [f for f in (reps_report.get(k) or []) if isinstance(f, dict)]
            if not folds:
                continue

            def mean(key):
                v = [f[key] for f in folds if isinstance(f.get(key), (int, float))]
                return f"{sum(v) / len(v):.3f}" if v else "—"
            L.append(f"| {KEY_NAMES[k]} | {len(folds)} | {folds[0].get('n_train_steps', '—')} | "
                     f"{mean('pca_var_retained')} | {[f.get('leace_rank') for f in folds]} | "
                     f"{[f.get('leace_dim_retained') for f in folds]} | {mean('leace_var_retained')} |")
    return L


def cells_section(cm, code):
    sys.path.insert(0, code)
    from ss_benchmark import grid  # noqa: E402  (locked; read only)
    fam_of = {}
    for f in FAMILY_ORDER:
        for c in grid.family_cells(f):
            fam_of.setdefault(c.index, []).append(f)
    cm = cm.copy()
    cm["families"] = [",".join(fam_of.get(int(c), [])) or "P3" for c in cm.cell]
    L = ["## 4. Relative bias and interval coverage per cell and arm (§11)", "",
         "Relative bias = mean(Ψ̂ − Ψ) / mean Ψ; coverage = share of replicates whose 95 % Wald interval contains Ψ. "
         "All metrics per cell and arm: `report_cells.csv`."]
    for s in ("primary", "single_file", "W0", "W5"):
        sub = cm[cm["set"] == s]
        if sub.empty:
            continue
        arms = [a for a in ARMS if a in set(sub.arm)]
        for metric, title, pct in (("rel_bias", "relative bias", True), ("coverage", "coverage", False)):
            piv = sub.pivot_table(index=["cell", "K", "P", "W", "alpha", "gamma", "phi", "families"], columns="arm",
                                  values=metric, aggfunc="first")[arms].reset_index()
            L += ["", f"**{s}: {title}** ({len(piv)} cells; M per cell {int(sub.M.min())}–{int(sub.M.max())})", "",
                  "| cell | K | P | W | α | γ | φ_A | family | " + " | ".join(arms) + " |",
                  "|" + "---:|" * 7 + "---|" + "---:|" * len(arms)]
            for _, r in piv.iterrows():
                L.append(f"| {int(r.cell)} | {int(r.K)} | {int(r.P)} | {int(r.W)} | {r.alpha:g} | {r.gamma:g} | "
                         f"{r.phi:g} | {r.families} | " + " | ".join(f3(r[a], pct) for a in arms) + " |")
        flags = sub[(sub.small_truth_flag.astype(bool)) | (sub.M_finite < sub.M)]
        L.append(f"\nFlags ({s}): small-truth cells {int(sub[sub.small_truth_flag.astype(bool)].cell.nunique())}; "
                 f"cell–arm pairs with non-finite replicates {int((sub.M_finite < sub.M).sum())}.")
        del flags
    p3 = cm[(cm["set"] == "primary") & (cm.families == "P3")]
    return L, cm, p3


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--step7", required=True)
    ap.add_argument("--step5", required=True)
    ap.add_argument("--gsite", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--code", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument("--placeholder", action="store_true")
    a = ap.parse_args(argv)
    paths = dict(families=os.path.join(a.step7, "families.json"), cells=os.path.join(a.step7, "cell_metrics.csv"),
                 checks=os.path.join(a.step5, "checks.json"), s13=os.path.join(a.step5, "section13.json"),
                 reps=os.path.join(a.step5, "reps_report.json"), gsite=a.gsite)
    fams, checks, s13 = jload(paths["families"]), jload(paths["checks"]), jload(paths["s13"])
    gsite, reps_report = jload(paths["gsite"]), jload(paths["reps"], required=False)
    cm = pd.read_csv(paths["cells"])
    ph = a.placeholder or is_placeholder(checks, s13, gsite, reps_report)
    banner = ["> **PLACEHOLDER — synthetic test output, not results. No DS203 data.**", ""] if ph else []
    L = [("# PLACEHOLDER report (test of make_report.py)" if ph else "# SS DS203 semi-synthetic benchmark: results "
          "report (§14 step 7)"), ""] + banner
    L += ["Inputs (SHA-256):", ""] + [f"* `{p}` `{sha(p)}`" for p in paths.values() if os.path.exists(p)] + [""]
    L += family_section(fams, checks, gsite) + [""]
    L += ceilings_section(s13, fams, bool(gsite.get("gate_pass_primary"))) + [""]
    L += checks_section(checks, gsite, reps_report) + [""]
    cl, cm2, p3 = cells_section(cm, a.code)
    L += [f"**P3 (descriptive):** {p3.cell.nunique()} primary-set cells belong to no family; they carry no directional "
          f"prediction and are reported in the tables below.", ""] + cl
    if ph:
        L += ["", "> **PLACEHOLDER — synthetic test output, not results.**"]
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    open(a.out, "w").write("\n".join(L) + "\n")
    cm2.insert(0, "label", "PLACEHOLDER" if ph else "")
    cm2.to_csv(os.path.join(os.path.dirname(os.path.abspath(a.out)), "report_cells.csv"), index=False)
    print(f"report written: {a.out} ({len(L)} lines){' [PLACEHOLDER]' if ph else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
