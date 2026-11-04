# --------------------------------------------------------------------------------------------------------------------
# Licence and upstream attribution (added 2026-11-04 for the public release; comment only — the code is unchanged).
# Original code in this file: Copyright (c) 2026 Hisashi Nakano, MIT License (LICENSE at the repository root).
# Upstream: WF-VAE (arXiv:2411.17459). Code: github.com/PKU-YuanGroup/WF-VAE @ d858bee8 — Apache License 2.0;
#   loaded at run time from third_party/ (not included).
#   Weights: huggingface.co/chestnutlzj/WF-VAE-L-16Chn @ 8c0aa9ce — Apache-2.0; not included.
# Embedded upstream material: CONFIG is the released config.json (Apache-2.0; changed by the authors: the
#   private keys _class_name and _diffusers_version are dropped); short quotations of the WF-VAE code,
#   scripts, README and paper (SPEC sources). Licence text: LICENSES/Apache-2.0.txt.
# Upstream material is NOT covered by the MIT licence; it remains under its upstream licence and is reproduced
# with attribution for non-commercial research use. Details: NOTICE, THIRD_PARTY_NOTICES.md, LICENSES/.
# --------------------------------------------------------------------------------------------------------------------
"""WF-VAE-L 16ch adapter (clip-level, secondary arm; PKU-YuanGroup WF-VAE, HF chestnutlzj/WF-VAE-L-16Chn).

* Architecture: causalvideovae WFVAEModel from third_party/WF-VAE (commit d858bee) with the released checkpoint's
  config.json (saved copy fm_sources/secondary/osplan_hf_WF-VAE-L-16Chn_config.json; identical to the repo's
  examples/wfvae-large-16chn.json, the --model_config of examples/train_ddp.sh): base_channels 192, latent_dim 16,
  2 + 2 resblocks, energy-flow hidden size 128 / 128, layernorm, AttnBlock3DFix, l1 Downsample + Haar 2D, l2
  Spatial2xTime2x3DDownsample + Haar 3D, trilinear temporal upsampling (CONFIG below). Random initialisation at code
  lock. 317,081,532 parameters + buffers (HF file listing "F32": 317081532; README "16-channel WF-VAE-L (316M)";
  paper Table 3, WF-VAE-L enc 84M / dec 232M).
* Clip length 33, input 256 × 256: the authors' evaluation setting ("All measurements are conducted on 33 frames with
  256×256 resolution videos.", paper Fig. 1; TRAIN_AND_VALIDATE.md NUM_FRAMES=33 / RESOLUTION=256; train_ddp.sh
  --eval_num_frames 33, --resolution 256). Training used 25 frames at 256 × 256 (stage I), then 49 (stage II).
  Constraint: L = 1 + 4k (causal first frame, 4x temporal compression; modeling_wfvae.py:568
  "t_upsampled = (t_latent - 1) * self.temporal_uptimes + 1", temporal_uptimes = 4 at :390); H, W multiples of 8.
* Normalisation: [0, 255] -> [0, 1] -> [-1, 1], RGB, layout (B, 3, T, H, W) (dataset/transform.py:145
  "clip.float() / 255.0"; dataset/video_dataset.py:91 and scripts/recon_single_video.py:72
  "Lambda(lambda x: 2.0 * x - 1.0)").
* Representation (N11): posterior mean, WFVAEModel.encode(x).latent_dist.mode() (modeling_wfvae.py:480
  DiagonalGaussianDistribution(h); distrib_utils.py:7 mean = first latent_dim channels of encoder.conv_out; no
  quant_conv since use_quant_layer = False, :349), shape (B, 16, 9, 32, 32) at 33 × 256 × 256, averaged over latent
  time and flattened: 16 × 32 × 32 = 16,384 values. The config scale / shift (0.18215 / 0), applied only by
  downstream diffusion pipelines, is not applied.
"""
import json
import os
import sys

import torch

_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_WFVAE = os.path.join(_REPO, "third_party", "WF-VAE")
_SRC = "data_audit/lead/fm_sources/"
_TP = "third_party/WF-VAE/"

