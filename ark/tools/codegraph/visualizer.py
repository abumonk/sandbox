"""Code graph visualization helpers."""
import json
from pathlib import Path

# Color mapping for code graph node types
NODE_COLORS = {
    "function": "#4CAF50",   # green
    "method": "#8BC34A",     # light green
    "class": "#2196F3",      # blue
    "module": "#FF9800",     # orange
    "unknown": "#9E9E9E",    # gray
}

NODE_SHAPES = {
    "function": "circle",
    "method": "circle",
    "class": "rect",
    "module": "hexagon",
}

LOD_THRESHOLDS = {
    # LOD level -> minimum zoom to show this node type
    "module": 0.1,     # always visible
    "class": 0.3,      # visible at medium zoom
    "function": 0.6,   # visible at closer zoom
    "method": 0.8,     # visible only when zoomed in
}

def graph_to_vis_data(graph_json: dict) -> dict:
    """Convert a code graph JSON to visualization-ready format."""
    vis_nodes = []
    vis_edges = []

    for name, props in graph_json.get("nodes", {}).items():
        node_type = props.get("type", "unknown")
        vis_nodes.append({
            "id": name,
            "label": name.split(".")[-1].split("::")[-1],  # short name
            "full_name": name,
            "type": node_type,
            "color": NODE_COLORS.get(node_type, NODE_COLORS["unknown"]),
            "shape": NODE_SHAPES.get(node_type, "circle"),
            "lod": LOD_THRESHOLDS.get(node_type, 0.5),
            **{k: v for k, v in props.items() if k != "type"},
        })

    for i, edge in enumerate(graph_json.get("edges", [])):
        vis_edges.append({
            "id": f"e{i}",
            "source": edge["source"],
            "target": edge["target"],
            "kind": edge.get("kind", "unknown"),
        })

    return {"nodes": vis_nodes, "edges": vis_edges}


def generate_codegraph_html(graph_json: dict, output_path: Path) -> None:
    """Generate a standalone HTML file with an interactive code graph visualization."""
    vis_data = graph_to_vis_data(graph_json)

    html = f"""<!DOCTYPE html>
<html>
<head>
<title>ARK Code Graph</title>
<style>
body {{ margin: 0; font-family: sans-serif; background: #1a1a2e; color: #eee; }}
#header {{ padding: 10px 20px; background: #16213e; display: flex; justify-content: space-between; align-items: center; }}
#header h1 {{ margin: 0; font-size: 18px; }}
#stats {{ font-size: 13px; color: #aaa; }}
#graph {{ width: 100vw; height: calc(100vh - 50px); }}
svg {{ width: 100%; height: 100%; }}
.node circle, .node rect {{ stroke: #fff; stroke-width: 1.5; cursor: pointer; }}
.node text {{ font-size: 10px; fill: #eee; pointer-events: none; }}
.edge {{ stroke: #555; stroke-width: 1; opacity: 0.6; }}
.edge.calls {{ stroke: #4CAF50; }}
.edge.imports {{ stroke: #FF9800; }}
.edge.inherits {{ stroke: #2196F3; }}
.tooltip {{ position: absolute; background: #222; color: #eee; padding: 8px 12px; border-radius: 4px; font-size: 12px; pointer-events: none; display: none; z-index: 10; }}
#legend {{ position: absolute; bottom: 20px; right: 20px; background: rgba(22,33,62,0.9); padding: 12px; border-radius: 6px; font-size: 12px; }}
.legend-item {{ display: flex; align-items: center; margin: 4px 0; }}
.legend-dot {{ width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }}
</style>
</head>
<body>
<div id="header">
  <h1>ARK Code Graph</h1>
  <div id="stats">{len(vis_data['nodes'])} nodes, {len(vis_data['edges'])} edges</div>
</div>
<div id="graph"></div>
<div class="tooltip" id="tooltip"></div>
<div id="legend">
  <div class="legend-item"><div class="legend-dot" style="background:#FF9800"></div>Module</div>
  <div class="legend-item"><div class="legend-dot" style="background:#2196F3"></div>Class</div>
  <div class="legend-item"><div class="legend-dot" style="background:#4CAF50"></div>Function</div>
  <div class="legend-item"><div class="legend-dot" style="background:#8BC34A"></div>Method</div>
</div>
<script src="https://d3js.org/d3.v7.min.js"></script>
<script>
const data = {json.dumps(vis_data)};
const width = window.innerWidth;
const height = window.innerHeight - 50;
const svg = d3.select("#graph").append("svg").attr("viewBox", [0, 0, width, height]);
const g = svg.append("g");
const zoom = d3.zoom().scaleExtent([0.05, 5]).on("zoom", (e) => g.attr("transform", e.transform));
svg.call(zoom);

const simulation = d3.forceSimulation(data.nodes)
  .force("link", d3.forceLink(data.edges).id(d => d.id).distance(80))
  .force("charge", d3.forceManyBody().strength(-200))
  .force("center", d3.forceCenter(width/2, height/2))
  .force("collision", d3.forceCollide(20));

const link = g.selectAll(".edge").data(data.edges).join("line")
  .attr("class", d => "edge " + d.kind);

const node = g.selectAll(".node").data(data.nodes).join("g")
  .attr("class", "node").call(d3.drag()
    .on("start", (e,d) => {{ if (!e.active) simulation.alphaTarget(0.3).restart(); d.fx=d.x; d.fy=d.y; }})
    .on("drag", (e,d) => {{ d.fx=e.x; d.fy=e.y; }})
    .on("end", (e,d) => {{ if (!e.active) simulation.alphaTarget(0); d.fx=null; d.fy=null; }}));

node.append("circle").attr("r", d => d.type==="module"?12:d.type==="class"?10:7)
  .attr("fill", d => d.color);
node.append("text").attr("dx", 14).attr("dy", 4).text(d => d.label);

const tooltip = d3.select("#tooltip");
node.on("mouseover", (e,d) => {{
  tooltip.style("display","block").html("<b>"+d.full_name+"</b><br>Type: "+d.type+(d.complexity?"<br>Complexity: "+d.complexity:""));
}}).on("mousemove", (e) => {{
  tooltip.style("left",(e.pageX+10)+"px").style("top",(e.pageY-10)+"px");
}}).on("mouseout", () => tooltip.style("display","none"));

simulation.on("tick", () => {{
  link.attr("x1",d=>d.source.x).attr("y1",d=>d.source.y).attr("x2",d=>d.target.x).attr("y2",d=>d.target.y);
  node.attr("transform",d=>"translate("+d.x+","+d.y+")");
}});
</script>
</body>
</html>"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
