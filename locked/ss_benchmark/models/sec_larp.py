# --------------------------------------------------------------------------------------------------------------------
# Licence and upstream attribution (added 2026-11-04 for the public release; comment only — the code is unchanged).
# Original code in this file: Copyright (c) 2026 Hisashi Nakano, MIT License (LICENSE at the repository root).
# Upstream: LARP (arXiv:2410.21264). Code: github.com/hywang66/LARP @ 8aaed63354c8c0fabcb8a86a2e31c34320e6db86 —
#   MIT License, Copyright (c) 2024 Hanyu Wang; loaded at run time from third_party/ (not included).
#   Weights: huggingface.co/hywang66/LARP-L-long-tokenizer @ c93a7e2d (no licence declared); not included.
# Embedded upstream material: CONFIG is the verbatim config.json of the Hugging Face repository (machine-
#   generated hyperparameter values of the LARP code); short quotations of the LARP code, README, scripts
#   and paper (SPEC sources).
# Upstream material is NOT covered by the MIT licence; it remains under its upstream licence and is reproduced
# with attribution for non-commercial research use. Details: NOTICE, THIRD_PARTY_NOTICES.md, LICENSES/.
# --------------------------------------------------------------------------------------------------------------------
"""LARP-L-Long tokenizer (secondary arm, generic video tokenizer; HF hywang66/LARP-L-long-tokenizer).

Code: third_party/LARP (hywang66/LARP @ 8aaed63354c8c0fabcb8a86a2e31c34320e6db86), models/{models,embed,transformer,
bottleneck,gptc,larp_tokenizer}.py only, loaded under a private package name (no training / loss / AR / dataset
imports; lpips, decord, easydict and the repo's utils package are not needed).

* Config: the released checkpoint's config.json, saved as data_audit/lead/fm_sources/secondary/larp_hf_config.json and
  copied verbatim into CONFIG below (checked against the saved copy in build() when present). Key fields:
  "input_size": 128, "frame_num": 16, "temporal_patch_size": 4, "patch_size": 8, "encoder_hidden_size": 768,
  "encoder_depth": 12, "encoder_num_heads": 12, "bottleneck_token_num": 1024, "bottleneck_dim": 16,
  "codebook_size": 8192, "stochastic": true, "l2_normalized": true, prior "gptc-S". Repo defaults for everything the
  config does not set (timm ViT blocks with mlp_ratio 4 and qkv_bias False, dropout 0.0; GPTC-S 12 x 384, 6 heads).
  Released safetensors: 196,239,520 F32 elements (parameters + persistent buffers, HF API listing); README: 173M.
* Clip length 16, input 128 x 128: paper "In all experiments, we use 16-frame video clips with a spatial resolution of
  128 x 128 for both training and evaluation" (secondary/larp_arxiv_2410.21264_fulltext.txt); reproduce script
  "--frame_num 16 --input_size 128" (secondary/larp_github_train_larp_tokenizer_reproduce.sh.txt).
* Normalisation: [0, 255] -> [0, 1] (x / 255, no mean / std), layout (B, C, T, H, W):
  third_party/LARP/datasets/video_dataset.py L344 "video = video.permute(-1,0,1,2).float() / 255. # # T,H,W,C ->
  C,T,H,W"; models/larp_tokenizer.py "# data: video in shape (b, c, t, h, w)".
* Representation (note N11): the codebook-lookup input, i.e. the continuous latent the quantiser compares with the
  code vectors: v = F.normalize(bottleneck.project_in(Z), dim=-1) ("l2_normalized": true), Z = encoder outputs at the
  1024 learned holistic query positions; (B, 1024, 16) (bottleneck norm 'none'), before the cosine-softmax and
  multinomial sampling (nothing is sampled or quantised). The same rule is used for OmniTokenizer (its l2_code input
  to the codebook). LARP has no latent time
  axis: the queries are an unordered set, each attending to all 4 x 16 x 16 spatio-temporal patches, so the N11
  "average over latent time" is vacuous and v is flattened to (B, 16384). This is the 16-dim bottleneck latent per
  token, the analogue of the Cosmos reference's 16-channel posterior-mode latent. The paper states a codebook
  dimension d' = 8; the released config has "bottleneck_dim": 16, which is used here.
"""
import copy
import importlib.util
import json
import os
import sys
import types

