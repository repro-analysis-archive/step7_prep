# Third-party notices — step7_prep

The model adapters in `locked/ss_benchmark/models/` are the authors' original code (MIT, `LICENSE`). They contain no upstream source file,
configuration file or weight file. They do contain upstream material quoted or adapted for provenance, listed below with
its licence; this material is **not** covered by the MIT licence. Licence texts as fetched on 2026-11-04 from the pinned
upstream revisions are in `LICENSES/upstream/`; the Apache License 2.0 is in `LICENSES/Apache-2.0.txt`.

Built on NVIDIA Cosmos: the NVIDIA Cosmos tokenizer weights are licensed by NVIDIA Corporation under the NVIDIA Open Model
License (https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/) and are not included.

## Per adapter

### `locked/ss_benchmark/models/prim_caformer.py`

* Upstream: SurgeNet (SurgeNetCholec / SurgeNetRARP, CAFormer-S18). Paper: Jaspers TJM et al., Med Image Anal 2026;108:103873, doi:10.1016/j.media.2025.103873. Code: github.com/TimJaspers0801/SurgeNet @ 54831cfacf3a6cac0bbf5119f72b9cb9c31c3e82 — MIT License, Copyright (c) 2025 Cris Claessens. metaformer.py is imported at run time from third_party/ (not included). Weights: huggingface.co/TimJaspersTue/SurgeNetModels @ cc21f4a1 — CC BY-NC 4.0 (HF card; the GitHub LICENSE_MODELS.txt states CC BY-NC-SA 4.0); not included.
* Embedded upstream material: short quotations of metaformer.py, the SurgeNet README and the paper (SOURCES).

### `locked/ss_benchmark/models/prim_resnet50.py`

* Upstream: SelfSupSurg ResNet-50 (MoCo v2 / SimCLR / SwAV / DINO). Paper: Ramesh S et al., "Dissecting self-supervised learning methods for surgical computer vision", Med Image Anal 2023;102844. Code, models and configs: github.com/CAMMA-public/SelfSupSurg (main @ 8a03d289) — CC BY-NC-SA 4.0; weights not included. Architecture: torchvision ResNet-50 (dependency, BSD-3-Clause).
* Embedded upstream material: three configuration values quoted from the SelfSupSurg hparams YAML and one sentence of the paper (SPEC sources), under CC BY-NC-SA 4.0 / the paper's terms.

### `locked/ss_benchmark/models/ref_cosmos.py`

* Upstream: NVIDIA Cosmos-1.0-Tokenizer-CV8x8x8 (arXiv:2501.03575). Built on NVIDIA Cosmos. Weights: huggingface.co/nvidia/Cosmos-1.0-Tokenizer-CV8x8x8 @ 5110dbb3 — licensed by NVIDIA Corporation under the NVIDIA Open Model License (gated); not included. Implementation: diffusers AutoencoderKLCosmos (dependency, Apache-2.0); equivalence checked against github.com/NVIDIA/Cosmos-Tokenizer @ 3584ae75 (Apache-2.0, not included).
* Embedded upstream material: two quotations of src/gpi_pack/video.py, github.com/gpi-pack/gpi_pack @ 8836037d — MIT License, Copyright (c) 2025 Kentaro Nakamura.

### `locked/ss_benchmark/models/sec_larp.py`

* Upstream: LARP (arXiv:2410.21264). Code: github.com/hywang66/LARP @ 8aaed63354c8c0fabcb8a86a2e31c34320e6db86 — MIT License, Copyright (c) 2024 Hanyu Wang; loaded at run time from third_party/ (not included). Weights: huggingface.co/hywang66/LARP-L-long-tokenizer @ c93a7e2d (no licence declared); not included.
* Embedded upstream material: CONFIG is the verbatim config.json of the Hugging Face repository (machine-generated hyperparameter values of the LARP code); short quotations of the LARP code, README, scripts and paper (SPEC sources).

### `locked/ss_benchmark/models/sec_leanvae.py`

* Upstream: LeanVAE (arXiv:2503.14325). Code: github.com/westlake-repl/LeanVAE @ 62f7c7d5 — MIT License, Copyright (c) 2025 westlake-repl; loaded at run time from third_party/ (not included). Weights: huggingface.co/Yumic/LeanVAE @ 4585e461 — MIT; not included.
* Embedded upstream material: architecture values and short quotations of the LeanVAE code, README, scripts and paper (SPEC sources).

