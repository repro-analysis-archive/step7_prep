"""Figures (vector PDF) and Tables 1-3 (CSV + Markdown) for the manuscript, from the step-5 / step-7 records.

Inputs (read only): <step7>/cell_metrics.csv, <step7>/families.json, <step5>/checks.json, <step5>/reps_report.json
(optional). Plain, journal-neutral styling (matplotlib defaults, TrueType fonts embedded). If any input is PLACEHOLDER
(or --placeholder), every figure carries a PLACEHOLDER watermark and every table a PLACEHOLDER row.

Figures (presentation decisions: PRESENTATION_DECISIONS.md; main-text slice W = 30, alpha = 0.5, gamma = 1, phi_A = 0,
primary set):
  fig1_bias_coverage_vs_K.pdf   relative bias and coverage against K, by arm, one column per P in {0, 5, 30}
  fig2_role_switch.pdf          Delta|bias| / mean truth (|bias| without C - |bias| with C) against K, one line per P,
                                one panel per with/without-C pair (positive = including C reduces |bias|)
  fig3_contrast_KP.pdf          the same contrast as K x P heatmaps at the slice, one panel per pair
  fig4_checks.pdf               E1 balanced accuracy (278 / 158), E3-site upper bounds after removal (linear / MLP),
                                E2 delta-AUC before / after removal, PCA / LEACE variance retained per fold
Supplementary (every cell of the primary grid, no averaging; rows alpha x gamma, columns W, panels K x P; phi_A = 0.5 on
its own page):
  figS1_contrast_all_cells.pdf  Delta|bias| / mean truth, one page pair per with/without-C pair
  figS2_rel_bias_all_cells.pdf  relative bias, one page pair per arm
  figS3_coverage_all_cells.pdf  95 % interval coverage, one page pair per arm
Tables: table1_data_sets, table2_models, table3_family_verdicts (.csv and .md).

    python make_figures.py --step7 DIR --step5 DIR --out DIR [--W 30 --alpha 0.5 --gamma 1] [--placeholder]
"""
import argparse
import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

plt.rcParams.update({"pdf.fonttype": 42, "ps.fonttype": 42, "font.size": 8, "axes.titlesize": 8,
                     "axes.labelsize": 8, "legend.fontsize": 7, "xtick.labelsize": 7, "ytick.labelsize": 7,
                     "lines.linewidth": 1.0, "lines.markersize": 3})
PAIRS = (("SITE", "NV"), ("FM-P", "FM-P-C"), ("FM-S", "FM-S-C"), ("REF", "REF-C"), ("ORACLE", "ORACLE-C"))
SINGLES = ("FM-P-nat", "FULL")
ARMS = ("NV", "SITE", "FM-P", "FM-P-C", "FM-S", "FM-S-C", "REF", "REF-C", "FM-P-nat", "ORACLE-C", "ORACLE", "FULL")
GRID = dict(K=(1, 2, 5, 15), P=(0, 5, 30), W=(0, 5, 30), alpha=(0.0, 0.5, 1.0), gamma=(0.5, 1.0))
PHI_GRID = dict(K=(1, 5), P=(0, 5), W=(5,))
KEYS = ("P", "S", "REF", "P-nat")
KEY_LABEL = {"P": "FM-P", "S": "FM-S", "REF": "REF", "P-nat": "FM-P-nat"}
FAMILY_ORDER = ("P1a", "P1b-SITE", "P1b-FM", "P2-SITE", "P2-FM", "P2-ORACLE")


def style_of(arm):
    """Colour shared by a with-C / without-C pair; solid = site-retained (with C), dashed = site-removed / no C."""
    colours = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    for i, (w, wo) in enumerate(PAIRS):
        if arm in (w, wo):
            return dict(color=colours[i], linestyle="-" if arm == w else "--", marker="o" if arm == w else "s")
    i = len(PAIRS) + SINGLES.index(arm)
    return dict(color=colours[i % len(colours)], linestyle=":", marker="^")


def watermark(fig, on):
    if on:
        fig.text(0.5, 0.5, "PLACEHOLDER", fontsize=40, color="0.85", ha="center", va="center", rotation=30,
                 zorder=0, alpha=0.6)
        fig.suptitle("PLACEHOLDER — synthetic test output, not results", fontsize=8, color="0.3")