import torch

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
_LARP = os.path.join(_ROOT, "third_party", "LARP")
_CONFIG_COPY = os.path.join(_ROOT, "data_audit", "lead", "fm_sources", "secondary", "larp_hf_config.json")
_PKG = "_larp_tp_models"

# verbatim copy of hywang66/LARP-L-long-tokenizer config.json (HF sha c93a7e2d9ea2eb21b8f84f38484ccc348b3347ea)
CONFIG = {
    "bottleneck": {
        "args": {
            "bottleneck_dim": 16,
            "norm": "none",
            "regularizer": {
                "args": {
                    "codebook_loss_weight": 1.0,
                    "codebook_size": 8192,
                    "commitment_loss_weight": 0.25,
                    "entropy_loss_temperature": 0.01,
                    "entropy_loss_weight": 0.0,
                    "l2_normalized": True,
                    "stochastic": True,
                    "stochastic_temperature": 0.03,
                },
                "name": "vq",
            },
        },
        "name": "bottleneck",
    },
    "bottleneck_token_num": 1024,
    "decoder_depth": 12,
    "decoder_hidden_size": 768,
    "decoder_name": "none",
    "decoder_num_heads": 12,
    "decoder_patch_size": 8,
    "decoder_temporal_patch_size": 4,
    "encoder_depth": 12,
    "encoder_hidden_size": 768,
    "encoder_name": "none",
    "encoder_num_heads": 12,
    "encoder_query_gaussian_init": True,
    "frame_num": 16,
    "in_channels": 3,
    "input_size": 128,
    "latent_pe_scale_factor": 10000,
    "learned_decoder_latent_pe": False,
    "learned_decoder_patch_query_embed": False,
    "learned_encoder_latent_query_embed": True,
    "learned_encoder_patch_pe": False,
    "patch_size": 8,
    "prior_model": {
        "args": {"l2_normalized": True},
        "avg_loss_over_rounds": True,
        "latent_ce_temperature": 1.0,
        "mix_ss_max_ratio": 0.5,
        "mix_ss_peak_steps_ratio": 0.3,
        "n_rounds": 2,
        "name": "gptc-S",
        "no_dropout": False,
        "no_grad_before_last_round": False,
        "use_mix_ss": True,
    },
    "query_init_std": 0.02,
    "temporal_patch_size": 4,
    "transformer_name": "transformer_encoder_parallel",
    "use_decoder_latent_token_type_embed": False,
    "use_decoder_patch_query_token_type_embed": True,
    "use_encoder_latent_query_token_type_embed": False,
    "use_encoder_patch_token_type_embed": False,
}

_S, _E, _T = ("data_audit/lead/fm_sources/secondary/", "data_audit/lead/fm_sources/eligibility_v04/",
              "third_party/LARP/")
