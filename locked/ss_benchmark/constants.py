"""Fixed constants of the SS protocol DS203 (frozen 4c86dc5) and the code-lock implementation choices.

Protocol seeds:
  20261005  window offsets (already drawn: dbd5984, adf9160; not redrawn here)
  20261006  case-level 5-fold split of the 278-case set, stratified by site (§2)
  20261007  replicate SeedSequence, spawned by (cell index, replicate index) (§10.2)
  20261008  bootstrap: case bootstrap for §5 checks; paired replicate bootstrap for §12.3

Code-lock seed (not a protocol seed): 99990001, root of every PLACEHOLDER design, feature, replicate draw and learner
seed used by the estimator gate, the compute projection, the fast tests and the dry runs.
"""

# ---- protocol seeds -------------------------------------------------------------------------------------------------
SEED_OFFSETS = 20261005
SEED_FOLDS = 20261006
SEED_REPLICATES = 20261007
SEED_BOOTSTRAP = 20261008
PROTOCOL_SEEDS = (SEED_OFFSETS, SEED_FOLDS, SEED_REPLICATES, SEED_BOOTSTRAP)

# ---- code-lock PLACEHOLDER seed -------------------------------------------------------------------------------------
SEED_PLACEHOLDER = 99990001
assert SEED_PLACEHOLDER not in PROTOCOL_SEEDS
PLACEHOLDER_LABEL = "PLACEHOLDER"

# ---- data (§2) ------------------------------------------------------------------------------------------------------
N_FOLDS = 5
STEP_SECONDS = 5.0
GRID_FPS = 2.0                       # §3.1 step 1: grid times 0.5 k s
GRID_FRAMES_PER_STEP = 10            # step t uses grid frames 10t ... 10t+9
REPRESENTATION_CENTRES = (2, 3, 4, 5)
N_REPRESENTATION_CASES = 278
N_PRIMARY_CASES = 158
ANALYSIS_REGION = (-30, 44)          # window-relative steps of the analysis region (§5.1, §5.2, §7.2)

# ---- preprocessing (§3) ---------------------------------------------------------------------------------------------
MASK_RADIUS = 0.45                   # × side (§3.1 step 3a); may only be replaced by the §3.1 mechanical check
MASK_CHECK_THRESHOLD = 0.25          # fraction of the central median (ρ ≤ 0.1)
MASK_CHECK_CENTRAL_RHO = 0.1
MASK_CHECK_SHRINK = 0.98
MASK_CHECK_SIZE = 256
MASK_CHECK_EVERY = 60                # every 60th grid frame
BOTTOM_BAND = 0.03                   # lowest 3 % of the square (§3.1 step 3b)
NEAR_UNIFORM_SIZE = 256
NEAR_UNIFORM_LUMA_SD = 4.0           # BT.601 luma SD on the 8-bit scale (§3.1 step 4)

# ---- representations (§4.2, §4.3) -----------------------------------------------------------------------------------
N_PCS = 64
COSMOS_MAX_FRAMES = 121
COSMOS_SIZE = 320
COSMOS_LATENT_SHAPE = (16, 40, 40)

# ---- DGP (§6) -------------------------------------------------------------------------------------------------------
MU = 1.0
TAU = 1.0
KAPPA = 1.0
LAMBDA = 1.0
SITE_LOADINGS = tuple(v / 5 ** 0.5 for v in (-3.0, -1.0, 1.0, 3.0))
DELTA = 1.05                         # multiplicative MTP d(a) = δ a (§7.1)

# ---- grid (§10) -----------------------------------------------------------------------------------------------------
GRID_K = (1, 2, 5, 15)
GRID_P = (0, 5, 30)
GRID_W = (0, 5, 30)
GRID_ALPHA = (0.0, 0.5, 1.0)
GRID_GAMMA = (0.5, 1.0)
PHI_PRIMARY = 0.0
PHI_SENSITIVITY = 0.5
PHI_K = (1, 5)
PHI_P = (0, 5)
PHI_W = (5,)
M_REPLICATES = 200
BUDGET_DAYS = 7.0
N_BOOTSTRAP = 2000

# ---- estimator gate (§9) --------------------------------------------------------------------------------------------
GATE_K = (1, 5, 15)
GATE_P = (0, 5)
GATE_W = 5
GATE_ALPHA = 0.5
GATE_GAMMA = 1.0
GATE_COVERAGE = (0.90, 0.99)
GATE_REL_BIAS = 0.05

