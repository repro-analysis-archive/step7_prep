# SS PROTOCOL — DS203 semi-synthetic causal benchmark (DRAFT v0.4, not frozen)

* **Repository:** `~/projects/medical_video_causal_gate/`
* **Governing records:**
  * gate v4 (baadf5c), including §5b;
  * Amendment 2 (ebc097d);
  * Decisions 002 (cdbbc6e), 003, 004 (314cd94) and 005 (3660721).
* **Pre-protocol facts:** 146f69b, e4ea0d8, 052590c, dba9c06, 39d6eeb, cb07e93, 2012acd, **dbd5984** (window design,
  metadata only), **[v0.4-final2] adf9160** (per-W sensitivity offsets, metadata only), and the v0.4 eligibility facts
  (`data_audit/lead/ss_eligibility_v04.py`, `out/ss_eligibility_v04.json`, `fm_sources/eligibility_v04/`):
  6245f25, superseded by e81ab5f (v0.4-final2 override), superseded by a437225 (content-boundedness Rule B), superseded
  by **[v0.4-final3] ca04c5b + d3563e7** (initialization check; in force: **d3563e7**, json sha256 32e538dee89dd9ea…);
  and **[v0.4-final3] b987010** (per-W G-SITE, metadata only).
  All are committed before, and separately from, any protocol commit.
* **Revision:**
  * v0.4 consolidates the investigator decisions D-1 to D-5 and answers the final audit of v0.2 (HOLD — DESIGN CORE
    NOW SOUND; RESOLVE POST-WINDOW S / P1b CONSISTENCY, D-2 MODEL SELECTION, AND CAUSAL-SET E1/E3 BEFORE FREEZE).
  * There is no v0.3 draft; v0.4 is built on v0.2.
  * Text changed in v0.4 is marked **[v0.4]**; **[v0.2]** marks earlier changes.
  * **[v0.4-final]** marks the final pre-freeze edits (two-level overlap rule, theory-motivated labels, claim wording,
    GPU feasibility test, extraction compute fallback, tie-breaks, estimator commit). Version history: §18.
  * **[v0.4-final3]** marks the replacement of the Rule-B override by the content-boundedness rule, the recomputed
    eligibility and the per-W G-SITE rule. Version history: §18.
  * **[v0.4-final2]** marks the freeze repairs (per-W offsets, clip temporal sampling, Rule-B override,
    site-associated wording, pretrained video-derived wording, E3 components). Version history: §18.

## 0. Status and disclosure

* **Written after the following were known:**
  * DS203 container metadata (durations, frame rates, resolutions, codecs);
  * the D7 / D8 audit;
  * descriptive viewing of six frames from one sample video per centre;
  * the foundation-model candidate tables;
  * the site-overlap table;
  * the throughput estimates.
* **[v0.2]** Window-design facts (dbd5984) from case metadata only: centre, annotated timestamp and duration (§7.2).
* **[v0.4]** The class definitions of §4.1.3 were fixed with knowledge of the candidate tables. Their purpose is to keep
  the three arms distinct in kind, not to target a model.
* **[v0.4]** The eligibility facts of §4.1.5 were re-determined before freeze from level-1–3 sources (commit
  6245f25; re-checked under the v0.4-final2 override, e81ab5f; **[v0.4-final3]** recomputed under the
  content-boundedness Rule B, a437225; initialization check, ca04c5b + d3563e7, in force **d3563e7**). **[v0.4-final3]**
  The eligible lists are therefore known. The ranking has not been applied, and no model has been selected.
* **[v0.4-final3]** The per-W G-SITE values were computed from case metadata only (commit **b987010**; §10.3).
* **[v0.4-final2]** Offsets for the per-W sensitivity sets were computed from case metadata only (commit **adf9160**;
  §7.2, §10.3).
* **[v0.4-final]** The two-level overlap rule of §4.1.1 was fixed after it was known that a strict reading would make
  every candidate ineligible (§4.1.1, disclosure).
* **Written before** any DS203 frame is decoded for analysis, any representation is extracted, any synthetic action or
  outcome is generated, or any causal estimate is computed.
* **Freeze:** the protocol becomes frozen when committed alone. Nothing in §14 from step 2 onward runs before that
  commit.

## 1. Purpose and claim scope

**Question.** **[v0.4-final2]** When site-associated information encoded in video-derived representations is included
in, or linearly removed from, the adjustment set of a sequential causal analysis, how do bias and interval validity
change? The change is studied as a function of:
* intervention duration;
* post-window actions;
* pre-window history;
* unmeasured confounding strength.

**Scope.**
* This is a **semi-synthetic causal benchmark**: real clinical video, real site heterogeneity, **[v0.4-final2]** real
  pretrained video-derived representations, and a known causal truth from synthesized actions and outcomes. A specific
  model is called a foundation model only where its own sources do so.
* **[v0.4-final2] Site-associated information.** Real acquisition heterogeneity is one important source of
  site-associated information. E1 and LEACE do not isolate acquisition information specifically: they measure and
  linearly remove information that predicts site, whatever its origin (acquisition or other site-associated context).
* **[v0.4]** It is **a deliberately constructed orthogonal benchmark using real video and real acquisition
  heterogeneity** (§7.2). It does not reproduce DS203's natural joint distribution of site, state and timing, and it is
  not described as doing so.
* It does not estimate any causal effect in DS203, and it does not establish how real clinical actions affect real
  outcomes.
* **[v0.4-final]** The directional claims (§12) are tests of theory-motivated prespecified hypotheses. They are stated
  as "consistent / inconsistent with the theory-motivated direction", not as derived from the theory maps.
* **[v0.4-final] Claim wording for the representations.** Collectively, the arms use **"video-derived
  representations"**:
  * primary: "domain-specific surgical/endoscopic visual representation derived from video frames";
  * secondary: "generic temporally contextualized video representation";
  * reference: "paper-linked reconstructive/generative video representation".
  * The primary arm is not described as a temporal video foundation model unless the selected model is itself
    temporally contextualized (§4.1.2). **[v0.4-final3]** Every currently eligible primary model is frame-level
    (§4.1.5).

## 2. Data

* **Representation-level checks:** all 278 full-length cases of centres 2–5. That is 279 counted cases minus
  Center3_020, whose annotated timestamp exceeds its video length. Centre 1 is excluded (mostly 5-min clips).
* **[v0.4] Primary causal set (D-5):** the common eligible set, n = 158, for every W, K and P (§7.2).
  * Centres 2–5 = 28 / 34 / 44 / 52; every centre keeps ≥ 20 cases.
  * E2 primary and the causal-set confirmation of E1 / E3 (§5) use this set.
* **[v0.4] Per-W sensitivity sets (D-5):** W = 0 → 204 cases; W = 5 → 201 cases; W = 30 → 158 (= primary). Scope in
  §10.3.
* **[v0.2] Single-file sensitivity set:** the 123 single-file cases of the primary causal set (centre 2: 13). Scope in
  §10.3.
* **[v0.4] Folds:**
  * defined once on the 278 cases: case-level 5-fold, stratified by site, seed **20261006**;
  * the 158-case set and the sensitivity sets use the same fold labels, restricted to their cases.
* **[v0.2] Multi-file cases:**
  * files are ordered by their version suffix (`_v01`, `_v02`, …) and placed end to end;
  * physical time = summed duration of the preceding files + time within the file, with no gap assumed;
  * the annotated timestamp lies on this axis, as in D8 (146f69b).
