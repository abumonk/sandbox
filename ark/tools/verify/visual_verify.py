"""
Visual Verifier
Checks visual-communication-specific invariants in ARK visual specs using Z3.

Checks:
  1. Diagram type validity     — each diagram's type is a valid DiagramType variant
  2. Visual review targets     — each visual_review's target references an existing
                                diagram, preview, or screenshot
  3. Annotation bounds (Z3)    — annotation element positions are non-negative and
                                within viewport bounds when specified
  4. Render config validity (Z3) — width > 0, height > 0, scale > 0, valid format
  5. Review cycle acyclicity (Z3) — visual_review items form no circular chains
                                   (Z3 ordinal assignment)
"""

from z3 import Int, Real, And, Or, Implies, Solver, sat, unsat

# ============================================================
# RESULT HELPERS
# ============================================================


def _pass(check: str, message: str) -> dict:
    return {"check": check, "status": "pass", "message": message}


def _fail(check: str, message: str) -> dict:
    return {"check": check, "status": "fail", "message": message}


def _warn(check: str, message: str) -> dict:
    return {"check": check, "status": "warn", "message": message}


# ============================================================
# HELPERS
# ============================================================

VALID_DIAGRAM_TYPES = {
    "mermaid", "flowchart", "architecture", "sequence",
    "class_diagram", "state", "er", "gantt",
}

VALID_RENDER_FORMATS = {"svg", "png", "html", "pdf"}


def _items_from_ark(ark_file: dict) -> list:
    """Extract the flat items list from an ARK AST dict."""
    raw = ark_file.get("items", [])
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        return list(raw.values())
    return []


def _collect(items: list, kind: str) -> list:
    return [it for it in items if isinstance(it, dict) and it.get("kind") == kind]


def _name(item: dict, fallback: str = "<unnamed>") -> str:
    return item.get("name") or item.get("id") or fallback


# ============================================================
# CHECK 1: Diagram Type Validity
# ============================================================

def check_diagram_types(diagrams: list) -> list:
    """Verify every diagram item's type is a valid DiagramType variant."""
    results = []
    if not diagrams:
        results.append(_pass("visual_diagram_types", "No diagram items to check"))
        return results

    for diag in diagrams:
        dname = _name(diag)
        dtype = diag.get("diagram_type") or diag.get("type")
        if dtype is None:
            results.append(_warn(
                "visual_diagram_types",
                f"Diagram '{dname}' has no type field — skipping",
            ))
        elif dtype not in VALID_DIAGRAM_TYPES:
            results.append(_fail(
                "visual_diagram_types",
                f"Diagram '{dname}' has invalid type '{dtype}'; "
                f"valid: {sorted(VALID_DIAGRAM_TYPES)}",
            ))
        else:
            results.append(_pass(
                "visual_diagram_types",
                f"Diagram '{dname}' type '{dtype}' is valid",
            ))
    return results


# ============================================================
# CHECK 2: Visual Review Target Resolution
# ============================================================

def check_review_targets(reviews: list, all_names: set) -> list:
    """Verify every visual_review's target references an existing item."""
    results = []
    if not reviews:
        results.append(_pass("visual_review_targets", "No visual_review items to check"))
        return results

    for rev in reviews:
        rname = _name(rev)
        target = rev.get("target") or rev.get("target_ref")
        if target is None:
            results.append(_warn(
                "visual_review_targets",
                f"visual_review '{rname}' has no target — skipping",
            ))
        elif target not in all_names:
            results.append(_fail(
                "visual_review_targets",
                f"visual_review '{rname}' references unknown target '{target}'",
            ))
        else:
            results.append(_pass(
                "visual_review_targets",
                f"visual_review '{rname}' target '{target}' resolved",
            ))
    return results


# ============================================================
# CHECK 3: Annotation Bounds (Z3)
# ============================================================