### `locked/ss_benchmark/models/sec_omnitokenizer.py`

* Upstream: OmniTokenizer (arXiv:2406.09399). Code: github.com/FoundationVision/OmniTokenizer @ 701b6190 — MIT License, Copyright (c) 2024 FoundationVision; executed at run time from third_party/ (not included). Weights: huggingface.co/Daniel0724/OmniTokenizer @ 9ebde216 (no licence declared); not included.
* Embedded upstream material: ARGS (values of scripts/recons/eval_video.sh and argparse defaults) and short quotations of the OmniTokenizer code, scripts, README and paper (SPEC sources).

### `locked/ss_benchmark/models/sec_videomae.py`

* Upstream: VideoMAE (arXiv:2203.12602). Code and checkpoints: github.com/MCG-NJU/VideoMAE @ 14ef8d85 — CC BY-NC 4.0; not included (architecture via transformers VideoMAEModel, dependency, Apache-2.0).
* Embedded upstream material: short quotations of the VideoMAE code (CC BY-NC 4.0) and paper (SPEC sources).
* Apache-2.0 notice: _rename_key and the qkv split in convert_original are adapted from Hugging Face Transformers v4.46.3, src/transformers/models/videomae/convert_videomae_to_pytorch.py, Copyright 2022 The HuggingFace Inc. team, licensed under the Apache License, Version 2.0 (LICENSES/Apache-2.0.txt). Changed by the authors: only the encoder renaming rules are kept.

### `locked/ss_benchmark/models/sec_wfvae.py`

* Upstream: WF-VAE (arXiv:2411.17459). Code: github.com/PKU-YuanGroup/WF-VAE @ d858bee8 — Apache License 2.0; loaded at run time from third_party/ (not included). Weights: huggingface.co/chestnutlzj/WF-VAE-L-16Chn @ 8c0aa9ce — Apache-2.0; not included.
* Embedded upstream material: CONFIG is the released config.json (Apache-2.0; changed by the authors: the private keys _class_name and _diffusers_version are dropped); short quotations of the WF-VAE code, scripts, README and paper (SPEC sources). Licence text: LICENSES/Apache-2.0.txt.

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

## Licence texts in `LICENSES/upstream/`

| file | project, revision | licence |
|---|---|---|
| `SurgeNet-LICENSE.txt` | TimJaspers0801/SurgeNet @ 54831cfa (`LICENSE.txt`) | MIT, © 2025 Cris Claessens |
| `SurgeNet-LICENSE_MODELS.txt` | TimJaspers0801/SurgeNet @ 54831cfa (`LICENSE_MODELS.txt`) | CC BY-NC-SA 4.0 (models) |
| `SelfSupSurg-LICENSE.txt` | CAMMA-public/SelfSupSurg @ 8a03d289 | CC BY-NC-SA 4.0 |
| `Cosmos-Tokenizer-LICENSE.txt` | NVIDIA/Cosmos-Tokenizer @ 3584ae75 | Apache-2.0 |
| `gpi_pack-LICENSE.txt` | gpi-pack/gpi_pack @ 8836037d | MIT, © 2025 Kentaro Nakamura |
| `LARP-LICENSE.txt` | hywang66/LARP @ 8aaed633 | MIT, © 2024 Hanyu Wang |
| `LeanVAE-LICENSE.txt` | westlake-repl/LeanVAE @ 62f7c7d5 | MIT, © 2025 westlake-repl |
| `OmniTokenizer-LICENSE.txt` | FoundationVision/OmniTokenizer @ 701b6190 | MIT, © 2024 FoundationVision |
| `VideoMAE-LICENSE.txt` | MCG-NJU/VideoMAE @ 14ef8d85 | CC BY-NC 4.0 |
| `WF-VAE-LICENSE.txt` | PKU-YuanGroup/WF-VAE @ d858bee8 | Apache-2.0 |
| `transformers-LICENSE.txt` | huggingface/transformers v4.46.3 | Apache-2.0, © 2018- The Hugging Face team |
