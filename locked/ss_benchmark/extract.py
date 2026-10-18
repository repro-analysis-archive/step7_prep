"""Extraction (§4.2): step representations from grid frames (frame- and clip-level) and the Cosmos reference path.

* Frame-level models: one embedding per grid frame; the step representation is the mean over the step's ten grid
  frames 10t … 10t+9.
* Clip-level models: one clip per step, of the model's documented clip length L: the L most recent grid frames ending
  at the step's last grid frame 10t+9 (no frame after 5t + 5); earlier frames come from preceding steps; at the video
  start the first grid frame is repeated (indices < 0 -> 0).
* Cosmos reference (Decision 005, §4.2; mirrors gpi_pack commit 8836037): the step's contiguous native frames with
  presentation time in [5t, 5t+5); at most 121, selected by np.linspace(0, n − 1, 121).round() (gpi_pack
  uniform_frame_indices); standardized crop and mask at native resolution, then resize to 320×320 (bilinear,
  antialiased); pixels scaled to [−1, 1]; replicate-padding to the spatial compression multiple (none needed at 320);
  latent = encoder output mode; representation = post_quant_conv(latent) averaged over latent time: 16 × 40 × 40.
All model calls are inference-only. ``encoder`` callables take a float tensor already normalised by the adapter.
"""
import numpy as np
import torch

from .constants import COSMOS_MAX_FRAMES, COSMOS_SIZE, GRID_FRAMES_PER_STEP, MASK_RADIUS
from .preprocess import apply_mask, centre_crop_square, resize


def step_grid_frames(t):
    return np.arange(GRID_FRAMES_PER_STEP * t, GRID_FRAMES_PER_STEP * (t + 1))


def clip_grid_frames(t, L):
    last = GRID_FRAMES_PER_STEP * t + GRID_FRAMES_PER_STEP - 1
    idx = np.arange(last - L + 1, last + 1)
    return np.maximum(idx, 0)


def frame_level_steps(frame_embeddings, n_steps):
    """frame_embeddings: (n_grid, D) for grid frames 0..; returns (n_steps, D) step means."""
    E = np.asarray(frame_embeddings)[:GRID_FRAMES_PER_STEP * n_steps]
    return E.reshape(n_steps, GRID_FRAMES_PER_STEP, -1).mean(1)


@torch.inference_mode()
def embed_frames(grid_tensor, encoder, batch=64, device="cpu"):
    """grid_tensor: (n_grid, 3, s, s) model-ready frames -> (n_grid, D) float32 numpy."""
    out = []
    for s in range(0, grid_tensor.shape[0], batch):
        out.append(encoder(grid_tensor[s:s + batch].to(device)).float().cpu())
    return torch.cat(out).numpy()


@torch.inference_mode()
def embed_clips(grid_tensor, encoder, L, n_steps, batch=4, device="cpu"):
    """grid_tensor: (n_grid, 3, s, s) model-ready frames; returns (n_steps, D) and the clip index lists."""
    out, clips = [], [clip_grid_frames(t, L) for t in range(n_steps)]
    for s in range(0, n_steps, batch):
        idx = clips[s:s + batch]
        x = torch.stack([grid_tensor[torch.as_tensor(c)] for c in idx])      # (B, L, 3, h, w)
        out.append(encoder(x.to(device)).float().cpu())
    return torch.cat(out).numpy(), clips


def cosmos_frame_selection(n_native):
    if n_native <= COSMOS_MAX_FRAMES:
        return np.arange(n_native)
    return np.linspace(0, n_native - 1, COSMOS_MAX_FRAMES).round().astype(np.int64)


def cosmos_prepare_frames(frames, r=MASK_RADIUS):
    """(T, H, W, 3) native RGB -> (T, 3, 320, 320) in [0, 255]: centre crop, mask at native resolution, resize."""
    x = centre_crop_square(np.asarray(frames))
    x = torch.from_numpy(np.ascontiguousarray(x)).permute(0, 3, 1, 2).float()
    x = apply_mask(x, r)
    return resize(x.permute(0, 2, 3, 1).numpy(), COSMOS_SIZE)


def cosmos_stack(prepared):
    """(T, 3, 320, 320) in [0, 255] -> (1, 3, T, 320, 320) in [−1, 1]."""
    x = prepared / 127.5 - 1.0
    return x.permute(1, 0, 2, 3).unsqueeze(0)


def cosmos_input(native_frames, r=MASK_RADIUS):
    """(T, H, W, 3) native RGB of one step -> (1, 3, T', 320, 320) in [−1, 1] (selection, crop, mask, resize)."""
    sel = cosmos_frame_selection(len(native_frames))
    return cosmos_stack(cosmos_prepare_frames(np.asarray(native_frames)[sel], r)), sel


@torch.inference_mode()
def cosmos_representation(vae, video, pad_multiple=8):
    """video: (1, 3, T, H, W) in [−1, 1]; returns post_quant_conv(latent) averaged over latent time, (C, h, w)."""
    pad_h = (-video.shape[-2]) % pad_multiple
    pad_w = (-video.shape[-1]) % pad_multiple
    if pad_h or pad_w:
        b, c, t, h, w = video.shape
        flat = video.permute(0, 2, 1, 3, 4).reshape(b * t, c, h, w)
        flat = torch.nn.functional.pad(flat, (0, pad_w, 0, pad_h), mode="replicate")
        video = flat.reshape(b, t, c, h + pad_h, w + pad_w).permute(0, 2, 1, 3, 4)
    latent = vae.encode(video).latent_dist.mode()
    dec_in = vae.post_quant_conv(latent)
    return dec_in.mean(dim=2)[0]
