"""Seed derivation (§10.2; implementation note N8).

* Replicate seeds: ``np.random.SeedSequence(root, spawn_key=(cell_index, replicate_index))``. This equals
  ``SeedSequence(root).spawn(...)[cell_index].spawn(...)[replicate_index]``.
* A named stream of a SeedSequence is its child with one extra spawn-key element ``int.from_bytes(name, 'big')``;
  e.g. the replicate's "c-permutation" stream (§6).
* root = 20261007 for the protocol grid; PLACEHOLDER runs use streams derived from 99990001 instead.
"""
import numpy as np

from .constants import SEED_PLACEHOLDER, SEED_REPLICATES


def name_key(name: str) -> int:
    return int.from_bytes(name.encode("ascii"), "big")


def child(seq: np.random.SeedSequence, *names) -> np.random.SeedSequence:
    """Child of ``seq`` addressed by names (str) or integers, appended to its spawn key."""
    key = tuple(seq.spawn_key) + tuple(name_key(n) if isinstance(n, str) else int(n) for n in names)
    return np.random.SeedSequence(seq.entropy, spawn_key=key)


def rng(seq: np.random.SeedSequence, *names) -> np.random.Generator:
    return np.random.default_rng(child(seq, *names) if names else seq)


def replicate_seq(cell_index: int, replicate_index: int, root: int = SEED_REPLICATES) -> np.random.SeedSequence:
    return np.random.SeedSequence(root, spawn_key=(int(cell_index), int(replicate_index)))


def placeholder_seq(*names) -> np.random.SeedSequence:
    """Stream derived from the code-lock PLACEHOLDER seed 99990001."""
    return child(np.random.SeedSequence(SEED_PLACEHOLDER), *names)


def placeholder_replicate_root() -> int:
    """Integer root for PLACEHOLDER replicate SeedSequences (derived from 99990001, distinct from 20261007)."""
    return int(placeholder_seq("replicates").generate_state(1, dtype=np.uint64)[0])
