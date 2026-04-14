"""rng.py — Seeded deterministic RNG with label-based forking.

`SeededRng(seed)` wraps `random.Random(seed)`. The `.fork(label)` helper
produces a new independent RNG whose seed is derived deterministically
from `(parent_seed, label)` via hashlib.sha256 — which is stable across
Python invocations (unlike the builtin `hash()` salted by PYTHONHASHSEED).

This is the evaluator's only entropy source; the `determinism` verifier
pass proves that no spec references wall-clock or environment state.

Public surface (matches design-evaluator.md):
  - `SeededRng(seed: int)`
  - `SeededRng.fork(label: str) -> SeededRng`
  - `.random() -> float` (uniform [0, 1))
  - `.randint(a, b) -> int` (inclusive endpoints)
  - `.choice(seq)`
  - `.uniform(a, b)`

Invariant (TC-19):
    SeededRng(s).fork(L) and SeededRng(s).fork(L) produce identical
    sequences across runs and processes.
"""

from __future__ import annotations

import hashlib
import random
from typing import Any, Iterable, Sequence


_MASK_32 = 0xFFFFFFFF


def _derive_subseed(parent_seed: int, label: str) -> int:
    """Deterministic 32-bit subseed from (parent_seed, label).

    Uses sha256 (stable across runs; `hash()` is PYTHONHASHSEED-salted
    and therefore non-deterministic across processes).
    """
    payload = f"{int(parent_seed)}::{label}".encode("utf-8")
    digest = hashlib.sha256(payload).digest()
    return int.from_bytes(digest[:4], "big") & _MASK_32


class SeededRng:
    """Deterministic, forkable RNG wrapper over `random.Random`."""

    __slots__ = ("_seed", "_rng")

    def __init__(self, seed: int):
        if not isinstance(seed, int):
            raise TypeError(f"SeededRng seed must be int, got {type(seed).__name__}")
        self._seed: int = int(seed) & _MASK_32
        self._rng = random.Random(self._seed)

    @property
    def seed(self) -> int:
        return self._seed

    # ------------------------------------------------------------------
    # Forking — deterministic by (parent_seed, label)
    # ------------------------------------------------------------------

    def fork(self, label: str) -> "SeededRng":
        """Return a new independent RNG subseeded from (self.seed, label).

        Identical calls produce identical child sequences across runs.
        """
        if not isinstance(label, str):
            raise TypeError(f"fork label must be str, got {type(label).__name__}")
        return SeededRng(_derive_subseed(self._seed, label))

    # ------------------------------------------------------------------
    # Sampling — forwarded to the underlying random.Random
    # ------------------------------------------------------------------

    def random(self) -> float:
        """Uniform float in [0, 1)."""
        return self._rng.random()

    def randint(self, a: int, b: int) -> int:
        """Uniform int in [a, b] (inclusive)."""
        return self._rng.randint(a, b)

    def uniform(self, a: float, b: float) -> float:
        """Uniform float in [a, b]."""
        return self._rng.uniform(a, b)

    def choice(self, seq: Sequence[Any]) -> Any:
        """Pick one element from seq."""
        return self._rng.choice(seq)

    def shuffle(self, seq: list[Any]) -> None:
        """Shuffle in-place (rarely needed in deterministic evaluation)."""
        self._rng.shuffle(seq)

    def sample(self, population: Iterable[Any], k: int) -> list[Any]:
        """Sample k elements without replacement."""
        return self._rng.sample(list(population), k)

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def __repr__(self) -> str:               # pragma: no cover
        return f"SeededRng(seed={self._seed})"
