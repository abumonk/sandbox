#!/usr/bin/env python3
"""Generate a single-file static HTML report covering ALL adventures.

Walks every .agent/adventures/ADV-*/ directory, embeds each *.md file as a
JSON blob, renders via marked.js on the client. Two-level sidebar: adventure
group → category group → file. Synthetic "Overview" page summarizes every
adventure with state, task count, artifact count, and report links.
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent  # .agent/adventures
OUT = ROOT / "report.html"

CATEGORY_ORDER = [
    "root", "manifest", "designs", "plans", "schemas", "roles",
    "research", "tests", "tasks", "reviews",
]


def parse_frontmatter(text: str) -> dict:
    """Extract YAML frontmatter scalars (strings/ints). No nested objects."""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    body = text[4:end]
    meta: dict = {}
    for line in body.splitlines():
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", line)
        if not m:
            continue
        k, v = m.group(1), m.group(2).strip()
        if v.startswith("[") and v.endswith("]"):
            meta[k] = [s.strip() for s in v[1:-1].split(",") if s.strip()]
        else:
            meta[k] = v
    return meta


def collect_adventure(adv_dir: Path) -> dict:
    """Collect all docs for one adventure. Returns summary + docs list."""
    docs = []
    for p in sorted(adv_dir.rglob("*.md")):
        rel = p.relative_to(adv_dir).as_posix()
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            text = f"<!-- read failure: {e} -->"
        parts = rel.split("/")
        category = parts[0] if len(parts) > 1 else "root"
        docs.append({
            "adv": adv_dir.name,
            "category": category,
            "path": rel,              # relative to adventure dir
            "key": f"{adv_dir.name}/{rel}",  # globally unique
            "title": parts[-1].removesuffix(".md"),
            "bytes": len(text.encode("utf-8")),
            "content": text,
        })

    # Parse manifest for summary fields
    manifest_path = adv_dir / "manifest.md"
    fm = {}
    if manifest_path.exists():
        fm = parse_frontmatter(manifest_path.read_text(encoding="utf-8", errors="replace"))

    # Parse metrics aggregate
    metrics_path = adv_dir / "metrics.md"
    mm = {}
    if metrics_path.exists():
        mm = parse_frontmatter(metrics_path.read_text(encoding="utf-8", errors="replace"))

    tasks = fm.get("tasks", [])
    summary = {
        "id": fm.get("id", adv_dir.name),
        "title": fm.get("title", adv_dir.name),
        "state": fm.get("state", "unknown"),
        "created": fm.get("created", ""),
        "updated": fm.get("updated", ""),
        "task_count": len(tasks) if isinstance(tasks, list) else 0,
        "doc_count": len(docs),
        "bytes": sum(d["bytes"] for d in docs),
        "total_tokens_in": mm.get("total_tokens_in", ""),
        "total_tokens_out": mm.get("total_tokens_out", ""),
        "total_cost": mm.get("total_cost", ""),
        "agent_runs": mm.get("agent_runs", ""),
        "has_report_en": (adv_dir / "report-en.md").exists(),
        "has_review_report": (adv_dir / "reviews" / "adventure-report.md").exists(),
        "has_validation": (adv_dir / "tests" / "validation-report.md").exists(),
    }
    return {"summary": summary, "docs": docs}


STATE_BADGE = {
    "completed": ("ok", "#1a7f37", "#dafbe1"),
    "active":    ("in-flight", "#9a6700", "#fff8c5"),
    "paused":    ("paused", "#656d76", "#eaeef2"),
    "blocked":   ("blocked", "#cf222e", "#ffebe9"),
    "reviewing": ("reviewing", "#0969da", "#ddf4ff"),
    "cancelled": ("cancelled", "#656d76", "#eaeef2"),
    "unknown":   ("?", "#656d76", "#eaeef2"),
}


def build_overview_md(adventures: list[dict]) -> str:
    lines = ["# Adventures Overview", "",
             f"**{len(adventures)} adventures** · "
             f"**{sum(a['summary']['doc_count'] for a in adventures)} markdown artifacts** · "
             f"**{sum(a['summary']['bytes'] for a in adventures)/1024/1024:.1f} MB** total", ""]
    lines.append("| ID | Title | State | Tasks | Docs | Size | Reports |")
    lines.append("|----|-------|-------|------:|-----:|-----:|---------|")
    for a in adventures:
        s = a["summary"]
        reports = []
        if s["has_report_en"]:
            reports.append(f"[report-en]({s['id']}/report-en.md)")
        if s["has_review_report"]:
            reports.append(f"[review]({s['id']}/reviews/adventure-report.md)")
        if s["has_validation"]:
            reports.append(f"[validation]({s['id']}/tests/validation-report.md)")
        lines.append(
            f"| {s['id']} | {s['title']} | `{s['state']}` | "
            f"{s['task_count']} | {s['doc_count']} | "
            f"{s['bytes']/1024:.0f} KB | {', '.join(reports) or '—'} |"
        )
    lines += ["", "## Quick Links", ""]
    for a in adventures:
        s = a["summary"]
        lines.append(f"### {s['id']} — {s['title']}")
        lines.append(f"- State: `{s['state']}` · Tasks: {s['task_count']} · Docs: {s['doc_count']} · Size: {s['bytes']/1024:.0f} KB")
        lines.append(f"- [Manifest]({s['id']}/manifest.md) · [Metrics]({s['id']}/metrics.md)")
        if s["has_report_en"]:
            lines.append(f"- [EN Report]({s['id']}/report-en.md)")
        if s["has_review_report"]:
            lines.append(f"- [Review Report]({s['id']}/reviews/adventure-report.md)")
        if s["has_validation"]:
            lines.append(f"- [Validation Report]({s['id']}/tests/validation-report.md)")
        lines.append("")
    return "\n".join(lines)


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/dompurify@3.0.9/dist/purify.min.js"></script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/github-markdown-css@5.5.1/github-markdown-light.css">
<style>
  :root {
    --sidebar-w: 360px;
    --bg: #ffffff;
    --panel: #f6f8fa;
    --border: #d0d7de;
    --muted: #656d76;
    --accent: #0969da;
    --accent-bg: #ddf4ff;
    --code-bg: #f6f8fa;
  }
  * { box-sizing: border-box; }
  html, body { height: 100%; margin: 0; font-family: -apple-system, BlinkMacSystemFont,
    "Segoe UI", sans-serif; color: #1f2328; background: var(--bg); }
  body { display: grid; grid-template-columns: var(--sidebar-w) 1fr; height: 100vh; }
  aside {
    background: var(--panel);
    border-right: 1px solid var(--border);
    overflow-y: auto;
    padding: 12px 10px 40px;
  }
  aside h1 { font-size: 13px; margin: 4px 4px 10px; color: var(--muted);
    text-transform: uppercase; letter-spacing: .05em; }
  aside input[type=search] {
    width: 100%; padding: 6px 9px; font-size: 13px;
    border: 1px solid var(--border); border-radius: 6px;
    background: white; margin-bottom: 10px;
  }
  aside .stats { font-size: 11px; color: var(--muted); margin: 0 4px 10px; }
  aside .overview {
    display: block; padding: 6px 8px; margin: 0 0 10px; font-size: 13px;
    background: var(--accent-bg); color: var(--accent); border-radius: 4px;
    text-decoration: none; font-weight: 600;
  }
  aside .overview.active { outline: 2px solid var(--accent); }
  details.adv { margin-bottom: 4px; }
  details.adv > summary {
    cursor: pointer; padding: 5px 6px; font-size: 12px; font-weight: 700;
    color: #24292f; border-radius: 4px; user-select: none;
    display: flex; align-items: center; gap: 6px;
  }
  details.adv > summary:hover { background: #eaeef2; }
  summary .count { font-weight: 400; color: var(--muted); margin-left: auto; font-size: 11px; }
  .badge {
    display: inline-block; padding: 1px 6px; border-radius: 10px;
    font-size: 10px; font-weight: 600; text-transform: uppercase;
    letter-spacing: .03em;
  }
  details.cat { margin: 2px 0 2px 10px; }
  details.cat > summary {
    cursor: pointer; padding: 2px 6px; font-size: 11px; font-weight: 600;
    color: #57606a; border-radius: 3px; user-select: none;
    text-transform: uppercase; letter-spacing: .04em;
  }
  details.cat > summary:hover { background: #eaeef2; }
  ul.doclist { list-style: none; margin: 2px 0 4px 0; padding: 0; }
  ul.doclist li { margin: 0; }
  ul.doclist a {
    display: block; padding: 2px 8px 2px 24px; font-size: 12px;
    color: #24292f; text-decoration: none; border-radius: 3px;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  ul.doclist a:hover { background: #eaeef2; }
  ul.doclist a.active { background: var(--accent-bg); color: var(--accent); font-weight: 600; }
  main { overflow-y: auto; background: var(--bg); }
  header.docheader {
    position: sticky; top: 0; z-index: 10; background: var(--bg);
    border-bottom: 1px solid var(--border); padding: 12px 32px;
    display: flex; align-items: center; gap: 14px;
  }
  header.docheader h2 { margin: 0; font-size: 15px; font-weight: 600;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  header.docheader .meta { font-size: 12px; color: var(--muted); margin-left: auto; white-space: nowrap; }
  article.markdown-body {
    max-width: 980px; margin: 0 auto; padding: 32px;
    background: var(--bg);
  }
  article.markdown-body h1, article.markdown-body h2 {
    border-bottom: 1px solid var(--border); padding-bottom: .3em;
  }
  article.markdown-body pre {
    background: var(--code-bg) !important;
    padding: 12px; border-radius: 6px; overflow-x: auto;
  }
  article.markdown-body table { border-collapse: collapse; display: block; overflow-x: auto; }
  article.markdown-body th, article.markdown-body td {
    border: 1px solid var(--border); padding: 6px 10px;
  }
  article.markdown-body th { background: var(--panel); }
  .empty { padding: 48px; color: var(--muted); font-size: 14px; text-align: center; }
  code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
</style>
</head>
<body>
<aside>
  <h1>__HEADING__</h1>
  <div class="stats">__STATS__</div>
  <input type="search" id="filter" placeholder="Filter files… (try 'design' or 'ADV-007/research')" autocomplete="off">
  <a href="#__overview" class="overview" id="overview-link">📋 Overview — all adventures</a>
  <nav id="nav"></nav>
</aside>
<main>
  <header class="docheader">
    <h2 id="doctitle">Loading…</h2>
    <span class="meta" id="docmeta"></span>
  </header>
  <article class="markdown-body" id="doc"><div class="empty">Select a document from the sidebar.</div></article>
</main>
<script id="docs-data" type="application/json">__DATA__</script>
<script id="overview-data" type="application/json">__OVERVIEW__</script>
<script>
const DATA = JSON.parse(document.getElementById('docs-data').textContent);
const OVERVIEW_MD = JSON.parse(document.getElementById('overview-data').textContent);
const STATE_COLORS = __STATE_COLORS__;
const CATEGORY_ORDER = __CATEGORY_ORDER__;

// flatten into a key map
const byKey = {};
for (const adv of DATA) for (const d of adv.docs) byKey[d.key] = d;

// Build sidebar
const nav = document.getElementById('nav');

function makeBadge(state) {
  const [label, fg, bg] = STATE_COLORS[state] || STATE_COLORS.unknown;
  const span = document.createElement('span');
  span.className = 'badge';
  span.textContent = label;
  span.style.color = fg;
  span.style.background = bg;
  return span;
}

for (const adv of DATA) {
  const advDet = document.createElement('details');
  advDet.className = 'adv';
  advDet.open = false;
  const advSum = document.createElement('summary');
  const strong = document.createElement('span');
  strong.textContent = adv.summary.id;
  advSum.appendChild(strong);
  advSum.appendChild(makeBadge(adv.summary.state));
  const ttl = document.createElement('span');
  ttl.style.flex = '1';
  ttl.style.fontWeight = '400';
  ttl.style.fontSize = '11px';
  ttl.style.color = '#57606a';
  ttl.style.overflow = 'hidden';
  ttl.style.textOverflow = 'ellipsis';
  ttl.style.whiteSpace = 'nowrap';
  ttl.textContent = adv.summary.title.replace(/^.+? — /, '').slice(0, 50);
  advSum.appendChild(ttl);
  const count = document.createElement('span');
  count.className = 'count';
  count.textContent = adv.summary.doc_count;
  advSum.appendChild(count);
  advDet.appendChild(advSum);

  // group docs by category
  const cats = {};
  for (const d of adv.docs) (cats[d.category] ||= []).push(d);
  const orderedCats = CATEGORY_ORDER.filter(c => cats[c]).concat(
    Object.keys(cats).filter(c => !CATEGORY_ORDER.includes(c)).sort());

  for (const c of orderedCats) {
    const catDet = document.createElement('details');
    catDet.className = 'cat';
    catDet.open = false;
    const catSum = document.createElement('summary');
    catSum.innerHTML = c + '<span class="count">' + cats[c].length + '</span>';
    catDet.appendChild(catSum);
    const ul = document.createElement('ul');
    ul.className = 'doclist';
    for (const d of cats[c].sort((a,b) => a.path.localeCompare(b.path))) {
      const li = document.createElement('li');
      const a = document.createElement('a');
      a.href = '#' + encodeURIComponent(d.key);
      a.textContent = d.path.split('/').pop();
      a.title = d.key;
      a.dataset.key = d.key;
      li.appendChild(a);
      ul.appendChild(li);
    }
    catDet.appendChild(ul);
    advDet.appendChild(catDet);
  }
  nav.appendChild(advDet);
}

// Filter
document.getElementById('filter').addEventListener('input', (e) => {
  const q = e.target.value.trim().toLowerCase();
  for (const advDet of nav.querySelectorAll('details.adv')) {
    let advVisible = 0;
    for (const catDet of advDet.querySelectorAll('details.cat')) {
      let catVisible = 0;
      for (const li of catDet.querySelectorAll('li')) {
        const k = li.firstChild.dataset.key.toLowerCase();
        const hit = !q || k.includes(q);
        li.style.display = hit ? '' : 'none';
        if (hit) catVisible++;
      }
      catDet.style.display = catVisible ? '' : 'none';
      if (q && catVisible) catDet.open = true;
      advVisible += catVisible;
    }
    advDet.style.display = advVisible ? '' : 'none';
    if (q && advVisible) advDet.open = true;
  }
});

// Render
marked.setOptions({ gfm: true, breaks: false, headerIds: true, mangle: false });
function render(key) {
  const title = document.getElementById('doctitle');
  const meta = document.getElementById('docmeta');
  const art = document.getElementById('doc');
  let content, path, bytes;
  if (key === '__overview') {
    content = OVERVIEW_MD;
    path = 'Overview — all adventures';
    bytes = OVERVIEW_MD.length;
  } else {
    const d = byKey[key];
    if (!d) {
      art.innerHTML = '<div class="empty">Not found: ' + key + '</div>';
      title.textContent = 'Not found'; meta.textContent = '';
      return;
    }
    content = d.content; path = d.key; bytes = d.bytes;
  }
  title.textContent = path;
  meta.textContent = (bytes/1024).toFixed(1) + ' KB';
  const raw = marked.parse(content);
  art.innerHTML = DOMPurify.sanitize(raw, { ADD_ATTR: ['id'] });
  for (const a of nav.querySelectorAll('a')) {
    a.classList.toggle('active', a.dataset.key === key);
  }
  document.getElementById('overview-link').classList.toggle('active', key === '__overview');
  document.querySelector('main').scrollTop = 0;
}

function fromHash() {
  const h = decodeURIComponent(location.hash.replace(/^#/, ''));
  if (h === '__overview') render('__overview');
  else if (h && byKey[h]) {
    render(h);
    // open the containing adventure + category
    const [adv] = h.split('/');
    for (const det of nav.querySelectorAll('details.adv')) {
      if (det.querySelector('summary').firstChild.textContent === adv) {
        det.open = true;
        for (const c of det.querySelectorAll('details.cat')) {
          if (c.querySelector('a[data-key="'+h.replace(/"/g,'\\"')+'"]')) c.open = true;
        }
        det.scrollIntoView({ block: 'nearest' });
      }
    }
  } else {
    render('__overview');
  }
}
window.addEventListener('hashchange', fromHash);
nav.addEventListener('click', (e) => {
  const a = e.target.closest('a[data-key]');
  if (!a) return;
  e.preventDefault();
  location.hash = '#' + encodeURIComponent(a.dataset.key);
  render(a.dataset.key);
});
document.getElementById('overview-link').addEventListener('click', (e) => {
  e.preventDefault();
  location.hash = '#__overview';
  render('__overview');
});
fromHash();
</script>
</body>
</html>
"""


def main() -> int:
    adv_dirs = sorted([p for p in ROOT.iterdir() if p.is_dir() and p.name.startswith("ADV-")])
    adventures = [collect_adventure(p) for p in adv_dirs]

    total_docs = sum(a["summary"]["doc_count"] for a in adventures)
    total_bytes = sum(a["summary"]["bytes"] for a in adventures)
    stats = (f"{len(adventures)} adventures · {total_docs} files · "
             f"{total_bytes/1024/1024:.1f} MB")

    overview_md = build_overview_md(adventures)

    html = (TEMPLATE
            .replace("__TITLE__", "Claudovka Adventures — All Markdown Report")
            .replace("__HEADING__", "Claudovka Adventures")
            .replace("__STATS__", stats)
            .replace("__CATEGORY_ORDER__", json.dumps(CATEGORY_ORDER))
            .replace("__STATE_COLORS__", json.dumps(STATE_BADGE))
            .replace("__DATA__", json.dumps(adventures, ensure_ascii=False))
            .replace("__OVERVIEW__", json.dumps(overview_md, ensure_ascii=False)))

    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size/1024/1024:.2f} MB) from {len(adventures)} adventures, {total_docs} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
