"""ops.py — Shape-grammar operation primitives.

One class per primitive op (ExtrudeOp, SplitOp, CompOp, ScopeOp, IOp,
TOp, ROp, SOp).  Each implements:

    apply(scope: Scope, rng: SeededRng, label: str)
        -> list[tuple[Scope, str, str]]

The evaluator calls `apply` for every op in a rule and enqueues the
returned (child_scope, child_symbol, child_label) triples.

**IOp** is the terminal producer.  It does NOT return child work items;
instead it returns the sentinel list

    [(_TERMINAL_SENTINEL, asset_path, label)]

where ``_TERMINAL_SENTINEL`` is the module-level constant exported as
``TERMINAL``.  The evaluator checks ``child_symbol is TERMINAL`` to
distinguish produced terminals from ordinary rewrite work.

Factory
-------
``make_op(kind, **fields) -> Op``
    Dispatches on ``kind`` (the ``$data kind`` field in the IR entity dict)
    and constructs the matching op class.

``OP_REGISTRY``
    ``dict[str, type[Op]]`` mapping kind-string -> class; used by the
    evaluator for dispatch.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from shape_grammar.tools.scope import Scope, Vec3
from shape_grammar.tools.rng import SeededRng


# ---------------------------------------------------------------------------
# Terminal sentinel
# ---------------------------------------------------------------------------

class _TerminalMarker:
    """Singleton sentinel; ``is``-comparable identity marker for IOp results."""
    _instance: "_TerminalMarker | None" = None

    def __new__(cls) -> "_TerminalMarker":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "TERMINAL"


TERMINAL: _TerminalMarker = _TerminalMarker()
"""Sentinel symbol placed in the child_symbol slot by IOp.

