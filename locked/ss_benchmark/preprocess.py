"""Preprocessing (§3): 2-fps physical-time grid, centre crop, resize, common mask, near-uniform flag, native arm.

* Physical time (§2): for multi-file cases, files are ordered by version suffix and placed end to end; a frame's
  physical time = summed duration of the preceding files + its presentation time within its file.
* Grid (§3.1 step 1): grid times 0.5k s; at each grid time the first decoded frame whose presentation time is ≥ the
  grid time (tolerance 1e-9 s for floating-point representation of PTS) is used; no re-encoding, no interpolation.
  Step t uses grid frames 10t … 10t+9; a step is complete only when all ten grid frames exist.
* Crop and resize (§3.1 step 2): centre square of side min(H, W) (offsets floor((H − side)/2), floor((W − side)/2)),
  resized bilinear with antialiasing (torch.nn.functional.interpolate, align_corners=False, antialias=True).
* Mask (§3.1 step 3): pixels whose centre lies outside the circle of radius r × side about the square's centre are set
  to 0, and the lowest round(0.03 × side) rows are set to 0; applied before model normalisation. r = 0.45 unless the
  mechanical check (§14 step 4a) returns another value.
* Mechanical check (§3.1 step 3): per centre, the mean BT.601 luma frame at 256×256 (cropped and resized, unmasked)
  over every 60th grid frame of every case; radial profile m_c(ρ) over 1-px annuli |d − k| < 0.5 (d = distance of
  the pixel centre from the image centre, k = 1, 2, …), ρ = k / 256; ρ_c = the largest ρ with m_c(ρ′) ≥ 0.25 ×
  median{m_c(ρ″): ρ″ ≤ 0.1} for all ρ′ ≤ ρ; r = 0.45 if min_c ρ_c ≥ 0.45, else 0.98 × min_c ρ_c.
* Near-uniform (§3.1 step 4): BT.601 luma SD over the unmasked disc (inside the mask circle, outside the bottom band)
  of the standardized 256×256 frame < 4.0 on the 8-bit scale; frames are kept and flagged.
* Native arm (§3.2): the same grid frames resized to the model input size with no crop and no mask.
"""
import json
import subprocess

import numpy as np
import torch
import torch.nn.functional as F

from .constants import (BOTTOM_BAND, GRID_FPS, GRID_FRAMES_PER_STEP, MASK_CHECK_CENTRAL_RHO, MASK_CHECK_SHRINK,
                        MASK_CHECK_SIZE, MASK_CHECK_THRESHOLD, MASK_RADIUS, NEAR_UNIFORM_LUMA_SD, NEAR_UNIFORM_SIZE,
                        STEP_SECONDS)

PTS_TOL = 1e-9


# ---------------------------------------------------------------------------------------------------------------------
# time axis and grid
# ---------------------------------------------------------------------------------------------------------------------
def physical_pts(per_file_pts, per_file_durations):
    """Concatenate per-file presentation times (files in version order) onto the physical time axis."""
    out, offset = [], 0.0
    for pts, dur in zip(per_file_pts, per_file_durations):
        out.append(np.asarray(pts, float) + offset)
        offset += float(dur)
    return np.concatenate(out)


def grid_frame_indices(pts, n_steps=None):
    """Indices (into the presentation-ordered frames) of the 2-fps grid frames; -1 where no frame exists."""
    pts = np.asarray(pts, float)
    assert np.all(np.diff(pts) >= 0), "pts must be in presentation order"
    if n_steps is None:
        n_grid = int(np.floor(pts[-1] * GRID_FPS)) + 1
    else:
        n_grid = int(n_steps) * GRID_FRAMES_PER_STEP
    g = np.arange(n_grid) / GRID_FPS
    idx = np.searchsorted(pts, g - PTS_TOL, side="left")
    idx[idx >= len(pts)] = -1
    return idx