# released config.json of chestnutlzj/WF-VAE-L-16Chn ("_class_name": "WFVAEModel"), private keys dropped
CONFIG = {
    "attention_type": "AttnBlock3DFix",
    "base_channels": 192,
    "connect_res_layer_num": 1,
    "decoder_energy_flow_hidden_size": 128,
    "decoder_num_resblocks": 2,
    "dropout": 0.0,
    "encoder_energy_flow_hidden_size": 128,
    "encoder_num_resblocks": 2,
    "l1_dowmsample_block": "Downsample",
    "l1_downsample_wavelet": "HaarWaveletTransform2D",
    "l1_upsample_block": "Upsample",
    "l1_upsample_wavelet": "InverseHaarWaveletTransform2D",
    "l2_dowmsample_block": "Spatial2xTime2x3DDownsample",
    "l2_downsample_wavelet": "HaarWaveletTransform3D",
    "l2_upsample_block": "Spatial2xTime2x3DUpsample",
    "l2_upsample_wavelet": "InverseHaarWaveletTransform3D",
    "latent_dim": 16,
    "norm_type": "layernorm",
    "scale": [0.18215, 0.18215, 0.18215, 0.18215],
    "shift": [0, 0, 0, 0],
    "t_interpolation": "trilinear",
    "use_attention": True,
}
TEMPORAL_COMPRESSION, SPATIAL_COMPRESSION = 4, 8

SPEC = dict(
    name="WF-VAE-L 16ch", arm="secondary", kind="clip", input_size=(256, 256), clip_length=33,
    length_constraint="L = 1 + 4k (causal first frame, 4x temporal compression); H, W multiples of 8",
    representation="posterior mean encode(x).latent_dist.mode() (first 16 channels of encoder.conv_out; no "
                   "quant_conv), (B, 16, 9, 32, 32) mean over latent time, flattened to 16*32*32 = 16384",
    normalisation="[0,255] -> x/255 -> 2x-1 in [-1,1], RGB, (B, 3, T, H, W)",
    sources=[
        # architecture config
        dict(quote="\"_class_name\": \"WFVAEModel\",", copy=_SRC + "secondary/osplan_hf_WF-VAE-L-16Chn_config.json",
             level=3),
        dict(quote="\"base_channels\": 192,", copy=_SRC + "secondary/osplan_hf_WF-VAE-L-16Chn_config.json", level=3),
        dict(quote="\"latent_dim\": 16,", copy=_SRC + "secondary/osplan_hf_WF-VAE-L-16Chn_config.json", level=3),
        dict(quote="--model_config examples/wfvae-large-16chn.json",
             copy=_SRC + "eligibility_v04/wfvae_train_ddp_sh.txt", level=2),
        dict(quote="We have released our **16-channel WF-VAE-L (316M)** model along with the training code.",
             copy=_SRC + "secondary/wfvae_github_README.md", level=2),
        dict(quote="\"F32\": 317081532", copy=_SRC + "secondary/osplan_chestnutlzj__WF-VAE-L-16Chn_hfapi.json",
             level=2),
        # clip length and input size
        dict(quote="All measurements are conducted on 33 frames with 256×256 resolution videos.",
             copy=_SRC + "secondary/wfvae_arxiv_2411.17459_fulltext.txt", level=1),
        dict(quote="Experiments are conducted on 33 frames with 256×256 resolution.",
             copy=_SRC + "secondary/wfvae_arxiv_2411.17459_fulltext.txt", level=1),
        dict(quote="NUM_FRAMES=33", copy=_SRC + "eligibility_v04/wfvae_TRAIN_AND_VALIDATE_md.txt", level=2),
        dict(quote="RESOLUTION=256", copy=_SRC + "eligibility_v04/wfvae_TRAIN_AND_VALIDATE_md.txt", level=2),
        dict(quote="--eval_num_frames 33", copy=_SRC + "eligibility_v04/wfvae_train_ddp_sh.txt", level=2),
        dict(quote="--resolution 256", copy=_SRC + "eligibility_v04/wfvae_train_ddp_sh.txt", level=2),
        dict(quote="where we preprocess videos to 25 frames with",
             copy=_SRC + "secondary/wfvae_arxiv_2411.17459_fulltext.txt", level=1),
        dict(quote="increase the number of frames to 49", copy=_SRC + "secondary/wfvae_arxiv_2411.17459_fulltext.txt",
             level=1),
        # length constraint
        dict(quote="self.temporal_uptimes = 4", copy=_TP + "causalvideovae/model/vae/modeling_wfvae.py", level=3),
        dict(quote="t_upsampled = (t_latent - 1) * self.temporal_uptimes + 1",
             copy=_TP + "causalvideovae/model/vae/modeling_wfvae.py", level=3),
        # normalisation
        dict(quote="return clip.float() / 255.0", copy=_TP + "causalvideovae/dataset/transform.py", level=3),
        dict(quote="Lambda(lambda x: 2.0 * x - 1.0),", copy=_TP + "causalvideovae/dataset/video_dataset.py", level=3),
        # representation
        dict(quote="self.use_quant_layer = False", copy=_TP + "causalvideovae/model/vae/modeling_wfvae.py", level=3),
        dict(quote="posterior = DiagonalGaussianDistribution(h)",
             copy=_TP + "causalvideovae/model/vae/modeling_wfvae.py", level=3),
        dict(quote="self.mean, self.logvar = torch.chunk(parameters, 2, dim=1)",
             copy=_TP + "causalvideovae/model/utils/distrib_utils.py", level=3),
        dict(quote="latents = encode_result.mode().to(data_type)", copy=_TP + "scripts/recon_video.py", level=3),
    ],
    third_party=dict(repo="PKU-YuanGroup/WF-VAE", commit="d858bee85324341388f2dd1a51a9bd76a4cda4e2"),
)


