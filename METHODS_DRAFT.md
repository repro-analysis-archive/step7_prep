# Methods (draft)

*Drafted 2026-10-09 from the frozen protocol (`docs/SS_PROTOCOL_DS203.md`, commit `4c86dc5`) and the repository records named in each section. That draft did not depend on step-5, step-6 or step-7 outcomes.*

*Updated 2026-10-20, after all results were known, from the facts of the evaluator record `SS_DS203_PROJECT_RECORD_for_evaluator_20261020_v5.md` (SHA-256 `c1d8d651…dc27684`; committed copy `step7_prep/evidence/`, `84d8e2d`) only: r and all commit hashes filled; the executed order; the bootstrap's resampling of the truths; operational times; a new section "Exploratory analyses (outside the frozen protocol)"; the deviation register. No number was changed. Post-result presentation choices are recorded in `POST_RESULT_PRESENTATION.md`.*

*`[REF: …]` marks a literature reference for the investigator to supply. `[TO FILL: …]` marks an item the investigator must still supply.*

## Study design and protocol freeze

* **Design.** This is a semi-synthetic causal benchmark: real clinical video, real between-site heterogeneity, and real pretrained video-derived representations, combined with synthetic actions and outcomes whose causal truth is known exactly [REF: semi-synthetic benchmarks for causal inference].
* **Question.** How do bias and interval validity of a sequential causal analysis change when site-associated information encoded in video-derived representations is included in, or linearly removed from, the adjustment set? The change is studied as a function of:
  * intervention duration;
  * post-window actions;
  * pre-window history;
  * unmeasured-confounding strength.
* **Scope.** The benchmark is a deliberately constructed orthogonal design. It does not estimate any causal effect in the source dataset.
* **Freeze.** The analysis protocol was frozen before any video frame was decoded for analysis, any representation was extracted, or any synthetic action, outcome or estimate was generated.
  * Freeze commit: `4c86dc5f7df357a09311198f34e141972fe0175a`, 2026-10-05 12:22:23 +0900. The protocol file alone; SHA-256 `cd7e1402…d748926`. Recorded in `decisions/SS_PROTOCOL_FREEZE_RECORD.md` (freeze record commit `8f63e43`).
* **Review.** Until 2026-10-07, stages were reviewed in written audit documents from a review process separate from the implementation sessions [TO FILL: review nature]. From 2026-10-07 the investigator is the sole approver.
  * Directional predictions are prespecified, theory-motivated hypotheses [REF: theory maps for site adjustment in sequential causal analysis]. They are reported as "consistent / inconsistent with the theory-motivated direction".
* **Execution order.** The protocol fixes the order (§14):
  1. freeze;
  2. code lock;
  3. model selection;
  4. extraction;
  5. pre-causal checks and §13;
  6. causal grid;
  7. aggregation and report.

  Section 15 forbids changes after the freeze, except by a committed amendment, and forbids re-running extraction or the grid with different settings after seeing results.
* **Executed order** (repository records; confirmed in `step7_prep/CONFIRM_ITEMS_20261019.md`, commit `fa2b8c7`):
  1. protocol freeze `4c86dc5` (2026-10-05 12:22 +0900), freeze record `8f63e43`;
  2. SDR implementation `af56777`, final code lock `98cba1e`; adapter correction `ad8833a` and model reselection `ba73820` after the lock;
  3. step 4–5 runner `9e1aa71`; step-4 record `8d4c61a`;
  4. step-5 record `0ebf2cf` → §13 record `0667430` → step-6 runner `7adaf13`, ordered by ancestry (all three committed at 14:26:41 on 2026-10-12);
  5. step 6 started at 14:26:42 with no shards present. The first completed unit is dated 14:27:03.80 (file modification time), 22.8 s after `0ebf2cf`. There was one attempt only. Step 6 completed on 2026-10-18 at 20:20:34 (last unit 20:17:38; 73,200 units, 18 workers);
  6. step-7 record `2880d73`, committed automatically by the step-7 runner, which does not display results before committing.

## Data

* **Source.** DS203 is the Appendix300 dataset of laparoscopic appendectomy videos from five surgical centres in Germany: four public hospitals and one academic paediatric surgery department [REF: Appendix300 dataset descriptor, Sci Data 2026]. It was released on OPARA on 2026-04-29 [REF: OPARA repository record].
  * The dataset files (11 parts, including the split full-length video archive; 1,692.5 GB) were downloaded and verified against the host's MD5 checksums (`data_audit/DS203_DOWNLOAD_COMPLETE.md`, `dba9c06`).
* **Videos.** Re-encoded H.264 (High profile) MP4, constant frame rate (container facts, `2012acd`):
  * centre 2: 1920 × 1080 at 25 fps (and eight 3840 × 2160 files);
  * centre 3: 3840 × 2160 at 25 fps;
  * centres 4–5: 1920 × 1080 at 50 fps.
