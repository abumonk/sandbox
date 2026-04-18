#!/usr/bin/env python3
"""Build a self-contained telemetry dashboard from all adventure metrics."""

import re
import sys
import json
from pathlib import Path
from datetime import datetime, timezone

ADVENTURES_DIR = Path(__file__).parent.parent / ".agent" / "adventures"
OUTPUT_FILE = Path(__file__).parent.parent / ".agent" / "telemetry-dashboard.html"

# ── Data parsing ─────────────────────────────────────────────────────────────

def parse_frontmatter(text):
    """Extract YAML-ish frontmatter between --- delimiters. Returns dict."""
    m = re.match(r'^---\s*\n(.*?)\n---', text, re.DOTALL)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        if ':' in line:
            k, _, v = line.partition(':')
            fm[k.strip()] = v.strip()
    return fm


def parse_duration_to_seconds(s):
    """Convert various duration strings to seconds float."""
    if not s or s.strip() in ('', '0', '-'):
        return 0.0
    s = str(s).strip()
    # Pure number → treat as seconds
    try:
        return float(s)
    except ValueError:
        pass
    total = 0.0
    for pat, mult in [
        (r'(\d+)\s*h', 3600),
        (r'(\d+)\s*min', 60),
        (r'(\d+)\s*s\b', 1),
    ]:
        for m in re.finditer(pat, s, re.IGNORECASE):
            total += float(m.group(1)) * mult
    return total


def format_duration(seconds):
    """Format seconds into a human-readable string."""
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        m, s = divmod(seconds, 60)
        return f"{m}m {s}s"
    h, rem = divmod(seconds, 3600)
    m = rem // 60
    return f"{h}h {m}m"


EXPECTED_COLS_12 = [
    'run id', 'timestamp', 'agent', 'task', 'model',
    'tokens in', 'tokens out', 'duration (s)', 'turns',
    'cost (usd)', 'result', 'confidence'
]


def parse_table_row(header_cols, cells):
    """Map cells onto normalized keys. Returns dict or None if malformed."""
    if len(cells) != len(header_cols):
        return None
    row = {}
    for h, v in zip(header_cols, cells):
        row[h.strip().lower()] = v.strip()
    # Require the 12-column schema
    required = {'run id', 'timestamp', 'agent', 'task', 'model',
                'tokens in', 'tokens out', 'duration (s)', 'turns',
                'cost (usd)', 'result', 'confidence'}
    if not required.issubset(row.keys()):
        return None
    try:
        return {
            'run_id':     row['run id'],
            'timestamp':  row['timestamp'],
            'agent':      row['agent'],
            'task':       row['task'],
            'model':      canonicalize_model(row['model']),
            'tokens_in':  int(row['tokens in']),
            'tokens_out': int(row['tokens out']),
            'duration_s': float(row['duration (s)']),
            'turns':      int(row['turns']),
            'cost':       float(row['cost (usd)']),
            'result':     row['result'],
            'confidence': row['confidence'].lower(),
        }
    except (ValueError, KeyError):
        return None


def canonicalize_model(m):
    m = m.lower().strip()
    if 'opus' in m:
        return 'opus'
    if 'sonnet' in m:
        return 'sonnet'
    if 'haiku' in m:
        return 'haiku'
    return 'unknown'


def parse_metrics(path):
    """Parse a metrics.md file. Returns (frontmatter_dict, [run_rows])."""
    text = path.read_text(encoding='utf-8', errors='replace')
    fm = parse_frontmatter(text)

    rows = []
    in_table = False
    header_cols = None

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith('|'):
            if in_table:
                break  # table ended
            continue

        cells = [c.strip() for c in stripped.strip('|').split('|')]

        if not in_table:
            # First pipe line → header
            header_cols = [c.lower() for c in cells]
            in_table = True
            continue

        # Separator line (contains only dashes/spaces)?
        if all(re.match(r'^[-: ]+$', c) for c in cells):
            continue

        try:
            row = parse_table_row(header_cols, cells)
            if row:
                rows.append(row)
        except Exception:
            pass  # skip malformed rows

    return fm, rows


