# --------------------------------------------------------------------------------------------------------------------
# Licence and upstream attribution (added 2026-11-04 for the public release; comment only — the code is unchanged).
# Original code in this file: Copyright (c) 2026 Hisashi Nakano, MIT License (LICENSE at the repository root).
# Upstream: SurgeNet (SurgeNetCholec / SurgeNetRARP, CAFormer-S18). Paper: Jaspers TJM et al., Med Image Anal
#   2026;108:103873, doi:10.1016/j.media.2025.103873.
#   Code: github.com/TimJaspers0801/SurgeNet @ 54831cfacf3a6cac0bbf5119f72b9cb9c31c3e82 — MIT License,
#   Copyright (c) 2025 Cris Claessens. metaformer.py is imported at run time from third_party/ (not included).
#   Weights: huggingface.co/TimJaspersTue/SurgeNetModels @ cc21f4a1 — CC BY-NC 4.0 (HF card; the GitHub
#   LICENSE_MODELS.txt states CC BY-NC-SA 4.0); not included.
# Embedded upstream material: short quotations of metaformer.py, the SurgeNet README and the paper (SOURCES).
# Upstream material is NOT covered by the MIT licence; it remains under its upstream licence and is reproduced
# with attribution for non-commercial research use. Details: NOTICE, THIRD_PARTY_NOTICES.md, LICENSES/.
# --------------------------------------------------------------------------------------------------------------------
"""SurgeNetCholec / SurgeNetRARP adapter (frame-level, primary arm). Corrected by CODELOCK_CORRECTION_001.

* Architecture: the official SurgeNet network, `caformer_s18(pretrained='SurgeNet')` of the official model-definition
  file third_party/SurgeNet/metaformer.py (TimJaspers0801/SurgeNet @ 54831cfacf3a6cac0bbf5119f72b9cb9c31c3e82,
  sha256 94ef2937…c36718), imported unmodified as a module: CAFormer-S18 (depths 3/3/9/3, dims 64/128/320/512,
  SepConv / SepConv / Attention / Attention token mixers) with plain ReLU activations
  ("partial(SepConv, act1_layer=nn.ReLU)", "mlps=partial(Mlp, act_layer=nn.ReLU)"), LayerNormWithoutBias, res_scale
  1.0 in stages 3-4, output LayerNorm. (The code-lock version used timm `caformer_s18`, whose learnable StarReLU
  activations differ from the released network; see decisions/CODELOCK_CORRECTION_001_SURGENET_ADAPTER.md.)
* Weights: the released teacher-backbone file, loaded with strict key matching under the official parameter names.
  The classification head (MlpHead) is not part of the representation and is replaced by nn.Identity before loading;
  the released backbone files contain no head parameters.
* Representation: the official MetaFormer.forward_features(x)[0] = `self.norm(x.mean([1, 2]))` (LayerNorm of the
  stage-4 map averaged over H, W), 512-d.
* Input size 224 × 224; normalisation ImageNet mean / std on [0, 1] pixels (unchanged from the frozen extraction
  specification; no level-1-3 SurgeNet source states another).
"""
import contextlib
import importlib.util
import io
import os

import torch
import torch.nn as nn

_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_OFFICIAL = os.path.join(_REPO, "third_party", "SurgeNet", "metaformer.py")
OFFICIAL_SOURCE = dict(repo="TimJaspers0801/SurgeNet", commit="54831cfacf3a6cac0bbf5119f72b9cb9c31c3e82",
                       path="metaformer.py", sha256="94ef2937bb2b9c8d8b8d53dcfcff49374c6130d805ebd26de4c76ecda5c36718")
_MEAN = torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1)
_STD = torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1)
_T = "third_party/SurgeNet/metaformer.py"

_SOURCES = [
    dict(quote="We initiate pretraining from ImageNet-initialized weights as recommended by Ramesh et al. (2023)",
         copy="data_audit/lead/fm_sources/primary/surgenetxl_arxiv_pdf.txt", level=1),
    dict(quote="elif pretrained == 'SurgeNet':", copy=_T, level=2),
    dict(quote="partial(SepConv, act1_layer=nn.ReLU),", copy=_T, level=2),
    dict(quote="mlps=partial(Mlp, act_layer=nn.ReLU),", copy=_T, level=2),
    dict(quote="self.norm(x.mean([1, 2])),", copy=_T, level=2),
    dict(quote="res_scale_init_values=[None, None, 1.0, 1.0],", copy=_T, level=2),
    dict(quote="| SurgeNetCholec | CaFormer   | 50     | [Download](https://huggingface.co/TimJaspersTue/SurgeNetModels/"
               "resolve/main/CHOLEC_checkpoint_epoch0050_teacher.pth?download=true)",
         copy="data_audit/lead/fm_sources/primary/surgenet_github_readme.txt", level=2),
]


def _spec(name):
    return dict(name=name, arm="primary", kind="frame", input_size=(224, 224), clip_length=None,
                representation="official SurgeNet CAFormer-S18 (ReLU) forward_features(x)[0] = "
                               "norm(mean over H, W of the stage-4 map), 512",
                normalisation="ImageNet mean/std on [0,1] pixels", sources=_SOURCES,
                third_party=dict(repo=OFFICIAL_SOURCE["repo"], commit=OFFICIAL_SOURCE["commit"]))


SPECS = {"SurgeNetCholec": _spec("SurgeNetCholec (CAFormer-S18, SurgeNet ReLU variant)"),
         "SurgeNetRARP": _spec("SurgeNetRARP (CAFormer-S18, SurgeNet ReLU variant)")}
SPEC = SPECS["SurgeNetCholec"]

_MODULE = None


def official_module():
    """The official metaformer.py, imported unmodified (it registers nothing in timm: caformer_s18 is undecorated)."""
    global _MODULE
    if _MODULE is None:
        spec = importlib.util.spec_from_file_location("surgenet_official_metaformer", _OFFICIAL)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _MODULE = mod
    return _MODULE


def build(weights=None, device="cpu", dtype=torch.float32):
    with contextlib.redirect_stdout(io.StringIO()):          # the official constructor prints pretrained_weights
        model = official_module().caformer_s18(num_classes=0, pretrained="SurgeNet", pretrained_weights=None)
    model.head = nn.Identity()
    if weights is not None:
        sd = torch.load(weights, map_location="cpu", weights_only=True)
        model.load_state_dict(sd, strict=True)
    return model.to(device=device, dtype=dtype).eval()


def encode(model, x):
    p = next(model.parameters())
    x = ((x / 255.0 - _MEAN.to(x.device)) / _STD.to(x.device)).to(p.dtype)
    return model.forward_features(x)[0]
