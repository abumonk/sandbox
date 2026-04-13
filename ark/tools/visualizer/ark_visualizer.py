"""
ARK Visualizer
Генерирует интерактивную HTML-визуализацию графа системы.
Поддерживает LOD-переключение (zoom → detail level).
Поддерживает org-chart для studio/role items с tier-based layering.
"""

import json
import sys
from pathlib import Path


# ============================================================
# ENTITY GRAPH DATA EXTRACTION
# ============================================================

def generate_graph_data(ast_json: dict) -> dict:
    """Extract nodes and edges for d3 visualization, including orgchart data."""
    nodes = []
    links = []
    groups = {}  # island_name → [entity_names]

    for item in ast_json.get("items", []):
        kind = item.get("kind")
        name = item.get("name", item.get("target", "?"))

        if kind in ("abstraction", "class"):
            data_fields = [df["name"] for df in item.get("data_fields", [])]
            in_fields = []
            out_fields = []
            for port in item.get("in_ports", []):
                in_fields.extend(f["name"] for f in port.get("fields", []))
            for port in item.get("out_ports", []):
                out_fields.extend(f["name"] for f in port.get("fields", []))

            nodes.append({
                "id": name, "kind": kind, "group": "entity",
                "data": data_fields, "inputs": in_fields, "outputs": out_fields,
                "invariants": len(item.get("invariants", [])),
                "processes": len(item.get("processes", [])),
            })

            for parent in item.get("inherits", []):
                links.append({"source": name, "target": parent, "kind": "inherits"})

        elif kind == "island":
            strategy = item.get("strategy", "code")
            contains = item.get("contains", [])
            groups[name] = contains

            nodes.append({
                "id": name, "kind": "island", "group": "island",
                "strategy": strategy, "contains": contains,
                "data": [df["name"] for df in item.get("data_fields", [])],
            })

            for c in contains:
                links.append({"source": name, "target": c, "kind": "contains"})

        elif kind == "bridge":
            from_p = item.get("from_port", "")
            to_p = item.get("to_port", "")
            from_island = from_p.split(".")[0]
            to_island = to_p.split(".")[0]
            links.append({
                "source": from_island, "target": to_island,
                "kind": "bridge", "name": name,
                "has_contract": item.get("contract") is not None
            })

        elif kind == "verify":
            target = item.get("target", "?")
            checks = [c.get("name", "?") for c in item.get("checks", [])]
            nodes.append({
                "id": f"verify_{target}", "kind": "verify", "group": "verify",
                "target": target, "checks": checks
            })
            links.append({"source": f"verify_{target}", "target": target, "kind": "verifies"})

        elif kind == "registry":
            for entry in item.get("entries", []):
                ename = entry.get("name", "?")
                links.append({"source": "registry", "target": ename, "kind": "registers"})

    orgchart = extract_orgchart_data(ast_json)

    return {"nodes": nodes, "links": links, "groups": groups, "orgchart": orgchart}


# ============================================================
# ORG-CHART DATA EXTRACTION
# ============================================================

# Tier name → numeric level mapping
TIER_NAME_TO_LEVEL = {
    "director": 1, "directors": 1,
    "lead": 2, "leads": 2,
    "specialist": 3, "specialists": 3,
    "contributor": 4, "contributors": 4,
}

# Tier level → display info
TIER_DISPLAY = {
    1: {"name": "Directors",    "color": "gold"},
    2: {"name": "Leads",        "color": "steelblue"},
    3: {"name": "Specialists",  "color": "lightgreen"},
    4: {"name": "Contributors", "color": "#c8a0e8"},
}


def _resolve_tier_level(tier_val) -> int:
    """Convert tier value (int, str name, or AST expr dict) to numeric level."""
    if tier_val is None:
        return 3  # Default to specialist level
    # AST serializes numbers as {"expr": "number", "value": N}
    if isinstance(tier_val, dict):
        v = tier_val.get("value")
        if v is not None:
            return _resolve_tier_level(v)
        # Try name field for ident expressions
        name = tier_val.get("name", "")
        return TIER_NAME_TO_LEVEL.get(str(name).lower(), 3)
    if isinstance(tier_val, int):
        return tier_val
    if isinstance(tier_val, float):
        return int(tier_val)
    s = str(tier_val).lower().strip()
    return TIER_NAME_TO_LEVEL.get(s, 3)