* **Cases.** All 278 full-length cases of centres 2–5. That is 279 counted cases minus Center3_020, whose annotated timestamp exceeds its video length.
  * Centre 1 was excluded because most of its recordings are 5-min clips.
  * Together the 278 cases contain about 145.6 h of video (104,662 five-second steps).
* **Time axis.**
  * Multi-file cases were concatenated in version order on a physical time axis, with no gap assumed.
  * Time was discretised into 5-s steps, t covering [5t, 5t + 5) s.
  * The binary content state S_t indicates that the annotated appendix-visible time T_i has passed by the end of step t; the switch step is s_i = max(⌈T_i/5⌉ − 1, 0).
  * The site factor C is the centre (four levels).
* **Staging.** For extraction, the 350 archive members of the 278 cases (1.344 TB) were copied out of the stored, split ZIP archive byte for byte, each checked against the archive's CRC-32, without decoding or re-encoding (`decisions/STEP4_5_RUNNER.md`).

## Window construction and analysis sets

* **Window rule** (§7.2, fixed from case metadata before any frame was decoded; `dbd5984`):
  * Eligible cases satisfy s_i − 45 ≥ 0 and s_i + 60 ≤ n_i, with n_i = ⌊duration_i/5⌋.
  * Each eligible case receives a fixed offset O_i ∈ {−15, …, 15}, drawn by a within-site seeded permutation (seed 20261005; `ss_window_offsets.csv`, SHA-256 `4794e139…ea6c3`).
  * The window starts at w_i = s_i + O_i. Window steps w_i … w_i + K − 1 are preceded by W pre-window steps and followed by P post-window steps.
  * S at window-relative step j is therefore 1{O_i + j ≥ 0}. It is constant across cases from j = 15 onward, and post-window S varies across cases only when K < 15.
* **Why this rule.** Candidate rules were evaluated before any decoding. The final rule satisfies two prespecified requirements: within-step state variation and minimal site–state association (max V(C, S_j) = 0.053 over window-relative steps −30 … 44; `dbd5984`).
  * A switch-centred rule gave no between-case state variation.
  * A fixed procedure-time anchor gave V = 0.25–0.32.
  * Uniform eligible-window sampling gave too little state variation.

| set | cases | centres 2 / 3 / 4 / 5 | use |
|---|---:|---|---|
| representation set | 278 | all full-length cases | PCA / LEACE fitting, E1, E3-site |
| primary causal set | 158 | 28 / 34 / 44 / 52 | causal grid, E2, causal-set E1 / E3 |
| per-W set, W = 0 | 204 | 37 / 40 / 57 / 70 | sensitivity (§10.3) |
| per-W set, W = 5 | 201 | 37 / 40 / 56 / 68 | sensitivity (§10.3) |
| single-file set | 123 | 13 / 34 / 44 / 32 | sensitivity (§10.3) |

* **Per-centre counts.** From the committed offset files: `ss_window_offsets.csv` (`dbd5984`; single-file = `n_files` = 1) and `ss_window_offsets_perW.csv` (`adf9160`). The per-W G-SITE record (`b987010`) confirms the set sizes 158 / 204 / 201.
* **Exclusions.** 120 of the 278 cases are excluded from the primary set (21 / 7 / 27 / 65 by centre), mainly for early switches.
* **Per-W sets.** They keep the 158 primary offsets and receive offsets for their additional cases by the same rule and seed (`ss_window_offsets_perW.csv`, `adf9160`).
* **Folds.** Case-level 5-fold folds, stratified by site (seed 20261006), were defined once on the 278 cases and restricted to each analysis set.

## Preprocessing

* **Grid.** A fixed physical-time grid of 2 frames per second: at each grid time 0.5k s, the first decoded frame with presentation time ≥ the grid time. No re-encoding and no interpolation. Step t uses grid frames 10t … 10t + 9.
  * Frames were decoded with ffmpeg 4.4.2 to RGB24 [REF: FFmpeg].
* **Standardized acquisition (primary):**
  * centre crop to a square of the shorter side;
  * bilinear antialiased resize to the model input;
  * a common mask: a circle of radius r × side plus the lowest 3 % of the square, set to black before model normalisation.
  * r = 0.45 unless a mechanical check of the per-centre mean-frame radial profile (§3.1, §14 step 4a) gives a smaller visible radius; the only alternative permitted is r = 0.98 × min_c ρ_c.
  * Value used: **r = 0.45** (step-4 record `8d4c61a`, `results/step4/mask_check.json`; `run_meta.json` `mask_check_valid` = true; runner log "mask check valid (r = 0.45 stands)", preserved in `evidence/step4_5_progress_log_lines_43_57-63_234.txt`).
    * ρ_c = 0.5625 for centre 2 and 0.703125 for centres 3, 4 and 5 (the last profile point).
    * min_c ρ_c = 0.5625 ≥ 0.45, so the fallback was not used.
    * The per-centre profiles are in Supplementary Figure S4 and Table S4.
  * Near-uniform frames (BT.601 luma SD < 4.0 over the unmasked disc at 256 × 256) were kept and flagged.
