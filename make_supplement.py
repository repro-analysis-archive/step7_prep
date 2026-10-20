"""Reporting completion (CC_TASK_SS_reporting_completion_v1.md): supplementary figures and tables from committed records.

No number is computed here except for plotting. Every value is read with `git show <commit>:<path>` from a committed
record: the step-4 record (main repository 8d4c61a), the step-5 record (0ebf2cf), the X1/X2 records
(/srv/ss_exploratory 1c8e628) and the B records (/srv/ss_exploratory_B 458341f). CSV tables are verbatim copies of
the record files (or, for table X-E3, the record values as their JSON text). Markdown tables show 3 decimals, the
rounding of the committed reports; the script asserts that every rounded Markdown row equals the corresponding row of
the committed X_REPORT.md / B_REPORT.md. Presentation choices: POST_RESULT_PRESENTATION.md.

Outputs (in --out):
  figS4_mask_profiles.pdf, tableS4_mask_check.{csv,md}      mask-check profiles (protocol §3.1)
  tableX_group_summaries.{csv,md}, tableX_E3.{csv,md}       X1/X2 group summaries; X1 vs step-5 E3 and E2
  figX_cell_delta.pdf                                       per-cell Δ for X1 and X2, all 71 cells, by group
  tableB_ba.{csv,md}, tableB_judgements.csv, tableB_sens.{csv,md}, figB_ba_by_set.pdf
  CAPTIONS.md, SOURCES.md

    python make_supplement.py --fact-base SS_DS203_PROJECT_RECORD_for_evaluator_20261020_v5.md --out DIR
"""
import argparse
import csv
import hashlib
import io
import json
import os
import re
import subprocess

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

plt.rcParams.update({"pdf.fonttype": 42, "ps.fonttype": 42, "font.size": 8, "axes.titlesize": 8,
                     "axes.labelsize": 8, "legend.fontsize": 7, "xtick.labelsize": 7, "ytick.labelsize": 7,
                     "lines.linewidth": 1.0, "lines.markersize": 3})

MAIN = "/home/user/projects/medical_video_causal_gate"
XREPO = "/srv/ss_exploratory"
BREPO = "/srv/ss_exploratory_B"
SRC = {
    "mask_check": (MAIN, "8d4c61a0163e836c5df363166e4b1aee4352c174", "results/step4/mask_check.json"),
    "run_meta": (MAIN, "8d4c61a0163e836c5df363166e4b1aee4352c174", "results/step4/run_meta.json"),
    "checks5": (MAIN, "0ebf2cf632d752cdf5136473a3b6e368c0e5094c", "results/step5/checks.json"),
    "x_groups": (XREPO, "1c8e628ef5d3f0b228a10ba43b0ff17bc0fd96d0", "results_X/x_comparisons_groups.csv"),
    "x_cells": (XREPO, "1c8e628ef5d3f0b228a10ba43b0ff17bc0fd96d0", "results_X/x_comparisons_cells.csv"),
    "x1_e3": (XREPO, "1c8e628ef5d3f0b228a10ba43b0ff17bc0fd96d0", "results_X/x1_e3.json"),
    "x_report": (XREPO, "1c8e628ef5d3f0b228a10ba43b0ff17bc0fd96d0", "results_X/X_REPORT.md"),
    "b_main": (BREPO, "458341f9f873bfebe8ea293552dece64bf0ebdfd", "results_B/b_main.csv"),
    "b_judg": (BREPO, "458341f9f873bfebe8ea293552dece64bf0ebdfd", "results_B/b_judgements.csv"),
    "b_sens": (BREPO, "458341f9f873bfebe8ea293552dece64bf0ebdfd", "results_B/b_sensitivity_summary.csv"),
    "b_report": (BREPO, "458341f9f873bfebe8ea293552dece64bf0ebdfd", "results_B/B_REPORT.md"),
}
KEYS = ("P", "S", "REF")
GROUPS = ("P1b-FM", "P2-FM", "slice")
GROUP_LABEL = {"P1b-FM": "P1b-FM cells", "P2-FM": "P2-FM cells", "slice": "main-figure slice"}
SETS = ("S1", "S2", "S3")


def show(name):
    repo, commit, path = SRC[name]
    return subprocess.run(["git", "-C", repo, "show", f"{commit}:{path}"], capture_output=True, check=True,
                          env={"GIT_OPTIONAL_LOCKS": "0", "PATH": "/usr/bin:/bin"}).stdout


