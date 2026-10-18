"""Apply protocol §13 mechanically from the committed step-5 record (§14 step 5: "apply §13 before any causal run").

Reads only booleans already computed by the locked checks (`results/step5/checks.json`, written by the locked
`pipeline checks`) and the code-lock G-SITE record; evaluates every §13 rule that can be evaluated before the causal
grid; writes the §13 record. No threshold, statistic or judgement is introduced here: each rule's condition is the
locked pass field that implements the §5 criterion it names.

* E1 (§5.1)            -> checks[key]["E1_278"]["pass"], checks[key]["E1_primary"]["pass"]
* E2 primary (§5.2)    -> checks[key]["E2_primary"]["pass"]
* E3-site (§5.3)       -> checks[key]["E3_site_278"]["pass"], checks[key]["E3_site_primary"]["pass"]
* MLP margin (§5.3)    -> checks[key]["E3_site_<set>"]["mlp_exceeds_margin"]  (post-removal 2-layer MLP probe)
* E3-state (§5.3)      -> checks[key]["E3_state_primary"]["applicable"], ["pass_"]
* P1b-FM / P2-FM conditions (§12.2) -> checks["P"]["fm_conditions_primary"] (locked checks.fm_conditions)
* G-SITE (§5.4)        -> gsite_record.json "gate_pass_primary" (code lock)

Representation keys: P (FM-P, primary standardized), S (FM-S), REF (Cosmos reference) have a site-removed (-C)
version; P-nat (native, sensitivity) has none. The E1 rule names the standardized arms, so it is evaluated for P, S
and REF. Rules that depend on family verdicts (§12.3) are deferred to §14 step 7 and recorded as such.

    python scripts/apply_section13.py --checks results/step5/checks.json \
        --gsite results/codelock_gate/gsite_record.json --out-dir results/step5
Writes section13.json, grid_conditions.json (the locked grid driver's --conditions input) and SECTION13_RECORD.md.
"""
import argparse
import hashlib
import json
import os
import sys

FM_KEYS = ("P", "S", "REF")          # standardized representation arms with a -C version
ALL_KEYS = ("P", "P-nat", "S", "REF")
ARM_NAMES = {"P": "FM-P / FM-P−C", "S": "FM-S / FM-S−C", "REF": "REF / REF−C", "P-nat": "FM-P-nat"}

# §13 text, quoted verbatim from docs/SS_PROTOCOL_DS203.md (4c86dc5); version tags omitted
Q = {
    "E1_fails": ("E1 fails (standardized, 278-case set)",
                 "\"site-like information in representations\" is not established for this dataset. FM-vs-FM−C "
                 "comparisons are reported descriptively only."),
    "E2_fails": ("E2 fails",
                 "\"video representations recover the confounding state\" is not established. FM-vs-NV comparisons "
                 "cannot be read as confounder recovery."),
    "E3site_fails_278": ("E3-site fails on the 278-case set",
                         "the removal manipulation failed; FM−C arms are not interpreted."),
    "pass278_fail158": ("E1 and E3-site pass on the 278-case set but fail on the 158-case set",
                        "FM vs FM−C comparisons in the causal grid are reported descriptively only, and P1b-FM / "
                        "P2-FM are not tested."),
    "mlp_margin": ("E3-site passes but the MLP probe exceeds the margin",
                   "the claim ceiling is \"linear site information removed; nonlinear site information remains\"."),
    "E3site_passes_wording": ("E3-site passes",
                              "the wording is \"no longer exceeds the prespecified linear site-encoding boundary\", "
                              "never \"equivalent to chance\" or \"eliminated\"."),
    "E3state_fails": ("E3-state-retention fails (state destroyed)",
                      "FM−C differences are not attributed to site removal alone, and FM−C causal arms are not "
                      "interpreted."),
    "E3state_na": ("E3-state-retention not applicable (E2 primary fails)",
                   "the report states that retention of state information could not be assessed. FM−C "
                   "interpretation then rests on E3-site alone (§5.3)."),
    "GSITE_fails": ("G-SITE fails",
                    "C is not instrument-like in the constructed design at K = 1, P = 0. P2-SITE and P2-ORACLE become "
                    "P3, and no amplification claim is made."),
}
DEFERRED = {
    "E1E3_pass_FM_inconclusive": "E1 and E3 (both components, §5.3) pass but P1b-FM and P2-FM are INCONCLUSIVE "
                                 "(needs the family verdicts, §12.3)",
    "family_verdict_wording": "Family verdicts: stated as consistent / inconsistent with the theory-motivated "
                              "direction (§12)",
}
STANDING = ("Representation wording (\"video-derived representations\", arm-specific wording of §1)",
            "Native arm differs from standardized: attributed to acquisition shortcuts, not to image content",
            "REF arm: not a fair model comparison, not a pixel-level replication of K4, may retain frame-rate-derived "
            "information",
            "FULL arm: an exchangeability oracle / implementation sanity reference; its finite-sample bias is reported",
            "All claims describe a deliberately constructed orthogonal benchmark (§1, §7.2)")