* **Native acquisition (sensitivity).** The same grid frames, resized only. These frames retain acquisition cues: resolution, borders, overlays (including on-screen elapsed time at centre 5), compression and motion blur.

## Representation models and their selection

* **Eligibility** (§4.1), determined before freeze from level-1–3 sources (paper, official model card, documented pretraining configuration; `d3563e7`):
  * **Two-level overlap rule:** every training source of the released weights and of their initialisation must be documented as excluding DS203, its constituent datasets and known same-hospital clinical sources. Generic-web origin is excluded only for named, versioned benchmarks with a bounded content scope (Rule B), disclosed as a limitation.
  * **Three mutually exclusive classes:**
    * primary: medical / endoscopic representation-learning encoders;
    * secondary: generic reconstructive or generative video models;
    * surgical-domain generative models: ineligible for both.
* **Ranking and tie-breaks.** Within each class the rule ranks first by clip-level before frame-level (primary) or video VAE / tokenizer before masked autoencoder (secondary); then by most recent release, then by lowest documented compute. Four mechanical tie-breaks follow:
  1. an authors' level-1 recommendation;
  2. protocol-relevant FLOPs;
  3. measured synthetic-input peak GPU memory;
  4. lexical identifier.
* **Feasibility.** A synthetic-input GPU memory test (peak reserved ≤ 20.0 GB, bf16, batch 1) and an extraction-time projection (≤ 7 days) were applied in rank order without any DS203 frame (§14 step 3; `decisions/MODEL_SELECTION_RECORD.md`).
* **Selected:**
  * **Primary:** SurgeNetCholec, a CAFormer-S18 pretrained on surgical video [REF: SurgeNet]; checkpoint `CHOLEC_checkpoint_epoch0050_teacher.pth`, TimJaspersTue/SurgeNetModels @ `cc21f4a1`.
    * Frame-level, 224 × 224, ImageNet normalisation; the pooled 512-d feature, averaged over each step's ten grid frames.
    * The same model on native frames forms the native arm.
  * **Secondary:** LeanVAE, 4-channel checkpoint `LeanVAE-dim4.ckpt`, Yumic/LeanVAE @ `4585e461` [REF: LeanVAE].
    * Clip-level: 17 grid frames ending at the step's last grid frame, 256 × 256.
    * The posterior mean (4 × 32 × 32), averaged over latent time: 4,096 values.
    * Selected over the 16-channel checkpoint by tie-break 2 (115.970 versus 116.032 GFLOPs).
  * **Reference** (not ranked; Decision 005): the NVIDIA Cosmos tokenizer, nvidia/Cosmos-1.0-Tokenizer-CV8x8x8 @ `5110dbb3` [REF: Cosmos tokenizer], the representation used by [REF: Nakamura et al. 2026, video-based causal inference].
    * Native frames of each step (at most 121, uniformly selected), standardized crop and mask, resized to 320 × 320, scaled to [−1, 1].
    * The decoder input `post_quant_conv(latent)`, averaged over latent time: 16 × 40 × 40 = 25,600 values.
    * Our adapter (diffusers `AutoencoderKLCosmos`) matched the official Cosmos tokenizer code (NVIDIA/Cosmos-Tokenizer @ `3584ae75`) to within 3.7 × 10⁻⁷ (float32, fixed synthetic input; `decisions/STEP4_5_RUNNER.md` §3).
* **CODELOCK_CORRECTION_001** (`ad8833a`; `decisions/CODELOCK_CORRECTION_001_SURGENET_ADAPTER.md`):
  * The code-lock adapter for the SurgeNet checkpoints built timm's CAFormer-S18, whose token mixers and MLPs use StarReLU. The released checkpoints were trained with SurgeNet's own model code, which uses plain ReLU.
  * The mismatch could not be detected at code lock, which forbade downloading weights. It surfaced at step 3 as a failed strict load.
  * The adapter was corrected to import the official model definition unmodified (TimJaspers0801/SurgeNet @ `54831cfa`, `metaformer.py`) and to load with `strict=True`. Equivalence with the official code was exact (maximum absolute difference 0.0).
  * The primary arm was then reselected from rank 1 under the unchanged ranking (`ba73820`). The estimator, gate and all analysis code remained byte-identical to the code lock.
* **Extraction runs.** Run on an RTX 4500 Ada GPU in bf16 with deterministic GPU settings:
  * `cudnn.deterministic`, no cuDNN benchmarking, deterministic algorithms where supported;
  * on fixed synthetic inputs these gave bit-identical outputs for all three models, at a 3–6.4 % throughput cost.