def sha(b):
    return hashlib.sha256(b).hexdigest()


def f3(x):
    return f"{float(x):.3f}"


def jt(x):
    return json.dumps(x)


def md_table(header, rows):
    return ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)] + ["| " + " | ".join(map(str, r)) + " |"
                                                                             for r in rows]


def write(out, name, text):
    with open(os.path.join(out, name), "w") as fh:
        fh.write(text if text.endswith("\n") else text + "\n")


def report_rows(md_bytes, header_start):
    lines = md_bytes.decode().split("\n")
    i = next(k for k, l in enumerate(lines) if l.startswith(header_start))
    rows = []
    for l in lines[i + 2:]:
        if not l.startswith("|"):
            break
        rows.append(l)
    return rows


def fact_base_paragraph(text, start, end):
    """The paragraph of the fact base from the line starting with `start` up to (excluding) the line starting with
    `end`, joined into one line (the file is hard-wrapped)."""
    lines = text.split("\n")
    i = next(k for k, l in enumerate(lines) if l.startswith(start))
    j = next(k for k in range(i + 1, len(lines)) if lines[k].startswith(end) or not lines[k].strip())
    return " ".join(l.strip() for l in lines[i:j])


# ------------------------------------------------------------------------------------------------ mask check --
def mask(out, raw):
    mc = json.loads(raw["mask_check"])
    meta = json.loads(raw["run_meta"])
    cent = sorted(mc["profiles"])
    rows = [[f"centre {c}", "n_frames", jt(mc["profiles"][c]["n_frames"])] for c in cent]
    rows += [[f"centre {c}", "rho_c (visible_radius)", jt(mc["visible_radius"][c])] for c in cent]
    rows += [["all centres", "min_c rho_c (min_visible_radius)", jt(mc["min_visible_radius"])],
             ["all centres", "r (final mask radius, x side)", jt(mc["r"])],
             ["all centres", "mask_check_valid (run_meta.json)", jt(meta["mask_check_valid"])],
             ["all centres", "fallback r = 0.98 x min_c rho_c", "not used (recorded r = 0.45; min_c rho_c >= 0.45)"]]
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["scope", "item", "value"])
    w.writerows(rows)
    write(out, "tableS4_mask_check.csv", buf.getvalue())
    md = ["**Table S4. Mask check (protocol §3.1 step 3; step-4 record `8d4c61a`, `results/step4/mask_check.json` and "
          "`run_meta.json`)**", ""]
    md += md_table(["centre", "frames in the mean frame", "visible radius ρ_c (× side)", "profile points"],
                   [[c, mc["profiles"][c]["n_frames"], jt(mc["visible_radius"][c]), len(mc["profiles"][c]["rho"])]
                    for c in cent])
    md += ["", f"* min_c ρ_c = {jt(mc['min_visible_radius'])}; final r = {jt(mc['r'])} (× side).",
           "* Rule (§3.1): r = 0.45 if min_c ρ_c ≥ 0.45, otherwise r = 0.98 × min_c ρ_c. Recorded: r = 0.45; the "
           "fallback r = 0.98 × min_c ρ_c was not used.",
           f"* Validity: `run_meta.json` `mask_check_valid` = {jt(meta['mask_check_valid'])}; runner log (LaCie "
           "`ss_step4_5/logs/progress.log` line 234): \"mask check valid (r = 0.45 stands)\".",
           "* For centres 3–5, ρ_c equals the last profile point (0.703125)."]
    write(out, "tableS4_mask_check.md", "\n".join(md))
    fig, axes = plt.subplots(2, 2, figsize=(7.0, 5.0), sharex=True)
    for ax, c in zip(axes.ravel(), cent):
        p = mc["profiles"][c]
        ax.plot(p["rho"], p["m"], color="C0", label="radial profile m_c(ρ)")
        ax.axvline(mc["visible_radius"][c], color="C1", linestyle="-",
                   label=f"visible radius ρ_c = {jt(mc['visible_radius'][c])}")
        ax.axvline(mc["r"], color="k", linestyle="--", label=f"mask radius r = {jt(mc['r'])}")
        ax.set_title(f"Centre {c} ({p['n_frames']} frames)")
        ax.set_xlim(0, 0.72)
        ax.legend(loc="lower left", frameon=False)
    for ax in axes[1]:
        ax.set_xlabel("radius ρ (fraction of the square side)")
    for ax in axes[:, 0]:
        ax.set_ylabel("mean grayscale of the 1-px annulus")
    fig.suptitle("Supplementary Figure S4. Mask check: per-centre radial profiles of the mean standardized frame "
                 "(step-4 record 8d4c61a)", fontsize=8)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(os.path.join(out, "figS4_mask_profiles.pdf"))
    plt.close(fig)