* **Site factor C:** centre, 4 levels.
* **Step:** 5 s of physical time (as in Nakamura et al. 2026). Step t covers [5t, 5t + 5) s.
* **Content state:** S_t = 1 if 5t + 5 ≥ T_i (the appendix is visible by the end of step t), else 0 (D7). The switch
  step is s_i = max(⌈T_i / 5⌉ − 1, 0).

### 2.1 [v0.2] Time order within a step

1. The frames of [5t, 5t + 5) are observed.
2. At time 5t + 5, R_t (from those frames and, for clip models, earlier frames only; §4.2) and S_t are determined.
3. The synthetic action A_t occurs immediately after 5t + 5.
4. Y_i is determined after the last post-window step.

So R_t and S_t are strictly pre-treatment for A_t.
* An S switch in (5t + 4.5, 5t + 5] is in no grid frame of step t (grid frames are at 5t + 0.5k, k = 0…9). It appears
  in step t + 1.

## 3. Preprocessing

### 3.1 Primary: standardized acquisition

1. **[v0.2] Fixed physical-time grid of 2 frames per second.**
   * Grid times are 0.5k s on the physical time axis.
   * At each grid time, the first decoded frame whose presentation time is ≥ the grid time is used.
   * No re-encoding and no interpolation. Step t uses grid frames 10t … 10t + 9.
2. **Crop and resize.** Each frame is centre-cropped to a square of side equal to its shorter dimension, then resized
   (bilinear, antialiased) to the model's input size.
3. **[v0.2] Common mask, applied to every frame of every centre (values fixed here):**
   * (a) circular mask, centred, **radius r = 0.45 × side**; pixels outside are set to black before model
     normalization;
   * (b) bottom band, **the lowest 3 % of the square**, set to black. This is redundant with (a), since
     0.5 + 0.45 = 0.95 < 0.97; it is kept as a guard.
   * **Basis (e4ea0d8):**
     * the C2 image circle is "roughly as tall as the frame" (radius ≈ 0.5 side);
     * the C3 circle is wider than the frame height;
     * C4 and C5 are full-frame;
     * the C5 status bar (with elapsed time) occupies about the bottom 2.5 %;
     * the C5 privacy rectangle (x 1645–1845 of 1920) lies outside the centre crop;
     * the C3 icon sits in the lower-right margin.
   * **Mechanical check** (§14 step 4a, before extraction, on standardized frames):
     * Per centre, compute the grayscale mean frame at 256×256 over every 60th grid frame of every case.
     * Compute the radial profile m_c(ρ): the mean over the 1-px annulus at radius ρ, in units of side.
     * The visible radius ρ_c is the largest ρ with m_c(ρ′) ≥ 0.25 × median{m_c(ρ″): ρ″ ≤ 0.1} for all ρ′ ≤ ρ.
     * If min_c ρ_c ≥ 0.45, r = 0.45 stands. Otherwise r = 0.98 × min_c ρ_c. No other value is permitted.
     * The profiles are reported.
4. **[v0.2] Near-uniform frames.**
   * Definition: luma (BT.601) standard deviation over the unmasked disc, at 256×256, **below 4.0** on the 8-bit scale.
   * These frames are kept; their proportion is reported by centre and by S.

### 3.2 Sensitivity: native acquisition

* Frames on the same 2-fps grid, with only the model's default preprocessing (resize); no crop, no mask.
* **[v0.2]** The physical-time grid removes the raw frame rate as such. Remaining site cues are:
  * resolution, aspect ratio and borders;
  * overlays: the centre-5 status bar with its on-screen elapsed time, the centre-5 privacy rectangle, the centre-3
    icon;
  * compression;
  * motion blur;
  * other acquisition signatures.
* Native-arm results are reported as containing these cues.

## 4. Representations

### 4.1 [v0.4] Selection rules (replace v0.2 §4.1 and decision point D-2)

The rules below are applied mechanically after freeze (§14 step 3). The underlying facts were determined before freeze
(§4.1.5).

#### 4.1.1 Source hierarchy

Every eligibility fact is determined from, in order:
1. the original paper (for a training dataset, that dataset's own paper);
2. the official model card (official repository README or official file listing);
3. the documented pretraining-data list (official configs / training scripts);
4. secondary sources;
5. earlier internal tables (052590c, cb07e93).

**Standard of evidence:**
* A fact counts as NO (for an exclusion such as DS203 overlap), or holds (for a requirement such as "laparoscopic video
  in the pretraining data"), **only if a level-1 to level-3 source affirmatively supports it. Otherwise it is UNK. UNK
  is ineligible.**
* Levels 4–5 provide context only.

**[v0.4-final] Two-level overlap rule** (replaces the D-6 text). It is applied to every training source of the
released weights and of their initialisation or base weights.

**[v0.4-final3]** "Frozen auxiliary networks used only inside a training loss (e.g., perceptual-loss or discriminator
feature extractors) are not training sources of the released weights and are not assessed under Rules A–C. They shape
a similarity measure; they do not supply training samples. Any network whose weights initialize, or are distilled into,
the released model is a training source and is assessed."

**A. Direct DS203 / DS203-centre overlap.** For each training source:
* **YES:** DS203, a constituent DS203 dataset, or a known same-hospital clinical source (e.g., DSAD, University
  Hospital Carl Gustav Carus Dresden) is documented;
* **NO:** a level-1 to level-3 source establishes a closed or sufficiently defined corpus whose documented scope
  excludes DS203 and the known DS203 clinical sources. Examples:
  * a clinical set with a named non-DS203 recording site, or a stated non-German geography;
  * a versioned, non-surgical benchmark with fixed classes, finalized before DS203's release (2026-04-29);
* **UNK:** the source is open-ended or web-scale (YouTube, web lecture platforms, stock / social / Internet video), its
  base weights' data are undocumented, or its clinical / site provenance cannot be bounded (e.g., a clinical set with
  no stated recording site).

A candidate passes only if every source is NO. YES and UNK are ineligible.

**[v0.4-final3] B. Rule B — bounded generic-web benchmark override.** (This replaces the v0.4-final2 override and its
determinism sentence; see §18.)

> Generic web provenance alone does not change NO to UNK only for a named, versioned, fixed benchmark whose level-1–3
> documentation provides a sufficiently bounded content scope (for example, a fixed class/task ontology or equivalent
> closed benchmark definition) that permits the relevant DS203 / clinical-overlap concern to be affirmatively
> excluded.
>
> A fixed release remains UNK when it is an open-domain or broadly scraped web corpus whose clinical/content/site
> provenance cannot be bounded from level-1–3 sources. Release date alone is not sufficient for NO.
>
> This override applies only to the generic-web-origin clause. It never overrides Rule A's clinical/site-provenance
> clause.

* For a source that passes this override, generic web origin is disclosed separately as a limitation (§16):
  "incidental web-origin exposure cannot be excluded at the level of every source image."

**C. Same-hospital rule.**
* It applies to clinical / endoscopic pretraining sources, where acquisition-site provenance is meaningful.
* A generic object or action benchmark is not disqualified because individual web items cannot be traced.

**Justification and disclosure.**
* **Consistency:** the rule is consistent with 052590c, where NO was assigned to closed lists of named datasets,
  including ImageNet-initialized models, before the present outcome was known.
* **Purpose:** to bound direct DS203 / DS203-centre overlap, which is the contamination relevant to this study, as
  distinct from untraceable generic web origin.