def complete_steps(grid_idx):
    """Number of steps whose ten grid frames all exist."""
    ok = np.asarray(grid_idx) >= 0
    n = len(ok) // GRID_FRAMES_PER_STEP
    for t in range(n):
        if not ok[t * GRID_FRAMES_PER_STEP:(t + 1) * GRID_FRAMES_PER_STEP].all():
            return t
    return n


def step_native_indices(pts, t):
    """Indices of native frames with presentation time in [5t, 5t + 5) (Cosmos reference arm, §4.2)."""
    pts = np.asarray(pts, float)
    lo = np.searchsorted(pts, STEP_SECONDS * t - PTS_TOL, side="left")
    hi = np.searchsorted(pts, STEP_SECONDS * (t + 1) - PTS_TOL, side="left")
    return np.arange(lo, hi)


# ---------------------------------------------------------------------------------------------------------------------
# spatial operations (frames: uint8 or float array (N, H, W, 3) in [0, 255])
# ---------------------------------------------------------------------------------------------------------------------
def centre_crop_square(frames):
    frames = np.asarray(frames)
    H, W = frames.shape[-3:-1]
    side = min(H, W)
    top, left = (H - side) // 2, (W - side) // 2
    return frames[..., top:top + side, left:left + side, :]


def resize(frames, size):
    """(N, H, W, 3) [0,255] -> float32 tensor (N, 3, h, w), bilinear, antialiased."""
    size = (size, size) if np.isscalar(size) else tuple(size)
    x = torch.from_numpy(np.require(frames, requirements=["C", "W"])).permute(0, 3, 1, 2).float()
    if tuple(x.shape[-2:]) == size:
        return x
    return F.interpolate(x, size=size, mode="bilinear", align_corners=False, antialias=True)


def mask_array(side, r=MASK_RADIUS):
    """Boolean (side, side): True where pixels are kept (inside the circle and above the bottom band)."""
    c = (np.arange(side) + 0.5) - side / 2.0
    keep = (c[:, None] ** 2 + c[None, :] ** 2) <= (r * side) ** 2
    band = int(round(BOTTOM_BAND * side))
    if band:
        keep[side - band:, :] = False
    return keep


def apply_mask(x, r=MASK_RADIUS):
    """x: tensor (N, 3, s, s) -> masked copy (outside set to 0)."""
    keep = torch.from_numpy(mask_array(x.shape[-1], r))
    return x * keep.to(x.dtype)


def standardize(frames, size, r=MASK_RADIUS):
    """Primary standardized acquisition: crop -> resize -> mask; returns (N, 3, size, size) float32 in [0, 255]."""
    return apply_mask(resize(centre_crop_square(frames), size), r)


def native(frames, size):
    """Native acquisition (§3.2): resize only (no crop, no mask)."""
    return resize(frames, size)


def luma_bt601(x):
    """x: (N, 3, h, w) RGB -> (N, h, w)."""
    return 0.299 * x[:, 0] + 0.587 * x[:, 1] + 0.114 * x[:, 2]


def near_uniform_flags(frames, r=MASK_RADIUS):
    x = resize(centre_crop_square(frames), NEAR_UNIFORM_SIZE)
    y = luma_bt601(x).numpy()
    keep = mask_array(NEAR_UNIFORM_SIZE, r)
    sd = y[:, keep].std(axis=1)
    return sd < NEAR_UNIFORM_LUMA_SD, sd