# ------------------------------------------------------------------------------------------------------ X1/X2 --
def x_tables(out, raw):
    write(out, "tableX_group_summaries.csv", raw["x_groups"].decode())
    g = pd.read_csv(io.BytesIO(raw["x_groups"]), dtype=str)
    assert len(g) == 54
    hdr = ["analysis", "arm", "comparator", "group", "cells", "mean Δ", "95 % interval", "cells with Δ < 0"]
    rows = [[r.analysis, r.arm, r.comparator, r.group, r.n_cells, f3(r.mean_delta),
             f"[{f3(r.mean_delta_lo)}, {f3(r.mean_delta_hi)}]", r.n_cells_delta_negative] for r in g.itertuples()]
    md_rows = md_table(hdr, rows)[2:]
    rep = report_rows(raw["x_report"], "| analysis | arm | comparator | group |")
    assert md_rows == rep, "table X differs from the committed X_REPORT.md group table"
    md = ["**Table X. Exploratory X1/X2: group summaries of Δ = (|bias_X| − |bias_step-6|) / mean truth** "
          "(`results_X/x_comparisons_groups.csv`, `/srv/ss_exploratory` `1c8e628`; all 2 analyses × 3 arms × 3 "
          "comparators × 3 groups)", ""] + md_table(hdr, rows)
    md += ["", "* Negative Δ: the X arm has the smaller |bias|. Δ is (X arm − step-6 arm), not oriented by family "
               "prediction. Mean Δ is the unweighted mean over the group's cells; 95 % paired bootstrap percentile "
               "interval (B = 2,000; cells fixed).",
           "* Rows identical, at 3 decimals, to the group table of the committed `X_REPORT.md`; full precision and "
           "seed names in the CSV."]
    write(out, "tableX_group_summaries.md", "\n".join(md))

    e3 = json.loads(raw["x1_e3"])
    s5 = json.loads(raw["checks5"])
    long_rows = []
    site_rows, e2_rows = [], []
    for k in KEYS:
        for pr in ("linear", "mlp"):
            a, b = s5[k]["E3_site_primary"][pr], e3[k]["E3_site_primary_X1"][pr]
            for lab, src, d in (("step 5 (protocol LEACE)", "checks.json E3_site_primary", a),
                                ("X1 (LEACE refitted on the analysis region)", "x1_e3.json E3_site_primary_X1", b)):
                for f in ("n_cases", "ba", "lo_2p5", "hi_97p5", "upper_one_sided_95"):
                    long_rows.append(["E3-site (158-case analysis region)", k, pr, lab, src, f, jt(d[f])])
            site_rows.append([k, pr, f3(a["ba"]), f"[{f3(a['lo_2p5'])}, {f3(a['hi_97p5'])}]",
                              f3(a["upper_one_sided_95"]), f3(b["ba"]), f"[{f3(b['lo_2p5'])}, {f3(b['hi_97p5'])}]",
                              f3(b["upper_one_sided_95"])])
        conds = (("step 5, before removal", "checks.json E2_primary", s5[k]["E2_primary"]),
                 ("step 5, after protocol removal", "checks.json E2_primary_after_removal",
                  s5[k]["E2_primary_after_removal"]),
                 ("X1, after X1 removal", "x1_e3.json E2_primary_after_removal_X1",
                  e3[k]["E2_primary_after_removal_X1"]))
        for lab, src, d in conds:
            for f in ("auc_base", "auc_full", "delta_auc", "ci_lo", "ci_hi", "pass"):
                long_rows.append(["E2 primary (158-case analysis region)", k, "", lab, src, f, jt(d[f])])
            e2_rows.append([k, lab, f3(d["delta_auc"]), f"[{f3(d['ci_lo'])}, {f3(d['ci_hi'])}]",
                            "met" if d["pass"] else "not met"])
        for lab, src, d in (("step 5", "checks.json E3_state_primary", s5[k]["E3_state_primary"]),
                            ("X1", "x1_e3.json E3_state_primary_X1", e3[k]["E3_state_primary_X1"])):
            for f, v in d.items():
                long_rows.append(["E3-state retention (158-case)", k, "", lab, src, f, jt(v)])
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["block", "key", "probe", "condition", "source", "field", "value"])
    w.writerows(long_rows)
    write(out, "tableX_E3.csv", buf.getvalue())
    # consistency with the committed X_REPORT.md E3 table (linear / MLP BA and upper, step-5 linear upper)
    rep = {l.split("|")[1].strip(): [c.strip() for c in l.split("|")[1:-1]]
           for l in report_rows(raw["x_report"], "| key | linear BA |")}
    for k in KEYS:
        x = e3[k]["E3_site_primary_X1"]
        assert rep[k][1:5] == [f3(x["linear"]["ba"]), f3(x["linear"]["upper_one_sided_95"]), f3(x["mlp"]["ba"]),
                               f3(x["mlp"]["upper_one_sided_95"])]
        assert rep[k][6] == f3(s5[k]["E3_site_primary"]["linear"]["upper_one_sided_95"])

    def state(d):
        if not d.get("applicable", True):
            return "not applicable (E2 primary failed)"
        return f"retained fraction {f3(d['retained_fraction'])}"
    md = ["**Table X-E3. Exploratory X1: E3-site, E2 and E3-state retention on the 158-case analysis region, next to "
          "step 5** (X1: `results_X/x1_e3.json`, `1c8e628`; step 5: `results/step5/checks.json`, `0ebf2cf`)", "",
          "*E3-site: case-level site balanced accuracy after removal [95 % interval]; one-sided 95 % upper bound "
          "(boundary 0.35).*", ""]
    md += md_table(["key", "probe", "step-5 BA", "step-5 95 % interval", "step-5 upper", "X1 BA", "X1 95 % interval",
                    "X1 upper"], site_rows)
    md += ["", "*E2 primary: ΔAUC for S_t of base + R_t over base [95 % CI]; criterion ΔAUC ≥ 0.05 and CI "
               "excluding 0.*", ""]
    md += md_table(["key", "condition", "ΔAUC", "95 % CI", "E2 criterion"], e2_rows)
    md += ["", "*E3-state retention (post / pre ΔAUC ≥ 0.50):*", ""]
    md += md_table(["key", "step 5", "X1"], [[k, state(s5[k]["E3_state_primary"]), state(e3[k]["E3_state_primary_X1"])]
                                             for k in KEYS])
    md += ["", "* The X1 eraser is fitted on training folds and evaluated on held-out folds of the same population "
               "(the 158-case analysis region); its linear E3-site value is a check of the procedure and does not "
               "gate X1 (X_REPORT.md).",
           "* All values as recorded; the CSV gives every field as its JSON text."]
    write(out, "tableX_E3.md", "\n".join(md))