* **A strict reading** (every web-derived source UNK) would leave no eligible model in either arm (§4.1.5).
* "The rule was fixed after it was known that a strict reading would make every candidate ineligible."

#### 4.1.2 Clip-level definition

* "A clip-level model jointly consumes two or more temporally ordered frames and produces a representation conditioned
  on temporal context."
* A model that averages independent per-frame embeddings is frame-level.

#### 4.1.3 Mutually exclusive classes

* **Primary:** medical / endoscopic **representation-learning encoders** (self-supervised or discriminative).
  Generative models are excluded. **[v0.4-final]** Claim wording: "domain-specific surgical/endoscopic visual
  representation derived from video frames" (§1).
* **Secondary:** **generic** (non-medical) reconstructive or generative video models. **[v0.4-final]** Claim wording:
  "generic temporally contextualized video representation" (§1).
* **Neither:** surgical-domain generative models (e.g., Cosmos-H, SG2VID, MedSora, KVLR). They are ineligible for
  both arms.
* **Disclosure:** the class definitions were fixed with knowledge of the candidate tables, to keep the three arms
  distinct in kind, not to target a model.

#### 4.1.4 Rules

**Primary**, among 052590c-eligible candidates of the primary class:
1. laparoscopic video in the documented pretraining data;
2. **[v0.4-final]** every training source NO under rule A (§4.1.1). Rule C applies to clinical / endoscopic sources;
   this excludes models trained on DSAD;
3. compute documented: FLOPs per input, a parameter count, or a standard named architecture whose size is given in its
   level-1 paper;
4. **[v0.4-final] GPU memory feasibility** (rule frozen now, test run after freeze, §14 step 3):
   * **prior screen:** a level-1–3 parameter count (2 bytes per parameter < 14.4 GB) or the official checkpoint file
     size (< 14.4 GB);
   * **final determination: synthetic-input feasibility test.**
     * Conditions: inference only; batch size 1; bf16 where supported; the exact protocol input size and clip length
       (§4.2); the software stack intended for extraction; no DS203 frame.
     * **Feasible if peak reserved GPU memory ≤ 20.0 GB** on the 24 GB RTX 4500 Ada (4 GB headroom).
     * A candidate failing the test is infeasible, and the next-ranked candidate is taken;
5. **[v0.4-final] extraction compute feasibility** (§10.4): a top-ranked candidate whose projected extraction time
   exceeds 7 days is infeasible, and the next-ranked candidate is taken.

**Primary rank (scientific criteria):**
1. clip-level before frame-level;
2. most recent release (first public availability of the checkpoint, per a level-1–3 source);
3. lowest compute.

**[v0.4-final] Tie-breaks** (replace the drafted ones). After the scientific criteria, in order:
1. the authors' explicitly documented default or recommended checkpoint, supported by a level-1 source. If none is
   stated, none is inferred;
2. lower protocol-relevant compute;
3. lower measured synthetic-input peak memory (rule 4 test);
4. lexical order of the model / checkpoint identifier.

No DS203 representation quality, real-frame throughput or causal result may enter a tie-break.

The top-ranked feasible checkpoint (rules 4–5) is selected.

**Secondary**, among 052590c-eligible candidates of the secondary class:
1. every training source NO under rule A (§4.1.1);
2. compute documented (as in primary rule 3);
3. GPU memory feasibility (as in primary rule 4);
4. extraction compute feasibility (as in primary rule 5).

**Secondary rank:** video VAE / tokenizer before masked autoencoder; then most recent release; then lowest compute;
then the four tie-breaks above.

**Reference (Decision 005):** nvidia/Cosmos-1.0-Tokenizer-CV8x8x8, the default of the authors' gpi_pack (§4.2). It is
not subject to these rules.

If no candidate passes, that arm is dropped and reported. No rule is relaxed.

#### 4.1.5 [v0.4] Pre-freeze eligibility facts (no ranking applied, no selection)

* **[v0.4-final3] Source:** commit **d3563e7** (initialization check ca04c5b plus a note correction; supersedes
  a437225, e81ab5f and 6245f25), `out/ss_eligibility_v04.json`, under the two-level rule with the content-boundedness
  Rule B. 203 / 203 quotes verified; all at levels 1–3.
  * **[v0.4-final3] Initialization:** every eligible model's initialization is affirmatively stated in a level-1–3
    source (`init_stated`, `init_quotes`). An unstated initialization is an undocumented base (Rule A UNK).
  * For every source of every candidate the file records whether its level-1–3 documentation gives a bounded content
    scope (`per_candidate_source_boundedness`).
  * For each benchmark it records the ontology quote and a term check of its documented class / task list
    (`ontology_term_check`).
* The memory and compute feasibility rules (rules 4–5) are applied after freeze. The size facts below are the prior
  screen only.
* **[v0.4-final3] Eligible primary**, all frame-level:
  * SurgeNetCholec (CAFormer-S18);
  * SurgeNetRARP (CAFormer-S18);
  * SelfSupSurg ResNet-50 (MoCo v2 / SimCLR / SwAV / DINO checkpoints).
* **Eligible secondary**, all clip-level (training sources re-checked under the content-boundedness rule; unchanged):
  * VideoMAE (Kinetics-400 / SSv2 / UCF-101 checkpoints);
  * OmniTokenizer (ImageNet + K600);
  * WF-VAE-L 16ch;
  * LARP-L-Long tokenizer;
  * LeanVAE.
* **Strict-reading counterfactual:** none in either arm.
* **Tie-break order** (both arms, after the scientific criteria): authors' level-1 default → lower compute → lower
  synthetic-input peak memory → lexical identifier.
* **Ineligible:** every other candidate.
  * Primary class, rule A **YES** (DSAD, a same-hospital clinical source): EndoViT, SurgeNetXL, SurgeNet /
    SurgeNetPublic.
  * **[v0.4-final2]** Primary class, rule A **UNK**:
    * clinical sets without a stated site: Endo-FM, EndoMamba, EndoSSL colonoscopy;
    * surgical web corpora with unbounded recording sites (clinical clause): SurgVLP family (SVL), LemonFM, SurgLIME,
      PL-Stitch (LEMON);
    * **[v0.4-final3]** a fixed release without a bounded content scope: Basel V-JEPA ViT-L. Its base data
      (VideoMix2M) include HowTo100M, whose task ontology includes a Health category ("Health 172" tasks).
  * SurgeNetRAMIE: laparoscopic video not affirmatively documented.
  * **[v0.4-final3]** EndoSSL laparoscopy ViT-B / ViT-L / ViT-S: the initialization of the released checkpoints is not
    stated in any level-1–3 source (paper, supplementary, README, released code), so it is an undocumented base
    (Rule A UNK). The paper's ablations compare starting "from scratch or from a good SSL pretrained checkpoint on
    ImageNet-1k" without saying which the released checkpoints used. The ViT-S size is given in the supplementary
    (23M).
  * Neither class: Cosmos-H ×4, MedSora, SG2VID, KVLR.
  * **[v0.4-final2]** Secondary, rule A **UNK**:
    * unversioned / self-collected web corpora: Open-Sora VAE, VideoMAE V2 (Instagram crawl), Open-Sora-Plan VAE,
      Reducio-VAE;
    * undocumented base weights: CV-VAE (Stable Diffusion VAE weights retained).
  * Open-MAGVIT2: compute not documented.

### 4.2 Extraction

