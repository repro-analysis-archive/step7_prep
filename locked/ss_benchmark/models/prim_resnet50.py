# --------------------------------------------------------------------------------------------------------------------
# Licence and upstream attribution (added 2026-11-04 for the public release; comment only — the code is unchanged).
# Original code in this file: Copyright (c) 2026 Hisashi Nakano, MIT License (LICENSE at the repository root).
# Upstream: SelfSupSurg ResNet-50 (MoCo v2 / SimCLR / SwAV / DINO). Paper: Ramesh S et al., "Dissecting
#   self-supervised learning methods for surgical computer vision", Med Image Anal 2023;102844.
#   Code, models and configs: github.com/CAMMA-public/SelfSupSurg (main @ 8a03d289) — CC BY-NC-SA 4.0;
#   weights not included. Architecture: torchvision ResNet-50 (dependency, BSD-3-Clause).
# Embedded upstream material: three configuration values quoted from the SelfSupSurg hparams YAML and one
#   sentence of the paper (SPEC sources), under CC BY-NC-SA 4.0 / the paper's terms.
# Upstream material is NOT covered by the MIT licence; it remains under its upstream licence and is reproduced
# with attribution for non-commercial research use. Details: NOTICE, THIRD_PARTY_NOTICES.md, LICENSES/.
# --------------------------------------------------------------------------------------------------------------------
"""SelfSupSurg adapter: ResNet-50 (frame-level, primary arm; MoCo v2 / SimCLR / SwAV / DINO checkpoints).

* Architecture: torchvision ResNet-50 (the configs initialise from torchvision's resnet50-19c8e357.pth); the
  representation is the 2048-d global-average-pooled trunk output ("the feature vector (2048)").
* Input size 224 × 224 (the SSL configs' crops: "size_crops: [224, 224]"); normalisation ImageNet mean / std
  (configs: "mean: [0.485, 0.456, 0.406]", "std: [0.229, 0.224, 0.225]").
* Weights (§14 step 4; not exercised at code lock): VISSL checkpoints; the trunk state dict under
  classy_state_dict.base_model.model.trunk ("_feature_blocks." prefix) is mapped to torchvision names.
"""
import torch

_MEAN = torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1)
_STD = torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1)

SPEC = dict(name="SelfSupSurg (ResNet-50)", arm="primary", kind="frame", input_size=(224, 224), clip_length=None,
            representation="ResNet-50 global-average-pooled trunk features (2048)",
            normalisation="ImageNet mean/std on [0,1] pixels",
            sources=[dict(quote="replaced by a linear head that maps the feature vector (2048) to the number of outputs",
                          copy="data_audit/lead/fm_sources/primary/selfsupsurg_arxiv_pdf.txt", level=1),
                     dict(quote="size_crops: [224, 224]",
                          copy="data_audit/lead/fm_sources/eligibility_v04/selfsupsurg_cfg_h001_yaml.txt", level=3),
                     dict(quote="mean: [0.485, 0.456, 0.406]",
                          copy="data_audit/lead/fm_sources/eligibility_v04/selfsupsurg_cfg_h001_yaml.txt", level=3),
                     dict(quote="PARAMS_FILE: \"./checkpoints/defaults/resnet_50/resnet50-19c8e357.pth\"",
                          copy="data_audit/lead/fm_sources/eligibility_v04/selfsupsurg_cfg_h001_yaml.txt", level=3)],
            third_party=None)


def _vissl_to_torchvision(sd):
    for key in ("classy_state_dict", "base_model", "model", "trunk"):
        if isinstance(sd, dict) and key in sd:
            sd = sd[key]
    out = {}
    for k, v in sd.items():
        k = k.replace("_feature_blocks.", "")
        out[k] = v
    return out


CHECKPOINTS = {"moco_v2": "model_final_checkpoint_moco_v2_surg.torch",
               "simclr": "model_final_checkpoint_simclr_surg.torch",
               "swav": "model_final_checkpoint_swav_surg.torch",
               "dino": "model_final_checkpoint_dino_surg.torch"}


def build(weights=None, device="cpu", dtype=torch.float32, checkpoint=None):
    """``checkpoint`` names the release file (CHECKPOINTS); all four share this architecture and loader."""
    import torchvision
    assert checkpoint is None or checkpoint in CHECKPOINTS
    model = torchvision.models.resnet50(weights=None)
    model.fc = torch.nn.Identity()
    if weights is not None:
        sd = _vissl_to_torchvision(torch.load(weights, map_location="cpu", weights_only=False))
        missing, unexpected = model.load_state_dict(sd, strict=False)
        if missing or [k for k in unexpected if not k.startswith(("fc", "heads"))]:
            raise RuntimeError(f"checkpoint mismatch: missing {missing[:5]}, unexpected {unexpected[:5]}")
    return model.to(device=device, dtype=dtype).eval()


def encode(model, x):
    p = next(model.parameters())
    return model(((x / 255.0 - _MEAN.to(x.device)) / _STD.to(x.device)).to(p.dtype))