# ---------------------------------------------------------------------------------------------------------------------
# mechanical mask check (§3.1 step 3; runs at §14 step 4a)
# ---------------------------------------------------------------------------------------------------------------------
class MaskCheck:
    def __init__(self):
        self.sum = {}
        self.count = {}

    def add(self, centre, frames):
        y = luma_bt601(resize(centre_crop_square(frames), MASK_CHECK_SIZE)).double().sum(0).numpy()
        self.sum[centre] = self.sum.get(centre, 0.0) + y
        self.count[centre] = self.count.get(centre, 0) + len(frames)

    @staticmethod
    def selected_grid_frames(n_grid):
        return np.arange(0, n_grid, 60)

    @staticmethod
    def radial_profile(img):
        s = img.shape[0]
        c = (np.arange(s) + 0.5) - s / 2.0
        d = np.sqrt(c[:, None] ** 2 + c[None, :] ** 2)
        k = np.floor(d + 0.5).astype(int)
        kmax = int(k.max())
        sums = np.bincount(k.ravel(), weights=img.ravel(), minlength=kmax + 1)
        cnt = np.bincount(k.ravel(), minlength=kmax + 1)
        ks = np.flatnonzero((cnt > 0) & (np.arange(kmax + 1) >= 1))
        return ks / s, sums[ks] / cnt[ks]

    @staticmethod
    def visible_radius(rho, m):
        ref = np.median(m[rho <= MASK_CHECK_CENTRAL_RHO])
        ok = m >= MASK_CHECK_THRESHOLD * ref
        if not ok[0]:
            return 0.0
        first_bad = np.flatnonzero(~ok)
        return float(rho[-1] if len(first_bad) == 0 else rho[first_bad[0] - 1])

    def result(self):
        prof, rhos = {}, {}
        for c in sorted(self.sum):
            rho, m = self.radial_profile(self.sum[c] / self.count[c])
            prof[str(c)] = dict(rho=rho.tolist(), m=m.tolist(), n_frames=int(self.count[c]))
            rhos[str(c)] = self.visible_radius(rho, m)
        rmin = min(rhos.values())
        r = MASK_RADIUS if rmin >= MASK_RADIUS else MASK_CHECK_SHRINK * rmin
        return dict(visible_radius=rhos, min_visible_radius=rmin, r=r, profiles=prof)


# ---------------------------------------------------------------------------------------------------------------------
# decoding (ffmpeg CLI; real path, exercised in code lock only on synthetic test videos)
# ---------------------------------------------------------------------------------------------------------------------
def probe_video(path):
    """Width, height, duration and the sorted packet presentation times (s, relative to the container start time)."""
    s = json.loads(subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height:format=duration,start_time", "-of", "json", path],
        capture_output=True, text=True, check=True).stdout)
    pts = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "packet=pts_time",
                          "-of", "csv=p=0", path], capture_output=True, text=True, check=True).stdout.split()
    pts = np.sort(np.array([float(p.strip(",")) for p in pts if p.strip(",") not in ("", "N/A")]))
    st = s["streams"][0]
    start = float(s["format"].get("start_time", 0.0) or 0.0)
    return dict(width=int(st["width"]), height=int(st["height"]), duration=float(s["format"]["duration"]),
                start_time=start, pts=pts - start)


def iter_decoded_frames(path, width, height):
    """Yield (presentation index, RGB uint8 frame) for every decoded frame (no frame dropping or duplication)."""
    cmd = ["ffmpeg", "-v", "error", "-nostdin", "-i", path, "-map", "0:v:0", "-vsync", "passthrough",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"]
    nbytes = width * height * 3
    with subprocess.Popen(cmd, stdout=subprocess.PIPE) as p:
        k = 0
        while True:
            buf = p.stdout.read(nbytes)
            if len(buf) < nbytes:
                break
            yield k, np.frombuffer(buf, np.uint8).reshape(height, width, 3)
            k += 1
        p.wait()
        if p.returncode:
            raise RuntimeError(f"ffmpeg failed on {path} ({p.returncode})")


def decode_selected(path, indices, width, height):
    """Frames at the given presentation indices (sorted unique), in that order."""
    want = np.unique(np.asarray(indices))
    want = want[want >= 0]
    out, j = {}, 0
    for k, fr in iter_decoded_frames(path, width, height):
        if j < len(want) and k == want[j]:
            out[k] = fr.copy()
            j += 1
            if j == len(want):
                break
    return out