* **Frame-level models:** one embedding per grid frame, mean-pooled over the step's 10 frames.
* **[v0.2] Clip-level models (§4.1.2):** one clip per step, at the model's documented clip length L_m.
  * The clip is the L_m most recent grid frames ending at the step's last grid frame. No frame after 5t + 5 is used.
  * If L_m > 10, the earlier frames come from preceding steps.
  * At the video start, the first grid frame is repeated.
  * **[v0.4-final2]** "Clip-level models receive frames from the 2-fps grid. This may differ from each model's
    documented temporal sampling; it standardizes acquisition across centres at the cost of temporal fidelity."
* **[v0.4] Reference arm (D-3)** — "paper-linked Cosmos reference using the original temporal/representation
  definition under DS203-standardized spatial preprocessing":
  * Input: the step's contiguous native frames in [5t, 5t + 5); at most 121, uniformly selected (package default).
  * The standardized crop and mask (§3.1 steps 2–3) are applied, then the frames are resized to **320×320**.
  * The representation is the decoder input `post_quant_conv(latent)`, averaged over latent time:
    **16 × 40 × 40** = 25,600 values.
  * It is **not a pixel-level replication** of K4: K4's (16, 40, 60) shape implies a non-square, approximately
    320×480 input.
  * It can retain frame-rate-derived information, because it uses contiguous native frames rather than the 2-fps grid.
  * **[v0.4-final]** Claim wording: "paper-linked reconstructive/generative video representation" (§1).
* **[v0.4] PCA:** each representation R_t is reduced to 64 principal components.
  * PCA is fit on all steps of the training-fold cases of the 278-case set and applied to the held-out fold.

### 4.3 Linear site removal

* **[v0.4]** R_t^(−C) is a LEACE-type closed-form removal of linearly decodable site information.
  * It is fit on all steps of the training-fold cases of the 278-case set and applied to the held-out fold.
* **Reported:**
  * site decodability before and after (linear probe and 2-layer MLP probe, §5.3);
  * state incremental value retained (§5.2);
  * dimension and variance retained.
* Results are described as **"linearly site-removed"**, never as "site-invariant".

## 5. Pre-causal checks (after extraction, before any causal run)

**Shared settings:**
* **Folds:** as in §2.
* **Site probes:** per step; the case-level prediction is the mean predicted probability over the case's steps;
  balanced accuracy is computed over cases.
* **CIs:** case bootstrap stratified by site, 2,000 resamples, seed **20261008**.
* **[v0.4] Two sets:**
  * **[v0.4-final2]** E1 and E3-site are run on the 278-case set (primary representation check) and on the 158-case
    primary causal set (causal-set confirmation). E3-state-retention is run on the 158-case set only (§5.3);
  * **the 158-case results are never used for model selection.**

### 5.1 E1 Site encoding

* **Data:** all steps of the 278 full videos (primary) and the analysis region of the 158 cases (confirmation;
  relative steps −30 … 44, §7.2). Standardized and native arms.
* **Encoding present** if balanced accuracy ≥ 0.50 (chance 0.25) with the lower 95 % bound above 0.35.

### 5.2 [v0.2] E2 State recovery beyond time (fully prespecified)

**Primary.**
* **Data:** the analysis region of the 158 cases, steps w_i − 30 … w_i + 44 (§7.2).
* **Comparison:** held-out AUC for S_t of
  * base = elapsed time (natural cubic spline, 4 df, knots at training-fold quantiles), against
  * base + R_t (64 PCs).
* **Learner:** L2 logistic regression, penalty chosen by inner 5-fold CV over {10⁻⁴, 10⁻³, …, 10²} within the
  training folds.
* **Recovery present** if ΔAUC ≥ 0.05 and its 95 % case-cluster bootstrap CI excludes 0.

**Secondary (reported only).**
* The same comparison on all steps of the 278 full videos.
* base = elapsed time + H (past synthetic actions), under one fixed reference DGP cell: K = 5, P = 0, W = 5, α = 0.5,
  γ = 1, φ_A = 0, replicate 1.

**Stricter reference.** Normalized time (t / case length) is reported as a stricter reference. It uses future
information and is not a valid baseline.

### 5.3 E3 Removal success (equivalence form; D-4)

**[v0.4-final2] Two components:**
* **E3-site:** criterion (i), evaluated separately on the 278-case and the 158-case sets. After removal, the
  **linear-probe site balanced accuracy has a one-sided 95 % upper bound ≤ 0.35**.
* **E3-state-retention:** criterion (ii), evaluated on the 158-case set only. The E2-primary ΔAUC after removal is
  ≥ 50 % of its pre-removal value (point estimates).
  * If the E2 primary check fails (ΔAUC < 0.05 or its CI includes 0), E3-state-retention is **not applicable**. The
    report then states that retention of state information could not be assessed.
* **Interpretation of FM−C causal arms** (and the P1b-FM / P2-FM conditions) requires:
  * E3-site to pass on both sets; and
  * E3-state-retention to pass on the 158-case set, or to be not applicable.

**[v0.4] Wording when E3-site passes:** linear site decodability "**no longer exceeds the prespecified linear
site-encoding boundary**". It is never described as "equivalent to chance" or "eliminated", since 0.35 is 10 points
above chance. The representation is "linearly site-removed".

**MLP probe (fixed):**
* architecture: 2 layers, 256 hidden units, ReLU;
* training: Adam with learning rate 10⁻³, weight decay 10⁻⁴, at most 200 epochs, early stopping (patience 20) on a
  20 % inner validation split.

If E3-site passes but the MLP upper bound exceeds 0.35, the claim ceiling is **"linear site information removed;
nonlinear site information remains"**.

### 5.4 [v0.4] G-SITE: verification that the constructed benchmark satisfies its intended orthogonality condition

* **Status:** G-SITE is a design check computed at code lock from the design only. It is not an independent
  validation.
* **Outcome component.** In the P2 cells (K = 1, P = 0), the non-treatment outcome component is
  N_i = λ·S_{i, w_i} + β·U_i. U ⟂ C by construction.
* **Gate:** η² of S_{i, w_i} on C (one-way, primary causal set) **≤ 0.01**.
* **Also reported:** η² of Σ_{window ∪ post} S_it on C, for every cell.
* **If the gate fails:** P2-SITE and P2-ORACLE (§12) are not tested and are reported as P3.
* **[v0.4-final3] Per-W sets:** the same quantity and threshold apply to the per-W sensitivity sets (§10.3).
* **Basis:**
  * C enters only A.
  * Under §7.2, S at window-relative step j is 1{O_i + j ≥ 0}, a function of the site-stratified offset alone.
* **[v0.4] Scope: G-SITE checks marginal independence.** When W > 0, conditioning on past actions, which are common
  effects of C and U, induces dependence between C and U given H. Theory statement (i) held in all seven settings,
  including pre-window history (E2), so the P2 predictions are unchanged.
* **Disclosure:** with the fixed offsets, η² = 0.0014 (V = 0.038) at relative step 0, and max V = 0.053 over relative
  steps −30 … 44, are already known from metadata (dbd5984).

## 6. Semi-synthetic data-generating process

For case i, step t, with U_i ~ N(0, 1) synthetic and unseen in the video. The equations apply to steps
w_i − W … w_i + K + P − 1, **[v0.2]** with initial value A_{i, w_i − W − 1} = 0.

A_it = μ + γ·c(C_i) + κ·S_it + α·U_i + φ_A·A_{i,t−1} + ε_it, ε ~ N(0, 1)

Y_i = τ·Σ_{t∈window∪post} A_it + λ·Σ_{t∈window∪post} S_it + β·U_i + ε_Y, ε_Y ~ N(0, 1)