SPEC = dict(
    name="LARP-L-Long tokenizer",
    arm="secondary",
    kind="clip",
    input_size=(128, 128),
    clip_length=16,
    representation=(
        "codebook-lookup input: v = F.normalize(bottleneck.project_in(Z), dim=-1) for the 1024 learned holistic query "
        "tokens (Z = encoder output at the query positions, 768-d; project_in = in_linear 768->16, norm 'none'; "
        "l2_normalized true), before the cosine-softmax / sampling; (B, 1024, 16) "
        "flattened to (B, 16384). No latent time axis to average over: the holistic queries are an unordered set, "
        "each attending to all 4x16x16 spatio-temporal patches (N11 temporal averaging is vacuous)."),
    normalisation=("x / 255 -> [0, 1], no mean/std; (B, L, 3, H, W) -> (B, 3, T=L, H, W) "
                   "(third_party/LARP/datasets/video_dataset.py L344)"),
    sources=[
        dict(quote='"frame_num": 16, "in_channels": 3, "input_size": 128,',
             copy=_S + "larp_hf_config.json", level=3),
        dict(quote='"encoder_depth": 12, "encoder_hidden_size": 768, "encoder_name": "none", "encoder_num_heads": 12,',
             copy=_S + "larp_hf_config.json", level=3),
        dict(quote='"bottleneck_dim": 16, "norm": "none",', copy=_S + "larp_hf_config.json", level=3),
        dict(quote='"l2_normalized": true, "stochastic": true, "stochastic_temperature": 0.03 }, "name": "vq"',
             copy=_S + "larp_hf_config.json", level=3),
        dict(quote='"bottleneck_token_num": 1024,', copy=_S + "larp_hf_config.json", level=3),
        dict(quote='"patch_size": 8,', copy=_S + "larp_hf_config.json", level=3),
        dict(quote='"temporal_patch_size": 4, "transformer_name": "transformer_encoder_parallel",',
             copy=_S + "larp_hf_config.json", level=3),
        dict(quote='"name": "gptc-S",', copy=_S + "larp_hf_config.json", level=3),
        dict(quote="In all experiments, we use 16-frame video clips with a spatial resolution of 128 × 128 "
                   "128{\\times}128 for both training and evaluation",
             copy=_S + "larp_arxiv_2410.21264_fulltext.txt", level=1),
        dict(quote="As a result, a 16 × 128 × 128 16{\\times}128{\\times}128 video clip is split into 4 × 16 × 16 = "
                   "1024 4{\\times}16{\\times}16=1024 video patches",
             copy=_S + "larp_arxiv_2410.21264_fulltext.txt", level=1),
        dict(quote="--frame_num 16 --input_size 128",
             copy=_S + "larp_github_train_larp_tokenizer_reproduce.sh.txt", level=3),
        dict(quote="| LARP-L-Long-tokenizer | 173M | 20 (recon.) |", copy=_S + "larp_github_README.md", level=2),
        dict(quote="LARP-L, LARP-B, and LARP-S, with parameter counts of 173.0M, 116.3M, and 39.8M, respectively.",
             copy=_S + "larp_arxiv_2410.21264_fulltext.txt", level=1),
        dict(quote='"parameters": { "F32": 196239520 }',
             copy=_S + "larp_hywang66__LARP-L-long-tokenizer_hfapi.json", level=2),
        dict(quote="video = video.permute(-1,0,1,2).float() / 255. # # T,H,W,C -> C,T,H,W",
             copy=_T + "datasets/video_dataset.py", level=2),
        dict(quote="# data: video in shape (b, c, t, h, w)", copy=_T + "models/larp_tokenizer.py", level=2),
        dict(quote="LARP introduces a set of learned queries ( Carion et al., 2020 ; Li et al., 2023 ) that are "
                   "concatenated with the input patch sequences and then encoded into holistic discrete tokens.",
             copy=_S + "larp_arxiv_2410.21264_fulltext.txt", level=1),
        dict(quote="no specific flattening order is imposed due to the unordered nature of the holistic query set",
             copy=_S + "larp_arxiv_2410.21264_fulltext.txt", level=1),
        dict(quote="SVQ computes the cosine similarities 𝒔 {\\bm{s}} between the input vector 𝒗 {\\bm{v}} and all "
                   "code vectors in 𝑪 {\\bm{C}} , interprets these similarities as logits",
             copy=_S + "larp_arxiv_2410.21264_fulltext.txt", level=1),
        dict(quote="h = h[:, -query_length:, :]", copy=_T + "models/transformer.py", level=2),
        dict(quote="z = self.project_in(x) projected_z = z", copy=_T + "models/bottleneck.py", level=2),
        dict(quote="if self.l2_normalized: z = F.normalize(z, p=2, dim=-1)", copy=_T + "models/bottleneck.py", level=2),
        dict(quote="q_indices = torch.multinomial(probs, 1).squeeze(-1)", copy=_T + "models/bottleneck.py", level=2),
    ],
    third_party=dict(repo="hywang66/LARP", commit="8aaed63354c8c0fabcb8a86a2e31c34320e6db86"),
)

_cls = None