def extract_orgchart_data(ast_json: dict) -> dict:
    """
    Extract studio/role items from AST and build orgchart data shape:
    {
      "studios": [...],
      "roles": [...],
      "tiers": {...},   # level -> {name, color, roles:[...]}
      "edges": [...]    # escalation edges
    }
    Returns empty dict if no studio/role items found.
    """
    items = ast_json.get("items", [])
    roles = [i for i in items if i.get("kind") == "role"]
    studios = [i for i in items if i.get("kind") == "studio"]

    if not roles and not studios:
        return {}

    # Build tier map: level -> list of role names
    tier_roles: dict = {}  # level -> [role_dict]
    edges = []

    for role in roles:
        role_name = role.get("name", "?")
        tier_val = role.get("tier")
        level = _resolve_tier_level(tier_val)

        tier_display = TIER_DISPLAY.get(level, {"name": f"Tier {level}", "color": "#888"})

        role_entry = {
            "name": role_name,
            "tier": level,
            "tier_name": tier_display["name"],
            "color": tier_display["color"],
            "escalates_to": role.get("escalates_to"),
            "responsibilities": role.get("responsibilities", []),
            "skills": role.get("skills", []),
            "tools": role.get("tools", []),
            "description": role.get("description", ""),
        }

        if level not in tier_roles:
            tier_roles[level] = []
        tier_roles[level].append(role_entry)

        # Build escalation edge
        if role.get("escalates_to"):
            edges.append({
                "from": role_name,
                "to": role.get("escalates_to"),
                "type": "escalation"
            })

    # Build tiers list (sorted by level)
    tiers = {}
    for level in sorted(tier_roles.keys()):
        tier_display = TIER_DISPLAY.get(level, {"name": f"Tier {level}", "color": "#888"})
        tiers[str(level)] = {
            "level": level,
            "name": tier_display["name"],
            "color": tier_display["color"],
            "roles": tier_roles[level],
        }

    # Build studio summary list
    studio_list = []
    for s in studios:
        studio_list.append({
            "name": s.get("name", "?"),
            "contains": s.get("contains", []),
            "description": s.get("description", ""),
        })

    return {
        "studios": studio_list,
        "roles": [r for level_roles in tier_roles.values() for r in level_roles],
        "tiers": tiers,
        "edges": edges,
    }


# ============================================================
# HTML GENERATION
# ============================================================

