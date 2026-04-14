#!/usr/bin/env python3
"""Generate a single-file static HTML report for an adventure directory.

Walks all *.md under the adventure root, embeds each file's raw markdown as
a JSON blob, renders via marked.js (CDN) on the client. Left sidebar groups
files by subdirectory, with a filter box and section expand/collapse.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "report.html"


def collect_docs(root: Path) -> list[dict]:
    docs = []
    for p in sorted(root.rglob("*.md")):
        rel = p.relative_to(root).as_posix()
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            text = f"<!-- failed to read: {e} -->"
        # Group by top-level directory, or 'root' for files at the adventure root.
        parts = rel.split("/")
        group = parts[0] if len(parts) > 1 else "root"
        docs.append({
            "path": rel,
            "group": group,
            "title": parts[-1].removesuffix(".md"),
            "bytes": len(text.encode("utf-8")),
            "content": text,
        })
    return docs


def group_order(groups: set[str]) -> list[str]:
    preferred = [
        "root", "manifest", "designs", "plans", "schemas", "roles",
        "research", "tests", "tasks", "reviews",
    ]
    known = [g for g in preferred if g in groups]
    extras = sorted(g for g in groups if g not in preferred)
    return known + extras


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
    --sidebar-w: 320px;
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
    padding: 14px 12px 40px;
  }
  aside h1 { font-size: 13px; margin: 4px 0 10px; color: var(--muted);
    text-transform: uppercase; letter-spacing: .05em; }
  aside input[type=search] {
    width: 100%; padding: 6px 9px; font-size: 13px;
    border: 1px solid var(--border); border-radius: 6px;
    background: white; margin-bottom: 12px;
  }
  aside .stats { font-size: 11px; color: var(--muted); margin-bottom: 12px; }
  details { margin-bottom: 6px; }
  summary {
    cursor: pointer; padding: 4px 6px; font-size: 12px; font-weight: 600;
    color: #24292f; border-radius: 4px; user-select: none;
    text-transform: uppercase; letter-spacing: .03em;
  }
  summary:hover { background: #eaeef2; }
  summary .count { font-weight: 400; color: var(--muted); margin-left: 6px; }
  ul.doclist { list-style: none; margin: 2px 0 6px 0; padding: 0; }
  ul.doclist li { margin: 0; }
  ul.doclist a {
    display: block; padding: 3px 8px 3px 18px; font-size: 12.5px;
    color: #24292f; text-decoration: none; border-radius: 4px;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  ul.doclist a:hover { background: #eaeef2; }
  ul.doclist a.active { background: var(--accent-bg); color: var(--accent); font-weight: 600; }
  main {
    overflow-y: auto; padding: 0;
    background: var(--bg);
  }
  header.docheader {
    position: sticky; top: 0; z-index: 10; background: var(--bg);
    border-bottom: 1px solid var(--border); padding: 12px 32px;
    display: flex; align-items: center; gap: 14px;
  }
  header.docheader h2 { margin: 0; font-size: 16px; font-weight: 600; }
  header.docheader .meta { font-size: 12px; color: var(--muted); margin-left: auto; }
  header.docheader .rawlink { font-size: 12px; color: var(--accent); text-decoration: none; }
  header.docheader .rawlink:hover { text-decoration: underline; }
  article.markdown-body {
    max-width: 920px; margin: 0 auto; padding: 32px;
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
  .noresults { padding: 8px; color: var(--muted); font-size: 12px; font-style: italic; }
  code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
</style>
</head>
<body>
<aside>
  <h1>__HEADING__</h1>
  <div class="stats">__STATS__</div>
  <input type="search" id="filter" placeholder="Filter files…" autocomplete="off">
  <nav id="nav"></nav>
</aside>
<main>
  <header class="docheader">
    <h2 id="doctitle">Select a document</h2>
    <span class="meta" id="docmeta"></span>
  </header>
  <article class="markdown-body" id="doc"><div class="empty">Choose a file from the left to render its markdown.</div></article>
</main>
<script id="docs-data" type="application/json">__DATA__</script>
<script>
const DOCS = JSON.parse(document.getElementById('docs-data').textContent);
const GROUP_ORDER = __GROUP_ORDER__;
const byPath = Object.fromEntries(DOCS.map(d => [d.path, d]));

// Build sidebar
const nav = document.getElementById('nav');
for (const group of GROUP_ORDER) {
  const items = DOCS.filter(d => d.group === group);
  if (!items.length) continue;
  const det = document.createElement('details');
  det.open = true;
  det.dataset.group = group;
  const sum = document.createElement('summary');
  sum.innerHTML = group + '<span class="count">' + items.length + '</span>';
  det.appendChild(sum);
  const ul = document.createElement('ul');
  ul.className = 'doclist';
  for (const d of items) {
    const li = document.createElement('li');
    const a = document.createElement('a');
    a.href = '#' + encodeURIComponent(d.path);
    a.textContent = d.path.split('/').pop();
    a.title = d.path;
    a.dataset.path = d.path;
    li.appendChild(a);
    ul.appendChild(li);
  }
  det.appendChild(ul);
  nav.appendChild(det);
}

// Filter
document.getElementById('filter').addEventListener('input', (e) => {
  const q = e.target.value.trim().toLowerCase();
  for (const det of nav.querySelectorAll('details')) {
    let visible = 0;
    for (const li of det.querySelectorAll('li')) {
      const p = li.firstChild.dataset.path.toLowerCase();
      const hit = !q || p.includes(q);
      li.style.display = hit ? '' : 'none';
      if (hit) visible++;
    }
    det.style.display = visible ? '' : 'none';
    if (q) det.open = true;
  }
});

// Render helper
marked.setOptions({ gfm: true, breaks: false, headerIds: true, mangle: false });
function render(path) {
  const d = byPath[path];
  const art = document.getElementById('doc');
  const title = document.getElementById('doctitle');
  const meta = document.getElementById('docmeta');
  if (!d) {
    art.innerHTML = '<div class="empty">Not found: ' + path + '</div>';
    title.textContent = 'Not found';
    meta.textContent = '';
    return;
  }
  title.textContent = d.path;
  meta.textContent = (d.bytes/1024).toFixed(1) + ' KB';
  const raw = marked.parse(d.content);
  art.innerHTML = DOMPurify.sanitize(raw, { ADD_ATTR: ['id'] });
  // highlight active
  for (const a of nav.querySelectorAll('a')) {
    a.classList.toggle('active', a.dataset.path === path);
  }
  // scroll to top
  document.querySelector('main').scrollTop = 0;
}

// Hash routing
function fromHash() {
  const h = decodeURIComponent(location.hash.replace(/^#/, ''));
  if (h && byPath[h]) render(h);
  else if (DOCS.length) {
    // default: manifest.md if present
    const first = byPath['manifest.md'] || DOCS[0];
    render(first.path);
  }
}
window.addEventListener('hashchange', fromHash);
nav.addEventListener('click', (e) => {
  const a = e.target.closest('a[data-path]');
  if (!a) return;
  e.preventDefault();
  location.hash = '#' + encodeURIComponent(a.dataset.path);
  render(a.dataset.path);
});
fromHash();
</script>
</body>
</html>
"""


def main() -> int:
    docs = collect_docs(ROOT)
    groups = {d["group"] for d in docs}
    ordered = group_order(groups)
    total_kb = sum(d["bytes"] for d in docs) / 1024
    stats = f"{len(docs)} files · {total_kb:,.0f} KB · generated from <code>{ROOT.name}</code>"
    heading = f"{ROOT.name}"

    html = (TEMPLATE
            .replace("__TITLE__", f"{ROOT.name} — Markdown Report")
            .replace("__HEADING__", heading)
            .replace("__STATS__", stats)
            .replace("__GROUP_ORDER__", json.dumps(ordered))
            .replace("__DATA__", json.dumps(docs, ensure_ascii=False)))
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size/1024:,.0f} KB) from {len(docs)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
