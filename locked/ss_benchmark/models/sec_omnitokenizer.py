# --------------------------------------------------------------------------------------------------------------------
# Licence and upstream attribution (added 2026-11-04 for the public release; comment only — the code is unchanged).
# Original code in this file: Copyright (c) 2026 Hisashi Nakano, MIT License (LICENSE at the repository root).
# Upstream: OmniTokenizer (arXiv:2406.09399). Code: github.com/FoundationVision/OmniTokenizer @ 701b6190 —
#   MIT License, Copyright (c) 2024 FoundationVision; executed at run time from third_party/ (not included).
#   Weights: huggingface.co/Daniel0724/OmniTokenizer @ 9ebde216 (no licence declared); not included.
# Embedded upstream material: ARGS (values of scripts/recons/eval_video.sh and argparse defaults) and
#   short quotations of the OmniTokenizer code, scripts, README and paper (SPEC sources).
# Upstream material is NOT covered by the MIT licence; it remains under its upstream licence and is reproduced
# with attribution for non-commercial research use. Details: NOTICE, THIRD_PARTY_NOTICES.md, LICENSES/.
# --------------------------------------------------------------------------------------------------------------------
"""OmniTokenizer (ImageNet + K600), secondary arm, clip-level: VQVAE `imagenet_k600.ckpt` (variant "vq", default) and
VAE `imagenet_k600_vae.ckpt` (variant "vae"; README "| VAE | ImageNet + K600 | 0.78 | 13.02 |"; the authors'
eval_video.sh block for it is identical to the VQ block plus --use_vae). Both checkpoints share the encoder; the VAE's
pre_vq_conv maps 512 -> 2 x 8 channels (VQGAN.__init__ use_vae branch) and the representation is the posterior mean =
the first 8 channels (modules/vae.py DiagonalGaussianDistribution: `self.mean, self.logvar = torch.chunk(parameters,
2, dim=1)`; the authors' encode() samples, which is not done here), averaged over latent time: D = 8 x 32 x 32 = 8192.
The VQ description follows.

Code: third_party/OmniTokenizer (FoundationVision/OmniTokenizer @ 701b619003b3e941e769269c7626dbf111d0377e).
Checkpoint (not downloaded here): HF Daniel0724/OmniTokenizer imagenet_k600.ckpt, 742,455,697 B,
sha256 0a1d9f86...c01c (data_audit/lead/fm_sources/secondary/omnitok_Daniel0724__OmniTokenizer_hfapi.json).

Hyperparameters = the authors' evaluation command for imagenet_k600.ckpt
(scripts/recons/eval_video.sh; saved copy data_audit/lead/fm_sources/secondary/omnitok_github_scripts_recons_eval_video.sh.txt):
    --patch_embed 'linear' --patch_size 8 --temporal_patch_size 4 --spatial_depth 4 --temporal_depth 4
    --embedding_dim 512 --enc_block "ttww" --twod_window_size 8 --causal_in_temporal_transformer --causal_in_peg
    --dim_head 64 --heads 8 --spatial_pos "rope" --n_codes 8192 --codebook_dim 8 --l2_code
    --resolution 256 --sequence_length 17 --norm_type batch            (no --use_vae, no --use_external_codebook)
  remaining encoder arguments are argparse defaults (OmniTokenizer/omnitokenizer.py add_model_specific_args):
    attn_dropout 0, ff_dropout 0, ff_mult 4, defer_temporal_pool / defer_spatial_pool off, initialize_vit off;
    image_channels 3 (OmniTokenizer/data.py).
  Paper (arXiv 2406.09399, Implementation Details): "4 window attention-based spatial layers (window size = 8) and 4
  causal attention-based temporal layers. The hidden dimension is 512 and the latent dimension is 8". The released
  scripts use enc_block "ttww" (2 plain + 2 window spatial layers); the script is followed.
Clip length L = 17 (eval_video.sh --sequence_length 17; paper: "video sequence length being 17 frames").
Input size 256 x 256 (eval_video.sh --resolution 256).
Normalisation: RGB x / 255 - 0.5 -> [-0.5, 0.5], layout (B, 3, T, H, W): DecordVideoDataset "Returns BCTHW videos in
  the range [-0.5, 0.5]" via VideoNorm(mean=[0.5]*3, std=[1.0]*3) (OmniTokenizer/data.py, OmniTokenizer/video_utils.py).
  VideoNorm divides by 255 only if max > 1; here the division is unconditional (inputs are always on the 0-255 scale).
Representation (implementation note N11, pre-quantiser latent, never quantised): the tensor VQGAN.encode hands to the
  codebook (omnitokenizer.py: `h = self.pre_vq_conv(self.encoder(x, is_image))`, then with l2_code
  `h = F.normalize(h, p=2, dim=1)`, then `self.codebook(h)`), i.e. the l2-normalised 8-d factorised code after the
  512 -> 8 pre_vq_conv projection. Shape (B, 8, 5, 32, 32) for a 17 x 256 x 256 clip (first frame alone + 16 frames
  / temporal patch 4; 256 / patch 8); averaged over latent time T' = 5 and flattened (c, h, w): D = 8 * 32 * 32 = 8192.

Only the encoder + pre_vq_conv are built. OmniTokenizer_VQGAN is a pytorch_lightning module that also constructs the
decoder, discriminators and LPIPS (VGG weights), and the package __init__ imports the data pipeline; instead the
authors' unmodified source of OmniTokenizer_Encoder (omnitokenizer.py), Normalize (base.py) and modules/attention.py
is executed from the third_party files by path (no sys.path entry, no package import). attention.py's unused
`fairscale.nn.checkpoint_wrapper` import is skipped; `beartype` (runtime type checks on PEG / Transformer forward)
is used if installed, else replaced by an identity decorator. pre_vq_conv replicates VQGAN.__init__ (non-VAE branch)
so state-dict keys match the Lightning checkpoint ("encoder.*", "pre_vq_conv.*"). Attention runs on the
scaled_dot_product_attention path (torch >= 2.1), as in the authors' code; the README's "w/o
scaled_dot_product_attention" note concerns imagenet_only.ckpt only.
"""
import ast
import hashlib
import math
import pickle
from functools import lru_cache
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.utils.checkpoint
from einops import pack, rearrange, repeat, unpack
from einops.layers.torch import Rearrange
from timm.layers import trunc_normal_