def parse_manifest(path):
    """Parse a manifest.md file. Returns dict with id, title, state."""
    text = path.read_text(encoding='utf-8', errors='replace')
    fm = parse_frontmatter(text)
    return {
        'id':    fm.get('id', ''),
        'title': fm.get('title', '(no title)'),
        'state': fm.get('state', 'unknown'),
    }


# ── Data aggregation ─────────────────────────────────────────────────────────

def load_all_adventures():
    adventures = []
    issues = []

    adv_dirs = sorted(
        d for d in ADVENTURES_DIR.iterdir()
        if d.is_dir() and re.match(r'ADV-\d+', d.name)
    )

    for d in adv_dirs:
        adv_id = d.name
        metrics_path = d / 'metrics.md'
        manifest_path = d / 'manifest.md'

        manifest = {'id': adv_id, 'title': '(no manifest)', 'state': 'unknown'}
        if manifest_path.exists():
            try:
                manifest = parse_manifest(manifest_path)
            except Exception as e:
                issues.append(f"{adv_id} manifest parse error: {e}")

        fm = {}
        runs = []
        if metrics_path.exists():
            try:
                fm, runs = parse_metrics(metrics_path)
            except Exception as e:
                issues.append(f"{adv_id} metrics parse error: {e}")
        else:
            issues.append(f"{adv_id}: metrics.md missing")

        adv = {
            'id': adv_id,
            'title': manifest['title'],
            'state': manifest['state'],
            'tokens_in':   safe_int(fm.get('total_tokens_in', 0)),
            'tokens_out':  safe_int(fm.get('total_tokens_out', 0)),
            'cost':        safe_float(fm.get('total_cost', 0)),
            'duration_s':  parse_duration_to_seconds(fm.get('total_duration', '0')),
            'agent_runs':  safe_int(fm.get('agent_runs', 0)),
            'runs': runs,
        }
        adventures.append(adv)

    return adventures, issues


def safe_int(v):
    try:
        return int(str(v).replace(',', '').strip())
    except (ValueError, TypeError):
        return 0


def safe_float(v):
    try:
        return float(str(v).replace(',', '').strip())
    except (ValueError, TypeError):
        return 0.0


def fmt_cost(v):
    return f"${v:,.4f}"


def fmt_tokens(n):
    if n >= 1_000_000:
        return f"{n/1_000_000:.2f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


# ── Chart data builders ───────────────────────────────────────────────────────

def cost_by_model(all_runs):
    totals = {'opus': 0.0, 'sonnet': 0.0, 'haiku': 0.0, 'unknown': 0.0}
    for r in all_runs:
        m = r['model']
        totals[m] = totals.get(m, 0.0) + r['cost']
    return totals


def cost_by_agent_model(all_runs):
    """Top-10 agents by cost, each with per-model breakdown."""
    agent_model = {}
    for r in all_runs:
        a = r['agent']
        m = r['model']
        agent_model.setdefault(a, {})
        agent_model[a][m] = agent_model[a].get(m, 0.0) + r['cost']
    agent_total = {a: sum(v.values()) for a, v in agent_model.items()}
    top10 = sorted(agent_total, key=lambda a: -agent_total[a])[:10]
    return [(a, agent_model[a], agent_total[a]) for a in top10]


def confidence_breakdown(all_runs):
    counts = {'high': 0, 'medium': 0, 'low': 0, 'estimated': 0, 'other': 0}
    for r in all_runs:
        c = r['confidence']
        if c in counts:
            counts[c] += 1
        else:
            counts['other'] += 1
    return counts