def check_annotation_bounds(annotations: list, render_configs: dict = None) -> list:
    """Z3: verify annotation element positions are within viewport bounds."""
    results = []
    if not annotations:
        results.append(_pass("visual_annotation_bounds", "No annotation items to check"))
        return results

    # Build render config lookup for viewport bounds
    rc_lookup = {}
    if render_configs:
        for rc_name, rc in (render_configs.items() if isinstance(render_configs, dict)
                            else [(r.get("name", ""), r) for r in render_configs]):
            w = rc.get("width")
            h = rc.get("height")
            if w is not None and h is not None:
                rc_lookup[rc_name] = (int(w), int(h))

    for ann in annotations:
        aname = _name(ann)
        elements = ann.get("elements") or []
        if not elements:
            results.append(_pass(
                "visual_annotation_bounds",
                f"Annotation '{aname}' has no elements — nothing to check",
            ))
            continue

        # Try to find viewport bounds from render_config reference
        vp_w, vp_h = None, None
        rc_ref = ann.get("render_config") or ann.get("render_config_ref")
        if rc_ref and rc_ref in rc_lookup:
            vp_w, vp_h = rc_lookup[rc_ref]

        for i, elem in enumerate(elements):
            if not isinstance(elem, dict):
                continue
            pos = elem.get("position") or elem
            x = pos.get("x")
            y = pos.get("y")
            w = pos.get("width", 0)
            h = pos.get("height", 0)

            if x is None or y is None:
                continue

            # Z3 non-negativity check
            s = Solver()
            zx, zy, zw, zh = Int("x"), Int("y"), Int("w"), Int("h")
            s.add(zx == int(x), zy == int(y), zw == int(w), zh == int(h))

            constraints = [zx >= 0, zy >= 0, zw >= 0, zh >= 0]
            if vp_w is not None:
                constraints.append(zx + zw <= vp_w)
            if vp_h is not None:
                constraints.append(zy + zh <= vp_h)

            s.add(And(*constraints))
            # Check if constraints are satisfiable (they should be if coords are valid)
            neg = Or(zx < 0, zy < 0)
            if vp_w is not None:
                neg = Or(neg, zx + zw > vp_w)
            if vp_h is not None:
                neg = Or(neg, zy + zh > vp_h)

            s2 = Solver()
            s2.add(zx == int(x), zy == int(y), zw == int(w), zh == int(h))
            s2.add(neg)

            if s2.check() == sat:
                results.append(_fail(
                    "visual_annotation_bounds",
                    f"Annotation '{aname}' element {i}: position ({x},{y}) "
                    f"size ({w},{h}) out of bounds"
                    + (f" (viewport {vp_w}x{vp_h})" if vp_w else ""),
                ))
            else:
                results.append(_pass(
                    "visual_annotation_bounds",
                    f"Annotation '{aname}' element {i}: bounds OK",
                ))

    return results


# ============================================================
# CHECK 4: Render Config Validity (Z3)
# ============================================================

def check_render_configs(configs: list) -> list:
    """Z3: verify render config width > 0, height > 0, scale > 0, valid format."""
    results = []
    if not configs:
        results.append(_pass("visual_render_configs", "No render_config items to check"))
        return results

    for cfg in configs:
        cname = _name(cfg)
        ok = True

        # Check format
        fmt = cfg.get("format")
        if fmt is not None and fmt not in VALID_RENDER_FORMATS:
            results.append(_fail(
                "visual_render_configs",
                f"render_config '{cname}' has invalid format '{fmt}'; "
                f"valid: {sorted(VALID_RENDER_FORMATS)}",
            ))
            ok = False

        # Z3 check for positive dimensions
        width = cfg.get("width")
        height = cfg.get("height")
        scale = cfg.get("scale")

        s = Solver()
        checks = []

        if width is not None:
            zw = Int("width")
            s.add(zw == int(width))
            checks.append(("width", zw > 0, width))

        if height is not None:
            zh = Int("height")
            s.add(zh == int(height))
            checks.append(("height", zh > 0, height))

        if scale is not None:
            zs = Real("scale")
            s.add(zs == float(scale))
            checks.append(("scale", zs > 0, scale))

        for field_name, constraint, value in checks:
            s_check = Solver()
            if width is not None:
                s_check.add(Int("width") == int(width))
            if height is not None:
                s_check.add(Int("height") == int(height))
            if scale is not None:
                s_check.add(Real("scale") == float(scale))

            from z3 import Not
            s_check.add(Not(constraint))
            if s_check.check() == sat:
                results.append(_fail(
                    "visual_render_configs",
                    f"render_config '{cname}': {field_name}={value} is not positive",
                ))
                ok = False

        if ok:
            results.append(_pass(
                "visual_render_configs",
                f"render_config '{cname}' is valid",
            ))

    return results


