# step7_prep

**SS-DS203 step-7 reporting.** Step-7 reporting: the preparation directory versioned before any step-6 result was read, the step-7 orchestration, the results report with figures and tables (`RESULTS_20261019/`), the supplement (`SUPPLEMENT_20261020/`, figure source data), evidence preserved from non-committed logs, and the methods draft.

Part of the code and records of the manuscript *Semi-synthetic evaluation of site information and linear erasure in clinical video representations for sequentially doubly robust causal effect estimation* (Nakano H, Shiinoki T; article DOI: [TO FILL]). The six repositories of this release are archived together, as git bundles at tag `v1.0.0-submission`, on Zenodo: https://doi.org/10.5281/zenodo.23934337.

Repositories of this release:

* [`medical_video_causal_gate`](https://github.com/repro-analysis-archive/medical_video_causal_gate)
* [`ss_exploratory`](https://github.com/repro-analysis-archive/ss_exploratory)
* [`ss_exploratory_B`](https://github.com/repro-analysis-archive/ss_exploratory_B)
* [`step7_prep`](https://github.com/repro-analysis-archive/step7_prep)
* [`jbi_figures_tables`](https://github.com/repro-analysis-archive/jbi_figures_tables)
* [`ss-ds203-records`](https://github.com/repro-analysis-archive/ss-ds203-records)

Release: tag `v1.0.0-submission` (2026-11-04).

## Contents

`STEP7_PROCEDURE.md`, `PREP_REPORT.md`, `PRESENTATION_DECISIONS.md`, `POST_RESULT_PRESENTATION.md`, `step7_orchestrate.py`, `run_step7.sh`, `make_report.py`, `make_figures.py`, `make_supplement.py`, `locked/` (copy of the locked package and protocol), `PLACEHOLDER_test/` (synthetic dry run), `RESULTS_20261019/`, `SUPPLEMENT_20261020/`, `evidence/`, `METHODS_DRAFT.md`, `CONFIRM_ITEMS_20261019.md`, `X_B_READOUT_20261020.md`.

## Commit identifiers cited in the manuscript (Supplementary Methods) and records

Each identifier can be checked with `git show <ID>` in a clone of this repository.

| meaning | original ID (cited in the Supplementary Methods / records) | ID in this repository |
|---|---|---|
| evidence preservation | `84d8e2d` (`84d8e2d934db47fdc713087ee4b8fc7f89fa333d`) | `84d8e2d934db47fdc713087ee4b8fc7f89fa333d` (unchanged) |
| evaluator-record confirmation items | `fa2b8c7` (`fa2b8c7e2fd88d08b49092059e4e191910c0f44c`) | `fa2b8c7e2fd88d08b49092059e4e191910c0f44c` (unchanged) |
| reporting completion (task table; not in SM v4) | `43b70a2` (`43b70a2dd3e52f1471fa162bb1a6d1f49c53a150`) | `43b70a2dd3e52f1471fa162bb1a6d1f49c53a150` (unchanged) |

## Not included

* video files and per-frame representations of Appendix300
* model weights and upstream source code (see *Upstream models and licences*)

The history is published unchanged (no third-party material found); all commit identifiers are the original ones. Records in this repository cite original identifiers of `medical_video_causal_gate` and `ss_exploratory`; `COMMIT_ID_MAP.md` in those repositories resolves them. At release, a comment-only licence header was prepended to the eight files of `locked/ss_benchmark/models/` (Python AST unchanged); the locked versions are those of the earlier commits.

Scripts and records contain absolute paths of the machines on which the analysis ran (for example `/home/user/…`, `/srv/…`, `/media/user/LaCie/…`, `/Volumes/ADDATA/…`). They are recorded as they were; adapt them to re-run.

## Upstream models and licences

The eight model adapters in `locked/ss_benchmark/models/` are **the authors' original code** (MIT). They contain **no upstream source file, configuration file or weight file**: upstream code is obtained by the user from the upstream repositories at the pinned commits (secondary models and VideoMAE: `scripts/fetch_third_party.sh` in `medical_video_causal_gate`; SurgeNet `metaformer.py`: `decisions/CODELOCK_CORRECTION_001_SURGENET_ADAPTER.md` there) and weights are loaded from local paths under the upstream licences. What the adapters do contain is **upstream material quoted for provenance** (short verbatim quotations, each with its source, in `SPEC["sources"]` and the docstrings), two upstream configuration dictionaries (`sec_larp.py` `CONFIG`, `sec_wfvae.py` `CONFIG`) and one function adapted from Hugging Face transformers (`sec_videomae.py`). **This upstream material is not licensed under MIT**; it remains under the upstream licences below and is reproduced with attribution for non-commercial research use. Each adapter starts with a comment header stating this (added at release; the code is unchanged).

| adapter | upstream model | upstream code (pinned) — licence | weights / configuration — licence | paper |
|---|---|---|---|---|
| `locked/ss_benchmark/models/prim_caformer.py` | SurgeNetCholec / SurgeNetRARP (CAFormer-S18) | [TimJaspers0801/SurgeNet](https://github.com/TimJaspers0801/SurgeNet) @ `54831cfa` — MIT (© 2025 Cris Claessens) | [TimJaspersTue/SurgeNetModels](https://huggingface.co/TimJaspersTue/SurgeNetModels) @ `cc21f4a1` — CC BY-NC 4.0 (HF card); the GitHub `LICENSE_MODELS.txt` states CC BY-NC-SA 4.0 | Jaspers et al., Med Image Anal 2026;108:103873, doi:10.1016/j.media.2025.103873 |
| `locked/ss_benchmark/models/prim_resnet50.py` | SelfSupSurg ResNet-50 (MoCo v2 / SimCLR / SwAV / DINO) | [CAMMA-public/SelfSupSurg](https://github.com/CAMMA-public/SelfSupSurg) (`main` @ `8a03d289`) — CC BY-NC-SA 4.0 | same — CC BY-NC-SA 4.0 (code, models and datasets); architecture: torchvision ResNet-50 | Ramesh et al., Med Image Anal 2023;102844 |
| `locked/ss_benchmark/models/ref_cosmos.py` | NVIDIA Cosmos-1.0-Tokenizer-CV8x8x8 (reference) | [NVIDIA/Cosmos-Tokenizer](https://github.com/NVIDIA/Cosmos-Tokenizer) @ `3584ae75` — Apache-2.0 (equivalence check only); quoted: [gpi-pack/gpi_pack](https://github.com/gpi-pack/gpi_pack) @ `8836037d` — MIT (© 2025 Kentaro Nakamura) | [nvidia/Cosmos-1.0-Tokenizer-CV8x8x8](https://huggingface.co/nvidia/Cosmos-1.0-Tokenizer-CV8x8x8) @ `5110dbb3` — NVIDIA Open Model License (gated) | arXiv:2501.03575 |
| `locked/ss_benchmark/models/sec_larp.py` | LARP-L-Long tokenizer | [hywang66/LARP](https://github.com/hywang66/LARP) @ `8aaed633` — MIT (© 2024 Hanyu Wang) | [hywang66/LARP-L-long-tokenizer](https://huggingface.co/hywang66/LARP-L-long-tokenizer) @ `c93a7e2d` — no licence declared | arXiv:2410.21264 |
| `locked/ss_benchmark/models/sec_leanvae.py` | LeanVAE (16ch / 4ch) | [westlake-repl/LeanVAE](https://github.com/westlake-repl/LeanVAE) @ `62f7c7d5` — MIT (© 2025 westlake-repl) | [Yumic/LeanVAE](https://huggingface.co/Yumic/LeanVAE) @ `4585e461` — MIT | arXiv:2503.14325 |
| `locked/ss_benchmark/models/sec_omnitokenizer.py` | OmniTokenizer (ImageNet + K600, VQVAE / VAE) | [FoundationVision/OmniTokenizer](https://github.com/FoundationVision/OmniTokenizer) @ `701b6190` — MIT (© 2024 FoundationVision) | [Daniel0724/OmniTokenizer](https://huggingface.co/Daniel0724/OmniTokenizer) @ `9ebde216` — no licence declared | arXiv:2406.09399 |
| `locked/ss_benchmark/models/sec_videomae.py` | VideoMAE pre-training checkpoints | [MCG-NJU/VideoMAE](https://github.com/MCG-NJU/VideoMAE) @ `14ef8d85` — CC BY-NC 4.0; adapted code from [huggingface/transformers](https://github.com/huggingface/transformers) v4.46.3 — Apache-2.0 | official checkpoints of `MODEL_ZOO.md` — CC BY-NC 4.0 (repository licence) | arXiv:2203.12602 |
| `locked/ss_benchmark/models/sec_wfvae.py` | WF-VAE-L 16ch | [PKU-YuanGroup/WF-VAE](https://github.com/PKU-YuanGroup/WF-VAE) @ `d858bee8` — Apache-2.0 | [chestnutlzj/WF-VAE-L-16Chn](https://huggingface.co/chestnutlzj/WF-VAE-L-16Chn) @ `8c0aa9ce` — Apache-2.0 | arXiv:2411.17459 |

* **Apache-2.0 material:** `sec_videomae.py` (`_rename_key` and the `qkv` split of `convert_original`, adapted from transformers v4.46.3 `convert_videomae_to_pytorch.py`, Copyright 2022 The HuggingFace Inc. team; modified: encoder rules only) and `sec_wfvae.py` (`CONFIG` = the released `config.json`, private keys `_class_name` / `_diffusers_version` dropped). Licence text: `LICENSES/Apache-2.0.txt`. Neither upstream project ships a NOTICE file at the pinned revision.
* **Non-commercial licences:** quotations from VideoMAE (CC BY-NC 4.0) and SelfSupSurg (CC BY-NC-SA 4.0) are verbatim excerpts shared for non-commercial research with attribution; the corresponding weights are licensed for non-commercial use only.
* **Built on NVIDIA Cosmos.** The Cosmos tokenizer weights are licensed by NVIDIA Corporation under the NVIDIA Open Model License; they are not included here and must be obtained (and the licence accepted) from Hugging Face.
* Full notices: `NOTICE`, `THIRD_PARTY_NOTICES.md`, `LICENSES/` (upstream licence texts as fetched from the pinned revisions on 2026-11-04).

## Data source and attribution

The video data are Appendix300 (CC BY 4.0), used with attribution (manuscript references 1 and 45):

* Kolbinger FR, Kirchner M, Pfeiffer K, Bodenstedt S, Jenke AC, Barthel J, et al. Appendix300: Surgical video and patient metadata of 330 laparoscopic appendectomy cases from five institutions [dataset]. Technische Universität Dresden, OPARA; 2026-04-29. doi:10.25532/OPARA-1173. License: CC BY 4.0.
* Kolbinger FR, Kirchner M, Pfeiffer K, Bodenstedt S, Jenke AC, Barthel J, et al. Appendix300: Surgical video and patient metadata of 330 laparoscopic appendectomy cases from five institutions. Sci Data. 2026;13:886. doi:10.1038/s41597-026-07593-6.

No video file, video frame or per-frame representation is redistributed here.

## Licence

* **Original code** (the `*.py` / `*.sh` scripts and `locked/ss_benchmark/`): MIT License — see `LICENSE`. Copyright (c) 2026 Hisashi Nakano.
* **Records, results and figure data** (the reports, `RESULTS_20261019/`, `SUPPLEMENT_20261020/` (figure source data), `evidence/` and the records): Creative Commons Attribution 4.0 International (CC BY 4.0) — see `LICENSE-CC-BY-4.0`.
* **Not covered by either licence:** third-party material quoted or embedded in this repository remains under its own terms (the upstream material in the model adapters — see *Upstream models and licences*, `NOTICE`, `THIRD_PARTY_NOTICES.md`).

## How to cite

Please cite the article (DOI: [TO FILL]) and the Zenodo archive https://doi.org/10.5281/zenodo.23934337; machine-readable metadata: `CITATION.cff`.

## Use of AI tools

Most commits carry a `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` line: code and records were produced with Claude Code under the investigator's instructions, as declared in the manuscript. Automated record commits made by the runners carry no such line. The lines are kept unchanged.

## Authors and contact

* Hisashi Nakano (ORCID [0000-0002-9023-880X](https://orcid.org/0000-0002-9023-880X)), Department of Health Data Science, Niigata University of Health and Welfare — hisashi-nakano@nuhw.ac.jp (corresponding)
* Takehiro Shiinoki (ORCID [0000-0002-0246-8489](https://orcid.org/0000-0002-0246-8489)), Department of Radiation Oncology, Yamaguchi University
