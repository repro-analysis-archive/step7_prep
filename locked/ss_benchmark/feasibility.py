"""Step-3 feasibility code (§4.1.4 rules 4-5, §10.4 extraction compute fallback). Written at code lock; run at §14
step 3 in rank order, with no DS203 frame. Run in the extraction environment (/home/user/.venvs/ss_extract).

* REGISTRY keys are the extraction-spec keys (docs/codelock_extraction_spec.json); one entry per selectable
  checkpoint; docs/codelock_checkpoint_manifest.json maps every selectable checkpoint to exactly one entry.
* GPU memory feasibility (rule 4): inference only, batch size 1, bf16 on CUDA, the protocol input size and clip length
  (adapter SPEC), synthetic input; feasible iff torch.cuda.max_memory_reserved() ≤ 20.0 GB (reset before the model is
  built, so weights are included). The architecture determines memory; ``weights`` may be given but is not required.
* Extraction compute projection (§10.4 fallback): model hours = inputs needed / synthetic-input throughput (same input
  size, clip length, dtype and software stack; batch ``batch``), with inputs = grid frames at 2 fps (frame-level
  models; ×2 for the primary model, whose native arm (§3.2) is a second pass) or one clip per 5-s step (clip models and
  the Cosmos reference) over the DS203 video hours of out/ds203_wall_time_estimate.json (2012acd: all 403 files, a
  superset of the extraction set); decode and I/O hours from the same file at the 2-fps grid (best measured path for
  grid-sampled models; sequential decode for the Cosmos reference, which needs every native frame). The decision uses
  the serial sum io + decode + model (no pipelining assumed); the pipelined max is also reported. Infeasible iff the
  serial sum exceeds 7 days.
"""
import importlib
import json
import os
import time

import numpy as np
import torch

from .constants import BUDGET_DAYS, COSMOS_MAX_FRAMES

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WALL_TIME_FILE = os.path.join(REPO, "data_audit", "lead", "out", "ds203_wall_time_estimate.json")
GPU_LIMIT_GB = 20.0

REGISTRY = {
    "SurgeNetCholec": ("prim_caformer", {}),
    "SurgeNetRARP": ("prim_caformer", {}),
    "SelfSupSurg-ResNet50:moco_v2": ("prim_resnet50", {"checkpoint": "moco_v2"}),
    "SelfSupSurg-ResNet50:simclr": ("prim_resnet50", {"checkpoint": "simclr"}),
    "SelfSupSurg-ResNet50:swav": ("prim_resnet50", {"checkpoint": "swav"}),
    "SelfSupSurg-ResNet50:dino": ("prim_resnet50", {"checkpoint": "dino"}),
    "VideoMAE:k400-vit-s-1600": ("sec_videomae", {"checkpoint": "k400-vit-s-1600"}),
    "VideoMAE:k400-vit-b-800": ("sec_videomae", {"checkpoint": "k400-vit-b-800"}),
    "VideoMAE:k400-vit-b-1600": ("sec_videomae", {"checkpoint": "k400-vit-b-1600"}),
    "VideoMAE:k400-vit-l-1600": ("sec_videomae", {"checkpoint": "k400-vit-l-1600"}),
    "VideoMAE:k400-vit-h-1600": ("sec_videomae", {"checkpoint": "k400-vit-h-1600"}),
    "VideoMAE:ssv2-vit-s-2400": ("sec_videomae", {"checkpoint": "ssv2-vit-s-2400"}),
    "VideoMAE:ssv2-vit-b-800": ("sec_videomae", {"checkpoint": "ssv2-vit-b-800"}),
    "VideoMAE:ssv2-vit-b-2400": ("sec_videomae", {"checkpoint": "ssv2-vit-b-2400"}),
    "VideoMAE:ucf101-vit-b-3200": ("sec_videomae", {"checkpoint": "ucf101-vit-b-3200"}),
    "OmniTokenizer-imagenet_k600": ("sec_omnitokenizer", {"variant": "vq"}),
    "OmniTokenizer-imagenet_k600_vae": ("sec_omnitokenizer", {"variant": "vae"}),
    "WF-VAE-L-16ch": ("sec_wfvae", {}),
    "LARP-L-Long": ("sec_larp", {}),
    "LeanVAE-16ch": ("sec_leanvae", {"variant": "16ch"}),
    "LeanVAE-4ch": ("sec_leanvae", {"variant": "4ch"}),
    "Cosmos-CV8x8x8": ("ref_cosmos", {}),
}