_OT = Path(__file__).resolve().parents[2] / "third_party" / "OmniTokenizer"
_S = "data_audit/lead/fm_sources/secondary/"
_E = "data_audit/lead/fm_sources/eligibility_v04/"
_TP = "third_party/OmniTokenizer/"

ARGS = dict(  # eval_video.sh (imagenet_k600.ckpt block); the rest argparse defaults
    patch_embed="linear", patch_size=8, temporal_patch_size=4, spatial_depth=4, temporal_depth=4, embedding_dim=512,
    enc_block="ttww", twod_window_size=8, causal_in_temporal_transformer=True, causal_in_peg=True, dim_head=64,
    heads=8, spatial_pos="rope", n_codes=8192, codebook_dim=8, l2_code=True, use_vae=False,
    use_external_codebook=False, resolution=256, sequence_length=17, norm_type="batch", image_channels=3,
    defer_temporal_pool=False, defer_spatial_pool=False, attn_dropout=0.0, ff_dropout=0.0, ff_mult=4.0,
    initialize_vit=False)

CKPT = dict(repo="Daniel0724/OmniTokenizer", revision="9ebde216ba19b3eeaeec4e2960ebc2d0551c8b3d",
            file="imagenet_k600.ckpt", size=742455697,
            sha256="0a1d9f863f874d2af57855951fa53b92cb0d5aea4f8bf2d8f91007e44b14c01c")
CKPTS = {"vq": CKPT,
         "vae": dict(repo="Daniel0724/OmniTokenizer", revision="9ebde216ba19b3eeaeec4e2960ebc2d0551c8b3d",
                     file="imagenet_k600_vae.ckpt", size=742471379,
                     sha256="d1f1dfc5ca56093945d1ecb45c6bedf0a9157ac80dbf0547e33294a02edeb777")}