def _exec_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _larp_class():
    """Load the LARP model modules under a private package; `import models` / `import utils` inside them are bound to
    that package / an empty stub only while loading (other top-level `models` packages are left untouched)."""
    global _cls
    if _cls is not None:
        return _cls
    if _LARP not in sys.path:
        sys.path.append(_LARP)
    mdir = os.path.join(_LARP, "models")
    pkg = types.ModuleType(_PKG)
    pkg.__path__, pkg.__package__ = [mdir], _PKG
    sys.modules[_PKG] = pkg
    reg = _exec_module(_PKG + ".models", os.path.join(mdir, "models.py"))
    pkg.register, pkg.make, pkg.models = reg.register, reg.make, reg.models
    shadow = {"models": pkg, "utils": types.ModuleType("_larp_tp_utils")}   # utils: training-only metric
    try:
        import easydict  # noqa: F401
    except ImportError:                                                     # only attribute access is used
        ed = types.ModuleType("easydict")

        class EasyDict(dict):
            def __getattr__(self, k):
                try:
                    return self[k]
                except KeyError as e:
                    raise AttributeError(k) from e
        ed.EasyDict = EasyDict
        shadow["easydict"] = ed
    saved = {k: sys.modules.get(k) for k in shadow}
    sys.modules.update(shadow)
    try:
        for name in ("embed", "transformer", "bottleneck", "gptc", "larp_tokenizer"):
            setattr(pkg, name, _exec_module(f"{_PKG}.{name}", os.path.join(mdir, name + ".py")))
    finally:
        for k, v in saved.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v
    _cls = pkg.larp_tokenizer.LARPTokenizer
    return _cls


def _load_weights(model, weights):
    p = os.fspath(weights)
    if os.path.isdir(p):                                    # local HF snapshot: config.json + model.safetensors
        cfg = os.path.join(p, "config.json")
        if os.path.exists(cfg):
            with open(cfg) as f:
                assert json.load(f) == CONFIG, "checkpoint config differs from the released LARP-L-Long config"
        p = os.path.join(p, "model.safetensors")
    if p.endswith(".safetensors"):
        from safetensors.torch import load_file
        sd = load_file(p, device="cpu")
    else:                                                   # repo checkpoint {'model': {'args', 'sd'}} or a state dict
        ck = torch.load(p, map_location="cpu", weights_only=True)
        sd = ck["model"]["sd"] if isinstance(ck, dict) and "model" in ck else ck
    model.load_state_dict(sd, strict=True)


def build(weights=None, device="cpu", dtype=torch.float32):
    if os.path.exists(_CONFIG_COPY):
        with open(_CONFIG_COPY) as f:
            assert json.load(f) == CONFIG, "CONFIG drifted from the saved larp_hf_config.json"
    model = _larp_class()(**copy.deepcopy(CONFIG))          # full tokenizer incl. decoder and GPTC-S prior
    if weights is not None:
        _load_weights(model, weights)
    model.set_vq_eval_deterministic(True)                   # authors' --det; the quantiser is not used by encode()
    return model.to(device=device, dtype=dtype).eval()


@torch.inference_mode()
def encode(model, x):
    """x: (B, 16, 3, 128, 128) in [0, 255] -> (B, 16384) codebook-lookup input (1024 query tokens x 16)."""
    L, (H, W) = SPEC["clip_length"], SPEC["input_size"]
    assert x.ndim == 5 and tuple(x.shape[1:]) == (L, 3, H, W), tuple(x.shape)
    p = next(model.parameters())
    v = (x.to(device=p.device, dtype=torch.float32) / 255.0).to(p.dtype)
    v = v.permute(0, 2, 1, 3, 4).contiguous()               # (B, 3, T, H, W)
    tok = model.x_embedder(v) + model.get_encoder_patch_pe()    # (B, 1024, 768), fixed 3D sin-cos PE
    q = model.get_encoder_latent_query_embed().repeat(v.shape[0], 1, 1)
    z = model.encoder(tok, q)                               # (B, 1024, 768) outputs at the query positions
    z = model.bottleneck.project_in(z)                      # (B, 1024, 16)
    z = torch.nn.functional.normalize(z.float(), p=2, dim=-1)   # codebook-lookup input (l2_normalized: true)
    return z.flatten(1)