* **[v0.4] Site loadings c(C):**
  * values (−3, −1, 1, 3)/√5 (centred, unit variance over the four levels);
  * assigned to the four centres by a permutation drawn for each replicate from a pre-fixed seed: the replicate's
    SeedSequence child (§10.2) with spawn key "c-permutation";
  * the same mapping is used for all arms within a replicate;
  * results are interpreted as the effect of a **generic site-identity signal**, not of any specific centre.
* **Causal structure:**
  * C has no direct effect on Y; S_t affects A and Y; U affects A and Y.
  * Synthetic actions do not alter the video; S_t and C are fixed by the data and the window rule.
  * There is no treatment–confounder feedback (a limitation, §16).
* **Fixed constants:** μ = 1, τ = 1, κ = 1, λ = 1, β = α, φ_A = 0 (primary) or 0.5 (sensitivity).
* **Role of C (per §5b):**
  * for K ≥ 2 with a history containing past actions, or for P ≥ 1, C is a confounder through later actions, not an
    instrument;
  * C is instrument-like only at K = 1, P = 0, and there only if G-SITE passes (§5.4).

## 7. Estimand, truth and window

### 7.1 Estimand and truth

* **Policy:** multiplicative modified treatment policy d(a) = δ·a, δ = 1.05, applied at every step of a window of K
  steps.
  * The P post-window steps and the W pre-window steps follow their natural course.
  * The pre-window steps enter the history.