def contrast(cm, w, wo):
    a = cm[cm.arm == w].set_index("cell")
    b = cm[cm.arm == wo].set_index("cell")
    j = a.index.intersection(b.index)
    out = a.loc[j, ["K", "P", "W", "alpha", "gamma", "phi"]].copy()
    out["D"] = (b.loc[j, "abs_bias"] - a.loc[j, "abs_bias"]) / a.loc[j, "mean_truth"]
    return out


def fig1(cm, sl, out, ph):
    sub = cm[(cm.W == sl["W"]) & (cm.alpha == sl["alpha"]) & (cm.gamma == sl["gamma"]) & (cm.phi == 0)]
    fig, ax = plt.subplots(2, 3, figsize=(7.0, 4.2), sharex=True, sharey="row")
    for j, P in enumerate((0, 5, 30)):
        s = sub[sub.P == P]
        for arm in [a for p in PAIRS for a in p] + list(SINGLES):
            r = s[s.arm == arm].sort_values("K")
            if r.empty:
                continue
            st = style_of(arm)
            ax[0, j].plot(r.K, 100 * r.rel_bias, label=arm, **st)
            ax[1, j].plot(r.K, r.coverage, **st)
        ax[0, j].set_title(f"P = {P}")
        ax[0, j].axhline(0, color="0.5", lw=0.5)
        ax[1, j].axhline(0.95, color="0.5", lw=0.5)
        ax[1, j].set_xlabel("intervention duration K (steps)")
        ax[1, j].set_xscale("log")
        ax[1, j].set_xticks([1, 2, 5, 15])
        ax[1, j].set_xticklabels(["1", "2", "5", "15"])
    ax[0, 0].set_ylabel("relative bias (%)")
    ax[1, 0].set_ylabel("95 % interval coverage")
    h, lab = ax[0, 0].get_legend_handles_labels()
    for j in (1, 2):
        for hh, ll in zip(*ax[0, j].get_legend_handles_labels()):
            if ll not in lab:
                h.append(hh)
                lab.append(ll)
    fig.legend(h, lab, loc="center right", frameon=False)
    fig.text(0.01, 0.01, f"slice: W = {sl['W']}, α = {sl['alpha']:g}, γ = {sl['gamma']:g}, φ_A = 0", fontsize=6)
    fig.tight_layout(rect=(0, 0.02, 0.85, 0.96))
    watermark(fig, ph)
    fig.savefig(os.path.join(out, "fig1_bias_coverage_vs_K.pdf"))
    plt.close(fig)


def fig2(cm, sl, out, ph):
    sub = cm[(cm.W == sl["W"]) & (cm.alpha == sl["alpha"]) & (cm.gamma == sl["gamma"]) & (cm.phi == 0)]
    fig, ax = plt.subplots(1, len(PAIRS), figsize=(7.0, 2.5), sharey=True)
    for i, (w, wo) in enumerate(PAIRS):
        d = contrast(sub, w, wo)
        for P, mk in zip((0, 5, 30), ("o", "s", "^")):
            r = d[d.P == P].sort_values("K")
            if not r.empty:
                ax[i].plot(r.K, r.D, marker=mk, label=f"P = {P}", color="0.2", linestyle=("-", "--", ":")[(0, 5, 30).index(P)])
        ax[i].axhline(0, color="0.5", lw=0.5)
        ax[i].set_title(f"{w} vs {wo}")
        ax[i].set_xscale("log")
        ax[i].set_xticks([1, 2, 5, 15])
        ax[i].set_xticklabels(["1", "2", "5", "15"])
        ax[i].set_xlabel("K")
    ax[0].set_ylabel("Δ|bias| / mean truth")
    ax[-1].legend(frameon=False)
    fig.text(0.01, 0.01, f"Δ|bias| = |bias| without C − |bias| with C; positive: including C reduces |bias|. slice: W = {sl['W']}, α = {sl['alpha']:g}, "
                         f"γ = {sl['gamma']:g}, φ_A = 0", fontsize=6)
    fig.tight_layout(rect=(0.01, 0.05, 1, 0.92))
    watermark(fig, ph)
    fig.savefig(os.path.join(out, "fig2_role_switch.pdf"))
    plt.close(fig)


