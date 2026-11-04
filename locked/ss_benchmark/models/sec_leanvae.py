# --------------------------------------------------------------------------------------------------------------------
# Licence and upstream attribution (added 2026-11-04 for the public release; comment only — the code is unchanged).
# Original code in this file: Copyright (c) 2026 Hisashi Nakano, MIT License (LICENSE at the repository root).
# Upstream: LeanVAE (arXiv:2503.14325). Code: github.com/westlake-repl/LeanVAE @ 62f7c7d5 — MIT License,
#   Copyright (c) 2025 westlake-repl; loaded at run time from third_party/ (not included).
#   Weights: huggingface.co/Yumic/LeanVAE @ 4585e461 — MIT; not included.
# Embedded upstream material: architecture values and short quotations of the LeanVAE code, README,
#   scripts and paper (SPEC sources).
# Upstream material is NOT covered by the MIT licence; it remains under its upstream licence and is reproduced
# with attribution for non-commercial research use. Details: NOTICE, THIRD_PARTY_NOTICES.md, LICENSES/.
# --------------------------------------------------------------------------------------------------------------------
"""LeanVAE adapter (secondary arm; generic causal video VAE, westlake-repl/LeanVAE @ 62f7c7d).

Config (released checkpoints Yumic/LeanVAE LeanVAE-dim16.ckpt / LeanVAE-dim4.ckpt; README "LeanVAE-16ch" / "-4ch"):
    LeanVAE(embedding_dim=512, l_dim=128, h_dim=384, sep_num_layer=2, fusion_num_layer=4, ista_iter_num=2,
            ista_layer_num=2, latent_dim=16 | 4), patch (2, 4, 4) after a one-level Haar DWT -> 4x8x8 compression.
    Values: argparse defaults in third_party/LeanVAE/LeanVAE/models/autoencoder.py and scripts/train.sh; paper §4.2
    (2/2/4 ResNAF layers, two-layer NAF, K = 2 ISTA iterations); latent_dim from the README ("d=4 or 16") and the file
    names. The checkpoints store their own "args" (load_from_checkpoint); they are not downloaded, so the stored args
    are checked against this config only when weights are loaded. 39.8M parameters for both (README table); this
    build: 39,785,940 (16ch) / 39,767,496 (4ch), whole VAE.
Clip length: 17 frames (paper §5.1 training clips; Table 1 DAVIS 17×256×256; train.sh / leanvae_inference.py
    --sequence_length 17). Variable length is accepted under the constraint L = 4n + 1 (README; autoencoder.py assert).
Input size: 256×256 (paper Table 1 caption, the evaluation behind the README PSNR / LPIPS of both checkpoints;
    training used 96×128 … 352×288). H, W must be multiples of 8.
Normalisation: x / 255 − 0.5 -> [−0.5, 0.5] (leanvae_inference.py, regular_size = 2; data.py VideoNorm).
Representation (N11): LeanVAE.encode(x) without tiling = ISTA sensing projection Φp of the encoder feature p, which is
    exactly the posterior mean in LeanVAE.forward() (z_mean = latent_bottleneck.sample(p); std_layer gives the logvar;
    no quant_conv exists). Shape (B, d, 5, 32, 32) for 17×256×256; mean over latent time, flattened to d·32·32
    (16,384 for 16ch, 4,096 for 4ch). No sampling.
Source copies: data_audit/lead/fm_sources/secondary/leanvae_*, data_audit/lead/fm_sources/eligibility_v04/leanvae_*,
    third_party/LeanVAE/*.
Import: the LeanVAE package is loaded under a private alias whose __path__ is <repo>/third_party/LeanVAE/LeanVAE, so
    neither LeanVAE/__init__.py (pytorch_lightning, decord via data.py) nor LeanVAE/modules/__init__.py (LPIPS / VGG)
    is executed; backbones.py has an unused `from beartype import beartype`, stubbed for the import if absent.
Random init: ISTA.phi / ISTA.Q are drawn from numpy's global RNG in the third-party code (other weights: torch RNG).
"""
import argparse
import importlib
import sys
import types
from pathlib import Path