* **Committed outputs.** Every representation file's SHA-256 is in the step-4 record (`8d4c61a`). Weight-file SHA-256 values are in `MODEL_SELECTION_RECORD.md` and `STEP4_5_RUNNER.md`.

## PCA and linear site removal

* **PCA.** Each representation was reduced to 64 principal components, fitted fold-wise on all steps of the training-fold cases of the 278-case set and applied to the held-out fold.
  * Exact covariance eigendecomposition for d ≤ 8,192; otherwise seeded randomized SVD with 64 oversamples and 7 power iterations [REF: randomized SVD].
  * Component signs were fixed.
* **LEACE.** Site information was removed by the closed-form LEACE eraser [REF: LEACE, Belrose et al. 2023], fitted on the same training-fold steps with the one-hot centre as the concept. It is an oblique projection that removes all linearly decodable site information from the fitting data.
* **Arm pairs.** This yields site-retained (FM) and site-removed (FM−C) versions of the primary, secondary and reference representations. The native arm has no removed version.
* **Wording.** Representations after removal are described as "linearly site-removed", never as site-invariant.

## Semi-synthetic data-generating process and estimand

* **DGP.** For case i and trajectory step t (pre-window, window and post-window), with U_i ~ N(0, 1) synthetic and unseen in the video:

  A_it = μ + γ·c(C_i) + κ·S_it + α·U_i + φ_A·A_i,t−1 + ε_it,

  Y_i = τ·Σ_{window ∪ post} A_it + λ·Σ_{window ∪ post} S_it + β·U_i + ε_Y,

  * ε ~ N(0, 1); μ = τ = κ = λ = 1; β = α; φ_A = 0 (primary) or 0.5 (sensitivity).
  * Site loadings c(C) ∈ (−3, −1, 1, 3)/√5 are assigned to the four centres by a permutation drawn per replicate, so results concern a generic site-identity signal.
  * C affects only A. S affects A and Y; U affects A and Y.
* **Estimand.** The multiplicative modified treatment policy d(a) = 1.05·a applied at every window step [REF: modified treatment policies], with pre- and post-window steps natural; the estimand is Ψ(δ) − Ψ(1).
  * Its truth was computed exactly for each replicate: in closed form for φ_A = 0, by exact recursion for φ_A = 0.5.
  * A truth-only design check found no cell with |truth| < 0.025 (`results/codelock_gate/`).

## Adjustment arms

At each window step, nuisances condition on the history of past synthetic actions and on the arm's step-t covariates. Past representations and past S are not included.

| arm | step-t covariates |
|---|---|
| NV | H_t |
| SITE | H_t + C |
| FM-P, FM-P−C | H_t + primary representation (site-retained / site-removed) |
| FM-S, FM-S−C | H_t + secondary representation |
| REF, REF−C | H_t + reference representation |
| FM-P-nat | H_t + primary representation, native acquisition |
| ORACLE−C, ORACLE | H_t + S_t; H_t + S_t + C |
| FULL | H_t + S_t + C + U (exchangeability oracle and implementation sanity reference) |

## Estimator

* **SDR.** A cross-fitted sequentially doubly robust (SDR) estimator for the multiplicative MTP [REF: Díaz et al. 2021, nonparametric causal effects based on longitudinal modified treatment policies], implemented in this repository. Exact implementation commit: `af56777e0f52b5c350dd7ba557d55b2394cbd4bf` (`decisions/CODELOCK_FINAL_RECORD.md`).
  * **Density ratios:** probabilistic classification of observed versus shifted actions, r = exp(logit), with no trimming.
  * **Backward sequential pseudo-outcome regression** over the K window steps.
  * **Cross-fitting:** the fixed folds of the analysis set.
  * **Inference:** the influence function V₀ − Y, giving the standard error and a 95 % Wald interval.
* **Nuisance learners.** Each nuisance is fitted by one of two learners, chosen by lower 5-fold cross-validated loss within the training fold (ties to the linear learner):
  * **Outcome regressions:** ridge with an inner-CV penalty over {10⁻³ … 10³}, or a 2-layer MLP (128 units, ReLU, Adam 10⁻³, weight decay 10⁻⁴, ≤ 300 epochs, early stopping with patience 20 on a 20 % inner split).
  * **Density ratios:** L2 logistic regression or the same MLP.
  * The implementation choices the protocol leaves open (N1–N12) are listed in `docs/CODELOCK_NOTES.md`.
* **Code-lock estimator gate** (§9; PLACEHOLDER features, FULL arm, M = 200, six cells K ∈ {1, 5, 15} × P ∈ {0, 5}, W = 5, α = 0.5, γ = 1):
  * coverage 0.905–0.950 and |bias| / truth ≤ 0.03 (maximum 0.0294) in every cell (criteria: coverage within [0.90, 0.99], |bias| below 5 % of the true contrast);
  * every replicate finite.

## Design grid, replication and seeds