def x_figure(out, raw):
    c = pd.read_csv(io.BytesIO(raw["x_cells"]))
    assert len(c) == 1278
    with PdfPages(os.path.join(out, "figX_cell_delta.pdf")) as pdf:
        for an in ("X1", "X2"):
            for comp, comp_lab in (("minusC", "step-6 k−C (same arm, original features)"),
                                   ("FM", "step-6 FM-k (site retained)"), ("NV", "step-6 NV")):
                fig, axes = plt.subplots(3, 1, figsize=(7.0, 9.0))
                for ax, arm in zip(axes, ("FM-P-C", "FM-S-C", "REF-C")):
                    sub = c[(c.analysis == an) & (c.arm == arm) & (c.comparison == comp)]
                    assert len(sub) == 71
                    pos, ticks, labels, start = 0, [], [], []
                    for gi, g in enumerate(GROUPS):
                        cells = sub[sub.groups.str.split(",").apply(lambda s: g in s)].sort_values("cell")
                        x = np.arange(pos, pos + len(cells))
                        ax.vlines(x, cells.delta_lo, cells.delta_hi, color=f"C{gi}", linewidth=0.7)
                        ax.plot(x, cells.delta, "o", color=f"C{gi}", markersize=2.5,
                                label=f"{GROUP_LABEL[g]} ({len(cells)})")
                        ticks += list(x)
                        labels += [str(int(v)) for v in cells.cell]
                        start.append((pos, pos + len(cells) - 1))
                        pos += len(cells) + 2
                    for a_, b_ in start[1:]:
                        ax.axvline(a_ - 1.5, color="0.7", linewidth=0.5)
                    ax.axhline(0, color="k", linewidth=0.6)
                    ax.set_xticks(ticks)
                    ax.set_xticklabels(labels, rotation=90, fontsize=4.5)
                    ax.set_xlim(-1, pos - 1)
                    ax.set_ylabel("Δ")
                    ax.set_title(f"{an} {arm} vs {sub.comparator.iloc[0]}")
                axes[-1].set_xlabel("cell index (grouped; cell 15 belongs to both the P2-FM group and the slice)")
                h, lab = axes[0].get_legend_handles_labels()
                fig.legend(h, lab, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 0.0))
                fig.suptitle(f"Supplementary Figure X ({an} vs {comp_lab}). EXPLORATORY (outside the frozen protocol). "
                             "Per-cell Δ = (|bias_X| − |bias_step-6|) / mean truth with 95 % paired bootstrap "
                             "intervals (B = 2,000); negative = X arm smaller |bias|. All 71 cells.", fontsize=7,
                             wrap=True)
                fig.tight_layout(rect=(0, 0.025, 1, 0.95))
                pdf.savefig(fig)
                plt.close(fig)