def adapter(key):
    mod_name, kw = REGISTRY[key]
    return importlib.import_module(f"ss_benchmark.models.{mod_name}"), kw


def synthetic_input(spec, batch, generator):
    H, W = spec["input_size"]
    if spec["kind"] == "frame":
        return torch.rand((batch, 3, H, W), generator=generator) * 255
    if spec["kind"] == "clip":
        return torch.rand((batch, spec["clip_length"], 3, H, W), generator=generator) * 255
    return torch.rand((1, 3, COSMOS_MAX_FRAMES, H, W), generator=generator) * 2 - 1      # Cosmos: [-1, 1], ≤121


def _build(mod, kw, weights, device, dtype):
    return mod.build(weights=weights, device=device, dtype=dtype, **kw)


def gpu_memory_test(key, weights=None, seed=0):
    mod, kw = adapter(key)
    spec = mod.SPEC
    dev, dtype = "cuda", torch.bfloat16
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    torch.manual_seed(seed); np.random.seed(seed)
    model = _build(mod, kw, weights, dev, dtype)
    x = synthetic_input(spec, 1, torch.Generator().manual_seed(seed)).to(dev)
    with torch.inference_mode():
        out = mod.encode(model, x)
    torch.cuda.synchronize()
    peak = torch.cuda.max_memory_reserved() / 1e9
    res = dict(model=key, kind=spec["kind"], input_shape=list(x.shape), dtype="bfloat16", batch=1,
               output_dim=int(out.shape[-1]), peak_reserved_gb=peak, feasible=bool(peak <= GPU_LIMIT_GB),
               weights="random-init" if weights is None else str(weights), torch=torch.__version__)
    del model, x, out
    torch.cuda.empty_cache()
    return res


def synthetic_throughput(key, batch, n_batches=10, weights=None, seed=0):
    """Inputs per second on synthetic inputs (bf16, CUDA), after one warm-up batch."""
    mod, kw = adapter(key)
    spec = mod.SPEC
    torch.manual_seed(seed); np.random.seed(seed)
    model = _build(mod, kw, weights, "cuda", torch.bfloat16)
    b = 1 if spec["kind"] == "cosmos" else batch
    x = synthetic_input(spec, b, torch.Generator().manual_seed(seed)).to("cuda")
    with torch.inference_mode():
        mod.encode(model, x)
        torch.cuda.synchronize()
        t0 = time.perf_counter()
        for _ in range(n_batches):
            mod.encode(model, x)
        torch.cuda.synchronize()
    dt = time.perf_counter() - t0
    del model, x
    torch.cuda.empty_cache()
    return dict(model=key, batch=b, inputs_per_second=b * n_batches / dt, seconds=dt)


def extraction_projection(key, inputs_per_second, wall_time_file=WALL_TIME_FILE, primary_native_pass=None):
    mod, _ = adapter(key)
    spec = mod.SPEC
    wt = json.load(open(wall_time_file))
    hours = float(wt["video_hours_all_files"])
    if spec["kind"] == "frame":
        n_inputs = hours * 3600 * 2.0
        if primary_native_pass if primary_native_pass is not None else spec["arm"] == "primary":
            n_inputs *= 2
        decode = min(v for k, v in wt["decode_only"]["2"].items())
    elif spec["kind"] == "clip":
        n_inputs = hours * 3600 / 5.0
        decode = min(v for k, v in wt["decode_only"]["2"].items())
    else:
        n_inputs = hours * 3600 / 5.0
        decode = min(v for k, v in wt["decode_only"]["2"].items() if k.endswith(" seq"))
    io = max(float(v) for v in wt["io_only"]["2"].values())
    model_h = n_inputs / inputs_per_second / 3600
    serial = io + decode + model_h
    return dict(model=key, video_hours=hours, n_inputs=n_inputs, model_hours=model_h, decode_hours=decode,
                io_hours=io, serial_hours=serial, pipelined_hours=max(io, decode, model_h),
                serial_days=serial / 24, feasible=bool(serial / 24 <= BUDGET_DAYS))