The evaluator checks ``child_symbol is TERMINAL`` to recognise a produced
terminal shape, rather than a non-terminal symbol to be further rewritten.
"""


# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------

class Op(ABC):
    """Abstract base for all shape-grammar operation primitives."""

    #: Unique id for this op instance; used as the RNG fork label.
    id: str

    @abstractmethod
    def apply(
        self,
        scope: Scope,
        rng: SeededRng,
        label: str,
    ) -> list[tuple[Any, str, str]]:
        """Apply this op to *scope* and return a list of child triples.

        Each triple is ``(child_scope, child_symbol, child_label)`` where
        *child_symbol* is either a rule-name string or the ``TERMINAL``
        sentinel (for IOp).

        Parameters
        ----------
        scope:
            Current geometric scope.
        rng:
            Already-forked RNG for this op (the evaluator forks by op.id
            before calling).
        label:
            Inherited semantic label string from the parent scope.
        """

    @classmethod
    @abstractmethod
    def from_ir(cls, entity: dict[str, Any]) -> "Op":
        """Construct this op from an IR entity dict (the $data block)."""


# ---------------------------------------------------------------------------
# Helper — add Vec3 tuples component-wise
# ---------------------------------------------------------------------------

def _v3_add(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _v3_mul(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] * b[0], a[1] * b[1], a[2] * b[2])


# ---------------------------------------------------------------------------
# Concrete op classes
# ---------------------------------------------------------------------------

@dataclass
class ExtrudeOp(Op):
    """Extrude a 2-D profile to 3-D by setting ``scope.size.z = height``.

    One child is produced with the same symbol and label; its size.z is
    set to *height* and all other transform fields are inherited.
    """

    id: str
    height: float
    symbol: str = ""   # child symbol; empty = inherit from caller

    def apply(
        self,
        scope: Scope,
        rng: SeededRng,
        label: str,
    ) -> list[tuple[Scope, str, str]]:
        tx, ty, _ = scope.size
        child_scope = scope.with_transform(size=(tx, ty, float(self.height)))
        child_symbol = self.symbol if self.symbol else "__inherit__"
        return [(child_scope, child_symbol, label)]

    @classmethod
    def from_ir(cls, entity: dict[str, Any]) -> "ExtrudeOp":
        return cls(
            id=entity.get("id", "extrude"),
            height=float(entity.get("height", 1.0)),
            symbol=entity.get("symbol", ""),
        )


@dataclass
class SplitOp(Op):
    """Split the scope along *axis* ('x'|'y'|'z') into N sub-scopes.

    *sizes* is a sequence of floats (or relative weights when prefixed
    with ``~`` in the spec; here they are passed as floats already
    normalised or not).  Absolute sizes are used as-is; if their sum
    differs from the scope extent along *axis* they are normalised to
    fill the full extent proportionally.

    Each child sub-scope is translated along the split axis so that the
    pieces tile the original extent.  Children reuse the parent symbol
    unless ``symbols`` is supplied (one per piece).
    """

    id: str
    axis: str                    # 'x' | 'y' | 'z'
    sizes: list[float]
    symbols: list[str] = field(default_factory=list)

    # axis index helper
    _AXIS_IDX: dict[str, int] = field(
        default_factory=lambda: {"x": 0, "y": 1, "z": 2},
        init=False,
        repr=False,
        compare=False,
    )

    def apply(
        self,
        scope: Scope,
        rng: SeededRng,
        label: str,
    ) -> list[tuple[Scope, str, str]]:
        axis_idx = {"x": 0, "y": 1, "z": 2}[self.axis]

        raw = list(self.sizes)
        total = sum(raw)

        # Normalise so pieces fill the full scope extent along the axis.
        extent = scope.size[axis_idx]
        if total > 0 and extent > 0:
            scale = extent / total
            sizes = [s * scale for s in raw]
        else:
            sizes = raw

        children: list[tuple[Scope, str, str]] = []
        offset = 0.0
        for i, sz in enumerate(sizes):
            # Build child translation: shift along axis by cumulative offset.
            t = list(scope.translation)
            t[axis_idx] += offset

            # Build child size: same as parent except along split axis.
            s = list(scope.size)
            s[axis_idx] = sz

            child_scope = scope.with_transform(
                translation=tuple(t),  # type: ignore[arg-type]
                size=tuple(s),         # type: ignore[arg-type]
            )

            child_symbol = (
                self.symbols[i]
                if i < len(self.symbols)
                else "__inherit__"
            )
            children.append((child_scope, child_symbol, label))
            offset += sz

        return children

    @classmethod
    def from_ir(cls, entity: dict[str, Any]) -> "SplitOp":
        return cls(
            id=entity.get("id", "split"),
            axis=entity.get("axis", "y"),
            sizes=[float(s) for s in entity.get("sizes", [1.0])],
            symbols=entity.get("symbols", []),
        )


@dataclass
class CompOp(Op):
    """Decompose the scope into face/edge/vertex components.

    Each component is emitted as a child scope whose semantic label is
    augmented with the component type tag (``<label>.<component_type>``).

    In this reference implementation the six faces of the axis-aligned
    bounding box are named: ``top``, ``bottom``, ``left``, ``right``,
    ``front``, ``back``.  If *component_type* is a recognised face name,
    only that face is emitted; otherwise all six are emitted.
    """

    id: str
    component_type: str   # 'faces' | 'edges' | 'vertices' | a specific face name

    _FACE_NAMES: tuple[str, ...] = field(
        default=("top", "bottom", "left", "right", "front", "back"),
        init=False,
        repr=False,
        compare=False,
    )

    def apply(
        self,
        scope: Scope,
        rng: SeededRng,
        label: str,
    ) -> list[tuple[Scope, str, str]]:
        face_names = ("top", "bottom", "left", "right", "front", "back")

        if self.component_type in face_names:
            components = [self.component_type]
        elif self.component_type == "edges":
            # 12 edges — simplified to 4 representative labels
            components = ["edge_x0", "edge_x1", "edge_y0", "edge_y1",
                          "edge_z0", "edge_z1", "edge_x2", "edge_x3",
                          "edge_y2", "edge_y3", "edge_z2", "edge_z3"]
        elif self.component_type == "vertices":
            # 8 corners
            components = [
                "v000", "v001", "v010", "v011",
                "v100", "v101", "v110", "v111",
            ]
        else:
            # Default: all 6 faces
            components = list(face_names)

        children: list[tuple[Scope, str, str]] = []
        for comp in components:
            child_label = f"{label}.{comp}" if label else comp
            # Component scopes share the parent transform; callers may
            # further resolve face centres via geometry helpers.
            children.append((scope, "__inherit__", child_label))

        return children

    @classmethod
    def from_ir(cls, entity: dict[str, Any]) -> "CompOp":
        return cls(
            id=entity.get("id", "comp"),
            component_type=entity.get("component_type", "faces"),
        )


@dataclass
class ScopeOp(Op):
    """Push attribute overrides into the current scope.

    Returns a single child with the updated scope and same symbol/label.
    This is the mechanism for setting user-defined attrs (e.g. material,
    colour, lod-bias) that propagate to child derivations.
    """

    id: str
    attrs: dict[str, Any] = field(default_factory=dict)
    symbol: str = ""

    def apply(
        self,
        scope: Scope,
        rng: SeededRng,
        label: str,
    ) -> list[tuple[Scope, str, str]]:
        child_scope = scope.push(self.attrs)
        child_symbol = self.symbol if self.symbol else "__inherit__"
        return [(child_scope, child_symbol, label)]

    @classmethod
    def from_ir(cls, entity: dict[str, Any]) -> "ScopeOp":
        return cls(
            id=entity.get("id", "scope"),
            attrs=dict(entity.get("attrs", {})),
            symbol=entity.get("symbol", ""),
        )


@dataclass
class IOp(Op):
    """Insert a terminal asset — produces a Terminal immediately.

    ``apply`` returns a singleton list::

        [(TERMINAL, asset_path, label)]

    The evaluator detects ``child_symbol is TERMINAL`` and converts the
    triple into a proper ``Terminal`` object rather than re-queuing it.
    """

    id: str
    asset_path: str

    def apply(
        self,
        scope: Scope,
        rng: SeededRng,
        label: str,
    ) -> list[tuple[Any, str, str]]:
        # Pass the scope itself as the first element so the evaluator can
        # attach final transform info to the Terminal it creates.
        return [(TERMINAL, self.asset_path, label)]

    @classmethod
    def from_ir(cls, entity: dict[str, Any]) -> "IOp":
        return cls(
            id=entity.get("id", "i"),
            asset_path=str(entity.get("asset_path", "")),
        )


@dataclass
class TOp(Op):
    """Translate: shift ``scope.translation`` by ``(dx, dy, dz)``."""

    id: str
    dx: float = 0.0
    dy: float = 0.0
    dz: float = 0.0
    symbol: str = ""

    def apply(
        self,
        scope: Scope,
        rng: SeededRng,
        label: str,
    ) -> list[tuple[Scope, str, str]]:
        new_t = _v3_add(scope.translation, (self.dx, self.dy, self.dz))
        child_scope = scope.with_transform(translation=new_t)
        child_symbol = self.symbol if self.symbol else "__inherit__"
        return [(child_scope, child_symbol, label)]

    @classmethod
    def from_ir(cls, entity: dict[str, Any]) -> "TOp":
        return cls(
            id=entity.get("id", "t"),
            dx=float(entity.get("dx", 0.0)),
            dy=float(entity.get("dy", 0.0)),
            dz=float(entity.get("dz", 0.0)),
            symbol=entity.get("symbol", ""),
        )


@dataclass
class ROp(Op):
    """Rotate: add ``(rx, ry, rz)`` to ``scope.rotation`` (additive Euler)."""

    id: str
    rx: float = 0.0
    ry: float = 0.0
    rz: float = 0.0
    symbol: str = ""

    def apply(
        self,
        scope: Scope,
        rng: SeededRng,
        label: str,
    ) -> list[tuple[Scope, str, str]]:
        new_r = _v3_add(scope.rotation, (self.rx, self.ry, self.rz))
        child_scope = scope.with_transform(rotation=new_r)
        child_symbol = self.symbol if self.symbol else "__inherit__"
        return [(child_scope, child_symbol, label)]

    @classmethod
    def from_ir(cls, entity: dict[str, Any]) -> "ROp":
        return cls(
            id=entity.get("id", "r"),
            rx=float(entity.get("rx", 0.0)),
            ry=float(entity.get("ry", 0.0)),
            rz=float(entity.get("rz", 0.0)),
            symbol=entity.get("symbol", ""),
        )


@dataclass
class SOp(Op):
    """Scale: multiply ``scope.scale`` component-wise by ``(sx, sy, sz)``."""

    id: str
    sx: float = 1.0
    sy: float = 1.0
    sz: float = 1.0
    symbol: str = ""

    def apply(
        self,
        scope: Scope,
        rng: SeededRng,
        label: str,
    ) -> list[tuple[Scope, str, str]]:
        new_s = _v3_mul(scope.scale, (self.sx, self.sy, self.sz))
        child_scope = scope.with_transform(scale=new_s)
        child_symbol = self.symbol if self.symbol else "__inherit__"
        return [(child_scope, child_symbol, label)]

    @classmethod
    def from_ir(cls, entity: dict[str, Any]) -> "SOp":
        return cls(
            id=entity.get("id", "s"),
            sx=float(entity.get("sx", 1.0)),
            sy=float(entity.get("sy", 1.0)),
            sz=float(entity.get("sz", 1.0)),
            symbol=entity.get("symbol", ""),
        )


# ---------------------------------------------------------------------------
# Registry + factory
# ---------------------------------------------------------------------------

OP_REGISTRY: dict[str, type[Op]] = {
    "extrude": ExtrudeOp,
    "split":   SplitOp,
    "comp":    CompOp,
    "scope":   ScopeOp,
    "i":       IOp,
    "t":       TOp,
    "r":       ROp,
    "s":       SOp,
}
"""Central mapping from kind-string to Op class.

Used by the evaluator to build ops from IR rule dicts.
"""


def make_op(kind: str, **fields: Any) -> Op:
    """Construct an Op by kind-string and keyword fields.

    Parameters
    ----------
    kind:
        One of ``"extrude"``, ``"split"``, ``"comp"``, ``"scope"``,
        ``"i"``, ``"t"``, ``"r"``, ``"s"``.
    **fields:
        Keyword arguments forwarded to the concrete op constructor.
        Must include at least ``id``.

    Raises
    ------
    KeyError
        When *kind* is not in ``OP_REGISTRY``.
    """
    if kind not in OP_REGISTRY:
        raise KeyError(
            f"Unknown op kind {kind!r}. "
            f"Valid kinds: {sorted(OP_REGISTRY)}"
        )
    cls = OP_REGISTRY[kind]
    return cls(**fields)  # type: ignore[return-value]