SPEC = dict(
    name="OmniTokenizer (ImageNet + K600) VQVAE encoder, imagenet_k600.ckpt",
    arm="secondary",
    kind="clip",
    input_size=(256, 256),
    clip_length=17,
    representation="pre-quantiser latent F.normalize(pre_vq_conv(encoder(x)), p=2, dim=1) (the codebook input; "
                   "l2-normalised 8-d factorised code, not quantised), (B, 8, 5, 32, 32), mean over latent time "
                   "-> flatten (c, h, w): D = 8192",
    normalisation="RGB x / 255 - 0.5 -> [-0.5, 0.5] (VideoNorm mean 0.5, std 1.0), layout (B, 3, T, H, W)",
    sources=[
        dict(quote="--spatial_pos \"rope\" \\ --n_codes 8192 --codebook_dim 8 --l2_code --commitment_weight 1.0 "
                   "--no_random_restart \\ --vqgan_ckpt \"./ckpts_pub/imagenet_k600.ckpt\"",
             copy=_S + "omnitok_github_scripts_recons_eval_video.sh.txt", level=3),
        dict(quote="python3 vqgan_eval.py --inference_type 'video' --patch_embed 'linear' --patch_size 8 "
                   "--temporal_patch_size 4 --spatial_depth 4 --temporal_depth 4 --embedding_dim 512 --disc_layers 3 "
                   "\\ --enc_block \"ttww\" --dec_block \"tttt\" --twod_window_size 8 \\ "
                   "--causal_in_temporal_transformer --causal_in_peg --dim_head 64 --heads 8 --apply_noise "
                   "--apply_blur --spatial_pos \"rope\"",
             copy=_S + "omnitok_github_scripts_recons_eval_video.sh.txt", level=3),
        dict(quote="--vqgan_ckpt \"./ckpts_pub/imagenet_k600.ckpt\" \\ --batch_size 8 --data_path {PATH_TO_DATA_DIR} "
                   "--train_datalist './annotations/k600_train.txt' --val_datalist './annotations/k600_val.txt' \\ "
                   "--loader_type \"joint\" --dataset 'imagenet_k600' --save ./k600 \\ --resolution 256 "
                   "--sequence_length 17 --discriminator_iter_start 0 --norm_type batch",
             copy=_S + "omnitok_github_scripts_recons_eval_video.sh.txt", level=3),
        dict(quote="| VQVAE | ImageNet + K600 | 1.23 | 25.97 | [imagenet_k600.ckpt](https://huggingface.co/"
                   "Daniel0724/OmniTokenizer/resolve/main/imagenet_k600.ckpt) |",
             copy=_S + "omnitok_github_README.md", level=2),
        dict(quote="For the evaluation of omnitokenizer, please refer to ```scripts/recons/eval_image_inet.sh```, "
                   "```scripts/recons/eval_image_face.sh```, ```scripts/recons/eval_video.sh```.",
             copy=_S + "omnitok_github_README.md", level=2),
        dict(quote="OmniTokenizer adopts a decoupled spatial-temporal architecture consisting of 4 window "
                   "attention-based spatial layers (window size = 8) and 4 causal attention-based temporal layers. "
                   "The hidden dimension is 512 and the latent dimension is 8, following ViT-VQGAN [ 62 ] .",
             copy=_S + "omnitok_arxiv_2406.09399_fulltext.txt", level=1),
        dict(quote="For the joint training stage, we forward the model with image and video data iteratively, with "
                   "the video sequence length being 17 frames.",
             copy=_S + "omnitok_arxiv_2406.09399_fulltext.txt", level=1),
        dict(quote="Factorized codes and l 2 l_{2} -normalized codes [ 62 ] are also used to boost the codebook "
                   "usage.",
             copy=_S + "omnitok_arxiv_2406.09399_fulltext.txt", level=1),
        dict(quote="In this way, we compress the input resolution from ( 1 + T ) × H × W (1+T)\\times H\\times W to "
                   "( 1 + T t ) × H p × W p (1+\\frac{T}{t})\\times\\frac{H}{p}\\times\\frac{W}{p} .",
             copy=_S + "omnitok_arxiv_2406.09399_fulltext.txt", level=1),
        dict(quote="h = self.pre_vq_conv(self.encoder(x, is_image)) if not self.use_vae: if self.l2_code and not "
                   "self.use_external_codebook: h = F.normalize(h, p=2, dim=1) vq_output = self.codebook(h)",
             copy=_E + "omnitok_omnitokenizer_py.txt", level=2),
        dict(quote="if not self.use_vae: self.pre_vq_conv = nn.Sequential( Rearrange(\"b c t h w -> b t h w c\"), "
                   "nn.Linear(args.embedding_dim, args.codebook_dim), Rearrange(\"b t h w c -> b c t h w\") )",
             copy=_E + "omnitok_omnitokenizer_py.txt", level=2),
        dict(quote="parser.add_argument('--attn_dropout', type=float, default=0.) "
                   "parser.add_argument('--ff_dropout', type=float, default=0.) "
                   "parser.add_argument('--ff_mult', type=float, default=4.)",
             copy=_E + "omnitok_omnitokenizer_py.txt", level=2),
        dict(quote="Returns BCTHW videos in the range [-0.5, 0.5]",
             copy=_TP + "OmniTokenizer/data.py", level=2),
        dict(quote="video = self.norm(vid_frm_array).permute(1, 0, 2, 3)",
             copy=_TP + "OmniTokenizer/data.py", level=2),
        dict(quote="mean=[0.5, 0.5, 0.5], std=[1.0, 1.0, 1.0],",
             copy=_TP + "OmniTokenizer/video_utils.py", level=2),
        dict(quote="if torch.max(img) > 1 and self.mean.max() <= 1: img.div_(255.0) "
                   "re = img.sub_(self.mean).div_(self.std)",
             copy=_TP + "OmniTokenizer/video_utils.py", level=2),
    ],
    third_party=dict(repo="FoundationVision/OmniTokenizer", commit="701b619003b3e941e769269c7626dbf111d0377e"),
    variants={"vq": "imagenet_k600.ckpt: F.normalize(pre_vq_conv(encoder(x)), dim=1) (codebook-lookup input)",
              "vae": "imagenet_k600_vae.ckpt: posterior mean = first 8 of the 16 pre_vq_conv channels (no sampling)"},
    default_variant="vq",
)
SPEC["sources"] += [
    dict(quote="| VAE | ImageNet + K600 | 0.78 | 13.02 | [imagenet_k600_vae.ckpt](https://huggingface.co/Daniel0724/"
               "OmniTokenizer/resolve/main/imagenet_k600_vae.ckpt) |", copy=_S + "omnitok_github_README.md", level=2),
    dict(quote="--vqgan_ckpt \"./ckpts_pub/imagenet_k600_vae.ckpt\"", copy=_TP + "scripts/recons/eval_video.sh",
         level=3),
    dict(quote="nn.Linear(args.embedding_dim, args.codebook_dim * 2),", copy=_TP + "OmniTokenizer/omnitokenizer.py",
         level=2),
    dict(quote="self.mean, self.logvar = torch.chunk(parameters, 2, dim=1)", copy=_TP + "OmniTokenizer/modules/vae.py",
         level=2),
]


