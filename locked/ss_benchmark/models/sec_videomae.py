"""VideoMAE adapter (clip-level, secondary arm): the official self-supervised PRE-TRAINING checkpoints.

Class line (frozen): "VideoMAE eligibility applies to official pre-training checkpoints of the masked-autoencoder
model; supervised fine-tuned classification/action-recognition checkpoints are outside the secondary
reconstructive/generative class."

* Checkpoints (canonical identifiers): the nine distinct pre-training checkpoints of the official MODEL_ZOO.md
  (fm_sources/secondary/videomae_github_MODEL_ZOO.md; Google-Drive file ids below); the second K400 ViT-B 800-ep row
  reuses the same pre-training checkpoint ("same as above"). The Hugging Face MCG-NJU pre-trained-only repositories
  are converted copies ("first released in this repository"; aliases: videomae-base = K400 ViT-B 1600,
  videomae-base-short = K400 ViT-B 800, videomae-large = K400 ViT-L 1600, videomae-base-ssv2 = SSv2 ViT-B 2400); they
  are aliases, not separate ranking candidates, and are not used for extraction.
* Architecture: the original definitions pretrain_videomae_{small,base,large,huge}_patch16_224 of the official
  repository (third_party/VideoMAE/modeling_pretrain.py @ MCG-NJU/VideoMAE 14ef8d85, retrieved under
  decisions/CODELOCK_AUTH_002): encoder embed / depth / heads = S 384 / 12 / 6, B 768 / 12 / 12, L 1024 / 24 / 16,
  H 1280 / 32 / 16; mlp_ratio 4; qkv_bias True (q and v biases); LayerNorm eps 1e-6; init_values 0 (no layer
  scale); patch 16, tubelet 2, 16 frames, 224 × 224; fixed sinusoid position table. Implemented with transformers'
  VideoMAEModel configured to these values; original state dicts are mapped with the encoder rules of transformers'
  convert_videomae_to_pytorch.py. Equivalence with the original encoder code is checked in
  tests/test_codelock_extra.py on random weights.
* Input: L = 16 grid frames, 224 × 224, layout (B, T, 3, H, W).
* Normalisation (the pre-training data pipeline governs; rule R1): RGB frames / 255, then per channel
  (x − mean) / std with mean (0.485, 0.456, 0.406) and std (0.229, 0.224, 0.225), the values applied to every
  pre-training input by DataAugmentationForVideoMAE (datasets.py @ 14ef8d85, retrieved under
  decisions/CODELOCK_AUTH_003: "self.input_mean = [0.485, 0.456, 0.406]  # IMAGENET_DEFAULT_MEAN",
  "self.input_std = [0.229, 0.224, 0.225]  # IMAGENET_DEFAULT_STD", "normalize = GroupNormalize(self.input_mean,
  self.input_std)", composed after "Stack(roll=False)" and "ToTorchFormatTensor(div=True)"; transforms.py:
  Stack keeps RGB order when roll=False, ToTorchFormatTensor divides by 255, GroupNormalize applies "t.sub_(m).div_(s)"
  per channel). build_pretraining_dataset uses this transform for every pre-training dataset, so the values are the
  same for all nine checkpoints. Note: modeling_finetune.py::_cfg() reports mean / std 0.5 as model default_cfg
  metadata, but the pre-training data pipeline is the source that trained the pre-training checkpoints and governs
  under the source-priority rule.
* Representation: the encoder's forward_features output with no token masked, i.e. the final LayerNorm (encoder
  `self.norm`, = videomae.layernorm) applied to the last block's output, averaged over all 1,568 patch tokens
  (8 temporal × 14 × 14 spatial); VideoMAE has no CLS token. 384 (S), 768 (B), 1,024 (L) or 1,280 (H) values.
* Inference: eval(); no token masking; dropout / drop-path rates 0.
"""
import os

import torch