def fig3(cm, sl, out, ph):
    """Main text: Delta|bias| / mean truth as K x P heatmaps at the slice, one panel per with/without-C pair."""
    sub = cm[(cm.W == sl["W"]) & (cm.alpha == sl["alpha"]) & (cm.gamma == sl["gamma"]) & (cm.phi == 0)]
    Ks, Ps = GRID["K"], GRID["P"]
    mats = []
    for w, wo in PAIRS:
        m = np.full((len(Ks), len(Ps)), np.nan)
        for _, r in contrast(sub, w, wo).iterrows():
            m[Ks.index(int(r.K)), Ps.index(int(r.P))] = r.D
        mats.append(m)
    vmax = max([np.nanmax(np.abs(m)) for m in mats if np.isfinite(m).any()] or [1.0]) or 1.0
    fig, ax = plt.subplots(1, len(PAIRS), figsize=(7.4, 2.9))
    fig.subplots_adjust(left=0.07, right=0.86, top=0.74, bottom=0.2, wspace=0.35)
    for i, ((w, wo), m) in enumerate(zip(PAIRS, mats)):
        im = heat(ax[i], m, Ks, Ps, "RdBu", -vmax, vmax)
        ax[i].set_title(f"{w}\nvs {wo}")
        ax[i].set_xlabel("P")
        if i == 0:
            ax[i].set_ylabel("K")
    fig.colorbar(im, cax=fig.add_axes([0.89, 0.2, 0.015, 0.54]), label="Δ|bias| / mean truth")
    fig.text(0.01, 0.01, f"slice: W = {sl['W']}, α = {sl['alpha']:g}, γ = {sl['gamma']:g}, φ_A = 0; blank = not run",
             fontsize=6)
    watermark(fig, ph)
    fig.savefig(os.path.join(out, "fig3_contrast_KP.pdf"))
    plt.close(fig)


def heat(a, m, rows, cols, cmap, vmin, vmax, fmt="{:+.2f}"):
    im = a.imshow(m, cmap=cmap, vmin=vmin, vmax=vmax, aspect="auto")
    a.set_xticks(range(len(cols)))
    a.set_xticklabels([f"{c:g}" for c in cols])
    a.set_yticks(range(len(rows)))
    a.set_yticklabels([f"{r:g}" for r in rows])
    for (r, c), v in np.ndenumerate(m):
        if np.isfinite(v):
            a.text(c, r, fmt.format(v), ha="center", va="center", fontsize=5)
    return im


def all_cells_pages(pdf, values, title, cmap, vmin, vmax, label, ph, fmt="{:+.2f}"):
    """values: DataFrame with K, P, W, alpha, gamma, phi, v. Two pages: phi_A = 0 (216 cells), phi_A = 0.5 (24)."""
    combos = [(a, g) for a in GRID["alpha"] for g in GRID["gamma"]]
    for phi, grid in ((0.0, GRID), (0.5, PHI_GRID)):
        sub = values[values.phi == phi]
        fig, ax = plt.subplots(len(combos), len(grid["W"]), figsize=(2.4 * len(grid["W"]) + 1.2, 9.0), squeeze=False)
        im = None
        for i, (al, ga) in enumerate(combos):
            for j, W in enumerate(grid["W"]):
                m = np.full((len(grid["K"]), len(grid["P"])), np.nan)
                q = sub[(sub.alpha == al) & (sub.gamma == ga) & (sub.W == W)]
                for _, r in q.iterrows():
                    if int(r.K) in grid["K"] and int(r.P) in grid["P"]:
                        m[grid["K"].index(int(r.K)), grid["P"].index(int(r.P))] = r.v
                im = heat(ax[i, j], m, grid["K"], grid["P"], cmap, vmin, vmax, fmt)
                if i == 0:
                    ax[i, j].set_title(f"W = {W}")
                if j == 0:
                    ax[i, j].set_ylabel(f"α = {al:g}, γ = {ga:g}\nK")
                if i == len(combos) - 1:
                    ax[i, j].set_xlabel("P")
        fig.colorbar(im, ax=ax, shrink=0.5, label=label)
        fig.suptitle(f"{title} — φ_A = {phi:g} ({'216' if phi == 0 else '24'} cells; blank = not run)", fontsize=8)
        if ph:
            fig.text(0.5, 0.5, "PLACEHOLDER", fontsize=40, color="0.85", ha="center", va="center", rotation=30,
                     zorder=0, alpha=0.6)
            fig.text(0.5, 0.005, "PLACEHOLDER — synthetic test output, not results", ha="center", fontsize=7,
                     color="0.3")
        pdf.savefig(fig)
        plt.close(fig)