def _exec(relpath, ns, names=None, skip_imports=()):
    """Execute top-level statements of an unmodified third_party source file in ns (names=None: all, minus
    imports from skip_imports; else only the named defs)."""
    path = _OT / relpath
    tree = ast.parse(path.read_text(), filename=str(path))

    def keep(n):
        if isinstance(n, ast.ImportFrom):
            return names is None and (n.module or "").split(".")[0] not in skip_imports
        if isinstance(n, ast.Import):
            return names is None and not any(a.name.split(".")[0] in skip_imports for a in n.names)
        return names is None or getattr(n, "name", None) in names

    tree.body = [n for n in tree.body if keep(n)]
    exec(compile(tree, str(path), "exec"), ns)
    missing = set(names or ()) - set(ns)
    if missing:
        raise ImportError(f"{relpath}: {sorted(missing)} not found")
    return ns


@lru_cache(maxsize=None)
def _encoder_cls():
    try:
        from beartype import beartype
    except ImportError:
        beartype = lambda f: f  # noqa: E731
    att = _exec("OmniTokenizer/modules/attention.py", {"__name__": "omnitok_attention", "beartype": beartype},
                skip_imports=("beartype", "fairscale"))
    base = _exec("OmniTokenizer/base.py", {"__name__": "omnitok_base", "torch": torch}, names={"Normalize"})
    ns = dict(__name__="omnitok_omnitokenizer", math=math, torch=torch, nn=nn, F=F, rearrange=rearrange,
              repeat=repeat, pack=pack, unpack=unpack, Rearrange=Rearrange, trunc_normal_=trunc_normal_,
              checkpoint=torch.utils.checkpoint, Transformer=att["Transformer"], Normalize=base["Normalize"])
    _exec("OmniTokenizer/omnitokenizer.py", ns, names={"pair", "divisible_by", "OmniTokenizer_Encoder"})
    return ns["OmniTokenizer_Encoder"]


