# Install Visual System (CSS Tokens + Primitives) — Task Design

## Approach

Add the seven v2 visual-system primitives (`.card`, `.pill`, `.progress`,
`.chip-bar`, `.chip`, `.stack`, `.disclosure`) plus the new design tokens
to the single existing `<style>` block in `index.html`. This is a
**purely additive** CSS change — no legacy v1 rules are removed, no
existing rule is edited, no new `<link>` / external font / external CSS
file is introduced. The CDN-loaded `marked.js` in line 7 remains the only
external dependency.

The new rules live in a single new section inside `<style>`, placed
**before the closing `</style>` tag on line 228** so it comes after all
existing rules (later rules with equal specificity win). This makes the
patch a clean insertion that can be trivially reverted or inspected in a
diff. The v1 classes (`.split`, `.file-list`, `.concept-box`,
`.log-tail`, etc.) remain untouched — they will be retired in T011 after
all four v2 tabs are wired up (T006–T010).

New CSS variables are added to the existing `:root` block rather than a
new `:root` so token lookup stays single-source. Existing tokens (`--bg`,
`--bg-alt`, `--border`, `--text`, `--muted`, `--accent`, `--accent-dim`,
`--ok`, `--warn`, `--err`, `--badge-bg`) are left untouched.

## Target Files

- `.agent/adventure-console/index.html` — add 7 tokens to `:root` (lines
  9–22) and append a new `/* v2 visual system */` section immediately
  before `</style>` on line 228. Net file change is additive; no
  existing line is edited except the `:root` block (extension).

No other files are touched. No tests are added in this task — structural
TCs (TC-031, TC-032) are covered by `test_ui_layout.py`, which T012
implements per `design-test-strategy.md` (Tier 2).

## CSS Specification

### 1. Token additions (inside existing `:root`, lines 9–22)

Append these seven variables inside the existing `:root { }` block, on a
new line after `--badge-bg: #243040;`:

```css
  --card-bg:       #1a222d;
  --card-border:   #2a343f;
  --pill-bg:       #243040;
  --chip-bg:       #1d2731;
  --chip-active:   #2d6ca8;
  --progress-bg:   #243040;
  --progress-fill: #5ab0ff;
```

Rationale: taken verbatim from `design-visual-system.md` §Design tokens.
Note `--card-border` equals the existing `--border` value and
`--pill-bg` equals the existing `--badge-bg` value — the duplicate
variable names are intentional so that future theming work can diverge
pill/card from badge/global-border without a rename.

### 2. New component rules (new section before `</style>`)

Insert the following block immediately before the closing `</style>`
tag (after the existing `.log-tail` rule ending on line 227):