import torch

_REPO = Path(__file__).resolve().parents[2]
_TP = _REPO / "third_party" / "LeanVAE"
_ALIAS = "_leanvae_tp"

# released architecture (autoencoder.py add_model_specific_args defaults == scripts/train.sh flags)
_CONFIG = dict(embedding_dim=512, l_dim=128, h_dim=384, sep_num_layer=2, fusion_num_layer=4,
               ista_iter_num=2, ista_layer_num=2)
_INPUT = (256, 256)
_L = 17

SPEC = dict(
    name="LeanVAE",
    arm="secondary",
    kind="clip",
    input_size=_INPUT,
    clip_length=_L,
    clip_length_constraint="L = 4n + 1 (L % 4 == 1); H, W multiples of 8; latent (d, (L-1)/4 + 1, H/8, W/8)",
    representation="posterior mean mu = Phi p (LeanVAE.encode, no tiling; == z_mean of LeanVAE.forward), "
                   "(B, d, 5, 32, 32) at 17x256x256, mean over latent time, flattened -> (B, d*32*32)",
    normalisation="x / 255 - 0.5 -> [-0.5, 0.5] (leanvae_inference.py regular_size = 2)",
    config=dict(_CONFIG, patch_size=(2, 4, 4), compression=(4, 8, 8), use_tile_inference=False),
    default_variant="16ch",
    variants={
        "16ch": dict(latent_dim=16, out_dim=16 * 32 * 32, checkpoint="Yumic/LeanVAE/LeanVAE-dim16.ckpt",
                     ckpt_bytes=159199850,
                     ckpt_sha256="1c1d65765e44ced040a43a0bb7084a936e5b3862d21df4a9fd13580508cd1ecb"),
        "4ch": dict(latent_dim=4, out_dim=4 * 32 * 32, checkpoint="Yumic/LeanVAE/LeanVAE-dim4.ckpt",
                    ckpt_bytes=159125886,
                    ckpt_sha256="cd54560ca3e713e8aee69fddca21519a19d6bf9a46ee380e523e12f716aa5963"),
    },
    sources=[
        # clip length
        dict(quote="For each training step, we randomly sample 17 consecutive frames from a video.",
             copy="data_audit/lead/fm_sources/secondary/leanvae_arxiv_2503.14325_fulltext.txt", level=1),
        dict(quote="parser.add_argument('--sequence_length', type=int, default=17)",
             copy="third_party/LeanVAE/leanvae_inference.py", level=3),
        dict(quote="--sequence_length 17 \\",
             copy="data_audit/lead/fm_sources/eligibility_v04/leanvae_train_sh.txt", level=3),
        dict(quote="video, video_rec = model.inference(video) ## Frame count must be 4n+1 (e.g., 5, 9, 13, 17...)",
             copy="data_audit/lead/fm_sources/secondary/leanvae_github_README.md", level=2),
        dict(quote='assert x.shape[2] % 4 == 1, f"Expected frame_num % 4 == 1, but got {x.shape[2] % 4}"',
             copy="third_party/LeanVAE/LeanVAE/models/autoencoder.py", level=3),
        # input size
        dict(quote="The input resolution in DAVIS is 17×256×256, with the encoded latent of the size 5x32x32.",
             copy="data_audit/lead/fm_sources/secondary/leanvae_arxiv_2503.14325_fulltext.txt", level=1),
        dict(quote="The videos are resized and cropped to resolutions ranging from  96 × 128 96\\times 128  to  "
                   "352 × 288 352\\times 288 , with their original aspect ratios preserved.",
             copy="data_audit/lead/fm_sources/secondary/leanvae_arxiv_2503.14325_fulltext.txt", level=1),
        # variants / checkpoints
        dict(quote="| **LeanVAE-4ch**  | 26.04  | 0.0899  | 39.8M    | 0.203    |",
             copy="data_audit/lead/fm_sources/secondary/leanvae_github_README.md", level=2),
        dict(quote="| **LeanVAE-16ch** | 30.15  | 0.0461  | 39.8M    | 0.203    |",
             copy="data_audit/lead/fm_sources/secondary/leanvae_github_README.md", level=2),
        dict(quote="latent = model.encode(video)  # (B, C, T+1, H, W) → (B, d, T/4+1, H/8, W/8), where d=4 or 16",
             copy="data_audit/lead/fm_sources/secondary/leanvae_github_README.md", level=2),
        dict(quote='"rfilename": "LeanVAE-dim16.ckpt",',
             copy="data_audit/lead/fm_sources/secondary/leanvae_Yumic__LeanVAE_hfapi.json", level=2),
        dict(quote='"rfilename": "LeanVAE-dim4.ckpt",',
             copy="data_audit/lead/fm_sources/secondary/leanvae_Yumic__LeanVAE_hfapi.json", level=2),
        dict(quote='python leanvae_inference.py --ckpt_path "./ckpts/LeanVAE-dim16.ckpt"',
             copy="third_party/LeanVAE/scripts/inference.sh", level=3),
        # architecture config
        dict(quote='parser.add_argument("--embedding_dim", type=int, default=512, help="Dimension of the embedding '
                   'space.")',
             copy="third_party/LeanVAE/LeanVAE/models/autoencoder.py", level=3),
        dict(quote="--latent_dim 4 \\ --ista_iter_num 2 \\ --ista_layer_num 2 \\ --l_dim 128 \\ --h_dim 384 \\ "
                   "--sep_num_layer 2 \\ --fusion_num_layer 4 \\",
             copy="data_audit/lead/fm_sources/eligibility_v04/leanvae_train_sh.txt", level=3),
        dict(quote="by stacking 2, 2, and 4 layers of ResNAF, respectively.",
             copy="data_audit/lead/fm_sources/secondary/leanvae_arxiv_2503.14325_fulltext.txt", level=1),
        dict(quote="The number of iterations K is set to 2.",
             copy="data_audit/lead/fm_sources/secondary/leanvae_arxiv_2503.14325_fulltext.txt", level=1),
        dict(quote="All evaluated models are causal and have a video compression ratio of 4 × 8 × 8.",
             copy="data_audit/lead/fm_sources/secondary/leanvae_arxiv_2503.14325_fulltext.txt", level=1),
        # normalisation
        dict(quote="regular_size = 2 # input range is [-0.5, 0.5] if regular_size = 2, [-1, 1] if regular_size = 1",
             copy="third_party/LeanVAE/leanvae_inference.py", level=3),
        dict(quote="video = video /( 127.5 * regular_size) - (1.0 / regular_size)",
             copy="third_party/LeanVAE/leanvae_inference.py", level=3),
        dict(quote="Returns BCTHW videos in the range [-0.5, 0.5]",
             copy="third_party/LeanVAE/LeanVAE/data.py", level=3),
        # representation
        dict(quote="z = self.latent_bottleneck.sample(p)",
             copy="third_party/LeanVAE/LeanVAE/models/autoencoder.py", level=3),
        dict(quote="posterior = DiagonalGaussianDistribution(parameters=(z_mean, z_std))",
             copy="third_party/LeanVAE/LeanVAE/models/autoencoder.py", level=3),
        dict(quote="self.mean, self.logvar = parameters",
             copy="third_party/LeanVAE/LeanVAE/modules/vae.py", level=3),
    ],
    third_party=dict(repo="westlake-repl/LeanVAE", commit="62f7c7d560b83f408b5041f799d70317d9b37713"),
)