# ---------------------------------------------------------------------------------------------------------- B --
def b_tables(out, raw):
    write(out, "tableB_ba.csv", raw["b_main"].decode())
    write(out, "tableB_judgements.csv", raw["b_judg"].decode())
    write(out, "tableB_sens.csv", raw["b_sens"].decode())
    m = pd.read_csv(io.BytesIO(raw["b_main"]), dtype=str)
    j = pd.read_csv(io.BytesIO(raw["b_judg"]), dtype=str)
    s = pd.read_csv(io.BytesIO(raw["b_sens"]), dtype=str)
    assert len(m) == 36 and len(j) == 36 and len(s) == 36
    hdr = ["key", "analysis", "probe", "set", "cases", "rows", "BA", "95 % interval", "one-sided 95 % upper",
           "exceeds 0.35"]
    rows = [[r["key"], f"({r['analysis']})", r["probe"], r["set"], r["cases"], r["rows"], f3(r["ba"]),
             f"[{f3(r['lo_2p5'])}, {f3(r['hi_97p5'])}]", f3(r["upper_one_sided_95"]),
             {"True": "yes", "False": "no"}[r["exceeds_boundary_0.35"]]] for _, r in m.iterrows()]
    assert md_table(hdr, rows)[2:] == report_rows(raw["b_report"], "| key | analysis | probe | set | cases |"), \
        "table B differs from the committed B_REPORT.md"
    md = ["**Table B. Exploratory B: case-level site balanced accuracy per key × analysis × probe × set** "
          "(`results_B/b_main.csv`, `/srv/ss_exploratory_B` `458341f`)", "",
          "(a) transport: the S1 probe (fitted as in E3) evaluated on each set; (b) within-set refit. Reported "
          "separately; never pooled or contrasted. S1 = 278 cases, all steps; S2 = 158 cases, all steps; S3 = 158 "
          "cases, analysis region (75 steps per case).", ""] + md_table(hdr, rows)
    md += ["", "**Judgement statements as generated** (`results_B/b_judgements.csv`; judgement = whether the one-sided "
               "95 % upper bound exceeds 0.35)", ""]
    md += md_table(list(j.columns), j.values.tolist())
    md += ["", "* Rows of the first table identical, at 3 decimals, to the committed `B_REPORT.md`; the judgement "
               "statements are copied unchanged."]
    write(out, "tableB_ba.md", "\n".join(md))
    hdr = ["key", "analysis", "probe", "set", "draws", "median BA", "2.5–97.5 % across draws", "min–max"]
    rows = [[r.key, f"({r.analysis})", r.probe, r.set, r.draws, f3(r.median), f"{f3(r.p2_5)}–{f3(r.p97_5)}",
             f"{f3(r.min)}–{f3(r.max)}"] for r in s.itertuples()]
    assert md_table(hdr, rows)[2:] == report_rows(raw["b_report"], "| key | analysis | probe | set | draws |"), \
        "table B-sens differs from the committed B_REPORT.md"
    md = ["**Table B-sens. Exploratory B: equal-size subsampling** (`results_B/b_sensitivity_summary.csv`, "
          "`458341f`). 28 cases per centre and 75 steps per case in S1–S3; 20 draws; descriptive point estimates, no "
          "bootstrap, no judgement.", ""] + md_table(hdr, rows)
    md += ["", "* Rows identical, at 3 decimals, to the committed `B_REPORT.md` (same row order as the record)."]
    write(out, "tableB_sens.md", "\n".join(md))