def supplementary(cm, out, ph):
    cols = ["K", "P", "W", "alpha", "gamma", "phi"]
    with PdfPages(os.path.join(out, "figS1_contrast_all_cells.pdf")) as pdf:
        for w, wo in PAIRS:
            d = contrast(cm, w, wo).rename(columns={"D": "v"})
            vmax = float(np.nanmax(np.abs(d.v))) if len(d) and np.isfinite(d.v).any() else 1.0
            all_cells_pages(pdf, d, f"S1. {w} vs {wo}: Δ|bias| / mean truth", "RdBu", -vmax, vmax,
                            "Δ|bias| / mean truth", ph)
    with PdfPages(os.path.join(out, "figS2_rel_bias_all_cells.pdf")) as pdf:
        for arm in ARMS:
            d = cm[cm.arm == arm][cols + ["rel_bias"]].rename(columns={"rel_bias": "v"})
            d = d.assign(v=100 * d.v)
            vmax = float(np.nanmax(np.abs(d.v))) if len(d) and np.isfinite(d.v).any() else 1.0
            all_cells_pages(pdf, d, f"S2. {arm}: relative bias (%)", "RdBu", -vmax, vmax, "relative bias (%)", ph,
                            fmt="{:+.0f}")
    with PdfPages(os.path.join(out, "figS3_coverage_all_cells.pdf")) as pdf:
        for arm in ARMS:
            d = cm[cm.arm == arm][cols + ["coverage"]].rename(columns={"coverage": "v"})
            all_cells_pages(pdf, d, f"S3. {arm}: 95 % interval coverage (nominal 0.95)", "viridis", 0.0, 1.0,
                            "coverage", ph, fmt="{:.2f}")


def fig4(checks, reps_report, out, ph):
    keys = [k for k in KEYS if k in checks]
    x = np.arange(len(keys))
    fig, ax = plt.subplots(1, 4, figsize=(7.2, 2.8))

    def pt(a, xi, e, key, lo="lo_2p5", hi="hi_97p5", **kw):
        if e:
            a.errorbar(xi, e[key], yerr=[[e[key] - e[lo]], [e[hi] - e[key]]], fmt="o", capsize=2, **kw)

    for i, k in enumerate(keys):
        c = checks[k]
        pt(ax[0], i - 0.12, c.get("E1_278"), "ba", color="0.1", label="278" if i == 0 else None)
        pt(ax[0], i + 0.12, c.get("E1_primary"), "ba", color="0.5", label="158" if i == 0 else None)
        for dx, s, col in ((-0.12, "278", "0.1"), (0.12, "primary", "0.5")):
            e = c.get(f"E3_site_{s}")
            if e:
                ax[1].plot(i + dx, e["linear"]["upper_one_sided_95"], "o", color=col)
                ax[1].plot(i + dx, e["mlp"]["upper_one_sided_95"], "x", color=col)
        for dx, key, col in ((-0.12, "E2_primary", "0.1"), (0.12, "E2_primary_after_removal", "0.5")):
            e = c.get(key)
            if e:
                ax[2].errorbar(i + dx, e["delta_auc"], yerr=[[e["delta_auc"] - e["ci_lo"]], [e["ci_hi"] - e["delta_auc"]]],
                               fmt="o", capsize=2, color=col)
        folds = [f for f in ((reps_report or {}).get(k) or []) if isinstance(f, dict)]
        for f in folds:
            if f.get("leace_var_retained") is not None:
                ax[3].plot(i - 0.12, f["pca_var_retained"], "o", color="0.1", alpha=0.7)
                ax[3].plot(i + 0.12, f["leace_var_retained"], "s", color="0.5", alpha=0.7)
    ax[0].axhline(0.25, color="0.6", lw=0.5, ls=":")
    ax[0].axhline(0.50, color="0.4", lw=0.5)
    ax[0].axhline(0.35, color="0.4", lw=0.5, ls="--")
    ax[0].set_title("E1: site BA\n(black 278, grey 158)")
    ax[1].axhline(0.35, color="0.4", lw=0.5, ls="--")
    ax[1].set_title("E3-site: upper bound\n(o linear, x MLP)")
    ax[2].axhline(0.05, color="0.4", lw=0.5, ls="--")
    ax[2].axhline(0.0, color="0.6", lw=0.5)
    ax[2].set_title("E2: ΔAUC\n(black before, grey after removal)")
    ax[3].set_title("variance retained per fold\n(● PCA 64, ■ after LEACE)")
    for a in ax:
        a.set_xticks(x)
        a.set_xticklabels([KEY_LABEL[k] for k in keys], rotation=30)
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    watermark(fig, ph)
    fig.savefig(os.path.join(out, "fig4_checks.pdf"))
    plt.close(fig)