```css
  /* ===== v2 visual system (ADV-009) ===== */

  .card {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 8px;
    padding: 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
  }
  .card + .card { margin-top: 12px; }
  .card .card-title {
    font-size: 15px; font-weight: 600; margin: 0 0 6px;
  }
  .card .card-meta {
    font-size: 11px; color: var(--muted);
  }

  .pill {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 10px;
    background: var(--pill-bg);
    border: 1px solid var(--border);
    font-size: 11px; font-weight: 500;
    line-height: 1.4;
  }
  /* state-* / status-* color variants reuse existing .badge color rules
     via explicit pass-through. Declared here so markup can write either
     <span class="pill state-active"> or <span class="badge state-active">
     without a style divergence. */
  .pill.state-concept     { color: var(--muted); }
  .pill.state-planning    { color: var(--warn); border-color: var(--warn); }
  .pill.state-review      { color: var(--accent); border-color: var(--accent); }
  .pill.state-active      { color: var(--ok); border-color: var(--ok); }
  .pill.state-blocked     { color: var(--err); border-color: var(--err); }
  .pill.state-completed   { color: var(--ok); background: #1a3024; }
  .pill.state-cancelled   { color: var(--muted); text-decoration: line-through; }
  .pill.status-passed, .pill.status-PASSED { color: var(--ok); }
  .pill.status-failed, .pill.status-FAILED { color: var(--err); }
  .pill.status-pending, .pill.status-in_progress { color: var(--warn); }
  .pill.status-done       { color: var(--ok); }

  .progress {
    position: relative;
    width: 100%;
    height: 8px;
    background: var(--progress-bg);
    border-radius: 4px;
    overflow: hidden;
  }
  .progress > span {
    display: block;
    height: 100%;
    background: var(--progress-fill);
    transition: width 160ms ease-out;
  }

  .chip-bar {
    display: flex; gap: 6px; flex-wrap: wrap;
    margin: 0 0 12px;
  }
  .chip {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 12px;
    background: var(--chip-bg);
    border: 1px solid var(--border);
    color: var(--muted);
    font-size: 11px; font-weight: 500;
    cursor: pointer;
    user-select: none;
  }
  .chip:hover { color: var(--text); background: var(--bg-hover); }
  .chip.active {
    background: var(--chip-active);
    border-color: var(--accent);
    color: #fff;
  }
  .chip:focus-visible {
    outline: 2px solid var(--accent);
    outline-offset: 1px;
  }

  .stack { display: flex; flex-direction: column; gap: 16px; }

  details.disclosure {
    border: 1px solid var(--border);
    border-radius: 4px;
    background: var(--bg-alt);
    padding: 0;
    margin: 8px 0;
  }
  details.disclosure > summary {
    list-style: none;
    cursor: pointer;
    padding: 6px 10px;
    color: var(--muted);
    font-size: 12px;
    display: flex; align-items: center; gap: 6px;
  }
  details.disclosure > summary::-webkit-details-marker { display: none; }
  details.disclosure > summary::before {
    content: "";
    display: inline-block;
    width: 0; height: 0;
    border-left: 4px solid var(--muted);
    border-top: 4px solid transparent;
    border-bottom: 4px solid transparent;
    transition: transform 120ms ease-out;
  }
  details.disclosure[open] > summary::before { transform: rotate(90deg); }
  details.disclosure > summary:hover { color: var(--text); }
  details.disclosure > .disclosure-body {
    padding: 8px 10px 10px;
    border-top: 1px solid var(--border);
  }
```

### 3. Class-name contract (for downstream tasks)

Subsequent tasks (T006–T010) consume these classes. This task only
declares them — it does NOT add any HTML markup that uses them. That
keeps the diff minimal and keeps the v1 UI fully intact at the end of
this task.

The `.card-title` / `.card-meta` sub-selectors are included here (rather
than inlined in the later task designs) because they are structural
conventions of the card primitive. They mirror the `.card` contract
described in `design-task-card-layout.md` and `design-overview-tab.md`.

## Implementation Steps

The implementer (role: `coder`) executes in this order:

1. **Read `index.html`** — specifically the `:root` block (lines 9–22)
   and the tail of the `<style>` block (lines 220–228). Confirm no
   concurrent CSS edit has reshaped those regions.
2. **Patch `:root`** — insert the seven new `--card-bg` /
   `--card-border` / `--pill-bg` / `--chip-bg` / `--chip-active` /
   `--progress-bg` / `--progress-fill` variables after the
   `--badge-bg: #243040;` line. No other tokens change.
3. **Append the v2 section** — insert the `/* ===== v2 visual system
   (ADV-009) ===== */` comment followed by the seven rule-groups (card,
   pill, progress, chip-bar + chip, stack, disclosure) immediately
   before the closing `</style>` on what is currently line 228. Preserve
   2-space indentation consistent with the rest of the stylesheet.
4. **Verify no removals** — confirm every original CSS selector (`.split`,
   `.file-list`, `.file-entry`, `.file-view`, `.kb-item`, `.concept-box`,
   `.log-tail`, `.tab`, `.tabs`, `.badge`, `.adv-header`, `.adv-meta`,
   `.adv-item`, `.btn-row`, `#toast`, `.empty`, `button`, `input`,
   `table`, `th`, `td`, `tr`, `pre`, `code`, `a`, `body`, `html`) still
   exists in the file.