SIZES = {  # modeling_pretrain.py pretrain_videomae_*_patch16_224
    "small": dict(hidden_size=384, num_hidden_layers=12, num_attention_heads=6),
    "base": dict(hidden_size=768, num_hidden_layers=12, num_attention_heads=12),
    "large": dict(hidden_size=1024, num_hidden_layers=24, num_attention_heads=16),
    "huge": dict(hidden_size=1280, num_hidden_layers=32, num_attention_heads=16),
}
CHECKPOINTS = {  # key: (size, dataset, pre-training epochs, MODEL_ZOO Google-Drive file id, HF alias)
    "k400-vit-s-1600": ("small", "Kinetics-400", 1600, "1nU-H1u3eJ-VuyCveU7v-WIOcAVxs5Hww", None),
    "k400-vit-b-800": ("base", "Kinetics-400", 800, "1JfrhN144Hdg7we213H1WxwR3lGYOlmIn", "MCG-NJU/videomae-base-short"),
    "k400-vit-b-1600": ("base", "Kinetics-400", 1600, "1tEhLyskjb755TJ65ptsrafUG2llSwQE1", "MCG-NJU/videomae-base"),
    "k400-vit-l-1600": ("large", "Kinetics-400", 1600, "1qLOXWb_MGEvaI7tvuAe94CV7S2HXRwT3", "MCG-NJU/videomae-large"),
    "k400-vit-h-1600": ("huge", "Kinetics-400", 1600, "1AJQR1Rsi2N1pDn9tLyJ8DQrUREiBA1bO", None),
    "ssv2-vit-s-2400": ("small", "Something-Something V2", 2400, "1p_I1aaONOeUvRmRQw1UT3-L2H8XJClHu", None),
    "ssv2-vit-b-800": ("base", "Something-Something V2", 800, "181hLvyrrPW2IOGA46fkxdJk0tNLIgdB2", None),
    "ssv2-vit-b-2400": ("base", "Something-Something V2", 2400, "1I18dY_7rSalGL8fPWV82c0-foRUDzJJk",
                        "MCG-NJU/videomae-base-ssv2"),
    "ucf101-vit-b-3200": ("base", "UCF101", 3200, "1BHev4meNgKM0o_8DMRbuzAsKSP3IpQ3o", None),
}
MEAN, STD = (0.485, 0.456, 0.406), (0.229, 0.224, 0.225)   # datasets.py DataAugmentationForVideoMAE
CLASS_LINE = ("VideoMAE eligibility applies to official pre-training checkpoints of the masked-autoencoder model; "
              "supervised fine-tuned classification/action-recognition checkpoints are outside the secondary "
              "reconstructive/generative class.")

SPEC = dict(name="VideoMAE", arm="secondary", kind="clip", input_size=(224, 224), clip_length=16,
            representation="encoder forward_features (final LayerNorm of the last block) with no token masked, "
                           "mean over all 1568 patch tokens (8 x 14 x 14; no CLS token)",
            normalisation="RGB x/255, mean (0.485, 0.456, 0.406), std (0.229, 0.224, 0.225): the pre-training data "
                          "pipeline (datasets.py DataAugmentationForVideoMAE); _cfg() 0.5 is default_cfg metadata only",
            checkpoints=CHECKPOINTS, class_line=CLASS_LINE,
            sources=[dict(quote="encoder_embed_dim=384, encoder_depth=12, encoder_num_heads=6,",
                          copy="third_party/VideoMAE/modeling_pretrain.py", level=3),
                     dict(quote="encoder_embed_dim=1280, encoder_depth=32, encoder_num_heads=16,",
                          copy="third_party/VideoMAE/modeling_pretrain.py", level=3),
                     dict(quote="norm_layer=partial(nn.LayerNorm, eps=1e-6),",
                          copy="third_party/VideoMAE/modeling_pretrain.py", level=3),
                     dict(quote="self.input_mean = [0.485, 0.456, 0.406]  # IMAGENET_DEFAULT_MEAN",
                          copy="third_party/VideoMAE/datasets.py", level=3),
                     dict(quote="self.input_std = [0.229, 0.224, 0.225]  # IMAGENET_DEFAULT_STD",
                          copy="third_party/VideoMAE/datasets.py", level=3),
                     dict(quote="normalize = GroupNormalize(self.input_mean, self.input_std)",
                          copy="third_party/VideoMAE/datasets.py", level=3),
                     dict(quote="ToTorchFormatTensor(div=True),", copy="third_party/VideoMAE/datasets.py", level=3),
                     dict(quote="transform = DataAugmentationForVideoMAE(args)",
                          copy="third_party/VideoMAE/datasets.py", level=3),
                     dict(quote="t.sub_(m).div_(s)", copy="third_party/VideoMAE/transforms.py", level=3),
                     dict(quote="return (img.float().div(255.) if self.div else img.float(), label)",
                          copy="third_party/VideoMAE/transforms.py", level=3),
                     dict(quote="elif img_group[0].mode == 'RGB': if self.roll:",
                          copy="third_party/VideoMAE/transforms.py", level=3),
                     dict(quote="'mean': (0.5, 0.5, 0.5), 'std': (0.5, 0.5, 0.5),",
                          copy="third_party/VideoMAE/modeling_finetune.py", level=3),
                     dict(quote="\"num_frames\": 16,",
                          copy="data_audit/lead/fm_sources/secondary/videomae_videomae-base_config.json", level=3),
                     dict(quote="VideoMAE ViT-S 7 16 57×5×3 22 79.0 93.8",
                          copy="data_audit/lead/fm_sources/secondary/videomae_arxiv_2203.12602v3.txt.layout.txt",
                          level=1)],
            normalisation_note=("modeling_finetune.py::_cfg() reports mean/std 0.5 as model default_cfg metadata, but "
                                "the pre-training data pipeline is the source that trained the pre-training "
                                "checkpoints, and it governs under the source-priority rule. Fine-tuned checkpoints "
                                "remain outside the secondary class."),
            third_party=dict(repo="MCG-NJU/VideoMAE", commit="14ef8d856287c94ef1f985fe30f958eb4ec2c55d"))