def b_figure(out, raw):
    m = pd.read_csv(io.BytesIO(raw["b_main"]))
    fig, axes = plt.subplots(3, 2, figsize=(7.0, 8.5), sharey=True)
    x0 = np.arange(len(SETS))
    for i, k in enumerate(KEYS):
        for jx, (an, an_lab) in enumerate((("a", "(a) transport: S1-fitted probe"), ("b", "(b) within-set refit"))):
            ax = axes[i, jx]
            for pi, (pr, mk, off) in enumerate((("linear", "o", -0.08), ("mlp", "s", 0.08))):
                sub = m[(m.key == k) & (m.analysis == an) & (m.probe == pr)].set_index("set").loc[list(SETS)]
                x = x0 + off
                ax.vlines(x, sub.lo_2p5, sub.hi_97p5, color=f"C{pi}", linewidth=0.8)
                ax.plot(x, sub.ba, mk, color=f"C{pi}", label=f"{pr}: BA [95 % interval]")
                ax.plot(x, sub.upper_one_sided_95, "_", color=f"C{pi}", markersize=9, markeredgewidth=1.2,
                        label=f"{pr}: one-sided 95 % upper bound")
            ax.axhline(0.35, color="k", linestyle="--", linewidth=0.8, label="boundary 0.35 (upper bound)")
            ax.axhline(0.25, color="0.5", linestyle=":", linewidth=0.8, label="chance 0.25")
            ax.set_xticks(x0)
            ax.set_xticklabels(["S1\n278 cases\nall steps", "S2\n158 cases\nall steps", "S3\n158 cases\nanalysis region"])
            ax.set_xlim(-0.5, 2.5)
            ax.set_ylim(0.1, 1.02)
            ax.set_title(f"{k} — {an_lab}")
            if jx == 0:
                ax.set_ylabel("case-level site BA")
    h, lab = axes[0, 0].get_legend_handles_labels()
    fig.legend(h, lab, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 0.0))
    fig.suptitle("Supplementary Figure B. EXPLORATORY (outside the frozen protocol).\nSite balanced accuracy by "
                 "evaluation set; (a) and (b) in separate panels, never pooled.", fontsize=7)
    fig.tight_layout(rect=(0, 0.06, 1, 0.95))
    fig.savefig(os.path.join(out, "figB_ba_by_set.pdf"))
    plt.close(fig)