def recent_high_confidence(all_runs, n=20):
    """Last N rows with confidence:high, sorted by timestamp desc."""
    high = [r for r in all_runs if r['confidence'] == 'high' and r['timestamp']]
    high.sort(key=lambda r: r['timestamp'], reverse=True)
    return high[:n]


# ── HTML generation ───────────────────────────────────────────────────────────

MODEL_COLORS = {
    'opus':    '#e88aff',
    'sonnet':  '#5ab0ff',
    'haiku':   '#5fd38a',
    'unknown': '#8a96a4',
}

CONF_COLORS = {
    'high':      '#5fd38a',
    'medium':    '#f0b04a',
    'low':       '#e66a6a',
    'estimated': '#8a96a4',
    'other':     '#5ab0ff',
}

STATE_COLORS = {
    'completed': '#5fd38a',
    'active':    '#5ab0ff',
    'planned':   '#f0b04a',
    'unknown':   '#8a96a4',
}


def svg_bar_chart(data, title, width=600, bar_height=30, gap=6):
    """
    data: list of (label, value, color) tuples
    Returns SVG string.
    """
    if not data:
        return '<p style="color:var(--muted)">No data</p>'

    max_val = max(v for _, v, _ in data) or 1
    chart_w = width - 200  # left for labels, right for value
    total_h = (bar_height + gap) * len(data) + 10

    lines = [f'<svg width="{width}" height="{total_h}" style="font:12px \'Segoe UI\',sans-serif;overflow:visible">']
    for i, (label, val, color) in enumerate(data):
        y = i * (bar_height + gap)
        bar_w = int(chart_w * val / max_val)
        x_bar = 150
        # label
        lines.append(
            f'<text x="145" y="{y + bar_height//2 + 4}" '
            f'text-anchor="end" fill="#dbe1e8" font-size="11">'
            f'{label[:22]}</text>'
        )
        # background
        lines.append(
            f'<rect x="{x_bar}" y="{y}" width="{chart_w}" height="{bar_height}" '
            f'fill="#243040" rx="3"/>'
        )
        # bar
        if bar_w > 0:
            lines.append(
                f'<rect x="{x_bar}" y="{y}" width="{bar_w}" height="{bar_height}" '
                f'fill="{color}" rx="3"/>'
            )
        # value label
        label_x = x_bar + bar_w + 6 if bar_w < chart_w - 60 else x_bar + bar_w - 4
        anchor = 'start' if bar_w < chart_w - 60 else 'end'
        val_text = fmt_cost(val) if val > 0.01 else f'{val:.4f}'
        lines.append(
            f'<text x="{label_x}" y="{y + bar_height//2 + 4}" '
            f'text-anchor="{anchor}" fill="#dbe1e8" font-size="11">'
            f'{val_text}</text>'
        )
    lines.append('</svg>')
    return '\n'.join(lines)


def svg_stacked_bar_chart(data, width=700, bar_height=28, gap=6):
    """
    data: list of (agent_name, {model: cost}, total_cost)
    Returns SVG string.
    """
    if not data:
        return '<p style="color:var(--muted)">No data</p>'

    max_val = max(total for _, _, total in data) or 1
    chart_w = width - 200
    total_h = (bar_height + gap) * len(data) + 10
    models = ['opus', 'sonnet', 'haiku', 'unknown']

    lines = [f'<svg width="{width}" height="{total_h}" style="font:12px \'Segoe UI\',sans-serif;overflow:visible">']
    for i, (agent, by_model, total) in enumerate(data):
        y = i * (bar_height + gap)
        x_bar = 160
        # label
        lines.append(
            f'<text x="155" y="{y + bar_height//2 + 4}" '
            f'text-anchor="end" fill="#dbe1e8" font-size="11">'
            f'{agent[:26]}</text>'
        )
        # background track
        lines.append(
            f'<rect x="{x_bar}" y="{y}" width="{chart_w}" height="{bar_height}" '
            f'fill="#243040" rx="3"/>'
        )
        # stacked segments
        x_cur = x_bar
        for m in models:
            cost = by_model.get(m, 0.0)
            if cost <= 0:
                continue
            seg_w = int(chart_w * cost / max_val)
            if seg_w < 1:
                seg_w = 1
            lines.append(
                f'<rect x="{x_cur}" y="{y}" width="{seg_w}" height="{bar_height}" '
                f'fill="{MODEL_COLORS[m]}" title="{m}: {fmt_cost(cost)}"/>'
            )
            x_cur += seg_w
        # total label
        lines.append(
            f'<text x="{x_bar + int(chart_w * total / max_val) + 6}" '
            f'y="{y + bar_height//2 + 4}" fill="#dbe1e8" font-size="11">'
            f'{fmt_cost(total)}</text>'
        )
    lines.append('</svg>')
    return '\n'.join(lines)


