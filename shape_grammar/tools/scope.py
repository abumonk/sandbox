"""scope.py — Scope dataclass and ScopeStack for shape-grammar evaluation.

A Scope carries the transform state (translation, rotation, scale, size)
plus a `dict[str, Any]` attribute bag inherited down the derivation tree.
The ScopeStack is a simple LIFO stack that supports push/pop/top/get and
is the evaluator's dynamic-scope chain.

Transform vectors are represented as `tuple[float, float, float]` (Vec3).
Using tuples (not lists) keeps scopes immutable/hashable.

Semantic contract (matches design-evaluator.md):
  - `Scope.identity()` is the zero-translation, zero-rotation,
    unit-scale, zero-size scope with an empty attrs dict.
  - `Scope.push(override)` returns a NEW Scope with the given attrs
    layered over the parent's attrs (child overrides parent).
  - `ScopeStack.push(scope)` appends to the top; `top()` returns the
    current scope; `pop()` removes and returns it; `get(name)` resolves
    an attribute by walking the stack top -> bottom.

Attribute safety (e.g. get() on an undefined attr) is checked
statically by `shape_grammar/tools/verify/scope.py` — at runtime this
module raises KeyError for undefined attrs.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Optional


Vec3 = tuple[float, float, float]


_ZERO: Vec3 = (0.0, 0.0, 0.0)
_ONE: Vec3 = (1.0, 1.0, 1.0)


@dataclass(frozen=True)
class Scope:
    """Immutable transform + attribute bundle for one level of derivation."""

    translation: Vec3 = _ZERO
    rotation: Vec3 = _ZERO
    scale: Vec3 = _ONE
    size: Vec3 = _ZERO
    attrs: tuple[tuple[str, Any], ...] = field(default_factory=tuple)

    # ------------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------------

    @classmethod
    def identity(cls) -> "Scope":
        """Return the canonical identity scope."""
        return cls()

    def push(self, override: Optional[dict[str, Any]] = None) -> "Scope":
        """Return a new Scope that inherits this scope's attrs and layers
        the override map on top.

        Non-attribute transform fields are copied verbatim; pass a new
        Scope via dataclasses.replace when you need to change transforms.
        """
        base = dict(self.attrs)
        if override:
            base.update(override)
        return replace(self, attrs=tuple(sorted(base.items())))

    def with_transform(
        self,
        translation: Optional[Vec3] = None,
        rotation: Optional[Vec3] = None,
        scale: Optional[Vec3] = None,
        size: Optional[Vec3] = None,
    ) -> "Scope":
        """Return a new Scope with one or more transform fields replaced."""
        return replace(
            self,
            translation=translation if translation is not None else self.translation,
            rotation=rotation if rotation is not None else self.rotation,
            scale=scale if scale is not None else self.scale,
            size=size if size is not None else self.size,
        )

    # ------------------------------------------------------------------
    # Attribute access
    # ------------------------------------------------------------------

    def get(self, name: str, default: Any = None) -> Any:
        """Return the attribute value or `default` if missing."""
        for k, v in self.attrs:
            if k == name:
                return v
        return default

    def has(self, name: str) -> bool:
        return any(k == name for k, _ in self.attrs)

    def as_dict(self) -> dict[str, Any]:
        """Return attrs as a plain dict (useful for serialization)."""
        return dict(self.attrs)


class ScopeStack:
    """LIFO stack of scopes. The top is the current dynamic scope."""

    def __init__(self, initial: Optional[list[Scope]] = None):
        self._frames: list[Scope] = list(initial) if initial else []

    def push(self, scope: Scope) -> "ScopeStack":
        """Push a scope onto the top of the stack and return self."""
        self._frames.append(scope)
        return self

    def pop(self) -> Scope:
        """Pop and return the top scope."""
        if not self._frames:
            raise IndexError("ScopeStack: pop from empty stack")
        return self._frames.pop()

    def top(self) -> Scope:
        """Return (without removing) the top scope."""
        if not self._frames:
            raise IndexError("ScopeStack: top of empty stack")
        return self._frames[-1]

    def depth(self) -> int:
        return len(self._frames)

    def get(self, name: str) -> Any:
        """Walk the stack top->bottom and return the first defined attr.

        Raises KeyError when the attribute is defined nowhere in the chain.
        The scope-safety Z3 pass proves statically that every runtime
        `get(name)` will succeed; this runtime check is a belt-and-braces
        fallback.
        """
        for frame in reversed(self._frames):
            if frame.has(name):
                return frame.get(name)
        raise KeyError(f"scope attribute not defined: {name!r}")

    def __len__(self) -> int:
        return len(self._frames)

    def __repr__(self) -> str:            # pragma: no cover
        return f"ScopeStack(depth={len(self._frames)})"
