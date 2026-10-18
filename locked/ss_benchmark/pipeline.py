"""Steps 4-5 orchestration (§14 step 4a mask check, 4b extraction, PCA / LEACE build, step 5 checks). Real path
supported; during code lock exercised only on synthetic test videos and PLACEHOLDER data.

    python -m ss_benchmark.pipeline mask-check  --videos FULL_VIDEOS_DIR --out mask_check.json
    python -m ss_benchmark.pipeline extract     --videos FULL_VIDEOS_DIR --model KEY --acq standardized|native \
                                                --r R --out DIR [--weights PATH] [--batch B]
    python -m ss_benchmark.pipeline build-reps  --extract P=DIR [S=DIR REF=DIR P-nat=DIR] --out reps.npz
    python -m ss_benchmark.pipeline checks      --reps-full reps_full_P.npz [...] --out checks.json
    python -m ss_benchmark.pipeline near-uniform --extract DIR(standardized extraction) --out near_uniform.json

* Case files: FULL_VIDEOS_DIR/Center<c>/<any>/Center<c>_<op:03d>.mp4 or ..._v<NN>.mp4; multi-file cases ordered by
  version and placed end to end on the physical time axis (§2); local times are presentation times relative to the
  container start time.
* Extraction streams each case once: grid frames (§3.1) or, for the Cosmos reference, every native frame of each step
  with at most 121 kept (§4.2); frame models are batched; clip models keep a ring buffer of the last L grid frames and
  emit one clip per step at grid frame 10t+9; per case the (n_steps, D) float32 array, the near-uniform flags
  (standardized arm) and a manifest entry (files, frame counts, steps, sha256) are written; finished cases are skipped
  on resume. A grid frame lying at or after its step end (possible only with a > 0.5-s frame gap) is counted and
  reported, not altered.
"""
import argparse
import collections
import glob
import hashlib
import json
import os
import re
import sys

import numpy as np

from . import checks, design, extract, preprocess, reduce
from .constants import ANALYSIS_REGION, GRID_FRAMES_PER_STEP, MASK_RADIUS, N_FOLDS

K_MAX = 15


# ---------------------------------------------------------------------------------------------------------------------
# case files and time axis
# ---------------------------------------------------------------------------------------------------------------------
def case_files(videos_dir, centre, op):
    pat = re.compile(rf"^Center{centre}_{op:03d}(?:_v(\d+))?\.mp4$")
    hits = []
    for f in glob.glob(os.path.join(videos_dir, f"Center{centre}", "*", f"Center{centre}_{op:03d}*.mp4")):
        m = pat.match(os.path.basename(f))
        if m:
            hits.append((int(m.group(1) or 0), f))
    hits.sort()
    if not hits:
        raise FileNotFoundError(f"no files for Center{centre}_{op:03d}")
    return [f for _, f in hits]


def case_timeline(files):
    infos = [preprocess.probe_video(f) for f in files]
    pts = preprocess.physical_pts([i["pts"] for i in infos], [i["duration"] for i in infos])
    file_id = np.concatenate([np.full(len(i["pts"]), k) for k, i in enumerate(infos)])
    local = np.concatenate([np.arange(len(i["pts"])) for i in infos])
    duration = float(sum(i["duration"] for i in infos))
    return infos, pts, file_id, local, duration


def iter_case_frames(files, infos, wanted_global):
    """Yield (global presentation index, frame) for the wanted indices, file by file, in order."""
    wanted = np.unique(np.asarray(wanted_global))
    offset = 0
    for f, info in zip(files, infos):
        n = len(info["pts"])
        mine = wanted[(wanted >= offset) & (wanted < offset + n)] - offset
        if len(mine):
            j = 0
            for k, fr in preprocess.iter_decoded_frames(f, info["width"], info["height"]):
                if k == mine[j]:
                    yield offset + k, fr
                    j += 1
                    if j == len(mine):
                        break
        offset += n