* **Grid.**
  * The primary grid crosses K ∈ {1, 2, 5, 15}, P ∈ {0, 5, 30}, W ∈ {0, 5, 30}, α ∈ {0, 0.5, 1} and γ ∈ {0.5, 1}: 216 cells.
  * 24 further cells set φ_A = 0.5: K ∈ {1, 5}, P ∈ {0, 5}, W = 5, all α and γ.
* **Replication.** M = 200 synthetic replicates per cell: new U, ε, ε_Y and site-loading permutation; the same videos and representations.
  * Replicate seeds: NumPy `SeedSequence(20261007, spawn_key = (cell, replicate))` [REF: NumPy SeedSequence].
  * All arms of a replicate share its draws, so arm comparisons are paired.
* **Sensitivity runs** (§10.3; reported separately, never entering family verdicts):
  * the single-file set (P1b and P2 cells; NV, SITE, FM-P, FM-P−C);
  * the W = 0 and W = 5 sets (NV, SITE, FM-P, FM-P−C, ORACLE, ORACLE−C).
* **Size.** 73,200 (set, cell, replicate) units and 700,800 SDR fits.
* **Compute budget and workers.**
  * The code-lock projection (all 20 logical CPUs busy) was 5.99 days, below the 7-day budget, so none of the frozen reductions was applied.
  * The grid ran with 18 worker processes on logical CPUs 0–17, with one BLAS / OpenMP thread per process, as at code lock.
  * Worker count does not change results: the code-lock determinism test gave byte-identical outputs with 3 and 5 workers, and a PLACEHOLDER test of the grid driver gave byte-identical shards with 1 and 2 workers.

## Pre-causal checks and G-SITE

* **Shared settings.**
  * Site probes run per step; the case-level prediction is the mean predicted probability over the case's steps.
  * Balanced accuracy (BA) is computed over cases, with stratified case-bootstrap CIs (2,000 resamples, seed 20261008).
  * The 158-case results were never used for model selection.

| check | data | criterion |
|---|---|---|
| E1 (site encoding) | 278 cases (all steps) and the 158-case analysis region; linear multinomial probe | BA ≥ 0.50 with lower 95 % bound > 0.35 (chance 0.25) |
| E2 (state recovery beyond time) | 158-case analysis region | ΔAUC for S_t of elapsed-time natural spline (4 df) plus 64 PCs over the spline alone ≥ 0.05, with its case-cluster bootstrap CI excluding 0 (L2 logistic, inner 5-fold CV) |
| E3-site (removal success) | after LEACE, on both sets | linear-probe BA one-sided 95 % upper bound ≤ 0.35 |
| E3-state retention | 158-case set | post-removal ΔAUC ≥ 50 % of the pre-removal value; not applicable if E2 fails |

* **MLP probe.** A fixed 2-layer MLP probe (256 units) is reported before and after removal. If E3-site passes but the MLP bound exceeds 0.35, the ceiling "linear site information removed; nonlinear site information remains" applies.
* **Reporting-only analyses:** E2 on all 278 videos, with a normalised-time reference, and with past synthetic actions.
* **G-SITE.** A design check computed at code lock from centre and offset only: η² of S at the window start on C ≤ 0.01.
  * Result: primary 0.0014, W = 0 0.0037, W = 5 0.0045.

## Metrics, family verdicts and claim ceilings

* **Metrics (§11),** per set, cell and arm:
  * |bias|; relative bias (bias / mean truth);
  * 95 % interval coverage;
  * secondary metrics: bias / Monte-Carlo SD, RMSE, CI width, effective sample size and density-ratio range, support-failure rate.
* **Families (§12.2).** Six prespecified theory-motivated families compare "with C" against "without C" on fixed cell subsets:

| family | cells | comparison |
|---|---|---|
| P1a | α = 0 except K = 1, P = 0; 66 cells | ORACLE vs ORACLE−C |
| P1b-SITE | W = 0, P ∈ {5, 30}; 48 cells | SITE vs NV |
| P1b-FM | the same 48 cells | FM-P vs FM-P−C |
| P2-SITE | K = 1, P = 0; 18 cells | SITE vs NV |
| P2-FM | K = 1, P = 0, α > 0; 12 cells | FM-P vs FM-P−C |
| P2-ORACLE | K = 1, P = 0, α > 0; 12 cells | ORACLE vs ORACLE−C |

  All other cells and comparisons are P3, with no directional prediction.