# ============================================================
# CHECK 5: Review Cycle Acyclicity (Z3 Ordinals)
# ============================================================

def check_review_acyclicity(reviews: list) -> list:
    """Z3 ordinal check: ensure visual_review items don't form circular chains."""
    results = []
    if not reviews:
        results.append(_pass("visual_review_acyclicity", "No visual_review items to check"))
        return results

    # Build name → target mapping
    edges = {}
    for rev in reviews:
        rname = _name(rev)
        target = rev.get("target") or rev.get("target_ref")
        if rname and target:
            edges[rname] = target

    if not edges:
        results.append(_pass("visual_review_acyclicity", "No review chains to check"))
        return results

    # Collect all nodes
    all_nodes = set(edges.keys()) | set(edges.values())
    ordinals = {node: Int(f"ord_{node}") for node in all_nodes}

    s = Solver()
    # Non-negative ordinals
    for node, var in ordinals.items():
        s.add(var >= 0)

    # For each edge A → B (A reviews B), require ordinal(A) > ordinal(B)
    for reviewer, target in edges.items():
        if reviewer in ordinals and target in ordinals:
            s.add(ordinals[reviewer] > ordinals[target])

    if s.check() == sat:
        results.append(_pass(
            "visual_review_acyclicity",
            f"Review chain is acyclic ({len(edges)} edges verified)",
        ))
    else:
        # Find which edges form the cycle
        results.append(_fail(
            "visual_review_acyclicity",
            f"Circular review chain detected among: {sorted(edges.keys())}",
        ))

    return results


# ============================================================
# MAIN ENTRY
# ============================================================

def verify_visual(ark_file: dict) -> list:
    """Run all visual verification checks on a parsed ARK AST dict.

    Returns a flat list of result dicts, each with keys:
      - check:   str — check identifier
      - status:  "pass" | "fail" | "warn"
      - message: str — human-readable detail
    """
    items = _items_from_ark(ark_file)

    diagrams = _collect(items, "diagram")
    previews = _collect(items, "preview")
    annotations = _collect(items, "annotation")
    visual_reviews = _collect(items, "visual_review")
    screenshots = _collect(items, "screenshot")
    render_configs = _collect(items, "render_config")

    # Build set of all item names for target resolution
    all_names = set()
    for it in items:
        if isinstance(it, dict):
            n = it.get("name") or it.get("id")
            if n:
                all_names.add(n)

    # Also check ArkFile-level indices
    for key in ("diagrams", "previews", "screenshots", "annotations",
                "visual_reviews", "visual_searches", "render_configs"):
        idx = ark_file.get(key)
        if isinstance(idx, dict):
            all_names.update(idx.keys())

    results = []
    results.extend(check_diagram_types(diagrams))
    results.extend(check_review_targets(visual_reviews, all_names))

    # Build render_config dict for bounds checking
    rc_dict = {}
    for rc in render_configs:
        n = _name(rc)
        if n != "<unnamed>":
            rc_dict[n] = rc

    results.extend(check_annotation_bounds(annotations, rc_dict))
    results.extend(check_render_configs(render_configs))
    results.extend(check_review_acyclicity(visual_reviews))

    return results