def svg_confidence_pie(counts, size=220):
    """Render confidence breakdown as an SVG donut chart."""
    total = sum(counts.values()) or 1
    cx, cy, r_outer, r_inner = size//2, size//2, size//2 - 10, size//2 - 40

    def polar(cx, cy, r, angle_deg):
        import math
        rad = math.radians(angle_deg - 90)
        return cx + r * math.cos(rad), cy + r * math.sin(rad)

    lines = [f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" '
             f'style="font:11px \'Segoe UI\',sans-serif">']

    start = 0.0
    slices = [(k, v, CONF_COLORS.get(k, '#8a96a4')) for k, v in counts.items() if v > 0]

    for label, count, color in slices:
        sweep = 360 * count / total
        end = start + sweep
        x1, y1 = polar(cx, cy, r_outer, start)
        x2, y2 = polar(cx, cy, r_outer, end)
        ix1, iy1 = polar(cx, cy, r_inner, end)
        ix2, iy2 = polar(cx, cy, r_inner, start)
        large = 1 if sweep > 180 else 0
        path = (
            f'M {x1:.1f},{y1:.1f} '
            f'A {r_outer},{r_outer} 0 {large} 1 {x2:.1f},{y2:.1f} '
            f'L {ix1:.1f},{iy1:.1f} '
            f'A {r_inner},{r_inner} 0 {large} 0 {ix2:.1f},{iy2:.1f} Z'
        )
        pct = count / total * 100
        lines.append(f'<path d="{path}" fill="{color}" opacity="0.9">'
                     f'<title>{label}: {count} ({pct:.1f}%)</title></path>')
        start = end

    # Center text
    lines.append(f'<text x="{cx}" y="{cy - 6}" text-anchor="middle" '
                 f'fill="#dbe1e8" font-size="18" font-weight="bold">'
                 f'{sum(counts.values())}</text>')
    lines.append(f'<text x="{cx}" y="{cy + 12}" text-anchor="middle" '
                 f'fill="#8a96a4" font-size="11">runs</text>')
    lines.append('</svg>')
    return '\n'.join(lines)


def legend_html(items):
    """items: list of (label, color)"""
    parts = []
    for label, color in items:
        parts.append(
            f'<span style="display:inline-flex;align-items:center;gap:4px;margin-right:12px">'
            f'<span style="width:12px;height:12px;border-radius:2px;background:{color};'
            f'display:inline-block"></span>{label}</span>'
        )
    return '<div style="display:flex;flex-wrap:wrap;gap:4px;margin:8px 0">' + ''.join(parts) + '</div>'


def state_badge(state):
    color = STATE_COLORS.get(state, STATE_COLORS['unknown'])
    return (f'<span style="background:{color}22;color:{color};border:1px solid {color}66;'
            f'border-radius:3px;padding:1px 6px;font-size:11px">{state}</span>')