* **Aggregation (§12.3).**
  * The oriented relative difference per cell (positive = as predicted) is averaged over the family's cells.
  * A percentile bootstrap resamples replicates within cells (B = 2,000; seed 20261008); cells are fixed design points.
  * The same resampling indices are used for both arms of a pair and for the truths, so each cell's mean truth is recomputed on each resample. Section 12.3 does not state this. It is how the locked aggregation code (`ss_benchmark/grid.py`: `_d_values`, `family_verdict`) implements the bootstrap, confirmed against the repository (`CONFIRM_ITEMS_20261019.md`).
  * **SUPPORTED** if the lower bound is > 0 and D_j > 0 in ≥ 75 % of cells. **CONTRADICTED** if the upper bound is < 0 or D_j > 0 in ≤ 25 %. **INCONCLUSIVE** otherwise.
  * P1b-FM and P2-FM require E1 and E3-site to pass on both sets and E3-state retention to pass or be not applicable. The P2 families require G-SITE. A family whose conditions fail is reported as P3.
* **Claim ceilings (§13)** were applied mechanically:
  * from the committed step-5 record, before the causal grid (`scripts/apply_section13.py`; §13 record `0667430`);
  * the two rules that need family verdicts, at step 7.

## Execution, deviations and operations

* **Runners.** Steps 4–7 were run by orchestration-only runners that call the locked analysis code from a `git archive` snapshot of the launch commit and add no analysis logic. Each runner:
  * refuses to start unless HEAD equals the expected commit and the working tree is clean;
  * checkpoints each unit;
  * logs resource use, but no estimate.
* **Step 4–5 runner** (`9e1aa71`): staging, the mask check, extraction in two lanes, near-uniform flags, and an automatic records-only commit of the step-4 record before step 5 could start. Settings: 12 workers on 12 of 14 physical cores, 6 threads per process, a memory cap of 80 % of RAM, at most 2 concurrent disk readers.
* **Operational events** (`decisions/OPERATIONS_LOG_STEP4_5.md`; log excerpts preserved unchanged in `step7_prep/evidence/`, commit `84d8e2d`, with the commands and SHA-256 in `evidence/README.md`):
  * **Memory-guard stop.** On 2026-10-06 at 16:35:27 +0900 the step 4–5 runner's memory guard stopped the run with about 80 GiB of RAM available (strikes 16:34:57–16:35:27; `evidence/step4_5_progress_log_lines_43_57-63_234.txt`).
    * With that much memory available, only the guard's swap-out criterion (more than 64 MiB swapped out in 60 s) can have fired, so the stop was a false positive.
    * The kernel log shows no OOM line between 16:00 and 17:30 (`evidence/kernel_20261006_1600-1730.txt`, `evidence/kernel_20261006_1600-1730_oom_search.txt`).
  * **Swap settings.** `vm.swappiness` was set from 60 to 10, and swap was disabled and re-enabled, at 17:28:14–17:28:17 (system journal, sudo entries from TTY pts/4; `evidence/journal_20261006_1720-1735_sudo_swap.txt`). The operations log records the swappiness change without a time and does not record the swap off/on.
  * **Resume.** The run was resumed with the same launch commit at 17:28:48 (orchestrator process start, `decisions/OPERATIONS_LOG_STEP4_5.md`; runner preflight 17:28:49). The interrupted mask check, a single unit, restarted from the first case (mask-check start 14:20:15 and again 17:28:52; `evidence/step4_5_progress_log_lines_43_57-63_234.txt`); completed units were not recomputed.
  * **Watchdog.** A watchdog (`~/ops/runner_watchdog_v1.sh`, pid 4004380, log `~/ops/runner_watchdog.log`) was started on 2026-10-07 at 09:37:15 +0900 to relaunch the runner after a memory-pressure stop.
    * It never relaunched the runner: its log has no relaunch line and ends on 2026-10-12 at 14:28:06 with "watchdog exits without action … state complete" (`evidence/runner_watchdog.log`).
    * A check at about 08:15 on 2026-10-07, before it was started, had found no watchdog (`step7_prep/OPERATIONS_LOG_ADDENDUM.md`).
* **dts warnings.** ffmpeg emitted "non monotonically increasing dts" warnings. A separate quality check on 21 staged files found:
  * **No frame loss.** Four full decodes delivered exactly the expected frame counts.
  * **Cause:** duplicated source presentation timestamps (21 events in 21 files); the source decoding timestamps were monotonic.
  * **Effect:** 4 of 74,630 grid frames were shifted by one frame (about 56 per pass when scaled to the 278 cases); no frame crossed a step boundary.
  * No change was made.
* **Chaining to step 6.** The chain script (`/srv/ss_step6_prep/chain_5_to_6.sh`, authorised by the investigator) was launched on 2026-10-07 at 09:36 +0900 (pid 4003618, base conda Python), not on the Friday initially planned. It waited for the step 4–5 runner, reading only its state file. After the runner completed, it made three commits, each verified for parent and exact file set:
  1. the step-5 record;
  2. the §13 record, from the mechanical application;
  3. the step-6 runner and decision records.

  The chain commits are `0ebf2cf` (step-5 record), `0667430` (§13 record) and `7adaf13` (step-6 runner), all at 14:26:41 on 2026-10-12, in this order by ancestry. The chain then launched step 6, which started at 14:26:42 with no shards present. The basis is that, under the frozen protocol, step 6's computation does not depend on step-5 outcomes, and §13 is mechanical (`decisions/STEP6_RUNNER.md` §1).