def sha256(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def b(x):
    if not isinstance(x, bool):
        raise SystemExit(f"STOP: expected a boolean pass field, got {x!r}")
    return x


def evaluate(checks, gsite):
    missing = [k for k in ALL_KEYS if k not in checks]
    if missing:
        raise SystemExit(f"STOP: checks.json lacks representation keys {missing}")
    rules = []

    def add(rule, scope, fields, triggered):
        rules.append(dict(rule=rule, condition=Q[rule][0], consequence=Q[rule][1], scope=scope, fields=fields,
                          triggered=bool(triggered)))

    for k in FM_KEYS:
        c = checks[k]
        e1_278, e1_158 = b(c["E1_278"]["pass"]), b(c["E1_primary"]["pass"])
        e3_278, e3_158 = b(c["E3_site_278"]["pass"]), b(c["E3_site_primary"]["pass"])
        add("E1_fails", ARM_NAMES[k], {f"{k}.E1_278.pass": e1_278}, not e1_278)
        add("E3site_fails_278", ARM_NAMES[k], {f"{k}.E3_site_278.pass": e3_278}, not e3_278)
        add("pass278_fail158", ARM_NAMES[k],
            {f"{k}.E1_278.pass": e1_278, f"{k}.E3_site_278.pass": e3_278, f"{k}.E1_primary.pass": e1_158,
             f"{k}.E3_site_primary.pass": e3_158},
            e1_278 and e3_278 and not (e1_158 and e3_158))
        for s, lab in (("278", "278-case set"), ("primary", "158-case set")):
            e3 = c[f"E3_site_{s}"]
            p, m = b(e3["pass"]), b(e3["mlp_exceeds_margin"])
            add("mlp_margin", f"{ARM_NAMES[k]}, {lab}",
                {f"{k}.E3_site_{s}.pass": p, f"{k}.E3_site_{s}.mlp_exceeds_margin": m}, p and m)
            add("E3site_passes_wording", f"{ARM_NAMES[k]}, {lab}", {f"{k}.E3_site_{s}.pass": p}, p)
        st = c["E3_state_primary"]
        appl = b(st["applicable"])
        passed = None if not appl else b(st["pass_"])
        add("E3state_fails", ARM_NAMES[k], {f"{k}.E3_state_primary.applicable": appl,
                                            f"{k}.E3_state_primary.pass_": passed}, appl and not passed)
        add("E3state_na", ARM_NAMES[k], {f"{k}.E3_state_primary.applicable": appl}, not appl)
    for k in ALL_KEYS:
        e2 = b(checks[k]["E2_primary"]["pass"])
        add("E2_fails", ARM_NAMES[k], {f"{k}.E2_primary.pass": e2}, not e2)
    g = b(gsite["gate_pass_primary"])
    add("GSITE_fails", "design (code lock)", {"gsite.gate_pass_primary": g}, not g)
    fm = checks["P"]["fm_conditions_primary"]
    cond = {"E1": b(fm["E1"]), "E3-site": b(fm["E3-site"]), "E3-state": b(fm["E3-state"])}
    tested = {"P1b-FM": all(cond.values()), "P2-FM": all(cond.values()) and g, "P2-SITE": g, "P2-ORACLE": g,
              "P1a": True, "P1b-SITE": True}
    return rules, cond, tested


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--checks", required=True)
    ap.add_argument("--gsite", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args(argv)
    checks = json.load(open(a.checks))
    gsite = json.load(open(a.gsite))
    rules, cond, tested = evaluate(checks, gsite)
    os.makedirs(a.out_dir, exist_ok=True)
    rec = dict(protocol="docs/SS_PROTOCOL_DS203.md (4c86dc5) §13", generator="scripts/apply_section13.py",
               generator_sha256=sha256(os.path.abspath(__file__)),
               inputs={a.checks: sha256(a.checks), a.gsite: sha256(a.gsite)},
               rules=rules, deferred_to_step7=DEFERRED, standing_rules=list(STANDING),
               family_conditions_primary=cond, families_tested=tested,
               effect_on_step6="none: §13 governs interpretation and claims; the §14 step-6 computation (cells, arms, "
                               "replicates, learners) is fixed by §10 and the code-lock projection record")
    json.dump(rec, open(os.path.join(a.out_dir, "section13.json"), "w"), indent=1, sort_keys=True)
    json.dump({"primary": cond}, open(os.path.join(a.out_dir, "grid_conditions.json"), "w"), indent=1,
              sort_keys=True)
    lines = ["# §13 record (applied mechanically by scripts/apply_section13.py)", "",
             f"* Inputs: `{a.checks}` (SHA-256 `{rec['inputs'][a.checks]}`), `{a.gsite}` "
             f"(SHA-256 `{rec['inputs'][a.gsite]}`).",
             f"* Generator SHA-256: `{rec['generator_sha256']}`.",
             "* Effect on §14 step 6: none (" + rec["effect_on_step6"].split(": ", 1)[1] + ").", "",
             "## Rules evaluated before the causal grid", "",
             "| §13 condition | scope | locked fields | triggered | consequence when triggered |", "|---|---|---|---|---|"]
    for r in rules:
        f = "; ".join(f"`{k}` = {v}" for k, v in r["fields"].items())
        lines.append(f"| {r['condition']} | {r['scope']} | {f} | **{'yes' if r['triggered'] else 'no'}** | "
                     f"{r['consequence']} |")
    lines += ["", "## Family conditions (§12.2) for §14 step 7", "",
              f"* P1b-FM / P2-FM conditions from the locked `fm_conditions_primary` (key P): "
              f"E1 = {cond['E1']}, E3-site = {cond['E3-site']}, E3-state = {cond['E3-state']}; "
              f"G-SITE (code lock) = {not rules[-1]['triggered']}.",
              "* Families tested at step 7: " + ", ".join(f"{k} = {'yes' if v else 'no'}" for k, v in tested.items())
              + ".",
              "* `grid_conditions.json` holds these conditions as the locked grid driver's `--conditions` input.", "",
              "## Deferred to §14 step 7 (need the family verdicts)", ""]
    lines += [f"* {v}" for v in DEFERRED.values()]
    lines += ["", "## Standing rules (no step-5 condition)", ""] + [f"* {s}" for s in STANDING]
    open(os.path.join(a.out_dir, "SECTION13_RECORD.md"), "w").write("\n".join(lines) + "\n")
    print(f"§13 record written: {len(rules)} rule evaluations")
    return 0


if __name__ == "__main__":
    sys.exit(main())