def _subpackage(name, path):
    m = types.ModuleType(name)
    m.__path__ = [str(path)]
    sys.modules[name] = m
    return m


def _leanvae_class():
    key = _ALIAS + ".models.autoencoder"
    if key in sys.modules:
        return sys.modules[key].LeanVAE
    pkg = _TP / "LeanVAE"
    _subpackage(_ALIAS, pkg)
    _subpackage(_ALIAS + ".utils", pkg / "utils")
    _subpackage(_ALIAS + ".models", pkg / "models")
    mods = _subpackage(_ALIAS + ".modules", pkg / "modules")
    stub = "beartype" not in sys.modules and importlib.util.find_spec("beartype") is None
    if stub:
        bt = types.ModuleType("beartype")
        bt.beartype = lambda f: f
        sys.modules["beartype"] = bt
    try:
        bb = importlib.import_module(_ALIAS + ".modules.backbones")
    finally:
        if stub:
            del sys.modules["beartype"]
    vae = importlib.import_module(_ALIAS + ".modules.vae")
    for k in ("Encoder_Arch", "Decoder_Arch", "ISTA"):
        setattr(mods, k, getattr(bb, k))
    mods.DiagonalGaussianDistribution = vae.DiagonalGaussianDistribution
    return importlib.import_module(key).LeanVAE


