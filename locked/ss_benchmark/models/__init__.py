"""Model adapters for extraction (§4.1.5 eligible models and the §4.2 Cosmos reference).

Every adapter module defines
    SPEC = dict(name, arm, kind ('frame' | 'clip' | 'cosmos'), input_size (H, W), clip_length (clip models),
                representation, normalisation, sources=[{quote, copy, level}], third_party=None | {repo, commit})
    build(weights=None, device='cpu', dtype=torch.float32) -> torch.nn.Module in eval mode; weights=None gives the
        architecture with random initialisation (code lock: no weights are downloaded)
    encode(model, x) -> (B, D) float tensor;
        frame models: x (B, 3, H, W) standardized frames in [0, 255];
        clip models:  x (B, L, 3, H, W) standardized grid-frame clips in [0, 255].
Normalisation to the model's input range happens inside encode().
"""