# ---- nuisance learners (§9) and probes (§5) -------------------------------------------------------------------------
PENALTY_GRID_NUISANCE = (1e-3, 1e-2, 1e-1, 1e0, 1e1, 1e2, 1e3)       # ridge (§9); also L2 logistic ratios (note N3)
PENALTY_GRID_E2 = (1e-4, 1e-3, 1e-2, 1e-1, 1e0, 1e1, 1e2)            # E2 L2 logistic (§5.2); also linear site probe (N9)
INNER_FOLDS = 5
MLP_NUISANCE = dict(hidden=128, lr=1e-3, weight_decay=1e-4, max_epochs=300, patience=20, val_fraction=0.2)
MLP_PROBE = dict(hidden=256, lr=1e-3, weight_decay=1e-4, max_epochs=200, patience=20, val_fraction=0.2)
Z_975 = 1.959963984540054

# ---- checks (§5) ----------------------------------------------------------------------------------------------------
E1_BA = 0.50
E1_LOWER = 0.35
E2_DELTA_AUC = 0.05
E3_UPPER = 0.35
E3_RETENTION = 0.50
GSITE_MAX_ETA2 = 0.01

IMPLEMENTATION_NOTES = {
    "N1": "'2-layer MLP' (§9) and '2 layers, 256 hidden units' (§5.3) are implemented as two linear layers with one "
          "ReLU hidden layer (128 resp. 256 units).",
    "N2": "MLP mini-batch size: min(200, n_fit) (the scikit-learn 'auto' convention); weight decay as an L2 term added "
          "to the gradient of every parameter (torch.optim.Adam semantics); PyTorch nn.Linear default initialisation; "
          "early stopping on the inner-validation loss (MSE, binary or multinomial log-loss), patience counted in "
          "epochs without a strict improvement, best-epoch parameters restored.",
    "N3": "L2 logistic density-ratio classifier: penalty by inner 5-fold CV (log-loss) over the §9 ridge grid "
          "{1e-3..1e3} ('the same two learner families').",
    "N4": "Learner choice (§9): each learner is a procedure (ridge incl. its inner penalty CV; MLP incl. its early "
          "stopping); its loss is estimated by 5-fold CV within the outer training fold (case-level), the lower loss "
          "wins (ties: the linear learner), and the winner is refitted on the whole outer training fold.",
    "N5": "Ridge / L2-logistic penalty parameterisation: sum of squared errors + λ||b||² resp. sum of log-losses + "
          "(λ/2)||b||² (scikit-learn alpha / C = 1/λ conventions), on z-scored features, intercept unpenalised.",
    "N6": "SDR: Díaz et al. (2021) sequential regression V_t = m_t(δA_t, H_t) + r_t (V_{t+1} − m_t(A_t, H_t)), "
          "V_K = Y; density ratios r_t = exp(classifier logit) from the stacked (A_t, Λ=0) / (δA_t, Λ=1) "
          "classification; no trimming; contrast IF = V_0 − Y; SE = sd(IF, ddof=1)/sqrt(n); 95 % Wald interval.",
    "N7": "Cross-fitting uses the fixed §2 fold labels of the analysis set; training-fold pseudo-outcomes are computed "
          "in-sample from the training-fold fits (as in lmtp).",
    "N8": "Seeds: replicate SeedSequence(root, spawn_key=(cell, rep)); named streams are children with an extra spawn "
          "key int.from_bytes(name.encode('ascii'), 'big'), e.g. 'c-permutation'.",
    "N9": "Linear site probe (E1, E3-site): multinomial L2 logistic regression with the E2 learner settings (penalty "
          "by inner 5-fold CV over {1e-4..1e2}, log-loss).",
    "N10": "E1 lower bound = 2.5th percentile of the stratified case bootstrap (two-sided 95 %); E3-site upper bound "
           "= 95th percentile (one-sided 95 %, as stated); E2 CI = 2.5th / 97.5th percentiles.",
    "N11": "Secondary-model representation (not fixed in §4.2): KL-VAEs (WF-VAE-L, LeanVAE): the encoder posterior "
           "mean; VQ tokenizers (OmniTokenizer, LARP): the codebook-lookup input (after the authors' pre-quantiser "
           "projection and L2 normalisation; nothing quantised); averaged over latent time (LARP has none: holistic "
           "query tokens) and flattened, as for the Cosmos reference arm; VideoMAE: mean of the last hidden states.",
    "N12": "Compute-budget reduction (b) 'ridge only' is applied as linear learners only (ridge outcome regressions "
           "and L2-logistic density ratios).",
}