* **Step-6 runner.**
  * Before starting it confirms that `ss_benchmark/` is byte-identical to the SDR commit; the only exception is the extraction adapter of CODELOCK_CORRECTION_001, which the grid does not import.
  * It runs the locked grid driver without its final aggregation; the aggregation is step 7.
  * Its memory guard uses available memory and pressure-stall information rather than swap-out.
* **Sensitivity-set ceilings in the report layer.** The locked aggregation judges the single-file and per-W sensitivity families with the primary-set E1 / E3 conditions. Without changing locked code, the report keeps that verdict (labelled "locked aggregation") and states next to it the §13 claim ceiling obtained from each set's own step-5 E1–E3 ("protocol-consistent ceiling"). Step 5 computes no set-specific E1–E3 for the per-W sets, so their FM comparisons are reported descriptively only. Families that the locked code computes outside the §10.3 scope (e.g. W0:P1a) appear only in an exploratory section, never as verdicts.
* **Presentation.**
  * Main-text figures show the slice W = 30, α = 0.5, γ = 1 (primary set); supplementary heatmaps show every grid cell. This was fixed on 2026-10-09 before any step-6 result existed (`step7_prep/PRESENTATION_DECISIONS.md`).
  * Added on 2026-10-20, after the results were known: Supplementary Figure S4 / Table S4 (mask check) and the exploratory Tables X, X-E3, B, B-sens and Figures X, B (`step7_prep/SUPPLEMENT_20261020/`). These presentation choices are recorded separately in `step7_prep/POST_RESULT_PRESENTATION.md`.
* **Exploratory analyses.** X1 / X2 and B lie outside the frozen protocol; see the next section.
* **Deviation and operations register** (evaluator record v5 §11; the source and weight retrievals are carried from v2 §11 and documented in the decision records named):
  * **Source and weight retrievals.**
    1. Initial third-party code retrieval delivered bundled evaluation-tool weights (I3D, LPIPS / VGG); they were never loaded and were deleted (`CODELOCK_INCIDENT_001`). Hard-limit incident, documented.
    2. VideoMAE model source, authorised (`CODELOCK_AUTH_002`).
    3. VideoMAE `datasets.py` and `transforms.py`, authorised (`CODELOCK_AUTH_003`).
    4. SurgeNet official model source, authorised for CODELOCK_CORRECTION_001.
    5. VISSL raw source for the SelfSupSurg equivalence check: beyond the SurgeNet-only retrieval wording; source only, no weights; recorded in the correction record. Minor documented deviation.
    6. NVIDIA Cosmos-Tokenizer source at `3584ae75` for the reference equivalence check, authorised in the step 4–5 preparation.
    7. Weights of the selected models and the Cosmos reference, downloaded at step 3 / step 4–5 preparation with SHA-256 recorded.
  * **Post-lock changes:**
    * CODELOCK_CORRECTION_001, an adapter defect correction under the frozen source-priority rule;
    * the orchestration runners, the thread and worker settings, and the operational events above, which do not change analysis code or settings fixed by the protocol.
  * **Reporting and documentation:**
    * the per-centre mask-check profiles required by §3.1 were not in the first results report; they are now reported (Supplementary Figure S4, Table S4);
    * the swap off/on at 17:28:14–17:28:17 on 2026-10-06 is not in the operations log, which also gives the swappiness change without a time (system-journal excerpt preserved in `evidence/journal_20261006_1720-1735_sudo_swap.txt`);
    * the bootstrap's resampling of the truths is not stated in §12.3 (see Aggregation);
    * the Δ orientation and bootstrap seeds of the exploratory analyses X1 / X2 differ from §12.3 (next section).

## Exploratory analyses (outside the frozen protocol)

*Added 2026-10-20 from the evaluator record v5 §8–9. Neither analysis produces a verdict, alters a family verdict or §13, or replaces any protocol result.*

### X1 / X2

* **Plan and registration.** Plan `b6d1cf7` (2026-10-13 08:21 +0900); OSF https://osf.io/5c627, embargoed until 2028-10-13.
* **Disclosure.** The plan was written after the step-5 E3-site failure on the 158-case set was known and while step 6 was running, before access to step-6 results.
* **Analyses.**
  * X1: the LEACE eraser refitted on the 158-case analysis region; the FM−C arms (FM-P−C, FM-S−C, REF−C) rerun on these features.
  * X2: the original LEACE features with linear-only nuisance learners.
  * Both are compared, cell by cell and paired on replicates, with the step-6 arms k−C, FM-k and NV on the 71 cells of the P1b-FM group, the P2-FM group and the main-figure slice.