def config_for(size):
    from transformers import VideoMAEConfig
    s = SIZES[size]
    return VideoMAEConfig(image_size=224, patch_size=16, num_channels=3, num_frames=16, tubelet_size=2,
                          hidden_size=s["hidden_size"], num_hidden_layers=s["num_hidden_layers"],
                          num_attention_heads=s["num_attention_heads"], intermediate_size=4 * s["hidden_size"],
                          hidden_act="gelu", hidden_dropout_prob=0.0, attention_probs_dropout_prob=0.0,
                          qkv_bias=True, layer_norm_eps=1e-6, use_mean_pooling=False)


def _rename_key(name):
    """Encoder part of transformers' convert_videomae_to_pytorch.rename_key (Apache-2.0)."""
    if "encoder." in name:
        name = name.replace("encoder.", "")
    if "cls_token" in name:
        name = name.replace("cls_token", "videomae.embeddings.cls_token")
    if "pos_embed" in name and "decoder" not in name:
        name = name.replace("pos_embed", "videomae.embeddings.position_embeddings")
    if "patch_embed.proj" in name:
        name = name.replace("patch_embed.proj", "videomae.embeddings.patch_embeddings.projection")
    if "patch_embed.norm" in name:
        name = name.replace("patch_embed.norm", "videomae.embeddings.norm")
    if "blocks" in name:
        name = name.replace("blocks", "videomae.encoder.layer")
    if "attn.proj" in name:
        name = name.replace("attn.proj", "attention.output.dense")
    if "attn" in name and "bias" not in name:
        name = name.replace("attn", "attention.self")
    if "attn" in name:
        name = name.replace("attn", "attention.attention")
    if "norm1" in name:
        name = name.replace("norm1", "layernorm_before")
    if "norm2" in name:
        name = name.replace("norm2", "layernorm_after")
    if "mlp.fc1" in name:
        name = name.replace("mlp.fc1", "intermediate.dense")
    if "mlp.fc2" in name:
        name = name.replace("mlp.fc2", "output.dense")
    if "norm.weight" in name and "fc" not in name:
        name = name.replace("norm.weight", "videomae.layernorm.weight")
    if "norm.bias" in name and "fc" not in name:
        name = name.replace("norm.bias", "videomae.layernorm.bias")
    return name


def convert_original(sd, hidden_size):
    """Original pre-training state dict -> VideoMAEModel state dict (encoder only; the fixed position table, the
    decoder, mask token and encoder_to_decoder are not parameters of the representation)."""
    for key in ("model", "module", "state_dict"):
        if key in sd and isinstance(sd[key], dict):
            sd = sd[key]
    out = {}
    for key, val in sd.items():
        if key.startswith(("decoder", "encoder_to_decoder", "mask_token")) or key.endswith("pos_embed"):
            continue
        k = key[len("encoder."):] if key.startswith("encoder.") else key
        if k.startswith("head."):
            continue
        if "qkv" in k:
            layer = int(k.split(".")[1])
            p = f"encoder.layer.{layer}.attention.attention."
            if "weight" in k:
                out[p + "query.weight"] = val[:hidden_size]
                out[p + "key.weight"] = val[hidden_size:2 * hidden_size]
                out[p + "value.weight"] = val[-hidden_size:]
            continue
        k = _rename_key(k)
        out[k[len("videomae."):] if k.startswith("videomae.") else k] = val
    return out


def build(weights=None, device="cpu", dtype=torch.float32, checkpoint="k400-vit-b-1600"):
    """weights=None: random initialisation of the checkpoint's architecture; weights=path: the official original-format
    pre-training checkpoint file of ``checkpoint`` (strict key check)."""
    from transformers import VideoMAEModel
    size = CHECKPOINTS[checkpoint][0]
    config = config_for(size)
    model = VideoMAEModel(config)
    if weights is not None:
        sd = convert_original(torch.load(weights, map_location="cpu", weights_only=False), config.hidden_size)
        missing, unexpected = model.load_state_dict(sd, strict=False)
        if missing or unexpected:
            raise RuntimeError(f"checkpoint mismatch: missing {missing[:5]}, unexpected {unexpected[:5]}")
    model.ss_checkpoint = checkpoint
    return model.to(device=device, dtype=dtype).eval()


def encode(model, x):
    p = next(model.parameters())
    mean = torch.tensor(MEAN, device=x.device).view(1, 1, 3, 1, 1)
    std = torch.tensor(STD, device=x.device).view(1, 1, 3, 1, 1)
    out = model(pixel_values=((x / 255.0 - mean) / std).to(p.dtype))
    return out.last_hidden_state.mean(1)