# ---------------------------------------------------------------------------------------------------------------------
# step 4a: mask check
# ---------------------------------------------------------------------------------------------------------------------
def mask_check(videos_dir, out):
    cases = design.representation_cases()
    mc = preprocess.MaskCheck()
    for cid, c in zip(cases.case_id, cases.center):
        op = int(cid.split("_")[1])
        files = case_files(videos_dir, c, op)
        infos, pts, _, _, dur = case_timeline(files)
        n_steps = int(np.floor(dur / 5.0))
        gidx = preprocess.grid_frame_indices(pts, n_steps)
        sel = gidx[preprocess.MaskCheck.selected_grid_frames(len(gidx))]
        sel = sel[sel >= 0]
        frames = [fr for _, fr in iter_case_frames(files, infos, sel)]
        if frames:
            mc.add(int(c), np.stack(frames))
    res = mc.result()
    with open(out, "w") as f:
        json.dump(res, f, indent=1, sort_keys=True)
    return res


# ---------------------------------------------------------------------------------------------------------------------
# step 4b: extraction
# ---------------------------------------------------------------------------------------------------------------------
def _sha(a):
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def extract_case(files, model_key, model, mod, acq, r, batch, device):
    import torch
    spec = mod.SPEC
    infos, pts, _, _, dur = case_timeline(files)
    n_steps = int(np.floor(dur / 5.0))
    info = dict(files=[os.path.basename(f) for f in files], n_frames=int(len(pts)), duration=dur)
    if spec["kind"] == "cosmos":
        per_step = [preprocess.step_native_indices(pts, t) for t in range(n_steps)]
        keep = {t: idx[extract.cosmos_frame_selection(len(idx))] for t, idx in enumerate(per_step) if len(idx)}
        wanted = np.concatenate(list(keep.values())) if keep else np.array([], int)
        buf = collections.defaultdict(list)
        step_of = {int(g): t for t, idx in keep.items() for g in idx}
        out = np.full((n_steps, int(np.prod((16, 40, 40)))), np.nan, np.float32)
        last_needed = {t: int(idx[-1]) for t, idx in keep.items()}
        for g, fr in iter_case_frames(files, infos, wanted):
            t = step_of[g]
            buf[t].append(extract.cosmos_prepare_frames(fr[None], r)[0])     # selection already applied
            if g == last_needed[t]:
                video = extract.cosmos_stack(torch.stack(buf.pop(t)))
                out[t] = mod.encode(model, video.to(device)).float().cpu().numpy()[0]
        info.update(n_steps=n_steps, frames_per_step_min=int(min(len(v) for v in per_step)) if per_step else 0)
        return out, None, info
    gidx = preprocess.grid_frame_indices(pts, n_steps)
    n_ok = preprocess.complete_steps(gidx)
    gidx = gidx[:GRID_FRAMES_PER_STEP * n_ok]
    late = int((pts[gidx] >= 5.0 * (np.arange(len(gidx)) // GRID_FRAMES_PER_STEP) + 5.0).sum())
    H, W = spec["input_size"]
    pos_of = collections.defaultdict(list)
    for k, g in enumerate(gidx):
        pos_of[int(g)].append(k)
    prep = (lambda fr: preprocess.standardize(fr[None], (H, W), r)) if acq == "standardized" else \
        (lambda fr: preprocess.native(fr[None], (H, W)))
    flags = np.zeros(len(gidx), bool)
    feats, pending, clip_out = [], [], []
    L = spec.get("clip_length") or 1
    ring = collections.deque(maxlen=max(L, GRID_FRAMES_PER_STEP))
    next_k = 0
    for g, fr in iter_case_frames(files, infos, np.unique(gidx)):
        x = prep(fr)[0]
        nu = bool(preprocess.near_uniform_flags(fr[None], r)[0][0]) if acq == "standardized" else False
        for k in pos_of[g]:                       # grid indices are non-decreasing: positions arrive in order
            assert k == next_k
            next_k += 1
            flags[k] = nu
            if spec["kind"] == "frame":
                pending.append(x)
                if len(pending) == batch:
                    feats.append(mod.encode(model, torch.stack(pending).to(device)).float().cpu().numpy())
                    pending = []
            else:
                ring.append(x)                    # ring holds grid positions k - len(ring) + 1 .. k
                if k % GRID_FRAMES_PER_STEP == GRID_FRAMES_PER_STEP - 1:
                    first = k - len(ring) + 1
                    clip_idx = extract.clip_grid_frames(k // GRID_FRAMES_PER_STEP, L)
                    assert clip_idx.min() >= first
                    clip = torch.stack([ring[int(i) - first] for i in clip_idx])
                    clip_out.append(mod.encode(model, clip[None].to(device)).float().cpu().numpy()[0])
    assert next_k == len(gidx)
    if spec["kind"] == "frame":
        if pending:
            feats.append(mod.encode(model, torch.stack(pending).to(device)).float().cpu().numpy())
        E = np.concatenate(feats)
        out = extract.frame_level_steps(E, n_ok).astype(np.float32)
    else:
        out = np.stack(clip_out).astype(np.float32)
    info.update(n_steps=n_ok, n_steps_by_duration=n_steps, grid_frames_after_step_end=late)
    return out, flags if acq == "standardized" else None, info


def extract_all(videos_dir, model_key, acq, r, out_dir, weights=None, batch=64, device="cuda"):
    import torch
    from .feasibility import adapter
    mod, kw = adapter(model_key)
    dtype = torch.bfloat16 if device == "cuda" else torch.float32
    model = mod.build(weights=weights, device=device, dtype=dtype, **kw)
    os.makedirs(out_dir, exist_ok=True)
    man_p = os.path.join(out_dir, "manifest.json")
    manifest = json.load(open(man_p)) if os.path.exists(man_p) else {}
    cases = design.representation_cases()
    with torch.inference_mode():
        for cid, c in zip(cases.case_id, cases.center):
            if cid in manifest:
                continue
            op = int(cid.split("_")[1])
            files = case_files(videos_dir, c, op)
            arr, flags, info = extract_case(files, model_key, model, mod, acq, r, batch, device)
            np.save(os.path.join(out_dir, f"{cid}.npy"), arr)
            if flags is not None:
                np.save(os.path.join(out_dir, f"{cid}.near_uniform.npy"), flags)
            info.update(sha256=_sha(arr), shape=list(arr.shape), model=model_key, acquisition=acq, r=r,
                        weights=str(weights))
            manifest[cid] = info
            tmp = man_p + ".tmp"
            json.dump(manifest, open(tmp, "w"), indent=1, sort_keys=True)
            os.replace(tmp, man_p)
    return manifest


# ---------------------------------------------------------------------------------------------------------------------
# PCA / LEACE build and checks
# ---------------------------------------------------------------------------------------------------------------------
def build_reps(extract_dirs, out_npz, sets=("primary", "W0", "W5", "single_file"), cases=None, folds=None,
               designs=None):
    """Real design by default; ``cases`` (case_id, center), ``folds`` and ``designs`` may be injected (dry run)."""
    if cases is None:
        cases = design.representation_cases()
        folds = design.representation_folds().loc[cases.case_id].to_numpy()
        designs = {s: design.load_real_design(s) for s in sets}
    arrays = {}
    full = {}
    for key, d in extract_dirs.items():
        raw = [np.load(os.path.join(d, f"{cid}.npy")) for cid in cases.case_id]
        red = reduce.foldwise_reduce(raw, folds, cases.center.to_numpy(), n_folds=N_FOLDS,
                                     with_leace=key != "P-nat")
        full[key] = dict(R=red["R"], RC=red["R-C"], report=red["report"])
        pos = {cid: i for i, cid in enumerate(cases.case_id)}
        for s in sets:
            D = designs[s]
            idx = [pos[c] for c in D.ids]
            w = D.window_start()
            for out_key, src in ((key, "R"), (f"{key}-C", "R-C")):
                if not red[src]:
                    continue
                arr = np.stack([np.stack([red[src][v][i][wi:wi + K_MAX] for i, wi in zip(idx, w)])
                                for v in range(N_FOLDS)])
                arrays[f"{s}/{out_key}"] = arr.astype(np.float64)
            arrays[f"{s}/ids"] = np.asarray(D.ids, dtype="U16")
    np.savez(out_npz, **arrays)
    for key, f in full.items():
        lens = np.array([len(x) for x in f["R"][0]])
        np.savez(out_npz.replace(".npz", f"_full_{key}.npz"), lengths=lens,
                 **{f"R_{v}": np.concatenate(f["R"][v]) for v in range(N_FOLDS)},
                 **({f"RC_{v}": np.concatenate(f["RC"][v]) for v in range(N_FOLDS)} if f["RC"] else {}))
    json.dump({k: f["report"] for k, f in full.items()}, open(out_npz.replace(".npz", "_report.json"), "w"),
              indent=1, sort_keys=True, default=float)
    return arrays


def _unpack_full(path):
    z = np.load(path)
    lens = z["lengths"]
    cuts = np.cumsum(lens)[:-1]
    R = [np.split(z[f"R_{v}"], cuts) for v in range(N_FOLDS)]
    RC = [np.split(z[f"RC_{v}"], cuts) for v in range(N_FOLDS)] if "RC_0" in z.files else None
    return R, RC


def _reporting(d):
    """Mark a reporting-only result: no pass / fail field, never used by a rule (§5.2 secondary, §4.3)."""
    d = dict(d)
    d.pop("pass", None)
    d["reporting_only"] = True
    return d


def run_checks(full_paths, out_json, cases=None, folds=None, designs=None, roots=None, n_boot=None,
               replicate_root=None):
    """E1 / E2 / E3 (§5, §10.3 single-file) and the reporting-only paths, for every representation key.

    Real design unless injected (dry run): ``cases`` needs columns case_id, center, s (switch step); ``designs`` the
    primary and single-file Design objects; ``replicate_root`` the SeedSequence root of the E2-with-H reference
    replicate (default 20261007).
    Gate-relevant: E1_278, E1_<set>, E2_<set>, E2_<set>_after_removal, E3_site_<set|278>, E3_state_<set>,
    fm_conditions_primary. Reporting only (no pass field): E1_MLP_<278|set> (pre-removal MLP probe), E2_278,
    E2_278_normtime, E2_<set>_normtime, E2_primary_history.
    """
    from . import dgp, grid, seeds
    from .constants import SEED_REPLICATES
    if cases is None:
        cases = design.representation_cases()
        cases = cases.assign(s=design.representation_switch_steps().loc[cases.case_id].to_numpy())
        folds = design.representation_folds().loc[cases.case_id].to_numpy()
        designs = {s: design.load_real_design(s) for s in ("primary", "single_file")}
    root = SEED_REPLICATES if replicate_root is None else replicate_root
    kw = {} if roots is None else dict(roots=roots)
    kb = {} if n_boot is None else dict(n_boot=n_boot)
    sites = cases.center.to_numpy()
    s_all = cases.s.to_numpy()
    pos = {cid: i for i, cid in enumerate(cases.case_id)}
    lo, hi = ANALYSIS_REGION
    ref_cell = grid.find_cell(5, 0, 5, 0.5, 1.0)                       # §5.2 secondary reference DGP cell
    Dp = designs["primary"]
    d_ref = dgp.draw(Dp, ref_cell, seeds.replicate_seq(ref_cell.index, 0, root))
    A_ref, _ = dgp.simulate(Dp, ref_cell, d_ref)
    res = {}
    for key, path in full_paths.items():
        R, RC = _unpack_full(path)
        lens = np.array([len(x) for x in R[0]])
        all_idx = np.arange(len(cases))

        def all_steps(i):
            return np.arange(lens[i])

        r = {"E1_278": checks.e1(R, all_idx, sites, folds, all_steps, f"278:{key}", **kw),
             "E1_MLP_278": checks.mlp_site_probe(R, all_idx, sites, folds, all_steps, f"278:{key}", **kw)}
        rows278 = checks.e2_rows(all_idx, all_steps, s_all, lens)
        r["E2_278"] = _reporting(checks.e2_auc(rows278, R, folds, sites, f"278:{key}", **kw, **kb))
        r["E2_278_normtime"] = _reporting(checks.e2_auc(checks.normalized_time_rows(rows278), R, folds, sites,
                                                        f"278:{key}:normtime", **kw, **kb))
        for s in ("primary", "single_file"):
            D = designs[s]
            idx = np.array([pos[c] for c in D.ids])
            w = dict(zip(idx, D.window_start()))

            def region(i, w=w):
                return np.arange(w[i] + lo, w[i] + hi + 1)

            r[f"E1_{s}"] = checks.e1(R, idx, sites, folds, region, f"{s}:{key}", **kw)
            r[f"E1_MLP_{s}"] = checks.mlp_site_probe(R, idx, sites, folds, region, f"{s}:{key}", **kw)
            rows = checks.e2_rows(idx, region, s_all, lens)
            r[f"E2_{s}"] = checks.e2_auc(rows, R, folds, sites, f"{s}:{key}", **kw, **kb)
            r[f"E2_{s}_normtime"] = _reporting(checks.e2_auc(checks.normalized_time_rows(rows), R, folds, sites,
                                                             f"{s}:{key}:normtime", **kw, **kb))
            if RC is not None:
                r[f"E2_{s}_after_removal"] = checks.e2_auc(rows, RC, folds, sites, f"{s}:{key}-C", **kw, **kb)
                r[f"E3_site_{s}"] = checks.e3_site(RC, idx, sites, folds, region, f"{s}:{key}-C", **kw)
                r[f"E3_state_{s}"] = checks.e3_state_retention(r[f"E2_{s}"], r[f"E2_{s}_after_removal"])
        idx_p = np.array([pos[c] for c in Dp.ids])
        hrows, H = checks.history_rows(idx_p, Dp, A_ref, ref_cell.W, ref_cell.K)
        r["E2_primary_history"] = _reporting(checks.e2_auc(hrows, R, folds, sites, f"primary:{key}:history",
                                                           extra=H, **kw, **kb))
        r["E2_primary_history"]["reference_cell"] = dict(cell=ref_cell.index, replicate_spawn_index=0,
                                                         **ref_cell.as_dict())
        if RC is not None:
            r["E3_site_278"] = checks.e3_site(RC, all_idx, sites, folds, all_steps, f"278:{key}-C", **kw)
            r["fm_conditions_primary"] = checks.fm_conditions(r["E1_278"], r["E1_primary"], r["E3_site_278"],
                                                              r["E3_site_primary"], r["E3_state_primary"])
        res[key] = r
    with open(out_json, "w") as f:
        json.dump(res, f, indent=1, sort_keys=True, default=float)
    return res


def near_uniform(extract_dir, out_json, cases=None):
    """Near-uniform grid-frame proportions by centre, S and centre × S (§3.1 step 4; reporting only)."""
    if cases is None:
        cases = design.representation_cases()
        cases = cases.assign(s=design.representation_switch_steps().loc[cases.case_id].to_numpy())
    flags = [np.load(os.path.join(extract_dir, f"{cid}.near_uniform.npy")) for cid in cases.case_id]
    res = checks.near_uniform_summary(flags, cases.center.to_numpy(), cases.s.to_numpy())
    with open(out_json, "w") as f:
        json.dump(res, f, indent=1, sort_keys=True)
    return res


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a1 = sub.add_parser("mask-check"); a1.add_argument("--videos", required=True); a1.add_argument("--out", required=True)
    a2 = sub.add_parser("extract")
    for k in ("--videos", "--model", "--acq", "--out"):
        a2.add_argument(k, required=True)
    a2.add_argument("--r", type=float, default=MASK_RADIUS)
    a2.add_argument("--weights"); a2.add_argument("--batch", type=int, default=64); a2.add_argument("--device", default="cuda")
    a3 = sub.add_parser("build-reps"); a3.add_argument("--extract", nargs="+", required=True); a3.add_argument("--out", required=True)
    a4 = sub.add_parser("checks"); a4.add_argument("--reps-full", nargs="+", required=True); a4.add_argument("--out", required=True)
    a5 = sub.add_parser("near-uniform"); a5.add_argument("--extract", required=True); a5.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "mask-check":
        mask_check(a.videos, a.out)
    elif a.cmd == "extract":
        extract_all(a.videos, a.model, a.acq, a.r, a.out, a.weights, a.batch, a.device)
    elif a.cmd == "build-reps":
        build_reps(dict(x.split("=", 1) for x in a.extract), a.out)
    elif a.cmd == "checks":
        run_checks({os.path.basename(p).split("_full_")[1][:-4]: p for p in a.reps_full}, a.out)
    else:
        near_uniform(a.extract, a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