* **Run.** Launch `015595d`. Control C0 reproduced the step-6 records exactly, and the 28,400 truths are identical to step 6. Records `1c8e628` (2026-10-19 20:18).
* **Δ.**
  * Per cell, Δ = (|bias_X| − |bias_step-6|) / mean truth, which has the same form as D (§12.3) and uses the same per-cell mean truth as step 6 (1,278 / 1,278 rows).
  * The paired bootstrap follows the §12.3 scheme (B = 2,000; cells fixed).
  * Differences from §12.3:
    * Δ is always (X arm − step-6 arm), not oriented by family; negative Δ means the X arm has the smaller |bias|;
    * the bootstrap seed names differ from step 6;
    * per-cell intervals are added.
* **Ceiling** (v5 §8): exploratory; no verdict; cannot restore P1b-FM / P2-FM; nonlinear site information remains after X1; X2 changes do not show that erasure caused a difference.
* **Reported in** Tables X and X-E3 and Supplementary Figure X (`SUPPLEMENT_20261020/`).

### B

* **Plan and registration.** Plan `e1c27b4` (2026-10-19 10:00 +0900); OSF https://osf.io/g9ymw, embargoed until 2028-10-13.
* **Disclosure.** The plan was written after the step-7 verdicts were generated in the same working session. B uses no step-6 / step-7 or X quantity.
* **Design** (plan `e1c27b4`).
  * Evaluation sets: S1, the 278 cases with all steps; S2, the 158 primary cases with all steps; S3, the 158 cases in the analysis region.
  * (a) Transport: the S1-fitted E3 probe evaluated on each set. (b) Within-set refit. The two analyses are reported separately and never pooled.
  * Linear and MLP probes; case-level balanced accuracy with case-bootstrap intervals.
  * Judgement: whether the one-sided 95 % upper bound exceeds 0.35.
  * Sensitivity: equal-size subsampling (28 cases per centre, 75 steps per case, 20 draws); descriptive point estimates, no bootstrap, no judgement.
* **Run.** Launch `c7354ed`. Control C-B0 reproduced the step-5 E3 numbers for all keys. Records `458341f` (2026-10-20 00:29).
* **Ceiling** (v5 §9): B locates where the judgement changes; it does not identify why. The subsampling changes centre balance, case set and steps per case at the same time. *Hypothesis (not tested):* linear guardedness is exact only on the fitting population, so within-set refits on some subsets (S3 and the equal-size subsamples, but not S2, whose within-set linear BA is 0.231 / 0.239 / 0.208 for P / S / REF, upper bounds 0.251–0.282) recover some linear site information; whether window selection adds to this is not determined by B.
* **Reported in** Tables B and B-sens and Supplementary Figure B (`SUPPLEMENT_20261020/`).

## Software and hardware

* **Causal code:** Python 3.11.14, NumPy 2.3.5, SciPy 1.17.0, pandas 3.0.1, scikit-learn 1.6.1 [REF: NumPy; SciPy; pandas; scikit-learn].
* **Extraction:** PyTorch 2.5.1 (CUDA 12.1), torchvision 0.20.1, timm 1.0.15, transformers 4.46.3, diffusers 0.35.1, huggingface_hub 0.36.2, safetensors 0.8.0, einops 0.8.2 [REF: PyTorch; timm; diffusers], and ffmpeg 4.4.2.
* **Hardware and OS:** Ubuntu 22.04.4 LTS (Linux 5.15); Intel Core i5-14600K (14 cores, 20 threads); 125.6 GiB RAM; NVIDIA RTX 4500 Ada Generation (24 GB; driver 555.52.04); videos and representations on an external 10 TB rotational disk.

## Provenance

| step | commit / record |
|---|---|
| protocol freeze (§14 step 1) | `4c86dc5`; freeze record `8f63e43` |
| SDR implementation / code lock (§14 step 2) | `af56777` / `98cba1e` (`CODELOCK_FINAL_RECORD.md`) |
| model selection (§14 step 3) | `cb78391`, superseded after CODELOCK_CORRECTION_001 (`ad8833a`) by `ba73820` |
| step 4–5 runner | `9e1aa71` (`STEP4_5_RUNNER.md`) |
| step-4 record (automatic) | `8d4c61a` |
| step-5 record, §13 record, step-6 runner (chain) | `0ebf2cf`, `0667430`, `7adaf13` |
| step-7 record | `2880d73` |
| repository confirmation of the evaluator-record items | `fa2b8c7` (step7_prep, `CONFIRM_ITEMS_20261019.md`) |
| exploratory X1 / X2: plan / launch / records | `b6d1cf7` / `015595d` / `1c8e628` (`/srv/ss_exploratory`) |
| exploratory B: plan / launch / records | `e1c27b4` / `c7354ed` / `458341f` (`/srv/ss_exploratory_B`) |

**Data and code availability.** [TO FILL: dataset access statement for Appendix300 / OPARA licence; repository availability.]
