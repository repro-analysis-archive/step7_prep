"""Paper-linked Cosmos reference adapter (Decision 005; §4.2): nvidia/Cosmos-1.0-Tokenizer-CV8x8x8.

* Architecture: diffusers AutoencoderKLCosmos (the class gpi_pack loads); its default config is the CV8x8x8
  tokenizer (latent_channels 16, spatial / temporal compression 8, Haar patch 4). Random initialisation at code
  lock; at §14 step 4 the weights are loaded from a local copy of the gated repository (subfolder "vae") after the
  investigator accepts the licence (§17).
* Input: see extract.cosmos_input (≤ 121 native frames of [5t, 5t+5), crop + mask, 320 × 320, [−1, 1]); dtype bf16 on
  CUDA (gpi_pack "auto"); representation extract.cosmos_representation: post_quant_conv(latent) averaged over latent
  time, 16 × 40 × 40 = 25,600 values.
"""
import torch

SPEC = dict(name="Cosmos-1.0-Tokenizer-CV8x8x8", arm="reference", kind="cosmos", input_size=(320, 320),
            clip_length=None, representation="post_quant_conv(latent) mean over latent time (16, 40, 40)",
            normalisation="[0,255] -> [-1,1]",
            sources=[dict(quote="DEFAULT_COSMOS_MODEL_ID = \"nvidia/Cosmos-1.0-Tokenizer-CV8x8x8\"",
                          copy="data_audit/lead/fm_sources/reference/gpi_pack_video.py.txt", level=2),
                     dict(quote="For each segment, the representation used by the video paper is the Cosmos decoder "
                                "input (``vae.post_quant_conv(latent)``) averaged over its latent-time axis.",
                          copy="data_audit/lead/fm_sources/reference/gpi_pack_video.py.txt", level=2)],
            third_party=None)


def build(weights=None, device="cpu", dtype=torch.float32):
    from diffusers import AutoencoderKLCosmos
    if weights is None:
        vae = AutoencoderKLCosmos()
    else:
        vae = AutoencoderKLCosmos.from_pretrained(weights, subfolder="vae", local_files_only=True, torch_dtype=dtype)
    return vae.to(device=device, dtype=dtype).eval()


def encode(vae, video):
    from ..extract import cosmos_representation
    p = next(vae.parameters())
    return cosmos_representation(vae, video.to(p.dtype)).flatten()[None]