* **Estimand:** Ψ(δ) − Ψ(1).
* **Truth:** computed exactly from the DGP for each replicate (it depends on that replicate's c permutation). Closed
  form for φ_A = 0; exact recursion for φ_A = 0.5.

### 7.2 Window placement (D-1)

* **[v0.4] Design:** a deliberately constructed orthogonal benchmark using real video and real acquisition
  heterogeneity. It is not a reproduction of DS203's natural joint distribution.
* **Eligible set:** cases with s_i − 15 − 30 ≥ 0 and s_i + 15 + 15 + 30 ≤ n_i, where n_i = ⌊D_i / 5⌋. n = 158.
* **Offsets:** O_i ∈ {−15, …, 15}, assigned within each site from a seeded permutation (seed **20261005**).
  * The values are in `data_audit/lead/out/ss_window_offsets.csv` (sha256 4794e139…ea6c3, commit dbd5984).
  * **[v0.4] Each case's offset is fixed once and is unchanged across all cells, arms and replicates.**
  * **[v0.4-final2] Per-W sensitivity sets (§10.3).** The file above has no offset for 46 cases of the W = 0 set and
    43 cases of the W = 5 set.
    * Rule: the 158 primary offsets are kept unchanged. The missing cases of each per-W set receive offsets by the
      same procedure and seed (within-site seeded permutation of {−15, …, 15}, seed 20261005), applied to each per-W
      set separately.
    * Computed from case metadata only; file `data_audit/lead/out/ss_window_offsets_perW.csv` (sha256
      95513df0…f38d48, commit **adf9160**).
    * Within each per-W set, each case's offset is fixed once.
* **Window:**
  * the window starts at **w_i = s_i + O_i**;
  * window steps are w_i … w_i + K − 1;
  * W pre-window steps precede it and P post-window steps follow it.
* **[v0.4] State along the trajectory:**
  * S at window-relative step j is 1{O_i + j ≥ 0};
  * it is 1 for every case when j ≥ 15, and varies across cases when j < 15;
  * **post-window S is constant only when K ≥ 15**; for K < 15 the switch can occur in post-window steps;
  * P(S = 1) at relative step j (dbd5984): 0 for j ≤ −16, 0.35 at −5, 0.52 at 0, 0.67 at 4, 0.97 at 14, 1 from 15;
  * max V(C, S_j) = 0.053.
* **[v0.4] Disclosure:** "Candidate window-placement rules were evaluated before any frame decoding, representation
  extraction, synthetic treatment/outcome generation, or causal estimation. The final rule was selected to satisfy two
  prespecified structural requirements: within-step state variation and minimal site–state association."
* **Rejected rules (record, dbd5984):**
  * the v0.1 switch-centred rule (start = s_i − ⌊K/2⌋) gave one S sequence per K, so there was no between-case state
    variation;
  * a fixed procedure-time anchor (280 s, pooled median) gives V(C, S) = 0.25–0.32, a large site–state association;
  * seeded uniform eligible-window sampling leaves only 4 % of 75-s windows containing the switch, too little state
    variation.
* **Exclusions:**
  * 120 of 278 cases are excluded, mainly for early switches. 46 of 117 centre-5 cases show the appendix within 75 s
    and have no pre-switch footage.
  * Excluded by site: 21 / 7 / 27 / 65.

## 8. Adjustment arms

* **[v0.2] History H** = past synthetic actions in the trajectory: pre-window steps and earlier window steps.
  * Elapsed time is not included. Window-start elapsed time differs by site (medians 398–683 s, dbd5984), and the DGP
    does not depend on it.
* **[v0.4] Conditioning set.** At each window step t, the nuisances condition on H_t (all past synthetic actions in the
  trajectory) and on the arm's covariates at step t only. Past representations and past S are not included.

| arm | adjustment set (step-t covariates) |
|---|---|
| NV | H_t (no video) |
| SITE | H_t + C (explicit site; theory analogue of Z) |
| FM-P | H_t + R_t, primary model, standardized |
| FM-P−C | H_t + R_t^(−C), primary, standardized |
| FM-S, FM-S−C | as above, secondary model |
| REF, REF−C | as above, paper-linked Cosmos reference (§4.2) |
| FM-P-nat | H_t + R_t, primary, native (sensitivity) |
| ORACLE−C | H_t + S_t (exact state, no site) |
| ORACLE | H_t + S_t + C |
| **[v0.4] FULL** | H_t + S_t + C + U, the **exchangeability oracle / implementation sanity reference** (not called unbiased) |

## 9. Estimator and inference

* **[v0.4] Estimator:** a sequentially doubly robust (SDR) estimator for the multiplicative MTP, with
  influence-function-based standard errors, **implemented in this repository**.
  * The DR-FLEX / V3-C05 code path is **not used**: its commissioning scope and learners do not transfer without
    retuning.
  * The implementation is fixed at code lock (code only, no free numeric settings).
  * **[v0.4-final]** The exact code commit of the in-house SDR implementation is recorded at code lock (§14 step 2).
    It is referenced in the run record before the causal grid runs.
* **[v0.4] Estimator gate (code lock):**
  * Data: synthetic placeholder features with known truth only (no DS203 frame, no representation).
  * Test subset: K ∈ {1, 5, 15}, P ∈ {0, 5}, W = 5, α = 0.5, γ = 1, M = 200.
  * Pass: the FULL arm reaches 95 % coverage within [0.90, 0.99] and |bias| below 5 % of the true contrast in every
    test cell.
  * **If it fails: STOP before extraction.**
* **[v0.2] Nuisances**, with learner choice by lower cross-validated loss within the training fold:
  * **Outcome regressions:** ridge (penalty by inner 5-fold CV over {10⁻³, …, 10³}) or a 2-layer MLP (128 units,
    ReLU, Adam 10⁻³, weight decay 10⁻⁴, at most 300 epochs, early stopping with patience 20 on a 20 % inner split).
  * **Density ratios:** probabilistic classification with the same two learner families (L2 logistic regression or MLP,
    by log-loss).
* **[v0.4] Fitting sets:**
  * PCA and LEACE: all steps of the training-fold cases of the 278-case set;
  * causal nuisances: the training-fold cases of the analysis set (the 158-case set, or the §10.3 sensitivity set);
  * all predictions are made on held-out folds.
* **Intervals:** 95 % Wald intervals from the influence function.

## 10. Design grid and replication

### 10.1 Grid

* K ∈ {1, 2, 5, 15}; P ∈ {0, 5, 30}; W ∈ {0, 5, 30}; α ∈ {0, 0.5, 1}; γ ∈ {0.5, 1}. That is 216 cells.
* **[v0.2] φ_A = 0.5:** run on the subset K ∈ {1, 5}, P ∈ {0, 5}, W = 5, all α and γ (24 cells).

### 10.2 [v0.2] Replication and seeds

* M = 200 synthetic replicates per cell: new U, ε, ε_Y and c permutation; same videos and representations.
* Replicate seeds come from NumPy SeedSequence(**20261007**), spawned by (cell index, replicate index).
* All arms of a replicate share its draws (paired comparisons).

### 10.3 Sensitivity runs (fixed scope)

* **[v0.2] Single-file:** on the 123 single-file cases of the primary causal set: E1–E3, and the P1b and P2 families
  (§12) for arms NV, SITE, FM-P and FM-P−C.
* **[v0.4] Per-W sets (D-5):** the P1b and P2 family cells with W = 0 (204 cases) and W = 5 (201 cases), for arms NV,
  SITE, FM-P, FM-P−C, ORACLE and ORACLE−C.
  * They are reported separately and do not enter family verdicts.
  * **[v0.4-final2] Offsets:** `out/ss_window_offsets_perW.csv` (adf9160; rule in §7.2).
    * W = 0: 204 cases, centres 2–5 = 37 / 40 / 57 / 70 (46 new offsets); max V(C, S_j) over relative steps 0 … 44 =
      0.076.
    * W = 5: 201 cases, 37 / 40 / 56 / 68 (43 new offsets); max V(C, S_j) over relative steps −5 … 44 = 0.097.
    * The primary set has max V = 0.053.
  * **[v0.4-final3] Per-W G-SITE** (η² of S at the window start on C; b987010): W = 0: **0.0037**; W = 5: **0.0045**
    (primary: 0.0014). Both are ≤ 0.01.
  * **[v0.4-final3] Rule:** per-W P2 sensitivity results are interpreted as instrument-like comparisons only if that
    set's per-W G-SITE is ≤ 0.01. Otherwise they are labelled descriptive.

### 10.4 [v0.4] Compute budget

* **Projection (code lock):** the dry run times a representative subset of SDR fits (all K, both learners, all arms) and
  projects the full-grid wall time, including §10.3, on the available cores.
* **Budget:** 7 days of wall time.
* **If exceeded, reduce in this order until it fits:**
  * (a) P3 cells only: M = 100;
  * (b) P3 cells only: ridge only;
  * (c) P3 cells only: drop FM-S−C and REF−C.
* Family cells (P1a, P1b, P2) are never reduced.
* **If still over budget: STOP for a human decision before extraction.**

**[v0.4-final] Extraction compute fallback** (§4.1.4 rule 5).
* **Procedure (frozen):** for each arm's top-ranked eligible model, total extraction wall time for all DS203 steps is
  projected from:
  * a synthetic-input throughput benchmark (same input size, clip length and software stack as extraction), combined
    with
  * the already measured disk and decode throughput (2012acd).
* **If the projection exceeds 7 days**, the model is computationally infeasible and the next-ranked candidate is taken.
* Representation quality, decoding of real frames and causal results never enter this decision.

## 11. Metrics

**[v0.2] Primary**, per arm and cell:
* absolute bias |mean_r(Ψ̂_r − Ψ_r)|;
* relative bias (bias / mean truth);
* 95 % coverage.

**Secondary:**
* bias-to-Monte-Carlo-SD ratio (|bias| / SD of Ψ̂ over replicates);
* RMSE;
* CI width;
* effective sample size and density-ratio diagnostics;
* support-failure rate.

**Other rules:**
* Relative bias is reported for every cell.
* The DGP gives |truth| ≥ 0.05·K·(1 + γ·mean c). Cells with |truth| < 0.025, if any, are flagged at code lock.
* Within-cell comparisons between arms are paired on replicates.

## 12. Predictions and their aggregation

### 12.1 Mapping to the theory

**[v0.4-final] Status of all families: theory-motivated prespecified hypotheses.**
* Every family (P1a, P1b-SITE, P1b-FM, P2-SITE, P2-FM, P2-ORACLE) is a **theory-motivated prespecified hypothesis**.
  None is "theory-derived".
* **Reason:** the theory maps establish the direction under their own DGPs. The v0.4 DGP differs:
  * a four-level discrete site with permuted loadings;
  * a binary switching state;
  * a different post-window state process;
  * finite-sample nuisance estimation.
* No transport proof is given.
* Claims take the form "**consistent / inconsistent with the theory-motivated direction**". The family verdict rules
  (§12.3) are unchanged.
* The earlier labels and the reason for the change are kept in §18.

**Mapping.**
* The maps 47a49ea and 6165ece have Z, a trajectory-constant factor acting on A, and U, an unmeasured confounder.
* Here Z corresponds to C. The unmeasured confounding of an arm is U **plus whatever part of S the arm does not
  capture**.
* In NV and SITE, S is entirely unmeasured, so α = 0 does not mean "no unmeasured confounding".

**Statements of the maps that hold in all seven settings** (base, E1 × 2, E2 × 2, E3 × 2, E4):
* (i) at K = 1, P = 0, adjusting Z never reduces |bias|;
* (ii) with no unmeasured confounding, adjusting Z reduces |bias| in every other cell.

In addition, at W = 0 and P ≥ 1, adjusting Z reduces |bias| at every α in base, E1, E3 and E4. Pre-window history (E2)
breaks this in some rows: W = 5 at P = 5, α = 1; W = 30 at P = 5, α ≥ 0.5 and at P = 30, α = 1.

**[v0.4-final] P1a: what the correspondence does and does not give.**
* In ORACLE and ORACLE−C, S_t is conditioned on at each window step. S_t is a non-collider on every path from A_t
  through the switch timing to post-window S, so conditioning on it blocks that path.
* At α = 0, which is P1a's domain, no unmeasured confounder remains. At α > 0, U remains, including U-paths opened by
  conditioning on past actions.
* This is an identification / measurement correspondence with statement (ii). It does not by itself establish the
  directional bias inequality under the v0.4 DGP, so P1a is theory-motivated.

**[v0.4] P1b: an additional difference from the maps.**
* The theory maps contain constant or AR(1) Gaussian unmeasured confounding.
* In NV and SITE (and partly in the FM arms), the unmeasured confounder is S: a **binary, monotone, time-varying**
  state that switches within or after the window for K < 15.
* The maps do not cover such a confounder. v0.2's P1b used the maps with S folded into an effective α, which assumes a
  confounder that is constant over the post-window steps; that does not hold here.
* P1b is therefore further from the maps than the other families. Like them, it is a theory-motivated prespecified
  hypothesis, and its verdict rules are unchanged.

### 12.2 Families

Each family is a paired comparison of "with C" against "without C".

| family | status | cells | prediction | conditions |
|---|---|---|---|---|
| P1a | **[v0.4-final] theory-motivated prespecified hypothesis** (from statement ii) | α = 0, all cells except K = 1, P = 0 (66 cells) | ORACLE \|bias\| < ORACLE−C | — |
| P1b-SITE | **[v0.4-final] theory-motivated prespecified hypothesis** | W = 0, P ∈ {5, 30}, all K, α, γ (48 cells) | SITE < NV | — |
| P1b-FM | **[v0.4-final] theory-motivated prespecified hypothesis** | the same 48 cells | FM-P < FM-P−C | **[v0.4-final2]** E1 passes on both sets; E3-site passes on both sets; E3-state-retention passes or is not applicable (§5.3) |
| P2-SITE | **[v0.4-final] theory-motivated prespecified hypothesis** (from statement i) | K = 1, P = 0, all W, α, γ (18 cells) | SITE ≥ NV | G-SITE passes |
| P2-FM | **[v0.4-final] theory-motivated prespecified hypothesis** (from statement i) | K = 1, P = 0, α > 0 (12 cells) | FM-P ≥ FM-P−C | G-SITE passes; **[v0.4-final2]** E1 passes on both sets; E3-site passes on both sets; E3-state-retention passes or is not applicable (§5.3) |
| P2-ORACLE | **[v0.4-final] theory-motivated prespecified hypothesis** (from statement i) | K = 1, P = 0, α > 0 (12 cells) | ORACLE ≥ ORACLE−C | G-SITE passes |
| P3 | — | all other cells and comparisons | no directional prediction; reported against the maps | — |

### 12.3 Aggregation rule (fixed)

* **Oriented relative difference** for cell j of family F, with Ψ̄_j the mean truth (positive = as predicted):
  * P1: D_j = (|b_without C| − |b_with C|) / Ψ̄_j;
  * P2: D_j = (|b_with C| − |b_without C|) / Ψ̄_j.
* **Aggregate:** D̄_F = mean_j D_j.
* **[v0.4] Sampling unit.**
  * The 216 cells (and the 24 φ_A cells) are fixed design points, not a sample.
  * The 95 % CI is a percentile bootstrap that resamples the synthetic replicates within each cell, with the same
    indices for both arms of a pair; B = 2,000; seed 20261008.
  * Cells are not resampled.
* **Verdicts:**
  * **SUPPORTED** if the lower bound of D̄_F > 0 and D_j > 0 in ≥ 75 % of the family's cells;
  * **CONTRADICTED** if the upper bound < 0 or D_j > 0 in ≤ 25 % of cells;
  * **INCONCLUSIVE** otherwise.
* **Use in claims:**
  * Headline directional claims come only from family verdicts. Single cells are descriptive. All cells are reported.
  * **[v0.4-final]** A SUPPORTED verdict is reported as "consistent with the theory-motivated direction". A
    CONTRADICTED verdict is reported as "inconsistent with the theory-motivated direction".

## 13. Falsification rules and claim ceilings

* **E1 fails (standardized, 278-case set):** "site-like information in representations" is not established for this
  dataset. FM-vs-FM−C comparisons are reported descriptively only.
* **E2 fails:** "video representations recover the confounding state" is not established. FM-vs-NV comparisons cannot
  be read as confounder recovery.
* **[v0.4-final2] E3-site fails on the 278-case set:** the removal manipulation failed; FM−C arms are not interpreted.
* **[v0.4-final2] E1 and E3-site pass on the 278-case set but fail on the 158-case set:** FM vs FM−C comparisons in the
  causal grid are reported descriptively only, and P1b-FM / P2-FM are not tested.
* **[v0.4-final2] E3-site passes but the MLP probe exceeds the margin:** the claim ceiling is "linear site information removed;
  nonlinear site information remains".
* **[v0.4-final2] E3-site passes:** the wording is "no longer exceeds the prespecified linear site-encoding boundary", never
  "equivalent to chance" or "eliminated".
* **[v0.4-final2] E3-state-retention fails (state destroyed):** FM−C differences are not attributed to site removal
  alone, and FM−C causal arms are not interpreted.
* **[v0.4-final2] E3-state-retention not applicable (E2 primary fails):** the report states that retention of state
  information could not be assessed. FM−C interpretation then rests on E3-site alone (§5.3).
* **G-SITE fails:** C is not instrument-like in the constructed design at K = 1, P = 0. P2-SITE and P2-ORACLE become
  P3, and no amplification claim is made.
* **[v0.4-final2] E1 and E3 (both components, §5.3) pass but P1b-FM and P2-FM are INCONCLUSIVE:** a negative result, "encoded site information did not
  change causal behaviour here".
* **[v0.4-final] Family verdicts:** stated as consistent / inconsistent with the theory-motivated direction (§12). No
  family result is stated as a confirmation of the theory maps.
* **[v0.4-final] Representation wording:** "video-derived representations" with the arm-specific wording of §1. The
  primary arm is not called a temporal video foundation model unless the selected model is temporally contextualized.
* **Native arm differs from standardized:** attributed to acquisition shortcuts (resolution, borders, overlays
  including on-screen time, compression, motion blur), not to image content. The raw frame rate is removed by the grid.
* **[v0.4] REF arm:** the paper-linked Cosmos reference (§4.2). Its comparisons with FM arms are not a fair model
  comparison, it is not a pixel-level replication of K4, and it may retain frame-rate-derived information.
* **[v0.4] FULL arm:** an exchangeability oracle / implementation sanity reference. Its finite-sample bias is reported,
  not assumed zero.
* **[v0.4] All claims** describe a deliberately constructed orthogonal benchmark (§1, §7.2).

## 14. Execution order

1. Commit this protocol alone (freeze) and record the hash.
2. Code lock:
   * code for preprocessing, extraction, PCA / LEACE, the DGP, the SDR estimator, the probes and the seeds;
   * **[v0.4-final]** record the exact code commit of the in-house SDR implementation;
   * a dry run on fully synthetic placeholder features (no DS203 frames);
   * **[v0.4]** the estimator gate (§9) and the compute-budget projection (§10.4). STOP if either fails;
   * G-SITE (§5.4) computed from the design;
   * commit.
3. Apply the §4.1 ranking and tie-breaks to the §4.1.5 eligible lists.
   * **[v0.4-final]** In rank order, run the synthetic-input GPU memory feasibility test (§4.1.4 rule 4) and the
     extraction compute projection (§10.4), with no DS203 frame.
   * Take the top-ranked feasible checkpoint per arm, and record the selected checkpoints and the test results.
4. Extraction:
   * 4a. run the mask check (§3.1 step 3) and record r;
   * 4b. extract representations;
   * commit manifests and hashes.
5. **[v0.4]** Run E1–E3 on the 278-case and 158-case sets, commit, and apply §13 before any causal run.
6. **[v0.4-final]** Confirm that the SDR commit recorded at step 2 is the one in use, then run the causal grid (and
   §10.3) and commit.
7. Report.

## 15. Not authorized

* Any change to §§2–13 after freeze, except by a committed amendment stating its reason.
* Re-running extraction or the grid with different settings after seeing results.
* Adding arms, models or cells after step 5.
* **[v0.4]** Using any 158-case E1 / E3 result for model selection.

## 16. Limitations (stated in advance)

* One procedure type; one content variable with a single switch per case.
* Synthetic actions with no feedback into the video; a linear DGP.
* The reference model's training data are undisclosed.
* Centre 2 shares a hospital with DSAD (models trained on DSAD are ineligible).
* **[v0.4] Constructed design:** site–state orthogonality is constructed (§7.2), not natural.
* **Eligible set:**
  * it holds 158 of 278 cases;
  * early-switch cases are excluded, which under-represents centre 5 (52 of 117);
  * state variation is local to the switch (window starts within ±75 s of it);
  * **[v0.4]** S is 1 for every case from relative step 15 onward, so post-window S varies across cases only when
    K < 15;
  * centre 2 has only 13 single-file eligible cases.
* **[v0.4] Model pool:**
  * **[v0.4-final3]** all eligible primary models are frame-level, and all eligible secondary models are clip-level
    (§4.1.5);
  * the primary arm is therefore a "domain-specific surgical/endoscopic visual representation derived from video
    frames", not a temporal video model (§1);
  * a strict reading of the overlap rule would leave no model in either arm. The two-level rule (§4.1.1) was fixed
    with that knowledge.
* **[v0.4-final2] Temporal sampling:** "Clip-level models receive frames from the 2-fps grid. This may differ from
  each model's documented temporal sampling; it standardizes acquisition across centres at the cost of temporal
  fidelity."
* **[v0.4-final2] Site-associated, not acquisition-specific:** E1 and LEACE measure and remove site-associated
  information, of which real acquisition heterogeneity is one source. They do not isolate acquisition information
  (§1).
* **[v0.4-final3] Generic web origin (rule B):** for the fixed benchmarks relied on by eligible candidates in
  pretraining or initialisation (ImageNet, Kinetics-400, Kinetics-600, UCF-101, SSv2), "incidental web-origin exposure cannot be excluded at the level of every source image."

## 17. Investigator actions before freeze / before step 4

* **[v0.4] Settled:** D-1, D-3, D-4, D-5 and D-2 (replaced by §4.1).
* **[v0.4-final] Settled:** D-6 (two-level overlap rule, §4.1.1) and the tie-breaks (§4.1.4).
* **[v0.4-final] Before freeze:** the final freeze GO / NO-GO follows direct review of this text.
* **Before step 4:** accept the NVIDIA Open Model License for the Cosmos tokenizer weights on Hugging Face (only the
  investigator may accept terms).

## 18. [v0.4-final] Version history

* **v0.1:** switch-centred windows. Audit: HOLD, because S was identical across cases within each K cell.
* **v0.2:**
  * switch-relative site-stratified offsets (dbd5984), ORACLE−C arm, E2 / E3 / G-SITE prespecified;
  * predictions: P1a "theory analogue", P1b and P2 tied directly to the maps.
  * Final audit: HOLD (post-window S statement false; D-2; causal-set E1/E3).
* **v0.4 (consolidated draft):**
  * D-1 to D-5 applied;
  * P1b relabelled "prespecified empirical hypothesis (theory-motivated)" because the maps do not cover a binary,
    time-varying unmeasured state;
  * P1a and P2 labelled "theory-derived";
  * D-6 left open (content vs strict reading);
  * two drafted tie-breaks.
* **v0.4-final (this text):**
  * **all families relabelled "theory-motivated prespecified hypotheses"**. Reason: the theory maps establish direction
    under their own DGPs; the v0.4 DGP differs (four-level discrete site with permuted loadings, binary switching
    state, a different post-window state process, finite-sample nuisance estimation), and no transport proof is
    given;
  * D-6 replaced by the two-level overlap rule;
  * arm claim wording added;
  * GPU memory feasibility test (≤ 20.0 GB peak reserved) and extraction compute fallback (7 days);
  * tie-breaks replaced by the four-step order;
  * the SDR code commit recorded at code lock;
  * eligibility facts committed separately (6245f25).
* **v0.4-final2 (freeze repairs; one line per change):**
  * A1: per-W sensitivity offsets added. The 158 primary offsets are kept; the 46 / 43 missing cases are drawn by the
    same procedure and seed per set (adf9160). Text in §7.2, §10.3, header, §0.
  * A2: clip-level temporal-sampling sentence added to §4.2 and §16.
  * B1: Rule-B override for named, versioned, pre-release benchmarks added to §4.1.1, with a determinism sentence
    keeping the clinical / site-provenance clause for surgical web corpora.
  * B1 consequence: eligibility re-checked (e81ab5f, 166 / 166 quotes). Basel V-JEPA ViT-L becomes eligible (primary,
    clip-level) via HowTo100M in VideoMix2M. §4.1.5, §1 and §16 statements that all eligible primary models are
    frame-level were updated; ineligibility reasons were re-labelled by clause.
  * B2: the §1 question now reads "site-associated information … video-derived representations", and the §1 / §16
    note says E1 / LEACE do not isolate acquisition information. No other unqualified "acquisition information"
    occurred. "Acquisition shortcuts" (§13) and the acquisition-preprocessing headings (§3) are kept.
  * B3: "real foundation-model representations" → "real pretrained video-derived representations" (§1), with the
    foundation-model naming condition.
  * B4: E3 split into E3-site (278 and 158) and E3-state-retention (158 only; not applicable if E2 primary fails).
    §5, §5.3, §12.2 conditions and §13 use the new names.
* **v0.4-final3 (content-boundedness rule):**
  * "v0.4-final2 applied a broad override (a named, versioned release finalized before DS203 counts as NO). Its
    consequence made Basel V-JEPA eligible through HowTo100M. The investigator first accepted this consequence; the
    audit did not. The override was replaced by the content-boundedness rule because release date alone does not meet
    the protocol's pre-existing evidentiary standard, under which NO requires affirmative level-1–3 support excluding
    DS203 and known DS203-centre clinical material. The replacement is a general rule, not a list of named benchmarks,
    and it was adopted with knowledge that it makes Basel V-JEPA ineligible."
  * Item 1: Rule B replaced verbatim in §4.1.1. The v0.4-final2 override and its determinism sentence were removed, and
    the benchmark names in the old Rule-B bullet were removed from the rule.
  * Item 2: eligibility recomputed (a437225, 174 / 174 quotes; per-source boundedness for every candidate). Basel
    V-JEPA becomes ineligible (HowTo100M Health category); secondary lists unchanged. §4.1.5 updated.
  * Item 3: the §1 and §16 frame-level statements were restored. The §16 generic-web list now holds only the
    benchmarks relied on by eligible candidates.
  * Item 4: per-W G-SITE added: W = 0 0.0037, W = 5 0.0045 (b987010). Interpretation rule in §10.3, pointer in §5.4.
  * The `…_accept_B1` task was never received or applied, so there was nothing to reverse.
  * EndoSSL initialization check: EndoSSL laparoscopy ViT-B / ViT-L (and ViT-S) became ineligible, because their
    initialization is not stated in any level-1–3 source. The initialization of every other eligible model is
    affirmatively stated (quotes in d3563e7). Eligibility facts recommitted: ca04c5b, plus d3563e7 for a stale CV-VAE
    note. §4.1.5, §0 and the header hashes were updated.
  * Editing correction: the §0 sentence "The eligible lists are therefore known…", which a v0.4-final2 edit had
    attached to the per-W offsets bullet, was returned to the eligibility bullet.
  * Loss-network clause added to §4.1.1. Auxiliary networks of every eligible model were checked against level-1–3
    sources (14 / 14 quotes verified). They are either loss-only (frozen LPIPS, or discriminators and LARP's
    training-time AR prior trained jointly on the same data), or EMA copies of the model itself (DINO teacher, MoCo
    momentum encoder), whose lineage is the already-assessed initialization. None initializes or is distilled into
    the released model from an external source. No eligibility change; eligibility facts in force remain d3563e7.