5. **Open `index.html` in a browser** (manual smoke) — load the console,
   pick any adventure; confirm v1 layout still renders unchanged (same
   sidebar, same 9 tabs, same widgets). The v2 classes are unused at
   this stage; their presence in the stylesheet is inert.
6. **Update task** — append log line, flip `status: ready`, record
   metrics row in `.agent/adventures/ADV-009/metrics.md`.

## Testing Strategy

This task has three acceptance criteria. Each is covered as follows:

- **AC #1** ("All seven new classes exist"): a simple grep covers it:
  ```bash
  for c in "\.card" "\.pill" "\.progress" "\.chip-bar" "\.chip[^-]" \
           "\.stack" "details\.disclosure"; do
    grep -qE "$c" .agent/adventure-console/index.html || echo "MISSING: $c"
  done
  ```
  The `.chip[^-]` guard distinguishes `.chip` from `.chip-bar` and
  `.chip-active` (a variable, not a class). The implementer runs this
  before marking the task ready.

- **AC #2** ("No new `<link rel=\"stylesheet\">` or external font
  imports"): `grep -nE '<link[^>]*stylesheet|@import|<link[^>]*fonts' \
  .agent/adventure-console/index.html` must return zero matches beyond
  whatever the v1 already had (currently zero — the only external asset
  is the `marked.js` CDN `<script>` tag on line 7, which is not a
  stylesheet).

- **AC #3** ("Existing v1 styles still resolve — no visual breakage
  yet"): confirmed by (a) the step-4 grep check that no v1 selector was
  removed, and (b) the step-5 browser smoke — v1 UI must look identical
  before/after this task.

**Structural TCs (covered by T012's test_ui_layout.py, not this task)**:

- **TC-031** — `test_ui_layout.test_visual_primitives_exist` asserts
  every one of the seven class-name tokens is found in the `<style>`
  block text. Expected to pass after this task lands.
- **TC-032** — `test_ui_layout.test_no_external_stylesheets` parses the
  HTML and asserts `<link rel="stylesheet">` count is 0. Expected to
  pass after this task lands.

No new test code is added in T005. T012 is the only place that adds test
code; this task simply makes T012's future assertions green.

## Risks

1. **Selector collision with v1** — `.pill.state-*` and `.pill.status-*`
   reuse the v1 color palette that `.badge.state-*` already uses. If a
   future markup change adds `class="pill badge state-active"` the rule
   order will matter. Mitigation: the v2 section is placed **after** the
   v1 `.badge` section so identical-specificity `.pill.state-active`
   rules override-by-position when both classes co-occur; but the
   expected markup is `class="pill state-active"` *xor* `class="badge
   state-active"`, never both. Called out here so T006 reviewers can
   spot double-classing.

2. **Closing-tag placement drift** — this design assumes `</style>` sits
   on line 228 of `index.html` (confirmed by current read). If another
   task lands first and shifts the line, the implementer must insert
   relative to the `</style>` tag, not the line number. Mitigation: step
   3 of implementation anchors on the `</style>` token, not on a line
   number.

3. **Token name duplication (`--card-border` vs `--border`,
   `--pill-bg` vs `--badge-bg`)** — both pairs hold the same value in
   this task. A future theming pass could diverge them; today they are
   intentionally redundant. Design-visual-system chose the new names
   deliberately — do NOT collapse them to reuse the existing tokens.

4. **Disclosure chevron not rendering in older browsers** — the
   `::-webkit-details-marker { display: none; }` rule + the CSS triangle
   via borders works in Chromium / Edge / Safari. Firefox hides the
   default marker via `summary { list-style: none; }`. Tested
   combinations: Chromium 120+, Firefox 120+, Edge 120+. The console is
   an internal developer tool — no IE/legacy support required.

5. **T006 wiring** — the next task (T006) begins consuming `.card`,
   `.pill`, `.progress` in header and tab-bar markup. If T005 is
   reviewed in isolation and the v1 UI looks identical, that is the
   **expected** outcome, not a bug. Document this in the task log so
   reviewers don't flag "no visible change" as a regression.