def _args(variant):
    return argparse.Namespace(**_CONFIG, latent_dim=SPEC["variants"][variant]["latent_dim"],
                              use_tile_inference=False, chunksize_enc=9, chunksize_dec=5)


def _load(model, path, args):
    ckpt = torch.load(path, map_location="cpu", weights_only=True)
    if isinstance(ckpt, dict) and "args" in ckpt:          # released checkpoint: {"args", "state_dict"}
        keys = list(_CONFIG) + ["latent_dim"]
        bad = {k: (ckpt["args"].get(k), getattr(args, k)) for k in keys if ckpt["args"].get(k) != getattr(args, k)}
        if bad:
            raise ValueError(f"checkpoint args differ from the coded config (stored, coded): {bad}")
    sd = ckpt.get("state_dict", ckpt) if isinstance(ckpt, dict) else ckpt
    if any(k.startswith("autoencoder.") for k in sd):       # Lightning training checkpoint (pl_ckpt_inference.py)
        sd = {k[len("autoencoder."):]: v for k, v in sd.items() if k.startswith("autoencoder.")}
    missing, unexpected = model.load_state_dict(sd, strict=False)
    unexpected = [k for k in unexpected if not k.startswith(("dwt.", "idwt."))]   # non-persistent Haar buffers
    if missing or unexpected:
        raise RuntimeError(f"state dict mismatch: missing={missing}, unexpected={unexpected}")


def build(weights=None, device="cpu", dtype=torch.float32, variant=SPEC["default_variant"]):
    if variant not in SPEC["variants"]:
        raise ValueError(f"variant must be one of {sorted(SPEC['variants'])}")
    args = _args(variant)
    model = _leanvae_class()(args)
    if weights is not None:
        _load(model, weights, args)
    model.set_tile_inference(False)
    return model.to(device=device, dtype=dtype).eval().requires_grad_(False)


@torch.inference_mode()
def encode(model, x):
    """x: (B, L, 3, H, W) in [0, 255], L = 4n + 1, H, W multiples of 8 -> (B, d * H/8 * W/8)."""
    B, L, C, H, W = x.shape
    if L % 4 != 1 or H % 8 or W % 8 or C != 3:
        raise ValueError(f"expected (B, 4n+1, 3, 8h, 8w), got {tuple(x.shape)}")
    p = next(model.parameters())
    x = x.to(device=p.device, dtype=torch.float32).permute(0, 2, 1, 3, 4) / 255.0 - 0.5   # (B, 3, L, H, W)
    mu = model.encode(x.to(p.dtype).contiguous())                                         # (B, d, T', h, w)
    return mu.mean(dim=2).flatten(1)