class OmniTokenizerPreVQ(nn.Module):
    """encoder + pre_vq_conv of OmniTokenizer_VQGAN, argument for argument as in VQGAN.__init__ (VQ or VAE mode)."""

    def __init__(self, a=ARGS, variant="vq"):
        super().__init__()
        assert variant in ("vq", "vae")
        self.variant = variant
        self.encoder = _encoder_cls()(
            image_size=a["resolution"], image_channel=a["image_channels"], norm_type=a["norm_type"],
            block=a["enc_block"], window_size=a["twod_window_size"], spatial_pos=a["spatial_pos"],
            patch_embed=a["patch_embed"], patch_size=a["patch_size"], temporal_patch_size=a["temporal_patch_size"],
            defer_temporal_pool=a["defer_temporal_pool"], defer_spatial_pool=a["defer_spatial_pool"],
            spatial_depth=a["spatial_depth"], temporal_depth=a["temporal_depth"],
            causal_in_temporal_transformer=a["causal_in_temporal_transformer"], causal_in_peg=a["causal_in_peg"],
            dim=a["embedding_dim"], dim_head=a["dim_head"], heads=a["heads"], attn_dropout=a["attn_dropout"],
            ff_dropout=a["ff_dropout"], ff_mult=a["ff_mult"], initialize=a["initialize_vit"],
            sequence_length=a["sequence_length"])
        self.pre_vq_conv = nn.Sequential(
            Rearrange("b c t h w -> b t h w c"),
            nn.Linear(a["embedding_dim"], a["codebook_dim"] * (2 if variant == "vae" else 1)),
            Rearrange("b t h w c -> b c t h w"))

    def forward(self, x):
        # x: (B, 3, T, H, W) in [-0.5, 0.5] -> (B, codebook_dim, T', H/8, W/8), float32
        h = self.pre_vq_conv(self.encoder(x, is_image=False))
        if self.variant == "vae":
            return torch.chunk(h.float(), 2, dim=1)[0]  # posterior mean (DiagonalGaussianDistribution)
        return F.normalize(h.float(), p=2, dim=1)  # --l2_code


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 24), b""):
            h.update(b)
    return h.hexdigest()


def _state_dict(path, variant="vq"):
    try:
        ckpt = torch.load(path, map_location="cpu", weights_only=True)
    except pickle.UnpicklingError:
        # Lightning checkpoint with pickled hparams: full unpickling only for the pinned release file
        if _sha256(path) != CKPTS[variant]["sha256"]:
            raise
        ckpt = torch.load(path, map_location="cpu", weights_only=False)
    sd = ckpt.get("state_dict", ckpt)
    return {k: v for k, v in sd.items() if k.startswith(("encoder.", "pre_vq_conv."))}


def build(weights=None, device="cpu", dtype=torch.float32, variant="vq"):
    model = OmniTokenizerPreVQ(variant=variant)
    if weights is not None:
        model.load_state_dict(_state_dict(weights, variant), strict=True)
    return model.to(device=device, dtype=dtype).requires_grad_(False).eval()


def encode(model, x):
    """x: (B, L, 3, H, W) standardized RGB frames in [0, 255] -> (B, 8 * 32 * 32) float32."""
    L, (H, W) = SPEC["clip_length"], SPEC["input_size"]
    assert tuple(x.shape[1:]) == (L, 3, H, W), x.shape
    p = next(model.parameters())
    x = (x.to(device=p.device, dtype=torch.float32) / 255.0 - 0.5).to(p.dtype).permute(0, 2, 1, 3, 4)
    with torch.no_grad():
        z = model(x)  # (B, 8, 5, 32, 32)
    return z.mean(dim=2).flatten(1)
