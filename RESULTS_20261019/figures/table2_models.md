**Table 2. Models and representations**

| arm | model | kind | input | representation | reduction | selection |
|---|---|---|---|---|---|---|
| FM-P (primary, standardized) | SurgeNetCholec (CAFormer-S18), TimJaspersTue/SurgeNetModels @cc21f4a1, CHOLEC_checkpoint_epoch0050_teacher.pth | frame-level | 2-fps grid frames; crop, mask, 224², ImageNet normalisation | pooled normalised features, 512-d; mean of the step's 10 grid frames | PCA 64 (+ LEACE for FM-P−C) | §4.1 rank 1 (after CODELOCK_CORRECTION_001) |
| FM-P-nat (native sensitivity) | SurgeNetCholec (as above) | frame-level | 2-fps grid frames; resize only | as FM-P | PCA 64 (no −C arm) | §3.2 |
| FM-S (secondary) | LeanVAE-4ch, Yumic/LeanVAE @4585e461, LeanVAE-dim4.ckpt | clip-level (L = 17 grid frames) | 2-fps grid frames; crop, mask, 256² | posterior mean 4 × 32 × 32 averaged over latent time, 4,096-d | PCA 64 (+ LEACE for FM-S−C) | §4.1 secondary rank 1 (tie-break 2: GFLOPs) |
| REF (reference) | nvidia/Cosmos-1.0-Tokenizer-CV8x8x8 @5110dbb3 (diffusers AutoencoderKLCosmos) | native clip (≤ 121 native frames per 5-s step) | crop, mask, 320² | post_quant_conv(latent mode) averaged over latent time, 16 × 40 × 40 = 25,600 | PCA 64 via randomized SVD (+ LEACE for REF−C) | Decision 005 (not ranked) |