def build_html(adventures, issues):
    all_runs = []
    for a in adventures:
        for r in a['runs']:
            r['adventure_id'] = a['id']
            all_runs.append(r)

    # KPIs
    total_adventures = len(adventures)
    total_agent_runs = sum(a['agent_runs'] for a in adventures)
    total_tokens_in  = sum(a['tokens_in'] for a in adventures)
    total_tokens_out = sum(a['tokens_out'] for a in adventures)
    total_cost       = sum(a['cost'] for a in adventures)
    total_duration_s = sum(a['duration_s'] for a in adventures)

    # Charts data
    model_costs = cost_by_model(all_runs)
    agent_breakdown = cost_by_agent_model(all_runs)
    conf_counts = confidence_breakdown(all_runs)
    recent_high = recent_high_confidence(all_runs, 20)

    # Model bar
    model_bar_data = [
        (m, model_costs[m], MODEL_COLORS[m])
        for m in ('opus', 'sonnet', 'haiku', 'unknown')
        if model_costs[m] > 0
    ]
    model_bar_data.sort(key=lambda x: -x[1])
    model_bar_svg = svg_bar_chart(model_bar_data, 'Cost by Model')

    # Agent stacked bar
    agent_stacked_svg = svg_stacked_bar_chart(agent_breakdown)

    # Confidence pie
    conf_pie_svg = svg_confidence_pie(conf_counts)

    generated_at = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

    # ── Adventure table rows ─────────────────────────────────────────────────
    adv_rows = []
    for a in sorted(adventures, key=lambda x: x['id']):
        adv_rows.append(
            f'<tr>'
            f'<td><code>{a["id"]}</code></td>'
            f'<td style="max-width:280px">{a["title"]}</td>'
            f'<td>{state_badge(a["state"])}</td>'
            f'<td style="text-align:right">{a["agent_runs"]}</td>'
            f'<td style="text-align:right">{fmt_tokens(a["tokens_in"])}</td>'
            f'<td style="text-align:right">{fmt_tokens(a["tokens_out"])}</td>'
            f'<td style="text-align:right">{fmt_cost(a["cost"])}</td>'
            f'<td style="text-align:right">{format_duration(a["duration_s"])}</td>'
            f'</tr>'
        )
    adv_table = '\n'.join(adv_rows)

    # ── Recent captures table ────────────────────────────────────────────────
    recent_rows = []
    for r in recent_high:
        model_color = MODEL_COLORS.get(r['model'], '#8a96a4')
        recent_rows.append(
            f'<tr>'
            f'<td>{r["timestamp"][:19] if r["timestamp"] else ""}</td>'
            f'<td><code style="color:var(--accent)">{r["adventure_id"]}</code></td>'
            f'<td>{r["agent"]}</td>'
            f'<td><span style="color:{model_color}">{r["model"]}</span></td>'
            f'<td>{r["task"]}</td>'
            f'<td style="text-align:right">{fmt_cost(r["cost"])}</td>'
            f'<td style="text-align:right">{fmt_tokens(r["tokens_in"] + r["tokens_out"])}</td>'
            f'<td>{r["result"]}</td>'
            f'</tr>'
        )
    recent_table = '\n'.join(recent_rows) if recent_rows else (
        '<tr><td colspan="8" style="color:var(--muted);text-align:center">'
        'No high-confidence rows found</td></tr>'
    )

    # ── Issues section ───────────────────────────────────────────────────────
    issues_html = ''
    if issues:
        items = ''.join(f'<li style="color:var(--warn)">{i}</li>' for i in issues)
        issues_html = f'<details style="margin-top:16px"><summary style="cursor:pointer;color:var(--muted)">Parse issues ({len(issues)})</summary><ul style="margin:8px 0;padding-left:20px">{items}</ul></details>'

    # ── Model legend ─────────────────────────────────────────────────────────
    model_legend = legend_html([(m, c) for m, c in MODEL_COLORS.items()])
    conf_legend  = legend_html([(k, v) for k, v in CONF_COLORS.items() if k != 'other'])

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Agent Telemetry Dashboard</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  :root {{
    --bg:          #0f141a;
    --bg-alt:      #161d25;
    --bg-hover:    #1d2731;
    --border:      #2a343f;
    --text:        #dbe1e8;
    --muted:       #8a96a4;
    --accent:      #5ab0ff;
    --accent-dim:  #2d6ca8;
    --ok:          #5fd38a;
    --warn:        #f0b04a;
    --err:         #e66a6a;
    --card-bg:     #1a222d;
    --card-border: #2a343f;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{ min-height: 100%; background: var(--bg); color: var(--text);
    font: 13px/1.5 "Segoe UI", Helvetica, Arial, sans-serif; }}
  h1 {{ font-size: 18px; font-weight: 700; color: var(--text); }}
  h2 {{ font-size: 14px; font-weight: 600; color: var(--accent); margin-bottom: 10px; }}
  a  {{ color: var(--accent); text-decoration: none; }}
  code {{ font: 12px "Cascadia Mono","Consolas",monospace;
          background: var(--bg-alt); padding: 1px 4px; border-radius: 3px; }}

  /* Layout */
  .page {{ max-width: 1200px; margin: 0 auto; padding: 20px 24px 60px; }}
  .header {{ display:flex; align-items:center; justify-content:space-between;
             border-bottom: 1px solid var(--border); padding-bottom:12px; margin-bottom:20px; }}
  .meta {{ color: var(--muted); font-size:11px; }}

  /* KPI strip */
  .kpi-strip {{ display:flex; flex-wrap:wrap; gap:12px; margin-bottom:24px; }}
  .kpi-card {{
    background: var(--card-bg); border: 1px solid var(--card-border);
    border-radius: 6px; padding: 14px 18px; flex: 1; min-width: 140px;
  }}
  .kpi-label {{ font-size:11px; color:var(--muted); text-transform:uppercase;
                letter-spacing:.04em; margin-bottom:4px; }}
  .kpi-value {{ font-size:22px; font-weight:700; color:var(--text); }}
  .kpi-sub   {{ font-size:11px; color:var(--muted); margin-top:2px; }}

  /* Cards */
  .card {{
    background: var(--card-bg); border: 1px solid var(--card-border);
    border-radius: 6px; padding: 16px 18px; margin-bottom: 20px;
  }}

  /* Two-col grid */
  .grid2 {{ display:grid; grid-template-columns:1fr 1fr; gap:20px; margin-bottom:20px; }}
  @media(max-width:800px) {{ .grid2 {{ grid-template-columns:1fr; }} }}

  /* Tables */
  table {{ border-collapse:collapse; width:100%; font-size:12px; }}
  th, td {{ border:1px solid var(--border); padding:5px 8px;
             text-align:left; vertical-align:middle; }}
  th {{ background:var(--bg-alt); font-weight:600; color:var(--muted);
        text-transform:uppercase; font-size:11px; letter-spacing:.03em; }}
  tr:hover td {{ background:var(--bg-hover); }}
  .num {{ text-align:right; font-variant-numeric:tabular-nums; }}

  /* Scrollable table wrapper */
  .table-wrap {{ overflow-x:auto; }}

  /* Confidence donut + legend side by side */
  .pie-row {{ display:flex; align-items:flex-start; gap:24px; flex-wrap:wrap; }}
  .pie-legend {{ display:flex; flex-direction:column; gap:8px; padding-top:10px; }}
  .pie-legend-item {{ display:flex; align-items:center; gap:8px; font-size:12px; }}
  .swatch {{ width:14px; height:14px; border-radius:3px; flex-shrink:0; }}