def generate_html(graph_data: dict, title: str = "ARK System Graph") -> str:
    """Generate self-contained interactive HTML visualization"""

    graph_json = json.dumps(graph_data)
    has_orgchart = bool(graph_data.get("orgchart"))

    orgchart_toggle_btn = ""
    if has_orgchart:
        orgchart_toggle_btn = """
    <button class="lod-btn" id="toggle-orgchart" onclick="toggleView()">Org-Chart</button>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;600&family=Space+Grotesk:wght@400;600;700&display=swap');

  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    background: #0a0a0f;
    color: #e0e0e8;
    font-family: 'JetBrains Mono', monospace;
    overflow: hidden;
    height: 100vh;
  }}

  #header {{
    position: fixed; top: 0; left: 0; right: 0; z-index: 100;
    background: linear-gradient(180deg, rgba(10,10,15,0.95) 0%, rgba(10,10,15,0) 100%);
    padding: 16px 24px;
    display: flex; align-items: center; gap: 20px;
  }}

  #header h1 {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 18px; font-weight: 700;
    color: #7af;
    letter-spacing: 2px;
    text-transform: uppercase;
  }}

  .lod-controls {{
    display: flex; gap: 4px;
  }}

  .lod-btn {{
    background: rgba(122,170,255,0.1);
    border: 1px solid rgba(122,170,255,0.3);
    color: #7af; padding: 6px 14px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px; cursor: pointer;
    border-radius: 4px; transition: all 0.2s;
  }}
  .lod-btn:hover {{ background: rgba(122,170,255,0.2); }}
  .lod-btn.active {{ background: rgba(122,170,255,0.3); border-color: #7af; }}
  .lod-btn.view-active {{ background: rgba(255,200,80,0.2); border-color: #fc8; color: #fc8; }}

  #stats {{
    margin-left: auto;
    font-size: 11px; color: #667;
  }}

  #canvas {{ width: 100vw; height: 100vh; }}

  svg {{
    width: 100%; height: 100%;
  }}

  .node-group {{ cursor: pointer; }}

  .node-body {{
    rx: 8; ry: 8;
    stroke-width: 1.5;
    transition: all 0.3s;
  }}

  .node-group:hover .node-body {{
    stroke-width: 2.5;
    filter: drop-shadow(0 0 12px rgba(122,170,255,0.4));
  }}

  .node-label {{
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
    fill: #e0e0e8;
    pointer-events: none;
  }}

  .node-sublabel {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px;
    fill: #667;
    pointer-events: none;
  }}

  .node-port {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 8px;
    fill: #8a8;
    pointer-events: none;
  }}

  .node-port.port-in {{ fill: #8cf; }}
  .node-port.port-out {{ fill: #fc8; }}
  .node-port.port-data {{ fill: #c8f; }}

  .link {{
    stroke-width: 1.5;
    fill: none;
    opacity: 0.6;
  }}
  .link.inherits {{ stroke: #f8a; stroke-dasharray: 6 3; }}
  .link.contains {{ stroke: #8af; }}
  .link.bridge   {{ stroke: #af8; stroke-width: 2; }}
  .link.verifies {{ stroke: #fa8; stroke-dasharray: 3 3; }}
  .link.registers {{ stroke: #888; stroke-dasharray: 2 4; }}

  .link-label {{
    font-size: 9px; fill: #556;
    font-family: 'JetBrains Mono', monospace;
  }}

  /* LOD detail panels */
  .detail-panel {{
    display: none;
  }}
  .detail-panel.lod-2, .detail-panel.lod-3 {{
    display: block;
  }}

  /* Inspector */
  #inspector {{
    position: fixed; right: 20px; top: 80px;
    width: 280px;
    background: rgba(15,15,25,0.95);
    border: 1px solid rgba(122,170,255,0.2);
    border-radius: 8px;
    padding: 16px;
    font-size: 11px;
    display: none;
    z-index: 100;
    backdrop-filter: blur(10px);
  }}
  #inspector.visible {{ display: block; }}
  #inspector h3 {{
    font-family: 'Space Grotesk', sans-serif;
    color: #7af; margin-bottom: 12px;
    font-size: 14px;
  }}
  .inspector-section {{
    margin-bottom: 10px;
    padding-bottom: 8px;
    border-bottom: 1px solid rgba(255,255,255,0.05);
  }}
  .inspector-section h4 {{
    color: #556; font-size: 9px;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 4px;
  }}
  .tag {{
    display: inline-block;
    background: rgba(122,170,255,0.1);
    border: 1px solid rgba(122,170,255,0.2);
    padding: 2px 6px;
    border-radius: 3px;
    margin: 2px;
    font-size: 10px;
  }}
  .tag.strategy {{ background: rgba(170,255,122,0.1); border-color: rgba(170,255,122,0.2); color: #af8; }}
  .tag.in {{ color: #8cf; }}
  .tag.out {{ color: #fc8; }}
  .tag.data {{ color: #c8f; }}

  /* Org-chart tier bands */
  .tier-band {{
    fill: rgba(255,255,255,0.02);
    stroke: rgba(255,255,255,0.05);
    stroke-width: 1;
  }}
  .tier-label {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 2px;
    opacity: 0.4;
    pointer-events: none;
  }}

  /* Org-chart escalation links */
  .link.escalation {{
    stroke: #f8a;
    stroke-width: 2;
    stroke-dasharray: none;
    opacity: 0.8;
  }}

  /* Org-chart role node */
  .role-node-body {{
    rx: 20; ry: 20;
    stroke-width: 2;
  }}
  .role-node-group:hover .role-node-body {{
    stroke-width: 3;
    filter: drop-shadow(0 0 10px rgba(255,255,200,0.4));
  }}
  .role-node-name {{
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
    font-size: 12px;
    fill: #0a0a0f;
    pointer-events: none;
    dominant-baseline: middle;
    text-anchor: middle;
  }}
  .role-node-tier {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px;
    fill: rgba(10,10,15,0.6);
    pointer-events: none;
    dominant-baseline: middle;
    text-anchor: middle;
  }}

  /* Org-chart legend */
  #orgchart-legend {{
    position: fixed; left: 20px; bottom: 30px;
    background: rgba(15,15,25,0.92);
    border: 1px solid rgba(122,170,255,0.2);
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 11px;
    display: none;
    z-index: 100;
    backdrop-filter: blur(10px);
  }}
  #orgchart-legend.visible {{ display: block; }}
  #orgchart-legend h4 {{
    color: #556; font-size: 9px;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 8px;
  }}
  .legend-item {{
    display: flex; align-items: center; gap: 8px;
    margin-bottom: 4px;
  }}
  .legend-swatch {{
    width: 14px; height: 14px;
    border-radius: 50%;
    border: 1.5px solid rgba(255,255,255,0.3);
    flex-shrink: 0;
  }}
  .legend-text {{
    color: #aaa;
  }}
</style>
</head>
<body>

<div id="header">
  <h1>ARK</h1>
  <div class="lod-controls" id="entity-lod-controls">
    <button class="lod-btn active" onclick="setLOD(1)">LOD 1 — Overview</button>
    <button class="lod-btn" onclick="setLOD(2)">LOD 2 — Ports</button>
    <button class="lod-btn" onclick="setLOD(3)">LOD 3 — Details</button>
  </div>{orgchart_toggle_btn}
  <div id="stats"></div>
</div>

<div id="inspector">
  <h3 id="insp-name">—</h3>
  <div id="insp-body"></div>
</div>

<div id="orgchart-legend">
  <h4>Tier Legend</h4>
  <div id="legend-items"></div>
</div>

<div id="canvas">
  <svg id="svg"></svg>
</div>

<script>
const DATA = {graph_json};
let currentLOD = 1;
let selectedNode = null;
let currentView = 'entity'; // 'entity' | 'orgchart'

// ============================================================
// COLOR SCHEME
// ============================================================
const COLORS = {{
  abstraction: {{ fill: '#1a1a2e', stroke: '#f8a' }},
  class:       {{ fill: '#1a2a1a', stroke: '#8f8' }},
  island:      {{ fill: '#1a1a3a', stroke: '#7af' }},
  verify:      {{ fill: '#2a1a1a', stroke: '#fa8' }},
  default:     {{ fill: '#1a1a1a', stroke: '#555' }},
}};

// ============================================================
// FORCE SIMULATION
// ============================================================
const width = window.innerWidth;
const height = window.innerHeight;

const svg = document.getElementById('svg');
svg.setAttribute('viewBox', `0 0 ${{width}} ${{height}}`);

// Simple force-directed layout
class ForceLayout {{
  constructor(nodes, links) {{
    this.nodes = nodes.map((n, i) => ({{
      ...n,
      x: width/2 + (Math.random() - 0.5) * 400,
      y: height/2 + (Math.random() - 0.5) * 400,
      vx: 0, vy: 0
    }}));
    this.links = links.map(l => ({{
      ...l,
      sourceNode: this.nodes.find(n => n.id === l.source),
      targetNode: this.nodes.find(n => n.id === l.target),
    }})).filter(l => l.sourceNode && l.targetNode);

    this.nodeMap = {{}};
    this.nodes.forEach(n => this.nodeMap[n.id] = n);
  }}

  tick(iterations = 100) {{
    for (let iter = 0; iter < iterations; iter++) {{
      const alpha = 1 - iter / iterations;

      // Repulsion between all nodes
      for (let i = 0; i < this.nodes.length; i++) {{
        for (let j = i + 1; j < this.nodes.length; j++) {{
          const a = this.nodes[i], b = this.nodes[j];
          let dx = b.x - a.x, dy = b.y - a.y;
          let dist = Math.sqrt(dx*dx + dy*dy) || 1;
          let force = -800 / (dist * dist) * alpha;
          a.vx += dx/dist * force;
          a.vy += dy/dist * force;
          b.vx -= dx/dist * force;
          b.vy -= dy/dist * force;
        }}
      }}

      // Attraction along links
      for (const link of this.links) {{
        const a = link.sourceNode, b = link.targetNode;
        let dx = b.x - a.x, dy = b.y - a.y;
        let dist = Math.sqrt(dx*dx + dy*dy) || 1;
        let targetDist = link.kind === 'contains' ? 120 : 200;
        let force = (dist - targetDist) * 0.01 * alpha;
        a.vx += dx/dist * force;
        a.vy += dy/dist * force;
        b.vx -= dx/dist * force;
        b.vy -= dy/dist * force;
      }}

      // Center gravity
      for (const n of this.nodes) {{
        n.vx += (width/2 - n.x) * 0.001 * alpha;
        n.vy += (height/2 - n.y) * 0.001 * alpha;
        n.x += n.vx; n.y += n.vy;
        n.vx *= 0.9; n.vy *= 0.9;
        // Bounds
        n.x = Math.max(100, Math.min(width-100, n.x));
        n.y = Math.max(80, Math.min(height-80, n.y));
      }}
    }}
  }}
}}

const layout = new ForceLayout(DATA.nodes, DATA.links);
layout.tick(200);

// ============================================================
// ENTITY GRAPH RENDERING
// ============================================================

function getNodeSize(node) {{
  if (currentLOD === 1) return {{ w: 140, h: 50 }};
  if (currentLOD === 2) {{
    const ports = (node.inputs?.length || 0) + (node.outputs?.length || 0);
    return {{ w: 160, h: 55 + ports * 12 }};
  }}
  // LOD 3
  const fields = (node.data?.length || 0) + (node.inputs?.length || 0) +
                 (node.outputs?.length || 0);
  return {{ w: 200, h: 60 + fields * 14 }};
}}

function renderEntityGraph() {{
  svg.innerHTML = '';

  // Defs for arrows
  const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
  defs.innerHTML = `
    <marker id="arrow" viewBox="0 0 10 10" refX="10" refY="5"
      markerWidth="8" markerHeight="8" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#556"/>
    </marker>`;
  svg.appendChild(defs);

  // Links
  const linkGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
  for (const link of layout.links) {{
    const s = link.sourceNode, t = link.targetNode;
    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    line.setAttribute('x1', s.x); line.setAttribute('y1', s.y);
    line.setAttribute('x2', t.x); line.setAttribute('y2', t.y);
    line.setAttribute('class', `link ${{link.kind}}`);
    line.setAttribute('marker-end', 'url(#arrow)');
    linkGroup.appendChild(line);

    // Link labels at LOD 2+
    if (currentLOD >= 2 && link.name) {{
      const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      label.setAttribute('x', (s.x + t.x) / 2);
      label.setAttribute('y', (s.y + t.y) / 2 - 8);
      label.setAttribute('class', 'link-label');
      label.setAttribute('text-anchor', 'middle');
      label.textContent = link.name;
      linkGroup.appendChild(label);
    }}
  }}
  svg.appendChild(linkGroup);

  // Nodes
  for (const node of layout.nodes) {{
    const colors = COLORS[node.kind] || COLORS.default;
    const size = getNodeSize(node);
    const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    g.setAttribute('class', 'node-group');
    g.setAttribute('transform', `translate(${{node.x - size.w/2}}, ${{node.y - size.h/2}})`);
    g.onclick = () => selectNode(node);

    // Body rect
    const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    rect.setAttribute('width', size.w); rect.setAttribute('height', size.h);
    rect.setAttribute('fill', colors.fill); rect.setAttribute('stroke', colors.stroke);
    rect.setAttribute('class', 'node-body');
    g.appendChild(rect);

    // Kind badge
    const badge = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    badge.setAttribute('x', 8); badge.setAttribute('y', 14);
    badge.setAttribute('class', 'node-sublabel');
    badge.textContent = node.kind;
    g.appendChild(badge);

    // Name
    const name = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    name.setAttribute('x', 8); name.setAttribute('y', 32);
    name.setAttribute('class', 'node-label');
    name.setAttribute('font-size', '13');
    name.textContent = node.id;
    g.appendChild(name);

    // Strategy tag (LOD 1+)
    if (node.strategy) {{
      const stag = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      stag.setAttribute('x', size.w - 8); stag.setAttribute('y', 14);
      stag.setAttribute('class', 'node-sublabel');
      stag.setAttribute('text-anchor', 'end');
      stag.setAttribute('fill', '#af8');
      stag.textContent = `[${{node.strategy}}]`;
      g.appendChild(stag);
    }}

    // LOD 2+ : show ports
    if (currentLOD >= 2) {{
      let yOff = 48;
      for (const inp of (node.inputs || [])) {{
        const t = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        t.setAttribute('x', 12); t.setAttribute('y', yOff);
        t.setAttribute('class', 'node-port port-in');
        t.textContent = `@in  ${{inp}}`;
        g.appendChild(t); yOff += 12;
      }}
      for (const out of (node.outputs || [])) {{
        const t = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        t.setAttribute('x', 12); t.setAttribute('y', yOff);
        t.setAttribute('class', 'node-port port-out');
        t.textContent = `@out ${{out}}`;
        g.appendChild(t); yOff += 12;
      }}
    }}

    // LOD 3 : show $data
    if (currentLOD >= 3) {{
      let yOff = 48 + ((node.inputs?.length || 0) + (node.outputs?.length || 0)) * 12;
      for (const d of (node.data || [])) {{
        const t = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        t.setAttribute('x', 12); t.setAttribute('y', yOff);
        t.setAttribute('class', 'node-port port-data');
        t.textContent = `$data ${{d}}`;
        g.appendChild(t); yOff += 14;
      }}

      // Invariant/process counts
      if (node.invariants || node.processes) {{
        const info = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        info.setAttribute('x', 12); info.setAttribute('y', yOff + 4);
        info.setAttribute('class', 'node-sublabel');
        info.textContent = `inv:${{node.invariants||0}} proc:${{node.processes||0}}`;
        g.appendChild(info);
      }}
    }}

    svg.appendChild(g);
  }}

  // Stats
  document.getElementById('stats').textContent =
    `${{DATA.nodes.length}} nodes · ${{DATA.links.length}} edges · LOD ${{currentLOD}}`;
}}

// Alias for backwards compatibility
function render() {{ renderEntityGraph(); }}

// ============================================================
// ORG-CHART RENDERING
// ============================================================

function renderOrgChart() {{
  svg.innerHTML = '';
  const oc = DATA.orgchart;
  if (!oc || !oc.roles || oc.roles.length === 0) {{
    const txt = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    txt.setAttribute('x', width / 2); txt.setAttribute('y', height / 2);
    txt.setAttribute('fill', '#556'); txt.setAttribute('text-anchor', 'middle');
    txt.textContent = 'No studio/role data in this .ark file';
    svg.appendChild(txt);
    return;
  }}

  const tiers = oc.tiers || {{}};
  const tierLevels = Object.keys(tiers).map(Number).sort();
  const numTiers = tierLevels.length;

  if (numTiers === 0) return;

  // Layout: divide vertical space among tiers
  const topPad = 80;
  const bottomPad = 60;
  const usableH = height - topPad - bottomPad;
  const bandH = usableH / numTiers;

  // Build a position map for role nodes
  const rolePos = {{}};  // roleName -> {{x, y, color, ...data}}

  // Defs for arrows
  const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
  defs.innerHTML = `
    <marker id="esc-arrow" viewBox="0 0 10 10" refX="9" refY="5"
      markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1 L 9 5 L 0 9 z" fill="#f8a" opacity="0.9"/>
    </marker>
    <filter id="glow">
      <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
      <feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>`;
  svg.appendChild(defs);

  // Draw tier bands + roles
  tierLevels.forEach((level, ti) => {{
    const tier = tiers[String(level)];
    const roles = tier.roles || [];
    const bandY = topPad + ti * bandH;

    // Background band
    const band = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    band.setAttribute('x', 0);
    band.setAttribute('y', bandY);
    band.setAttribute('width', width);
    band.setAttribute('height', bandH);
    band.setAttribute('class', 'tier-band');
    svg.appendChild(band);

    // Tier label (left side)
    const tlabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    tlabel.setAttribute('x', 24);
    tlabel.setAttribute('y', bandY + bandH / 2);
    tlabel.setAttribute('class', 'tier-label');
    tlabel.setAttribute('fill', tier.color);
    tlabel.setAttribute('dominant-baseline', 'middle');
    tlabel.textContent = tier.name;
    svg.appendChild(tlabel);

    // LOD 0 (zoomed-out style — low detail): show tier summary only
    if (currentLOD === 1 && roles.length > 4) {{
      // Compact: show count pill instead of all nodes
      const pw = 160, ph = 38;
      const px = width / 2 - pw / 2, py = bandY + bandH / 2 - ph / 2;
      const pill = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
      pill.setAttribute('x', px); pill.setAttribute('y', py);
      pill.setAttribute('width', pw); pill.setAttribute('height', ph);
      pill.setAttribute('rx', ph / 2); pill.setAttribute('ry', ph / 2);
      pill.setAttribute('fill', tier.color); pill.setAttribute('opacity', '0.15');
      pill.setAttribute('stroke', tier.color); pill.setAttribute('stroke-width', '1.5');
      svg.appendChild(pill);
      const ptxt = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      ptxt.setAttribute('x', px + pw / 2); ptxt.setAttribute('y', py + ph / 2 + 1);
      ptxt.setAttribute('fill', tier.color);
      ptxt.setAttribute('font-family', "'Space Grotesk', sans-serif");
      ptxt.setAttribute('font-size', '12'); ptxt.setAttribute('font-weight', '600');
      ptxt.setAttribute('text-anchor', 'middle'); ptxt.setAttribute('dominant-baseline', 'middle');
      ptxt.textContent = `${{roles.length}} ${{tier.name}}`;
      svg.appendChild(ptxt);
      // Still record approximate center positions for edge drawing
      roles.forEach((role, ri) => {{
        rolePos[role.name] = {{ x: width / 2, y: bandY + bandH / 2, color: tier.color, ...role }};
      }});
      return;
    }}

    // LOD 1+ (medium+): draw individual role nodes
    const nodeW = 130, nodeH = 44;
    const spacing = Math.max(nodeW + 20, (width - 160) / Math.max(roles.length, 1));
    const totalW = roles.length * spacing;
    const startX = width / 2 - totalW / 2 + spacing / 2;

    roles.forEach((role, ri) => {{
      const cx = startX + ri * spacing;
      const cy = bandY + bandH / 2;

      rolePos[role.name] = {{ x: cx, y: cy, color: tier.color, ...role }};

      const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      g.setAttribute('class', 'node-group role-node-group');
      g.onclick = () => selectRoleNode(role);

      // Node background ellipse
      const ellipse = document.createElementNS('http://www.w3.org/2000/svg', 'ellipse');
      ellipse.setAttribute('cx', cx); ellipse.setAttribute('cy', cy);
      ellipse.setAttribute('rx', nodeW / 2); ellipse.setAttribute('ry', nodeH / 2);
      ellipse.setAttribute('fill', tier.color);
      ellipse.setAttribute('fill-opacity', currentLOD >= 2 ? '0.25' : '0.18');
      ellipse.setAttribute('stroke', tier.color);
      ellipse.setAttribute('stroke-width', '2');
      ellipse.setAttribute('class', 'role-node-body');
      g.appendChild(ellipse);

      // Role name
      const nameEl = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      nameEl.setAttribute('x', cx); nameEl.setAttribute('y', cy - (currentLOD >= 2 ? 7 : 0));
      nameEl.setAttribute('class', 'role-node-name');
      nameEl.setAttribute('fill', tier.color);
      nameEl.textContent = role.name;
      g.appendChild(nameEl);

      // LOD 2+: show tier name label inside node
      if (currentLOD >= 2) {{
        const tierEl = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        tierEl.setAttribute('x', cx); tierEl.setAttribute('y', cy + 9);
        tierEl.setAttribute('class', 'role-node-tier');
        tierEl.setAttribute('fill', tier.color);
        tierEl.setAttribute('opacity', '0.7');
        tierEl.textContent = tier.name.slice(0, -1);  // singular
        g.appendChild(tierEl);
      }}

      // LOD 3: show responsibilities count badge
      if (currentLOD >= 3 && (role.responsibilities?.length || role.skills?.length)) {{
        const respCount = role.responsibilities?.length || 0;
        const skillCount = role.skills?.length || 0;
        const badge = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        badge.setAttribute('x', cx + nodeW / 2 - 4);
        badge.setAttribute('y', cy - nodeH / 2 + 4);
        badge.setAttribute('font-family', "'JetBrains Mono', monospace");
        badge.setAttribute('font-size', '8');
        badge.setAttribute('fill', tier.color);
        badge.setAttribute('text-anchor', 'end');
        badge.setAttribute('dominant-baseline', 'hanging');
        badge.textContent = `r:${{respCount}} s:${{skillCount}}`;
        g.appendChild(badge);
      }}

      // Escalation badge (arrow indicator)
      if (role.escalates_to) {{
        const esc = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        esc.setAttribute('x', cx); esc.setAttribute('y', cy - nodeH / 2 - 8);
        esc.setAttribute('font-family', "'JetBrains Mono', monospace");
        esc.setAttribute('font-size', '9');
        esc.setAttribute('fill', '#f8a');
        esc.setAttribute('text-anchor', 'middle');
        esc.textContent = `-> ${{role.escalates_to}}`;
        g.appendChild(esc);
      }}

      svg.appendChild(g);
    }});
  }});

  // Draw escalation edges on top
  const edgeGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
  for (const edge of (oc.edges || [])) {{
    const src = rolePos[edge.from];
    const tgt = rolePos[edge.to];
    if (!src || !tgt) continue;

    // Draw curved path upward
    const dx = tgt.x - src.x;
    const dy = tgt.y - src.y;
    const cx1 = src.x + dx * 0.2;
    const cy1 = src.y + dy * 0.7;
    const cx2 = tgt.x - dx * 0.2;
    const cy2 = tgt.y - dy * 0.3;

    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', `M ${{src.x}} ${{src.y}} C ${{cx1}} ${{cy1}}, ${{cx2}} ${{cy2}}, ${{tgt.x}} ${{tgt.y}}`);
    path.setAttribute('class', 'link escalation');
    path.setAttribute('stroke', '#f8a');
    path.setAttribute('fill', 'none');
    path.setAttribute('stroke-width', '1.8');
    path.setAttribute('marker-end', 'url(#esc-arrow)');
    edgeGroup.appendChild(path);
  }}
  svg.appendChild(edgeGroup);

  // Build legend
  buildOrgChartLegend(tiers, tierLevels);

  // Stats
  const roleCount = oc.roles?.length || 0;
  const edgeCount = oc.edges?.length || 0;
  const studioCount = oc.studios?.length || 0;
  document.getElementById('stats').textContent =
    `${{studioCount}} studios · ${{roleCount}} roles · ${{edgeCount}} escalations · LOD ${{currentLOD}}`;
}}

function buildOrgChartLegend(tiers, tierLevels) {{
  const legend = document.getElementById('orgchart-legend');
  const items = document.getElementById('legend-items');
  items.innerHTML = '';
  tierLevels.forEach(level => {{
    const tier = tiers[String(level)];
    const div = document.createElement('div');
    div.className = 'legend-item';
    div.innerHTML = `
      <div class="legend-swatch" style="background:${{tier.color}}; border-color:${{tier.color}}"></div>
      <span class="legend-text">${{tier.name}}</span>`;
    items.appendChild(div);
  }});
  legend.classList.add('visible');
}}

// ============================================================
// INTERACTION — ORG-CHART
// ============================================================

function selectRoleNode(role) {{
  const insp = document.getElementById('inspector');
  insp.classList.add('visible');
  document.getElementById('insp-name').textContent = `role: ${{role.name}}`;

  let html = `<div class="inspector-section"><h4>Tier</h4>
    <span class="tag" style="color:${{role.color}}">${{role.tier_name}}</span></div>`;

  if (role.description) {{
    html += `<div class="inspector-section"><h4>Description</h4>${{role.description}}</div>`;
  }}
  if (role.escalates_to) {{
    html += `<div class="inspector-section"><h4>Escalates To</h4>
      <span class="tag" style="color:#f8a">${{role.escalates_to}}</span></div>`;
  }}
  if (role.responsibilities?.length) {{
    html += `<div class="inspector-section"><h4>Responsibilities</h4>`;
    role.responsibilities.forEach(r => html += `<span class="tag">${{r}}</span>`);
    html += `</div>`;
  }}
  if (role.skills?.length) {{
    html += `<div class="inspector-section"><h4>Skills</h4>`;
    role.skills.forEach(s => html += `<span class="tag in">${{s}}</span>`);
    html += `</div>`;
  }}
  if (role.tools?.length) {{
    html += `<div class="inspector-section"><h4>Tools</h4>`;
    role.tools.forEach(t => html += `<span class="tag out">${{t}}</span>`);
    html += `</div>`;
  }}

  document.getElementById('insp-body').innerHTML = html;
}}

// ============================================================
// VIEW TOGGLE
// ============================================================

function toggleView() {{
  const btn = document.getElementById('toggle-orgchart');
  const lodControls = document.getElementById('entity-lod-controls');
  const legend = document.getElementById('orgchart-legend');

  if (currentView === 'entity') {{
    currentView = 'orgchart';
    btn.classList.add('view-active');
    btn.textContent = 'Entity Graph';
    lodControls.style.display = 'none';
    legend.classList.add('visible');
    renderOrgChart();
  }} else {{
    currentView = 'entity';
    btn.classList.remove('view-active');
    btn.textContent = 'Org-Chart';
    lodControls.style.display = '';
    legend.classList.remove('visible');
    renderEntityGraph();
  }}
}}

// ============================================================
// INTERACTION — ENTITY GRAPH
// ============================================================

function setLOD(level) {{
  currentLOD = level;
  document.querySelectorAll('#entity-lod-controls .lod-btn').forEach((b, i) => {{
    b.classList.toggle('active', i === level - 1);
  }});
  if (currentView === 'entity') {{
    renderEntityGraph();
  }} else {{
    renderOrgChart();
  }}
}}

function selectNode(node) {{
  selectedNode = node;
  const insp = document.getElementById('inspector');
  insp.classList.add('visible');
  document.getElementById('insp-name').textContent = `${{node.kind}} ${{node.id}}`;

  let html = '';

  if (node.strategy) {{
    html += `<div class="inspector-section">
      <h4>Strategy</h4>
      <span class="tag strategy">${{node.strategy}}</span>
    </div>`;
  }}

  if (node.inputs?.length) {{
    html += `<div class="inspector-section"><h4>@in Ports</h4>`;
    node.inputs.forEach(i => html += `<span class="tag in">${{i}}</span>`);
    html += `</div>`;
  }}

  if (node.outputs?.length) {{
    html += `<div class="inspector-section"><h4>@out Ports</h4>`;
    node.outputs.forEach(o => html += `<span class="tag out">${{o}}</span>`);
    html += `</div>`;
  }}

  if (node.data?.length) {{
    html += `<div class="inspector-section"><h4>$data Fields</h4>`;
    node.data.forEach(d => html += `<span class="tag data">${{d}}</span>`);
    html += `</div>`;
  }}

  if (node.contains?.length) {{
    html += `<div class="inspector-section"><h4>Contains</h4>`;
    node.contains.forEach(c => html += `<span class="tag">${{c}}</span>`);
    html += `</div>`;
  }}

  if (node.checks?.length) {{
    html += `<div class="inspector-section"><h4>Checks</h4>`;
    node.checks.forEach(c => html += `<span class="tag">${{c}}</span>`);
    html += `</div>`;
  }}

  if (node.invariants) html += `<div class="inspector-section"><h4>Invariants</h4>${{node.invariants}}</div>`;
  if (node.processes) html += `<div class="inspector-section"><h4>Process Rules</h4>${{node.processes}}</div>`;

  document.getElementById('insp-body').innerHTML = html;
}}

// Close inspector on click outside
document.addEventListener('click', (e) => {{
  if (!e.target.closest('.node-group') && !e.target.closest('.role-node-group') && !e.target.closest('#inspector')) {{
    document.getElementById('inspector').classList.remove('visible');
  }}
}});

// Initial render
renderEntityGraph();
</script>
</body>
</html>"""


# ============================================================
# CLI
# ============================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="ARK Graph Visualizer")
    parser.add_argument("input", help=".ark or .json file")
    parser.add_argument("--out", help="Output .html file", default=None)
    args = parser.parse_args()

    filepath = Path(args.input)

    if filepath.suffix == ".ark":
        sys.path.insert(0, str(Path(__file__).parent.parent / "parser"))
        from ark_parser import parse, to_json
        source = filepath.read_text(encoding="utf-8")
        ark_file = parse(source)
        ast_json = json.loads(to_json(ark_file))
    else:
        ast_json = json.loads(filepath.read_text())

    graph_data = generate_graph_data(ast_json)
    html = generate_html(graph_data, f"ARK — {filepath.stem}")

    if args.out:
        out_path = Path(args.out)
    else:
        out_path = filepath.with_suffix(".html")

    out_path.write_text(html, encoding="utf-8")
    print(f"Visualizer written to {out_path}")


if __name__ == "__main__":
    main()