def write_table(df, path_stem, title, ph):
    df = df.astype(object)
    if ph:
        df = pd.concat([pd.DataFrame([{df.columns[0]: "PLACEHOLDER — synthetic test output, not results"}],
                                     dtype=object), df])
    df.to_csv(path_stem + ".csv", index=False)
    cols = list(df.columns)
    lines = [f"**{title}**", "", "| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    lines += ["| " + " | ".join("" if pd.isna(v) else str(v) for v in r) + " |" for r in df.itertuples(index=False)]
    open(path_stem + ".md", "w").write("\n".join(lines) + "\n")


def tables(fams, out, ph):
    t1 = pd.DataFrame([
        dict(set="representation set (E1, E3-site, PCA / LEACE)", cases=278, centres_2_3_4_5="all 278 full-length cases of "
             "centres 2–5", definition="279 counted cases minus Center3_020 (timestamp beyond video end); centre 1 "
             "excluded (mostly 5-min clips)", source="protocol §2"),
        dict(set="primary causal set", cases=158, centres_2_3_4_5="28 / 34 / 44 / 52",
             definition="s − 45 ≥ 0 and s + 60 ≤ n (n = ⌊duration / 5⌋); offsets O ∈ {−15…15} (seed 20261005)",
             source="protocol §2, §7.2; dbd5984"),
        dict(set="per-W set W = 0", cases=204, centres_2_3_4_5="37 / 40 / 57 / 70",
             definition="primary offsets kept; 46 new offsets, same rule and seed", source="protocol §10.3; adf9160"),
        dict(set="per-W set W = 5", cases=201, centres_2_3_4_5="37 / 40 / 56 / 68",
             definition="primary offsets kept; 43 new offsets", source="protocol §10.3; adf9160"),
        dict(set="single-file set", cases=123, centres_2_3_4_5="13 / 34 / 44 / 32",
             definition="primary cases with one video file", source="protocol §2; ss_window_offsets.csv (dbd5984)"),
        dict(set="excluded from the primary set", cases=120, centres_2_3_4_5="21 / 7 / 27 / 65",
             definition="mainly early switches (46 of 117 centre-5 cases show the appendix within 75 s)",
             source="protocol §7.2")])
    write_table(t1, os.path.join(out, "table1_data_sets"), "Table 1. Data and analysis sets", ph)
    t2 = pd.DataFrame([
        dict(arm="FM-P (primary, standardized)", model="SurgeNetCholec (CAFormer-S18), TimJaspersTue/SurgeNetModels "
             "@cc21f4a1, CHOLEC_checkpoint_epoch0050_teacher.pth", kind="frame-level", input="2-fps grid frames; "
             "crop, mask, 224², ImageNet normalisation", representation="pooled normalised features, 512-d; mean of "
             "the step's 10 grid frames", reduction="PCA 64 (+ LEACE for FM-P−C)",
             selection="§4.1 rank 1 (after CODELOCK_CORRECTION_001)"),
        dict(arm="FM-P-nat (native sensitivity)", model="SurgeNetCholec (as above)", kind="frame-level",
             input="2-fps grid frames; resize only", representation="as FM-P", reduction="PCA 64 (no −C arm)",
             selection="§3.2"),
        dict(arm="FM-S (secondary)", model="LeanVAE-4ch, Yumic/LeanVAE @4585e461, LeanVAE-dim4.ckpt",
             kind="clip-level (L = 17 grid frames)", input="2-fps grid frames; crop, mask, 256²",
             representation="posterior mean 4 × 32 × 32 averaged over latent time, 4,096-d",
             reduction="PCA 64 (+ LEACE for FM-S−C)", selection="§4.1 secondary rank 1 (tie-break 2: GFLOPs)"),
        dict(arm="REF (reference)", model="nvidia/Cosmos-1.0-Tokenizer-CV8x8x8 @5110dbb3 (diffusers "
             "AutoencoderKLCosmos)", kind="native clip (≤ 121 native frames per 5-s step)",
             input="crop, mask, 320²", representation="post_quant_conv(latent mode) averaged over latent time, "
             "16 × 40 × 40 = 25,600", reduction="PCA 64 via randomized SVD (+ LEACE for REF−C)",
             selection="Decision 005 (not ranked)")])
    write_table(t2, os.path.join(out, "table2_models"), "Table 2. Models and representations", ph)
    rows = []
    for f in FAMILY_ORDER:
        v = fams.get(f"primary:{f}")
        if v:
            rows.append(dict(family=f, comparison=f"{v['with_arm']} vs {v['without_arm']}", cells=v["n_cells"],
                             D_bar=f"{v['D_bar']:+.3f}", CI95=f"[{v['ci_lo']:+.3f}, {v['ci_hi']:+.3f}]",
                             share_positive=f"{v['share_positive']:.2f}", verdict=v["verdict"],
                             conditions_failed=", ".join(v["conditions_failed"]) or "none"))
        else:
            rows.append(dict(family=f, comparison="—", cells=0, verdict="not computed in this output"))
    write_table(pd.DataFrame(rows), os.path.join(out, "table3_family_verdicts"), "Table 3. Family verdicts "
                "(primary set, §12.3)", ph)


def is_placeholder(*objs):
    def walk(o):
        if isinstance(o, dict):
            return o.get("label") == "PLACEHOLDER" or o.get("placeholder") is True or any(walk(v) for v in o.values())
        if isinstance(o, list):
            return any(walk(v) for v in o)
        return isinstance(o, str) and o.startswith("PLACEHOLDER")
    return any(walk(o) for o in objs if o is not None)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--step7", required=True)
    ap.add_argument("--step5", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--W", type=int, default=30)
    ap.add_argument("--alpha", type=float, default=0.5)
    ap.add_argument("--gamma", type=float, default=1.0)
    ap.add_argument("--placeholder", action="store_true")
    a = ap.parse_args(argv)
    cm = pd.read_csv(os.path.join(a.step7, "cell_metrics.csv"))
    cm = cm[cm["set"] == "primary"]
    fams = json.load(open(os.path.join(a.step7, "families.json")))
    checks = json.load(open(os.path.join(a.step5, "checks.json")))
    rp = os.path.join(a.step5, "reps_report.json")
    reps_report = json.load(open(rp)) if os.path.exists(rp) else None
    ph = a.placeholder or is_placeholder(checks, reps_report)
    os.makedirs(a.out, exist_ok=True)
    sl = dict(W=a.W, alpha=a.alpha, gamma=a.gamma)
    fig1(cm, sl, a.out, ph)
    fig2(cm, sl, a.out, ph)
    fig3(cm, sl, a.out, ph)
    supplementary(cm, a.out, ph)
    fig4({k: v for k, v in checks.items() if isinstance(v, dict) and k in KEYS}, reps_report, a.out, ph)
    tables(fams, a.out, ph)
    print(f"figures and tables written to {a.out}{' [PLACEHOLDER]' if ph else ''}: "
          + ", ".join(sorted(os.listdir(a.out))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