# ---------------------------------------------------------------------------------------------------- captions --
def captions(out, fact_text, fact_sha):
    x_ceiling = fact_base_paragraph(fact_text, "- **Ceiling:** exploratory;", "## ")
    b_ceiling = fact_base_paragraph(fact_text, "- **Ceiling:** B locates", "## ")
    x_delta = fact_base_paragraph(fact_text, "- **Δ definition (confirmed):**", "- **X1 erasure")
    mask_dev = fact_base_paragraph(fact_text, "- **Mask check (confirmed, 8d4c61a):**", "- dts QC")
    cap = ["# Captions (supplementary figures and tables, 2026-10-20)", "",
           f"Ceilings and definitions are quoted verbatim from the fact base `SS_DS203_PROJECT_RECORD_for_evaluator_"
           f"20261020_v5.md` (SHA-256 `{fact_sha}`), §5, §8 and §9. Every number is from the committed records "
           "listed in `SOURCES.md`.", "",
           "## Supplementary Figure S4 and Table S4. Mask check (protocol §3.1)", "",
           "Per-centre radial profiles m_c(ρ) of the grayscale mean standardized frame (protocol §3.1: 256 × 256, every "
           "60th grid frame of every case), 180 points per centre, from the step-4 record (`8d4c61a`, `mask_check.json`). "
           "Orange: the visible radius ρ_c; dashed black: the mask radius r = 0.45. min_c ρ_c = 0.5625 ≥ 0.45, so "
           "r = 0.45 stands and the fallback r = 0.98 × min_c ρ_c was not used. Reported here to close the "
           "deviation recorded in the fact base:", "", f"> {mask_dev}", "",
           "## Table X. Exploratory X1/X2: group summaries", "",
           "EXPLORATORY (outside the frozen protocol; plan `b6d1cf7`, OSF https://osf.io/5c627). All 2 analyses × 3 "
           "arms × 3 comparators × 3 groups (54 rows).", "", f"> {x_delta}", "", f"> {x_ceiling}", "",
           "## Table X-E3. Exploratory X1: E3-site, E2 and E3-state retention next to step 5", "",
           "EXPLORATORY. X1 refits the LEACE eraser on the 158-case analysis region (training folds) and evaluates on "
           "held-out folds of the same population; step-5 values are the protocol LEACE (fitted on the 278-case "
           "set). Keys P, S, REF; probes linear and MLP.", "", f"> {x_ceiling}", "",
           "## Supplementary Figure X. Exploratory X1/X2: per-cell Δ", "",
           "EXPLORATORY. One page per analysis (X1, X2) × comparator (step-6 k−C, step-6 FM-k, step-6 NV); one "
           "panel per arm (FM-P−C, FM-S−C, REF−C); all 71 cells, grouped as P1b-FM (48), P2-FM (12) and the "
           "main-figure slice (12); cell 15 belongs to both P2-FM and the slice and is shown in both. Points: Δ; "
           "bars: 95 % paired bootstrap percentile intervals (B = 2,000). y-axes differ between panels.", "",
           f"> {x_delta}", "", f"> {x_ceiling}", "",
           "## Table B and Supplementary Figure B. Exploratory B: balanced accuracy by evaluation set", "",
           "EXPLORATORY (outside the frozen protocol; plan `e1c27b4`, OSF https://osf.io/g9ymw). All 3 keys × 2 "
           "analyses × 2 probes × 3 sets (36 cells) with the generated judgement statements. In the figure, "
           "(a) transport and (b) within-set refit are separate panels (never pooled); points: BA with 95 % "
           "interval; horizontal ticks: one-sided 95 % upper bound; dashed line: the 0.35 boundary, which applies "
           "to the upper bound; dotted line: chance 0.25.", "", f"> {b_ceiling}", "",
           "## Table B-sens. Exploratory B: equal-size subsampling", "",
           "EXPLORATORY. 28 cases per centre, 75 steps per case, 20 draws; median, 2.5–97.5 % across draws and "
           "range of the point BA; descriptive point estimates, no bootstrap, no judgement.", "",
           f"> {b_ceiling}"]
    write(out, "CAPTIONS.md", "\n".join(cap))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fact-base", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    raw = {k: show(k) for k in SRC}
    # the step-5 checks.json is unchanged between the step-5 record and the step-7 record commit
    main_7 = subprocess.run(["git", "-C", MAIN, "show", "2880d73:results/step5/checks.json"], capture_output=True,
                            check=True, env={"GIT_OPTIONAL_LOCKS": "0", "PATH": "/usr/bin:/bin"}).stdout
    assert main_7 == raw["checks5"]
    fact = open(a.fact_base, "rb").read()
    mask(a.out, raw)
    x_tables(a.out, raw)
    x_figure(a.out, raw)
    b_tables(a.out, raw)
    b_figure(a.out, raw)
    captions(a.out, fact.decode(), sha(fact))
    src = ["# Sources (read with `git show <commit>:<path>`; nothing modified)", ""]
    src += md_table(["name", "repository", "commit", "path", "SHA-256 of the blob"],
                    [[k, r, c[:7], p, sha(raw[k])] for k, (r, c, p) in SRC.items()])
    src += ["", f"Fact base for captions: `{os.path.basename(a.fact_base)}`, SHA-256 `{sha(fact)}`, provided by the "
                "investigator; committed copy `evidence/SS_DS203_PROJECT_RECORD_for_evaluator_20261020_v5.md` "
                "(step7_prep `84d8e2d`).", "",
            "Table S4 also quotes the step 4–5 runner-log line \"mask check valid (r = 0.45 stands)\" (LaCie "
            "`ss_step4_5/logs/progress.log` line 234, not in a repository); it is preserved unchanged in "
            "`evidence/step4_5_progress_log_lines_43_57-63_234.txt` (step7_prep `84d8e2d`; commands and SHA-256 in "
            "`evidence/README.md`)."]
    write(a.out, "SOURCES.md", "\n".join(src))
    print("written:", ", ".join(sorted(os.listdir(a.out))))


if __name__ == "__main__":
    main()
