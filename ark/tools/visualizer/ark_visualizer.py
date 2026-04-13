"""
ARK Visualizer
Генерирует интерактивную HTML-визуализацию графа системы.
Поддерживает LOD-переключение (zoom → detail level).
"""

import json
import sys
from pathlib import Path


def generate_graph_data(ast_json: dict) -> dict:
    """Extract nodes and edges for d3 visualization"""
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

    return {"nodes": nodes, "links": links, "groups": groups}


def generate_html(graph_data: dict, title: str = "ARK System Graph") -> str:
    """Generate self-contained interactive HTML visualization"""

    graph_json = json.dumps(graph_data)

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
</style>
</head>
<body>

<div id="header">
  <h1>⬡ ARK</h1>
  <div class="lod-controls">
    <button class="lod-btn active" onclick="setLOD(1)">LOD 1 — Overview</button>
    <button class="lod-btn" onclick="setLOD(2)">LOD 2 — Ports</button>
    <button class="lod-btn" onclick="setLOD(3)">LOD 3 — Details</button>
  </div>
  <div id="stats"></div>
</div>

<div id="inspector">
  <h3 id="insp-name">—</h3>
  <div id="insp-body"></div>
</div>

<div id="canvas">
  <svg id="svg"></svg>
</div>

<script>
const DATA = {graph_json};
let currentLOD = 1;
let selectedNode = null;

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
// RENDERING
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

function render() {{
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

// ============================================================
// INTERACTION
// ============================================================

function setLOD(level) {{
  currentLOD = level;
  document.querySelectorAll('.lod-btn').forEach((b, i) => {{
    b.classList.toggle('active', i === level - 1);
  }});
  render();
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
  if (!e.target.closest('.node-group') && !e.target.closest('#inspector')) {{
    document.getElementById('inspector').classList.remove('visible');
  }}
}});

// Initial render
render();
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