def _wfvae_class():
    # resolve_str_to_obj() imports "causalvideovae.model.modules.*", so the package root must be on sys.path
    if _WFVAE not in sys.path:
        sys.path.insert(0, _WFVAE)
    from causalvideovae.model.vae.modeling_wfvae import WFVAEModel
    src = os.path.abspath(sys.modules[WFVAEModel.__module__].__file__)
    if not src.startswith(_WFVAE + os.sep):
        raise ImportError(f"causalvideovae resolved outside third_party/WF-VAE: {src}")
    return WFVAEModel


def _state_dict(path):
    """Local checkpoint: a diffusers directory (config.json + diffusion_pytorch_model.safetensors), a .safetensors
    file, or a torch file (authors' .ckpt layout: ema_state_dict / state_dict[gen_model])."""
    if os.path.isdir(path):
        cfg = os.path.join(path, "config.json")
        if os.path.exists(cfg):
            got = {k: v for k, v in json.load(open(cfg)).items() if not k.startswith("_")}
            if got != CONFIG:
                raise ValueError(f"{cfg} is not the WF-VAE-L 16ch config")
        path = os.path.join(path, "diffusion_pytorch_model.safetensors")
    if path.endswith(".safetensors"):
        from safetensors.torch import load_file
        return load_file(path, device="cpu")
    sd = torch.load(path, map_location="cpu", weights_only=True)
    if sd.get("ema_state_dict"):
        return {k.replace("module.", ""): v for k, v in sd["ema_state_dict"].items()}
    if "state_dict" in sd:
        return sd["state_dict"].get("gen_model", sd["state_dict"])
    return sd


def build(weights=None, device="cpu", dtype=torch.float32):
    model = _wfvae_class()(**CONFIG)
    if weights is not None:
        model.load_state_dict(_state_dict(weights), strict=True)
    model.disable_tiling()                        # direct (non-chunked) encoding
    return model.to(device=device, dtype=dtype).eval()


@torch.no_grad()
def encode(model, x):
    """x: (B, L, 3, H, W) in [0, 255], L = 1 + 4k -> (B, 16 * H/8 * W/8) posterior mean averaged over latent time."""
    _, L, _, H, W = x.shape
    if (L - 1) % TEMPORAL_COMPRESSION or H % SPATIAL_COMPRESSION or W % SPATIAL_COMPRESSION:
        raise ValueError(f"WF-VAE needs L = 1 + 4k and H, W multiples of 8; got L={L}, H={H}, W={W}")
    p = next(model.parameters())
    x = 2.0 * (x.float() / 255.0) - 1.0
    x = x.permute(0, 2, 1, 3, 4).to(device=p.device, dtype=p.dtype)            # (B, 3, T, H, W)
    mu = model.encode(x).latent_dist.mode()                                     # (B, 16, 1 + (L-1)/4, H/8, W/8)
    return mu.float().mean(2).flatten(1)