</style>
</head>
<body>
<div class="page">

  <!-- Header -->
  <div class="header">
    <h1>Agent Telemetry Dashboard</h1>
    <div class="meta">Generated {generated_at} &nbsp;|&nbsp; {total_adventures} adventures</div>
  </div>

  <!-- KPI Strip -->
  <div class="kpi-strip">
    <div class="kpi-card">
      <div class="kpi-label">Adventures</div>
      <div class="kpi-value">{total_adventures}</div>
      <div class="kpi-sub">all time</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Agent Runs</div>
      <div class="kpi-value">{total_agent_runs}</div>
      <div class="kpi-sub">{len(all_runs)} rows parsed</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Tokens In</div>
      <div class="kpi-value">{fmt_tokens(total_tokens_in)}</div>
      <div class="kpi-sub">from frontmatter totals</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Tokens Out</div>
      <div class="kpi-value">{fmt_tokens(total_tokens_out)}</div>
      <div class="kpi-sub">from frontmatter totals</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Total Cost</div>
      <div class="kpi-value">{fmt_cost(total_cost)}</div>
      <div class="kpi-sub">sum of adventure costs</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Total Duration</div>
      <div class="kpi-value">{format_duration(total_duration_s)}</div>
      <div class="kpi-sub">wall-clock across adventures</div>
    </div>
  </div>

  <!-- Per-adventure table -->
  <div class="card">
    <h2>Per-Adventure Summary</h2>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Title</th>
            <th>State</th>
            <th class="num">Runs</th>
            <th class="num">Tokens In</th>
            <th class="num">Tokens Out</th>
            <th class="num">Cost</th>
            <th class="num">Duration</th>
          </tr>
        </thead>
        <tbody>
          {adv_table}
        </tbody>
      </table>
    </div>
  </div>

  <!-- Charts row 1 -->
  <div class="grid2">
    <!-- Cost by model -->
    <div class="card">
      <h2>Cost by Model</h2>
      {model_legend}
      {model_bar_svg}
    </div>

    <!-- Confidence breakdown -->
    <div class="card">
      <h2>Confidence Breakdown</h2>
      {conf_legend}
      <div class="pie-row">
        {conf_pie_svg}
        <div class="pie-legend">
          {"".join(
            f'<div class="pie-legend-item">'
            f'<div class="swatch" style="background:{CONF_COLORS.get(k,"#8a96a4")}"></div>'
            f'<span>{k}: <strong>{v}</strong></span></div>'
            for k, v in conf_counts.items() if v > 0
          )}
        </div>
      </div>
    </div>
  </div>

  <!-- Cost by agent stacked -->
  <div class="card">
    <h2>Cost by Agent (top 10, stacked by model)</h2>
    {model_legend}
    {agent_stacked_svg}
  </div>

  <!-- Recent high-confidence captures -->
  <div class="card">
    <h2>Recent High-Confidence Captures (last 20)</h2>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Adventure</th>
            <th>Agent</th>
            <th>Model</th>
            <th>Task</th>
            <th class="num">Cost</th>
            <th class="num">Tokens</th>
            <th>Result</th>
          </tr>
        </thead>
        <tbody>
          {recent_table}
        </tbody>
      </table>
    </div>
  </div>

  {issues_html}

</div><!-- /.page -->
</body>
</html>"""

    return html


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    print(f"Scanning {ADVENTURES_DIR} ...")
    adventures, issues = load_all_adventures()
    print(f"Loaded {len(adventures)} adventures")

    all_rows = sum(len(a['runs']) for a in adventures)
    print(f"Parsed {all_rows} run rows total")

    if issues:
        print(f"\nParse issues ({len(issues)}):")
        for i in issues:
            print(f"  - {i}")

    html = build_html(adventures, issues)
    OUTPUT_FILE.write_text(html, encoding='utf-8')
    print(f"\nDashboard written to: {OUTPUT_FILE}")

    # Summary stats
    total_cost = sum(a['cost'] for a in adventures)
    total_runs = sum(a['agent_runs'] for a in adventures)
    print(f"\nSummary: {len(adventures)} adventures, {total_runs} agent runs, ${total_cost:.4f} total cost")

    return 0


if __name__ == '__main__':
    sys.exit(main())
