# Superdesign theme context

The plugin uses offline CSS surfaces with no global web framework or remote font system. The compact receipts use a cool paper palette with accent blue, the triage/practice surfaces use scoped green/coral decision cues, and the executive dossier uses a document-like paper/ink system. The learning-proof sprint and private first-interview board v2 belong to the practice/triage family. V2 adds an explicit provenance trust strip and keeps decision, trust, and approval boundaries distinguishable in dark, print, forced-colors, intermediate-width, and mobile modes.

## Compact token summary

- Surfaces: white paper/card surfaces, pale blue-gray separators, dark ink text, muted secondary text.
- Compact decision accent: blue/cobalt accent with system-color fallbacks in forced-colors mode.
- Triage/practice accents: forest/coral decision cues; status colors are paired with visible labels.
- Layout: single column by default; compact fact grids become two columns only above `641px`; cards preserve print atomicity.
- Typography: system sans-serif stacks; no downloaded fonts or external resources.
- Accessibility: skip link, focus-visible rings, reduced-motion handling, print rules, forced-colors hooks, and text equivalents for scored values.
- Privacy: `noindex,nofollow,noarchive`, no external network requests, no image/font fetching.

## Raw CSS source dumps

### `plugins/professional-growth-coach/assets/executive-career-dossier-v1.css`

```css
:root {
  --paper: #f6f4ee;
  --forest: #173e30;
  --ink: #1a1a1a;
  --muted: #e2ddd6;
  --muted-text: #53605a;
  --line: #b8c7c0;
  --progress-track: #7f9186;
  --coral: #d96c52;
  --gold: #be9338;
  --surface: #ffffff;
  --forest-soft: #dce5e0;
  --coral-soft: #f7e4df;
  --gold-soft: #f5ecd8;
  --measure: 72ch;
  --serif: Georgia, "Times New Roman", Times, serif;
  --sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
}

* { box-sizing: border-box; }

html { color-scheme: light; background: var(--paper); }

body {
  margin: 0;
  min-width: 0;
  background: var(--paper);
  color: var(--ink);
  font-family: var(--sans);
  font-size: 16px;
  line-height: 1.55;
  overflow-wrap: anywhere;
}

a { color: var(--forest); text-underline-offset: 0.18em; }

a:focus-visible,
button:focus-visible,
summary:focus-visible {
  outline: 3px solid var(--coral);
  outline-offset: 3px;
}

.skip-link {
  position: fixed;
  z-index: 10;
  top: 0.5rem;
  left: 0.5rem;
  padding: 0.75rem 1rem;
  background: var(--surface);
  border: 1px solid var(--forest);
  transform: translateY(-200%);
}

.skip-link:focus { transform: none; }

main:focus-visible {
  outline: 3px solid var(--coral);
  outline-offset: 4px;
}

.shell {
  width: min(1160px, calc(100% - 2rem));
  margin-inline: auto;
}

.utility-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 1.5rem;
  padding-block: 2rem 1rem;
  border-bottom: 1px solid var(--forest);
}

.eyebrow,
.meta,
.status-label,
.section-kicker {
  margin: 0;
  color: var(--forest);
  font-size: 0.8125rem;
  font-weight: 700;
  letter-spacing: 0.11em;
  line-height: 1.5;
  text-transform: uppercase;
}

.report-title,
h2,
h3,
.score-value,
.priority-rank {
  font-family: var(--serif);
}

.report-title {
  margin: 0.15rem 0 0;
  font-size: clamp(2rem, 5vw, 3.45rem);
  font-style: italic;
  font-weight: 600;
  letter-spacing: -0.035em;
  line-height: 1;
}

.utility-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 0.65rem;
}

.privacy-chip,
.state-chip,
.confidence-chip {
  display: inline-flex;
  align-items: center;
  min-height: 2.25rem;
  padding: 0.4rem 0.75rem;
  border: 1px solid currentColor;
  color: var(--forest);
  font-size: 0.8125rem;
  font-weight: 700;
  line-height: 1.2;
}

button {
  min-width: 44px;
  min-height: 44px;
  padding: 0.6rem 0.9rem;
  border: 1px solid var(--forest);
  border-radius: 0;
  background: var(--forest);
  color: var(--surface);
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}

button:hover { background: var(--ink); }

main { padding-block: 1.25rem 3rem; }

.dossier-grid {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: 1rem;
}

.section-block {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px dotted var(--muted);
}
.span-12 { grid-column: span 12; }
.span-8 { grid-column: span 8; }
.span-7 { grid-column: span 7; }
.span-6 { grid-column: span 6; }
.span-5 { grid-column: span 5; }
.span-4 { grid-column: span 4; }

.card {
  min-width: 0;
  background: var(--surface);
  border: 1px solid var(--forest-soft);
  box-shadow: none;
  padding: clamp(1.15rem, 2.5vw, 1.75rem);
  animation: dossier-enter 0.6s ease both;
  transition: transform 0.2s ease;
}

.card:hover { transform: translateY(-2px); }
.card:nth-child(2n) { animation-delay: 0.08s; }
.card:nth-child(3n) { animation-delay: 0.16s; }

.card h2,
.card h3 { margin-top: 0; }

h2 {
  margin-bottom: 1rem;
  color: var(--forest);
  font-size: clamp(1.35rem, 3vw, 2rem);
  line-height: 1.15;
}

h3 {
  margin-bottom: 0.75rem;
  font-size: 1.25rem;
  line-height: 1.2;
}

p { max-width: var(--measure); }

.verdict-card {
  display: flex;
  min-height: 19rem;
  flex-direction: column;
  justify-content: space-between;
  border-top: 4px solid var(--forest);
}

.verdict-statement {
  margin: 0.3rem 0 0.85rem;
  max-width: 48ch;
  font-family: var(--serif);
  font-size: clamp(1.45rem, 3vw, 2.35rem);
  line-height: 1.16;
}

.start-here {
  margin-top: 1rem;
  padding: 1rem;
  background: var(--forest-soft);
  border-left: 4px solid var(--forest);
}

.start-here strong { display: block; color: var(--forest); }

.coverage-row,
.score-line,
.priority-header,
.copy-heading,
.metric-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.coverage-row { flex-wrap: wrap; margin-top: 1rem; }
.score-value { color: var(--forest); font-size: 2.5rem; font-weight: 600; line-height: 1; }
.score-note { color: #4f5955; font-size: 0.875rem; }

.scan-list,
.clean-list,
.priority-list,
.plan-list,
.question-list {
  margin: 0;
  padding: 0;
  list-style: none;
}

.scan-list li,
.clean-list li {
  padding: 0.8rem 0 0.8rem 1rem;
  border-left: 2px solid var(--muted);
}

.scan-list li + li,
.clean-list li + li { margin-top: 0.5rem; }

.label {
  display: block;
  margin-bottom: 0.15rem;
  color: #53605a;
  font-size: 0.8125rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  line-height: 1.5;
  text-transform: uppercase;
}

.priorities-grid .card { border-top: 4px solid var(--coral); }
.priority-rank { color: var(--coral); font-size: 2.25rem; line-height: 1; }
.priority-body dt { margin-top: 0.75rem; color: #53605a; font-size: 0.8125rem; font-weight: 700; text-transform: uppercase; }
.priority-body dd { margin: 0.15rem 0 0; }

.timebox {
  display: inline-block;
  margin-top: 1rem;
  padding: 0.25rem 0.55rem;
  background: var(--gold-soft);
  border: 1px solid var(--gold);
  font-weight: 700;
}

.analytics-card { border-top: 4px solid var(--gold); }
.metric-value { color: var(--forest); font-family: var(--serif); font-size: 2rem; font-weight: 600; }
.metric-row + .metric-row { margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid var(--muted); }

.dimension-grid { align-items: stretch; }
.dimension-card { grid-column: span 4; }
.dimension-card:last-child { grid-column: span 12; }
.not-evaluated { border-style: dashed; }

progress {
  display: block;
  width: 100%;
  height: 0.65rem;
  margin-top: 0.75rem;
  border: 0;
  border-radius: 0;
  background: var(--progress-track);
  color: var(--forest);
}

progress::-webkit-progress-bar { background: var(--progress-track); }
progress::-webkit-progress-value { background: var(--forest); }
progress::-moz-progress-bar { background: var(--forest); }

.visual-card { border-top: 4px solid var(--forest); }
.market-card { border-top: 4px solid var(--gold); }

.comparison-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 1rem;
  table-layout: fixed;
}

.comparison-table caption {
  padding-bottom: 0.75rem;
  text-align: left;
  font-weight: 700;
}

.comparison-table th,
.comparison-table td {
  padding: 0.8rem;
  border-bottom: 1px solid var(--muted);
  hyphens: auto;
  overflow-wrap: anywhere;
  text-align: left;
  vertical-align: top;
}

.comparison-table th { color: var(--forest); }

.copy-card { position: relative; }
.copy-text { margin: 1rem 0; padding: 1rem; background: var(--paper); border-left: 4px solid var(--forest); font-family: var(--serif); font-size: 1.15rem; }
.copy-status { display: block; min-height: 1.4em; margin-top: .5rem; color: #4f5955; font-size: .875rem; }
.boundary { color: #4f5955; font-size: 0.875rem; }
.screen-preparation-card {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 1rem;
  border-top: 4px solid var(--gold);
  font-size: 1rem;
}
.screen-preparation-card > h2 { grid-column: 1; grid-row: 1; margin-bottom: 0; }
.screen-preparation-card > .label,
.screen-preparation-card > .copy-text,
.screen-preparation-evidence,
.screen-preparation-boundary,
.screen-preparation-rehearsal { grid-column: 1 / -1; }
.readiness-chip {
  grid-column: 2;
  grid-row: 1;
  align-self: start;
  min-height: 44px;
  padding: 0.45rem 0.75rem;
  border: 1px solid currentColor;
  font-size: 0.875rem;
  font-weight: 700;
  line-height: 1.2;
}
.screen-preparation-state--ready { background: var(--forest-soft); color: var(--forest); }
.screen-preparation-state--requires-confirmation { background: var(--gold-soft); color: #654c10; }
.screen-preparation-state--omit { background: var(--coral-soft); color: #7c2f1e; }
.screen-preparation-state--paused { background: var(--muted); color: #39443f; }
.screen-preparation-evidence { padding: 1rem; background: var(--paper); }
.screen-preparation-question {
  grid-column: 1 / -1;
  padding: 1rem;
  border: 1px solid var(--forest);
  border-left: 4px solid var(--forest);
  background: var(--forest-soft);
}
.screen-preparation-question h3 { margin: 0; color: var(--forest); font-size: 1.2rem; }
.screen-preparation-question p { max-width: var(--measure); margin: 0.45rem 0 0; }
.screen-preparation-handoff {
  grid-column: 1 / -1;
  padding: 1rem;
  border: 1px dashed var(--forest);
  background: var(--paper);
}
.screen-preparation-handoff h3 { margin: 0; color: var(--forest); font-size: 1.1rem; }
.screen-preparation-handoff p { max-width: var(--measure); margin: 0.4rem 0 0; }
.screen-preparation-manual-note {
  grid-column: 1 / -1;
  margin: 0;
  padding: 0.75rem 1rem;
  border: 1px solid var(--gold);
  border-left: 4px solid var(--gold);
  background: var(--gold-soft);
}
.screen-preparation-manual-note h3 { margin: 0; color: #654c10; font-size: 1.1rem; }
.screen-preparation-manual-note p { max-width: var(--measure); margin: 0.4rem 0 0; }
.screen-preparation-boundary,
.screen-preparation-rehearsal { margin: 0; font-size: 1rem; }
.hold-card { border-left: 4px solid var(--coral); }
.question-card:first-child { border-top: 4px solid var(--coral); }

.plan-day {
  display: grid;
  grid-template-columns: minmax(3.5rem, auto) 1fr;
  gap: 1rem;
  padding: 1rem 0;
  border-bottom: 1px solid var(--muted);
}

.day-badge { color: var(--forest); font-family: var(--serif); font-size: 1.25rem; font-weight: 700; }

details summary {
  min-height: 44px;
  padding-block: 0.6rem;
  color: var(--forest);
  font-weight: 700;
  cursor: pointer;
}

.method-list { padding-left: 1.25rem; }
.method-list li + li { margin-top: 0.6rem; }
.method-list a { word-break: break-word; }

.footer {
  padding-block: 1.5rem 2.5rem;
  border-top: 1px solid var(--forest);
  color: #39443f;
  font-size: 0.875rem;
}

@media screen and (prefers-color-scheme: dark) {
  :root {
    color-scheme: dark;
    --paper: #101521;
    --surface: #182235;
    --ink: #f3f6ff;
    --muted: #b8c4d8;
    --muted-text: #b8c4d8;
    --line: #5f718e;
    --forest: #8fc9b0;
    --forest-soft: #223b35;
    --coral: #ff9f8d;
    --coral-soft: #3f282d;
    --gold: #f2c970;
    --gold-soft: #3b301f;
  }
  html,
  .dossier-document { background: var(--paper); color: var(--ink); }
  .dossier-document progress { background: var(--forest-soft); }
  .dossier-document progress::-webkit-progress-bar { background: var(--forest-soft); }
  .dossier-document progress::-moz-progress-bar { background: var(--forest); }
  .dossier-document .score-note,
  .dossier-document .label,
  .dossier-document .priority-body dt,
  .dossier-document .copy-status,
  .dossier-document .boundary,
  .dossier-document .footer { color: var(--muted); }
  .dossier-document .section-block,
  .dossier-document .metric-row + .metric-row,
  .dossier-document .comparison-table { border-color: var(--line); }
  .dossier-document .screen-preparation-state--requires-confirmation { color: var(--gold); background: var(--gold-soft); }
  .dossier-document .screen-preparation-state--omit { color: var(--coral); background: var(--coral-soft); }
  .dossier-document .screen-preparation-state--paused { color: var(--ink); background: var(--forest-soft); }
  .dossier-document .screen-preparation-evidence,
  .dossier-document .copy-text { background: var(--paper); }
  .dossier-document .screen-preparation-manual-note { background: var(--gold-soft); }
  .dossier-document .screen-preparation-manual-note h3 { color: var(--gold); }
}

@keyframes dossier-enter {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: none; }
}

@media (max-width: 900px) {
  .span-8,
  .span-7,
  .span-6,
  .span-5,
  .span-4,
  .dimension-card,
  .dimension-card:last-child { grid-column: span 12; }
  .utility-header { align-items: flex-start; flex-direction: column; }
  .utility-actions { justify-content: flex-start; }
  .verdict-card { min-height: auto; }
}

@media (max-width: 680px) {
  .screen-preparation-card { grid-template-columns: 1fr; }
  .screen-preparation-card > h2,
  .readiness-chip { grid-column: 1; grid-row: auto; }
}

@media (max-width: 480px) {
  .shell { width: min(100% - 1rem, 1160px); }
  .card { padding: 1rem; }
  .coverage-row,
  .score-line,
  .priority-header,
  .copy-heading,
  .metric-row { align-items: flex-start; flex-direction: column; }
  .comparison-table th,
  .comparison-table td { padding: 0.5rem 0.25rem; }
  .plan-day { grid-template-columns: 1fr; gap: 0.25rem; }
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation: none !important;
    scroll-behavior: auto !important;
    transition: none !important;
  }
}

@page { size: auto; margin: 14mm; }

@media print {
  html,
  .dossier-document { background: #ffffff; }
  .dossier-document {
    font-size: 12pt;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
  .shell { width: 100%; }
  .no-print,
  .skip-link { display: none !important; }
  .card,
  tr,
  .plan-day {
    break-inside: avoid;
    page-break-inside: avoid;
  }
  .screen-preparation-card {
    break-inside: avoid;
    break-after: avoid;
    page-break-inside: avoid;
    page-break-after: avoid;
  }
  .screen-preparation-question { break-inside: avoid; page-break-inside: avoid; }
  .screen-preparation-handoff { break-inside: avoid; page-break-inside: avoid; }
  .screen-preparation-manual-note { break-inside: avoid; page-break-inside: avoid; }
  h1,
  h2,
  h3 {
    break-after: avoid;
    page-break-after: avoid;
  }
  p,
  li { orphans: 3; widows: 3; }
  details { display: block; }
  details > * { display: block !important; }
  .card { animation: none; transition: none; }
  .footer {
    padding-bottom: 0;
    break-inside: avoid;
    page-break-inside: avoid;
  }
}

@media (forced-colors: active) {
  button { background: ButtonFace; color: ButtonText; border-color: ButtonText; }
  button:hover { background: Highlight; color: HighlightText; }
  .dossier-document .skip-link { background: Canvas; border-color: CanvasText; color: CanvasText; }
  .dossier-document .card { border-color: CanvasText; }
  a:focus-visible,
  button:focus-visible,
  summary:focus-visible,
  main:focus-visible { outline-color: Highlight; }
  .screen-preparation-question {
    border: 1px solid CanvasText;
    border-left: 4px solid Highlight;
    background: Canvas;
    color: CanvasText;
  }
  .screen-preparation-question h3 { color: CanvasText; }
  .screen-preparation-handoff { border: 1px dashed CanvasText; background: Canvas; color: CanvasText; }
  .screen-preparation-handoff h3 { color: CanvasText; }
  .screen-preparation-manual-note { border: 1px solid CanvasText; border-left: 4px solid Highlight; background: Canvas; color: CanvasText; }
  .screen-preparation-manual-note h3 { color: CanvasText; }
  .footer { color: CanvasText; border-color: CanvasText; }
}

@media (prefers-contrast: more) {
  .dossier-document .card { border-color: var(--ink); }
  .screen-preparation-question,
  .screen-preparation-handoff,
  .screen-preparation-manual-note { border-width: 2px; }
  .screen-preparation-question h3,
  .screen-preparation-handoff h3,
  .screen-preparation-manual-note h3 { text-decoration: underline; text-decoration-thickness: 0.12em; }
}

@media (forced-colors: active) and (prefers-contrast: more) {
  .dossier-document .card { border-color: CanvasText; }
}
```

### `plugins/professional-growth-coach/assets/private-first-interview-conversion-board-v2.css`

```css
:root {
  --paper: #f6f4ee; --surface: #fff; --ink: #1b1c1a; --muted: #536158;
  --forest: #173e30; --forest-soft: #dce5e0; --coral: #b9513a;
  --coral-soft: #f6e0da; --gold: #dfbf70; --line: #6f8175;
  --serif: Georgia, "Times New Roman", Times, serif;
  --sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
}
* { box-sizing: border-box; }
html { color-scheme: light; background: var(--paper); }
body { margin: 0; color: var(--ink); background: var(--paper); font: 16px/1.55 var(--sans); overflow-wrap: anywhere; }
main:focus-visible { outline: 3px solid var(--coral); outline-offset: 4px; }
.board-shell { width: min(920px, calc(100% - 2rem)); margin-inline: auto; }
.board-shell :focus-visible { outline: 3px solid var(--coral); outline-offset: 3px; }
.skip-link { position: fixed; z-index: 2; left: .5rem; top: .5rem; transform: translateY(-200%); padding: .75rem 1rem; background: var(--surface); border: 1px solid var(--forest); color: var(--forest); font-weight: 700; }
.skip-link:focus { transform: none; }
.board-header { display: flex; align-items: end; justify-content: space-between; gap: 1rem; padding: 2rem 0 1rem; border-bottom: 1px solid var(--forest); }
.board-kicker { margin: 0; color: var(--forest); font-size: .8125rem; font-weight: 700; letter-spacing: .09em; text-transform: uppercase; }
h1, h2, h3 { font-family: var(--serif); }
h1 { margin: .2rem 0 0; font-size: clamp(2rem, 6vw, 3.25rem); font-style: italic; line-height: 1.04; }
h2 { margin: 0; color: var(--forest); font-size: clamp(1.35rem, 3vw, 1.85rem); line-height: 1.16; }
.board-main h2 { scroll-margin-top: 1rem; }
h2:target { outline: 3px solid var(--gold); outline-offset: .35rem; }
h3 { margin: 0; font-size: 1.12rem; line-height: 1.2; }
.board-state { display: inline-flex; align-items: center; min-height: 2.25rem; padding: .4rem .75rem; border: 1px solid currentColor; color: var(--forest); font-size: .875rem; font-weight: 700; text-align: center; }
.board-main { padding: 1.5rem 0 3rem; }
.board-main > section + section { margin-top: 1.5rem; }
.board-decision { padding: clamp(1.15rem, 3vw, 2rem); background: var(--forest); border-left: 4px solid var(--gold); color: #fff; }
.board-decision-cockpit { box-shadow: 0 .65rem 1.75rem rgb(23 62 48 / .14); }
.board-decision-cockpit[data-board-state="ready"] { border-left-color: var(--gold); }
.board-decision-cockpit[data-board-state="clarify"] { border-left-color: var(--coral); }
.board-decision-cockpit[data-board-state="pause"] { border-left-color: var(--gold); box-shadow: 0 .65rem 1.75rem rgb(185 81 58 / .12); }
.board-decision-cockpit[data-board-state="stop"] { border-left-color: var(--coral); box-shadow: none; }
.board-decision h2 { color: #fff; }
.board-decision p { max-width: 72ch; }
.board-decision dl, .board-facts { display: grid; grid-template-columns: minmax(10rem, .35fr) minmax(0, 1fr); gap: .55rem 1rem; margin: 1rem 0 0; }
.board-decision dt { color: var(--gold); font-weight: 700; }
.board-decision dd, .board-facts dd { margin: 0; }
.board-cockpit-prompt { margin: 1rem 0 0; padding: .85rem 1rem; border-left: 2px solid var(--gold); background: rgb(255 255 255 / .12); font-weight: 700; }
.board-boundary { margin: 1rem 0 0; padding: .85rem 1rem; background: var(--coral-soft); border: 1px solid var(--coral); color: var(--ink); font-weight: 650; }
.board-trust-strip { padding: 1rem; border-left: 4px solid var(--gold); background: var(--forest-soft); }
.board-trust-strip ul { display: flex; flex-wrap: wrap; gap: .5rem 1rem; margin: .65rem 0 0; padding: 0; list-style: none; font-weight: 700; }
.board-trust-strip li { display: flex; align-items: center; gap: .35rem; }
.board-trust-strip li::before { content: "•"; color: var(--coral); }
.board-section-nav { margin-top: 1.5rem; padding: .75rem 1rem; border: 1px solid var(--line); background: var(--surface); }
.board-section-nav-label { margin: 0; color: var(--muted); font-size: .8rem; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; }
.board-section-nav ul { display: flex; flex-wrap: wrap; gap: .5rem .75rem; margin: .5rem 0 0; padding: 0; list-style: none; }
.board-section-nav a { display: inline-flex; min-height: 44px; align-items: center; padding: .35rem .6rem; color: var(--forest); font-weight: 700; text-decoration-thickness: .12em; text-underline-offset: .16em; }
.board-section-nav a:hover { color: var(--coral); }
.board-approval-boundary { margin-top: 1.5rem; padding: 1rem; background: var(--coral-soft); border: 2px solid var(--coral); }
.board-approval-boundary h2 { color: var(--ink); }
.board-approval-boundary ul { columns: 3; margin: .5rem 0 0; padding-left: 1.25rem; }
.board-sequence ol, .board-week-list, .board-review-list, .board-ladder-list, .board-proof-list, .board-risk-list { display: grid; gap: 1rem; margin: 1rem 0 0; padding: 0; list-style: none; }
.board-sequence ol { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.board-sequence li, .board-proof-card, .board-risk-card, .board-practice-gate, .board-day, .board-branch, .board-review { min-width: 0; padding: 1rem; background: var(--surface); border: 1px solid var(--line); }
.board-sequence li { border-top: 4px solid var(--forest); }
.board-number { display: block; color: var(--coral); font-size: .8rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }
.board-proof-list, .board-risk-list, .board-week-list, .board-review-list, .board-ladder-list { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.board-proof-card { border-left: 4px solid var(--forest); }
.board-risk-card { border-left: 4px solid var(--coral); }
.board-risk-card dl { margin: .75rem 0 0; }
.board-risk-card dt, .board-day dt, .board-review dt, .board-branch dt { margin-top: .6rem; color: var(--muted); font-size: .8rem; font-weight: 700; }
.board-risk-card dd, .board-day dd, .board-review dd, .board-branch dd { margin: .1rem 0 0; }
.board-practice-gate { background: var(--coral-soft); border-left: 4px solid var(--coral); }
.board-practice-gate[data-board-state="ready"] { border-left-color: var(--coral); }
.board-practice-gate[data-board-state="clarify"] { background: var(--forest-soft); border-left-color: var(--gold); }
.board-practice-gate[data-board-state="pause"] { background: var(--paper); border-left-color: var(--gold); }
.board-practice-gate p { max-width: 72ch; }
.board-practice-question { margin: .85rem 0 0; font-size: 1.05rem; }
.board-practice-instruction { margin: 1rem 0 0; font-weight: 700; }
.board-reentry-capsule { padding: 1rem; background: var(--forest-soft); border: 1px solid var(--forest); border-left: 4px solid var(--forest); }
.board-reentry-capsule p { max-width: 72ch; margin: .45rem 0 0; }
.board-reentry-recipe-label { color: var(--muted); font-size: .8rem; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; }
.board-reentry-recipe { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .75rem; margin: .65rem 0 0; padding: 0; list-style: none; }
.board-reentry-recipe li { display: grid; grid-template-columns: auto 1fr; gap: .6rem; min-width: 0; padding: .75rem; background: var(--surface); border: 1px solid var(--forest); }
.board-reentry-step { display: grid; width: 1.7rem; height: 1.7rem; place-items: center; border-radius: 50%; background: var(--forest); color: #fff; font-size: .8rem; font-weight: 700; }
.board-reentry-recipe strong, .board-reentry-recipe li > span:last-child > span { display: block; }
.board-reentry-recipe li > span:last-child > span { margin-top: .2rem; color: var(--muted); font-size: .9rem; }
.board-day { border-top: 4px solid var(--forest); }
.board-day strong, .board-review strong, .board-branch strong { color: var(--forest); }
.board-day dl, .board-review dl, .board-branch dl { display: grid; gap: .55rem; margin: .8rem 0 0; }
.board-branch { border-left: 4px solid var(--gold); }
.board-footer { padding: 1rem max(1rem, calc((100% - 920px) / 2)) 2rem; border-top: 1px solid var(--forest); color: var(--muted); font-size: .88rem; }
.board-footer p { margin: .4rem 0 0; }
@media (min-width: 641px) and (max-width: 900px) { .board-sequence ol { grid-template-columns: repeat(2, minmax(0, 1fr)); } .board-approval-boundary ul { columns: 2; } }
@media (max-width: 640px) { .board-header { display: block; } .board-state { margin-top: 1rem; } .board-sequence ol, .board-proof-list, .board-risk-list, .board-week-list, .board-review-list, .board-ladder-list, .board-reentry-recipe { grid-template-columns: 1fr; } .board-decision dl, .board-facts { grid-template-columns: 1fr; gap: .25rem; } .board-decision dt { margin-top: .6rem; } .board-trust-strip ul { display: grid; grid-template-columns: 1fr; } .board-approval-boundary ul { columns: 1; } }
@media screen and (prefers-color-scheme: dark) { :root { color-scheme: dark; --paper: #101521; --surface: #182235; --ink: #f3f6ff; --muted: #b8c4d8; --forest: #8fc9b0; --forest-soft: #244337; --coral: #ff9b83; --coral-soft: #4a2829; --gold: #f2d28a; --line: #5f718e; } .board-decision { background: #173e30; } .board-decision, .board-decision h2 { color: var(--ink); } }
@media print { :root { color-scheme: light; --paper: #fff; --surface: #fff; --ink: #000; --muted: #536158; --forest: #000; --forest-soft: #fff; --coral: #000; --coral-soft: #fff; --gold: #000; --line: #000; } html, body { background: var(--paper); color: var(--ink); } .board-shell { width: 100%; } .board-header, .board-decision, .board-trust-strip, .board-section-nav, .board-practice-gate, .board-reentry-capsule, .board-sequence, .board-proof, .board-risks, .board-week, .board-ladder, .board-reviews, .board-boundary, .board-approval-boundary, .board-footer { break-inside: avoid; page-break-inside: avoid; } .board-sequence li, .board-proof-card, .board-risk-card, .board-day, .board-branch, .board-review, .board-reentry-recipe li { break-inside: avoid; page-break-inside: avoid; } .board-section-nav { display: none; } .board-main h2:target { outline: 0; } .board-decision, .board-boundary, .board-trust-strip, .board-practice-gate, .board-reentry-capsule, .board-approval-boundary { color: var(--ink); border-color: var(--line); background: var(--paper); } .board-reentry-recipe li { border-color: var(--line); } .board-reentry-step { color: var(--ink); background: var(--paper); border: 1px solid var(--line); } .board-decision-cockpit { box-shadow: none; } .board-cockpit-prompt { background: var(--paper); border-color: var(--line); } .skip-link { display: none; } }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation-duration: .01ms !important; transition-duration: .01ms !important; scroll-behavior: auto !important; } }
@media (forced-colors: active) { .skip-link, .board-decision, .board-trust-strip, .board-section-nav, .board-practice-gate, .board-reentry-capsule, .board-approval-boundary, .board-sequence li, .board-proof-card, .board-risk-card, .board-day, .board-branch, .board-review, .board-reentry-recipe li { background: Canvas; color: CanvasText; border-color: CanvasText; } .skip-link:focus-visible, main:focus-visible, h2:target, .board-section-nav a:focus-visible { outline: 2px solid Highlight; outline-offset: 3px; } .board-section-nav a, .board-decision h2, .board-decision dt, .board-decision dd, .board-kicker, .board-approval-boundary h2, h2, strong { color: CanvasText; } .board-reentry-step { color: Canvas; background: CanvasText; border-color: CanvasText; } .board-reentry-recipe li > span:last-child > span { color: CanvasText; } }
```

### `plugins/professional-growth-coach/assets/private-recruiter-reply-triage-v1.css`

```css
:root {
  --paper: #f6f4ee;
  --surface: #ffffff;
  --ink: #1b1c1a;
  --forest: #173e30;
  --forest-soft: #dce5e0;
  --coral: #b9513a;
  --coral-soft: #f6e0da;
  --line: #b8c7c0;
  --measure: 72ch;
  --serif: Georgia, "Times New Roman", Times, serif;
  --sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
}

.private-recruiter-triage-document { margin: 0; background: var(--paper); color: var(--ink); font-family: var(--sans); font-size: 16px; line-height: 1.55; overflow-wrap: anywhere; }
.private-recruiter-triage-document * { box-sizing: border-box; }
.private-recruiter-triage-document :focus-visible { outline: 3px solid var(--coral); outline-offset: 3px; }
.private-recruiter-triage-document .triage-shell { width: min(920px, calc(100% - 2rem)); margin-inline: auto; }
.private-recruiter-triage-document .skip-link { position: fixed; z-index: 10; top: 0.5rem; left: 0.5rem; transform: translateY(-200%); padding: 0.75rem 1rem; background: var(--surface); border: 1px solid var(--forest); color: var(--forest); font-weight: 700; }
.private-recruiter-triage-document .skip-link:focus { transform: none; }
.private-recruiter-triage-document .triage-header { padding-block: 2rem 1rem; border-bottom: 1px solid var(--forest); }
.private-recruiter-triage-document .triage-kicker { margin: 0; color: var(--forest); font-size: 0.8125rem; font-weight: 700; letter-spacing: 0.09em; text-transform: uppercase; }
.private-recruiter-triage-document h1, .private-recruiter-triage-document h2 { font-family: var(--serif); }
.private-recruiter-triage-document h1 { margin: 0.2rem 0 0; font-size: clamp(2rem, 6vw, 3.25rem); font-style: italic; line-height: 1.04; }
.private-recruiter-triage-document h2 { margin: 0; color: var(--forest); font-size: clamp(1.35rem, 3vw, 1.85rem); line-height: 1.16; }
.private-recruiter-triage-document main { padding-block: 1.5rem 3rem; }
.private-recruiter-triage-document .triage-card { min-width: 0; padding: clamp(1.15rem, 3vw, 2rem); background: var(--surface); border-top: 4px solid var(--forest); box-shadow: 0 1px 0 rgb(23 62 48 / 10%); animation: triage-enter 0.35s ease both; }
.private-recruiter-triage-document .triage-card > * + * { margin-top: 1.5rem; }
.private-recruiter-triage-document .triage-state { display: inline-flex; align-items: center; min-height: 2.25rem; padding: 0.4rem 0.75rem; border: 1px solid currentColor; color: var(--forest); font-size: 0.875rem; font-weight: 700; line-height: 1.2; }
.private-recruiter-triage-document .triage-state--stop { color: #854117; background: #f7ecd5; }
.private-recruiter-triage-document .triage-section { padding: 1rem; border: 1px solid var(--line); }
.private-recruiter-triage-document .triage-section p, .private-recruiter-triage-document .triage-section ul { max-width: var(--measure); }
.private-recruiter-triage-document .triage-section p { margin: 0.55rem 0 0; }
.private-recruiter-triage-document .triage-section ul { margin: 0.65rem 0 0; padding-left: 1.25rem; }
.private-recruiter-triage-document .triage-section li + li { margin-top: 0.5rem; }
.private-recruiter-triage-document .triage-decision, .private-recruiter-triage-document .triage-missing { background: var(--forest-soft); border-left: 4px solid var(--forest); }
.private-recruiter-triage-document .triage-next-safe-action { background: var(--paper); border-left: 4px solid var(--coral); }
.private-recruiter-triage-document .triage-blocked { background: var(--coral-soft); border-color: var(--coral); }
.private-recruiter-triage-document .triage-handoff { border-left: 4px solid var(--forest); }
.private-recruiter-triage-document .triage-handoff-sequence { display: grid; gap: 1rem; margin: 1rem 0 0; padding: 0; list-style: none; counter-reset: handoff-step; }
.private-recruiter-triage-document .triage-handoff-sequence > li { position: relative; counter-increment: handoff-step; min-width: 0; padding-left: 3.25rem; }
.private-recruiter-triage-document .triage-handoff-sequence > li::before { content: counter(handoff-step); display: inline-grid; position: absolute; top: 0; left: 0; width: 2.25rem; height: 2.25rem; place-items: center; border: 1px solid var(--forest); border-radius: 50%; background: var(--forest-soft); color: var(--forest); font-weight: 800; line-height: 1; }
.private-recruiter-triage-document .triage-handoff-step-label { display: block; margin-bottom: 0.45rem; color: var(--forest); font-size: 0.8125rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; }
.private-recruiter-triage-document .triage-handoff-readiness { margin-top: 1rem; padding: 0.85rem 1rem; background: var(--paper); border: 1px solid var(--line); }
.private-recruiter-triage-document .triage-handoff-readiness h3 { margin: 0; color: var(--forest); font-family: var(--serif); font-size: 1.1rem; line-height: 1.2; }
.private-recruiter-triage-document .triage-handoff-readiness dl { display: grid; gap: 0.55rem; margin: 0.75rem 0 0; max-width: var(--measure); }
.private-recruiter-triage-document .triage-handoff-readiness-row { display: grid; grid-template-columns: minmax(14rem, 1fr) auto; gap: 0.75rem 1rem; align-items: baseline; }
.private-recruiter-triage-document .triage-handoff-readiness dt { color: var(--forest); font-weight: 700; }
.private-recruiter-triage-document .triage-handoff-readiness dd { margin: 0; font-weight: 700; }
.private-recruiter-triage-document .triage-handoff-focus { margin-top: 1rem; padding: 0.85rem 1rem; background: var(--forest-soft); border-left: 4px solid var(--forest); }
.private-recruiter-triage-document .triage-handoff-focus h3 { margin: 0; color: var(--forest); font-family: var(--serif); font-size: 1.1rem; line-height: 1.2; }
.private-recruiter-triage-document .triage-handoff-focus p { margin: 0.55rem 0 0; max-width: var(--measure); }
.private-recruiter-triage-document .triage-handoff-next-step { margin-top: 1rem; padding: 0.85rem 1rem; background: var(--paper); border-left: 4px solid var(--coral); }
.private-recruiter-triage-document .triage-handoff-next-step h3 { margin: 0; color: var(--forest); font-family: var(--serif); font-size: 1.1rem; line-height: 1.2; }
.private-recruiter-triage-document .triage-handoff-next-step p { margin: 0.55rem 0 0; max-width: var(--measure); }
.private-recruiter-triage-document .triage-handoff-reentry-cue { padding-top: 0.55rem; border-top: 1px solid var(--line); color: var(--forest); }
.private-recruiter-triage-document .triage-handoff-receipt { margin-top: 1rem; padding: 0.85rem 1rem; background: var(--paper); border: 1px solid var(--line); }
.private-recruiter-triage-document .triage-handoff-receipt h3 { margin: 0; color: var(--forest); font-family: var(--serif); font-size: 1.1rem; line-height: 1.2; }
.private-recruiter-triage-document .triage-handoff-receipt h4 { margin: 0.75rem 0 0; color: var(--forest); font-size: 0.8125rem; letter-spacing: 0.08em; text-transform: uppercase; }
.private-recruiter-triage-document .triage-handoff-receipt-group + .triage-handoff-receipt-group { margin-top: 0.8rem; padding-top: 0.8rem; border-top: 1px solid var(--line); }
.private-recruiter-triage-document .triage-handoff-receipt-list { display: grid; gap: 0.45rem; margin: 0.45rem 0 0; max-width: var(--measure); padding: 0; list-style: none; }
.private-recruiter-triage-document .triage-handoff-receipt-list li { padding-left: 1rem; border-left: 2px solid var(--line); }
.private-recruiter-triage-document .triage-handoff-receipt p { margin: 0.75rem 0 0; max-width: var(--measure); }
.private-recruiter-triage-document .triage-handoff-preview { margin-top: 1rem; padding: 1rem; background: var(--forest-soft); border-top: 1px solid var(--line); }
.private-recruiter-triage-document .triage-handoff-preview h3 { margin: 0; color: var(--forest); font-family: var(--serif); font-size: 1.2rem; line-height: 1.2; }
.private-recruiter-triage-document .triage-handoff-preview dl { display: grid; grid-template-columns: minmax(9rem, 0.35fr) minmax(0, 1fr); gap: 0.6rem 1rem; margin: 0.75rem 0 0; max-width: var(--measure); }
.private-recruiter-triage-document .triage-handoff-preview dt { color: var(--forest); font-weight: 700; }
.private-recruiter-triage-document .triage-handoff-preview dd { margin: 0; }
.private-recruiter-triage-document .triage-footer { padding-block: 1rem 2rem; border-top: 1px solid var(--forest); color: var(--forest); }

@media screen and (prefers-color-scheme: dark) {
  :root {
    color-scheme: dark;
    --paper: #101521;
    --surface: #182235;
    --ink: #f3f6ff;
    --muted: #b8c4d8;
    --line: #5f718e;
    --forest: #8fc9b0;
    --forest-soft: #223b35;
    --coral: #ff9f8d;
    --coral-soft: #3f282d;
    --decision-term: #f5d68a;
  }
  html,
  .private-recruiter-triage-document { background: var(--paper); color: var(--ink); }
  .private-recruiter-triage-document .triage-state--stop { color: var(--decision-term); background: var(--forest-soft); }
  .private-recruiter-triage-document .triage-next-safe-action { background: var(--surface); }
  .private-recruiter-triage-document .triage-blocked { background: var(--coral-soft); }
  .private-recruiter-triage-document .triage-handoff-readiness,
  .private-recruiter-triage-document .triage-handoff-next-step,
  .private-recruiter-triage-document .triage-handoff-receipt { background: var(--surface); }
  .private-recruiter-triage-document .triage-footer { color: var(--muted); border-color: var(--forest); }
}

@keyframes triage-enter { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }

@media (max-width: 640px) {
  .private-recruiter-triage-document .triage-shell { width: min(100% - 1rem, 920px); }
  .private-recruiter-triage-document .triage-state { align-items: flex-start; }
}

@media (prefers-reduced-motion: reduce) {
  .private-recruiter-triage-document *, .private-recruiter-triage-document *::before, .private-recruiter-triage-document *::after { animation: none !important; transition: none !important; scroll-behavior: auto !important; }
}

@page { size: auto; margin: 14mm; }

@media print {
  .private-recruiter-triage-document { background: #fff; font-size: 12pt; }
  .private-recruiter-triage-document .skip-link { display: none !important; }
  .private-recruiter-triage-document .triage-shell { width: auto; }
  .private-recruiter-triage-document .triage-card, .private-recruiter-triage-document .triage-section { break-inside: avoid; page-break-inside: avoid; }
  .private-recruiter-triage-document .triage-handoff-preview { break-inside: avoid; page-break-inside: avoid; }
  .private-recruiter-triage-document .triage-next-safe-action { break-inside: avoid; page-break-inside: avoid; }
  .private-recruiter-triage-document .triage-handoff-focus { break-inside: avoid; page-break-inside: avoid; }
  .private-recruiter-triage-document .triage-handoff-next-step { break-inside: avoid; page-break-inside: avoid; }
  .private-recruiter-triage-document .triage-handoff-reentry-cue { break-inside: avoid; page-break-inside: avoid; }
  .private-recruiter-triage-document .triage-handoff-receipt { break-inside: avoid; page-break-inside: avoid; }
  .private-recruiter-triage-document .triage-handoff-sequence > li { break-inside: avoid; page-break-inside: avoid; }
  .private-recruiter-triage-document .triage-card {
    box-shadow: none;
    animation: none !important;
    transition: none !important;
    transform: none !important;
  }
  .private-recruiter-triage-document .triage-footer {
    break-inside: avoid;
    page-break-inside: avoid;
  }
}

@media (forced-colors: active) {
  .private-recruiter-triage-document .skip-link { background: Canvas; border-color: CanvasText; color: CanvasText; }
  .private-recruiter-triage-document main:focus-visible { outline-color: Highlight; }
  .private-recruiter-triage-document .triage-section,
  .private-recruiter-triage-document .triage-decision,
  .private-recruiter-triage-document .triage-next-safe-action,
  .private-recruiter-triage-document .triage-blocked,
  .private-recruiter-triage-document .triage-missing { background: Canvas; color: CanvasText; border-color: CanvasText; }
  .private-recruiter-triage-document .triage-decision,
  .private-recruiter-triage-document .triage-next-safe-action,
  .private-recruiter-triage-document .triage-blocked,
  .private-recruiter-triage-document .triage-missing { border-left-color: CanvasText; }
  .private-recruiter-triage-document .triage-section h2,
  .private-recruiter-triage-document .triage-section h3,
  .private-recruiter-triage-document .triage-section dt,
  .private-recruiter-triage-document .triage-section dd { color: CanvasText; }
  .private-recruiter-triage-document .triage-handoff-sequence > li,
  .private-recruiter-triage-document .triage-handoff-step-label,
  .private-recruiter-triage-document .triage-handoff-readiness,
  .private-recruiter-triage-document .triage-handoff-focus,
  .private-recruiter-triage-document .triage-handoff-next-step,
  .private-recruiter-triage-document .triage-handoff-reentry-cue,
  .private-recruiter-triage-document .triage-next-safe-action,
  .private-recruiter-triage-document .triage-handoff-preview { border-color: CanvasText; }
  .private-recruiter-triage-document .triage-handoff-receipt { border-color: CanvasText; }
  .private-recruiter-triage-document .triage-handoff-step-label { color: CanvasText; }
  .private-recruiter-triage-document .triage-handoff-sequence > li::before { border-color: CanvasText; background: Canvas; color: CanvasText; }
  .private-recruiter-triage-document .triage-footer { color: CanvasText; border-color: CanvasText; }
}

@media (prefers-contrast: more) {
  .private-recruiter-triage-document .triage-state {
    border: 2px solid currentColor;
    text-decoration: underline;
    text-decoration-thickness: 0.12em;
    text-underline-offset: 0.15em;
  }
  .private-recruiter-triage-document .triage-next-safe-action,
  .private-recruiter-triage-document .triage-blocked {
    border: 2px solid currentColor;
    border-left-width: 5px;
  }
  .private-recruiter-triage-document .triage-next-safe-action h2,
  .private-recruiter-triage-document .triage-blocked h2 {
    text-decoration: underline;
    text-decoration-thickness: 0.12em;
    text-underline-offset: 0.15em;
  }
}

@media (max-width: 640px) {
  .private-recruiter-triage-document .triage-handoff-preview dl { grid-template-columns: 1fr; gap: 0.25rem; }
  .private-recruiter-triage-document .triage-handoff-preview dd + dt { margin-top: 0.75rem; }
  .private-recruiter-triage-document .triage-handoff-readiness-row { grid-template-columns: 1fr; gap: 0.1rem; }
  .private-recruiter-triage-document .triage-handoff-readiness-row + .triage-handoff-readiness-row { margin-top: 0.55rem; }
}
```

### `plugins/professional-growth-coach/assets/recruiter-practice-session-v1.css`

```css
:root {
  --paper: #f6f4ee;
  --surface: #ffffff;
  --ink: #1b1c1a;
  --forest: #173e30;
  --forest-soft: #dce5e0;
  --coral: #b9513a;
  --coral-soft: #f6e0da;
  --decision-term: #dfbf70;
  --line: #6f8175;
  --measure: 72ch;
  --serif: Georgia, "Times New Roman", Times, serif;
  --sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
}

* { box-sizing: border-box; }

html { color-scheme: light; background: var(--paper); }

.recruiter-practice-document {
  margin: 0;
  background: var(--paper);
  color: var(--ink);
  font-family: var(--sans);
  font-size: 16px;
  line-height: 1.55;
  overflow-wrap: anywhere;
}

.recruiter-practice-document :focus-visible {
  outline: 3px solid var(--coral);
  outline-offset: 3px;
}

.recruiter-practice-document .skip-link {
  position: fixed;
  z-index: 10;
  top: 0.5rem;
  left: 0.5rem;
  transform: translateY(-200%);
  padding: 0.75rem 1rem;
  background: var(--surface);
  border: 1px solid var(--forest);
  color: var(--forest);
  font-weight: 700;
}

.recruiter-practice-document .skip-link:focus { transform: none; }

.recruiter-practice-document .practice-shell {
  width: min(920px, calc(100% - 2rem));
  margin-inline: auto;
}

.recruiter-practice-document .practice-header {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 1rem;
  padding-block: 2rem 1rem;
  border-bottom: 1px solid var(--forest);
}

.recruiter-practice-document .practice-kicker,
.recruiter-practice-document .practice-label {
  margin: 0;
  color: var(--forest);
  font-size: 0.8125rem;
  font-weight: 700;
  letter-spacing: 0.09em;
  text-transform: uppercase;
}

.recruiter-practice-document h1,
.recruiter-practice-document h2 {
  font-family: var(--serif);
}

.recruiter-practice-document h1 {
  margin: 0.2rem 0 0;
  font-size: clamp(2rem, 6vw, 3.25rem);
  font-style: italic;
  line-height: 1.04;
}

.recruiter-practice-document h2 {
  margin: 0;
  color: var(--forest);
  font-size: clamp(1.35rem, 3vw, 1.85rem);
  line-height: 1.16;
}

.recruiter-practice-document .state-chip {
  display: inline-flex;
  align-items: center;
  min-height: 2.25rem;
  padding: 0.4rem 0.75rem;
  border: 1px solid currentColor;
  color: var(--forest);
  font-size: 0.875rem;
  font-weight: 700;
  line-height: 1.2;
  text-align: center;
}

.recruiter-practice-document .state-chip--feedback_available { color: #854117; background: #f7ecd5; }
.recruiter-practice-document .state-chip--ready_to_practice { color: var(--forest); background: var(--forest-soft); }
.recruiter-practice-document .state-chip--awaiting_answer { color: #5c4a12; background: #f5ecd8; }
.recruiter-practice-document main { padding-block: 1.5rem 3rem; }

.recruiter-practice-document .practice-session {
  min-width: 0;
  padding: clamp(1.15rem, 3vw, 2rem);
  background: var(--surface);
  border-top: 4px solid var(--forest);
  box-shadow: 0 1px 0 rgb(23 62 48 / 10%);
  animation: practice-enter 0.35s ease both;
}

.recruiter-practice-document .practice-session > * + * { margin-top: 1.5rem; }
.recruiter-practice-document .practice-summary { max-width: var(--measure); margin: 0.5rem 0 0; }

.recruiter-practice-document .practice-context,
.recruiter-practice-document .practice-prompt,
.recruiter-practice-document .practice-rehearsal,
.recruiter-practice-document .practice-evidence,
.recruiter-practice-document .practice-boundary,
.recruiter-practice-document .practice-feedback,
.recruiter-practice-document .practice-decision {
  padding: 1rem;
  border: 1px solid var(--line);
}

.recruiter-practice-document .practice-prompt { background: var(--forest-soft); border-left: 4px solid var(--forest); }
.recruiter-practice-document .practice-prompt p { margin: 0.55rem 0 0; max-width: var(--measure); font-family: var(--serif); font-size: clamp(1.2rem, 2.5vw, 1.55rem); line-height: 1.25; }
.recruiter-practice-document .practice-rehearsal { background: #f8f7f2; }
.recruiter-practice-document .practice-next-action { background: var(--forest); color: #fff; border: 1px solid var(--forest); padding: 1rem; }
.recruiter-practice-document .practice-next-action h2 { color: #fff; }
.recruiter-practice-document .practice-next-action p { max-width: var(--measure); margin: 0.45rem 0 0; }
.recruiter-practice-document .practice-next-action--ready_to_practice { border-left: 4px solid #9fc4b4; }
.recruiter-practice-document .practice-next-action--awaiting_answer { border-left: 4px solid #dfbf70; }
.recruiter-practice-document .practice-handoff { padding: 1rem; border: 1px dashed var(--forest); background: #f8f7f2; }
.recruiter-practice-document .practice-handoff h2 { font-size: 1.25rem; }
.recruiter-practice-document .practice-handoff p { max-width: var(--measure); margin: 0.45rem 0 0; }
.recruiter-practice-document .practice-handoff--dossier { border-left: 4px solid var(--forest); }
.recruiter-practice-document .practice-handoff--reply { border-left: 4px solid var(--coral); }
.recruiter-practice-document .practice-rehearsal-hint { max-width: var(--measure); margin: 0.45rem 0 0; color: #46534d; }
.recruiter-practice-document .practice-rehearsal ol { display: grid; gap: 0.5rem; margin: 0.65rem 0 0; padding-left: 1.5rem; }
.recruiter-practice-document .practice-rehearsal li::marker { color: var(--forest); font-weight: 700; }
.recruiter-practice-document .practice-evidence ul { margin: 0.65rem 0 0; padding-left: 1.25rem; }
.recruiter-practice-document .practice-evidence li + li { margin-top: 0.5rem; }
.recruiter-practice-document .practice-boundary { background: var(--coral-soft); border-color: var(--coral); }
.recruiter-practice-document .practice-boundary p { margin: 0.45rem 0 0; }
.recruiter-practice-document .practice-feedback { border-left: 4px solid var(--coral); }
.recruiter-practice-document .practice-decision {
  padding: 1rem;
  border: 1px solid var(--forest);
  border-left: 4px solid var(--decision-term);
  background: var(--forest);
  color: #fff;
}
.recruiter-practice-document .practice-decision h2 { color: #fff; }
.recruiter-practice-document .practice-decision-explanation {
  max-width: var(--measure);
  margin: 0.45rem 0 0;
}
.recruiter-practice-document .practice-decision dl {
  display: grid;
  grid-template-columns: minmax(9rem, 0.35fr) minmax(0, 1fr);
  gap: 0.5rem 1rem;
  min-width: 0;
  margin: 1rem 0 0;
}
.recruiter-practice-document .practice-decision dt {
  min-width: 0;
  color: var(--decision-term);
  font-weight: 700;
}
.recruiter-practice-document .practice-decision dd {
  min-width: 0;
  margin: 0;
  color: #fff;
}
.recruiter-practice-document .visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
.recruiter-practice-document .practice-feedback ul { margin: 0.65rem 0 0; padding-left: 1.25rem; }
.recruiter-practice-document .practice-feedback li + li { margin-top: 0.5rem; }
.recruiter-practice-document .feedback-label { font-weight: 700; color: var(--ink); }
.recruiter-practice-document .feedback-label--solid { color: var(--ink); }
.recruiter-practice-document .feedback-label--confirm { color: var(--ink); }
.recruiter-practice-document .feedback-label--do_not_assert { color: var(--ink); }
.recruiter-practice-document .feedback-item { padding: 0.55rem 0.65rem; border-left: 3px solid var(--line); }
.recruiter-practice-document .feedback-item--solid { border-left-color: var(--forest); background: var(--forest-soft); }
.recruiter-practice-document .feedback-item--confirm { border-left-color: #854117; background: #f7ecd5; }
.recruiter-practice-document .feedback-item--do_not_assert { border-left-color: var(--coral); background: var(--coral-soft); }

.recruiter-practice-document .practice-footer {
  padding-block: 1rem 2rem;
  border-top: 1px solid var(--forest);
  color: var(--forest);
}

@media screen and (prefers-color-scheme: dark) {
  :root {
    color-scheme: dark;
    --paper: #101521;
    --surface: #182235;
    --ink: #f3f6ff;
    --muted: #b8c4d8;
    --line: #5f718e;
    --forest: #8fc9b0;
    --forest-soft: #223b35;
    --coral: #ff9f8d;
    --coral-soft: #3f282d;
    --gold-soft: #3b301f;
    --decision-term: #f5d68a;
  }
  html,
  .recruiter-practice-document { background: var(--paper); color: var(--ink); }
  .recruiter-practice-document .state-chip--feedback_available { color: var(--coral); background: var(--coral-soft); }
  .recruiter-practice-document .state-chip--awaiting_answer { color: var(--decision-term); background: var(--forest-soft); }
  .recruiter-practice-document .practice-rehearsal,
  .recruiter-practice-document .practice-handoff { background: var(--surface); }
  .recruiter-practice-document .practice-rehearsal-hint { color: var(--muted); }
  .recruiter-practice-document .practice-next-action,
  .recruiter-practice-document .practice-decision { background: var(--forest-soft); color: var(--ink); }
  .recruiter-practice-document .practice-next-action h2,
  .recruiter-practice-document .practice-decision h2,
  .recruiter-practice-document .practice-decision dd { color: var(--ink); }
  .recruiter-practice-document .feedback-item--confirm {
    background: var(--gold-soft);
    border-left-color: var(--decision-term);
    color: var(--ink);
  }
  .recruiter-practice-document .feedback-label--confirm { color: var(--ink); }
  .recruiter-practice-document .practice-boundary { background: var(--coral-soft); }
  .recruiter-practice-document .practice-footer { color: var(--muted); border-color: var(--forest); }
}

@keyframes practice-enter {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 640px) {
  .recruiter-practice-document .practice-shell { width: min(100% - 1rem, 920px); }
  .recruiter-practice-document .practice-header { align-items: start; flex-direction: column; }
  .recruiter-practice-document .state-chip { text-align: left; }
  .recruiter-practice-document .practice-decision dl { grid-template-columns: 1fr; }
}

@media (prefers-reduced-motion: reduce) {
  .recruiter-practice-document *,
  .recruiter-practice-document *::before,
  .recruiter-practice-document *::after {
    animation: none !important;
    transition: none !important;
    scroll-behavior: auto !important;
  }
}

@media (forced-colors: active) {
  .recruiter-practice-document .skip-link { background: Canvas; border-color: CanvasText; color: CanvasText; }
  .recruiter-practice-document main:focus-visible { outline-color: Highlight; }
  .recruiter-practice-document .practice-context,
  .recruiter-practice-document .practice-prompt,
  .recruiter-practice-document .practice-rehearsal,
  .recruiter-practice-document .practice-evidence,
  .recruiter-practice-document .practice-boundary { background: Canvas; color: CanvasText; border-color: CanvasText; }
  .recruiter-practice-document .practice-prompt,
  .recruiter-practice-document .practice-boundary { border-left-color: CanvasText; }
  .recruiter-practice-document .practice-context h2,
  .recruiter-practice-document .practice-prompt h2,
  .recruiter-practice-document .practice-rehearsal h2,
  .recruiter-practice-document .practice-evidence h2,
  .recruiter-practice-document .practice-boundary h2,
  .recruiter-practice-document .practice-label,
  .recruiter-practice-document .practice-rehearsal-hint,
  .recruiter-practice-document .practice-rehearsal li::marker { color: CanvasText; }
  .recruiter-practice-document .practice-handoff { border: 1px dashed CanvasText; background: Canvas; color: CanvasText; }
  .recruiter-practice-document .practice-handoff h2 { color: CanvasText; }
  .recruiter-practice-document .practice-next-action { background: Canvas; color: CanvasText; border-color: CanvasText; }
  .recruiter-practice-document .practice-next-action h2 { color: CanvasText; }
  .recruiter-practice-document .practice-next-action--ready_to_practice,
  .recruiter-practice-document .practice-next-action--awaiting_answer { border-left-color: CanvasText; }
  .recruiter-practice-document .practice-feedback { border: 1px solid CanvasText; background: Canvas; color: CanvasText; }
  .recruiter-practice-document .feedback-item { border: 1px solid CanvasText; background: Canvas; color: CanvasText; }
  .recruiter-practice-document .practice-decision { border: 1px solid CanvasText; background: Canvas; color: CanvasText; }
  .recruiter-practice-document .practice-decision h2,
  .recruiter-practice-document .practice-decision dt,
  .recruiter-practice-document .practice-decision dd { color: CanvasText; }
  .recruiter-practice-document .feedback-label--solid,
  .recruiter-practice-document .feedback-label--confirm,
  .recruiter-practice-document .feedback-label--do_not_assert { color: CanvasText; }
  .recruiter-practice-document .practice-footer { color: CanvasText; border-color: CanvasText; }
}

@media (prefers-contrast: more) {
  .recruiter-practice-document .state-chip,
  .recruiter-practice-document .practice-next-action,
  .recruiter-practice-document .practice-handoff,
  .recruiter-practice-document .practice-feedback,
  .recruiter-practice-document .feedback-item,
  .recruiter-practice-document .practice-decision { border-width: 2px; }
  .recruiter-practice-document .feedback-label { text-decoration: underline; text-decoration-thickness: 0.12em; }
}

@page { size: auto; margin: 14mm; }

@media print {
  .recruiter-practice-document { background: #fff; font-size: 12pt; }
  .recruiter-practice-document .skip-link { display: none !important; }
  .recruiter-practice-document .practice-shell { width: auto; }
  .recruiter-practice-document .practice-session,
  .recruiter-practice-document .practice-context,
  .recruiter-practice-document .practice-prompt,
  .recruiter-practice-document .practice-rehearsal,
  .recruiter-practice-document .practice-next-action,
  .recruiter-practice-document .practice-evidence,
  .recruiter-practice-document .practice-boundary,
  .recruiter-practice-document .practice-feedback {
    break-inside: avoid;
    page-break-inside: avoid;
  }
  .recruiter-practice-document .practice-handoff {
    break-inside: avoid;
    page-break-inside: avoid;
  }
  .recruiter-practice-document .practice-feedback {
    break-after: avoid-page;
  }
  .recruiter-practice-document .practice-decision {
    break-inside: avoid;
    page-break-inside: avoid;
    break-before: avoid-page;
    background: transparent;
    color: var(--ink);
    border: 1px solid var(--ink);
  }
  .recruiter-practice-document .practice-decision h2,
  .recruiter-practice-document .practice-decision dt,
  .recruiter-practice-document .practice-decision dd {
    color: var(--ink);
  }
  .recruiter-practice-document .practice-next-action {
    background: transparent;
    color: var(--ink);
    border: 1px solid var(--ink);
    border-left-width: 4px;
  }
  .recruiter-practice-document .practice-next-action h2 { color: var(--ink); }
  .recruiter-practice-document .practice-session {
    animation: none !important;
    transition: none !important;
    transform: none !important;
  }
  .recruiter-practice-document .practice-session { box-shadow: none; }
  .recruiter-practice-document .practice-footer {
    break-inside: avoid;
    page-break-inside: avoid;
  }
}
```

### `plugins/professional-growth-coach/assets/private-recruiter-followthrough-checkpoint-v1.css`

```css
:root { color-scheme: light dark; --ink: #172033; --muted: #536174; --surface: #fff; --accent: #315bd6; --line: #d9dfeb; }
* { box-sizing: border-box; }
html { font: 100%/1.5 system-ui, sans-serif; background: #f4f6fa; color: var(--ink); }
body { margin: 0; }
.skip-link { position: absolute; left: -10000px; top: auto; }
.skip-link:focus { left: 1rem; top: 1rem; padding: .5rem; background: var(--surface); color: var(--ink); }
main:focus-visible { outline: 3px solid var(--accent); outline-offset: 4px; }
.checkpoint-shell { max-width: 48rem; margin: 0 auto; padding: clamp(1rem, 4vw, 3rem); }
.checkpoint-card { background: var(--surface); border: 1px solid var(--line); border-radius: 1rem; padding: clamp(1.25rem, 4vw, 2.5rem); box-shadow: 0 .5rem 2rem rgb(23 32 51 / .08); }
.checkpoint-kicker { color: var(--accent); font-size: .8rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }
h1 { margin-top: .25rem; font-size: clamp(1.6rem, 4vw, 2.35rem); }
.checkpoint-facts { display: grid; gap: 1rem; margin: 2rem 0; }
.checkpoint-facts div { border-top: 1px solid var(--line); padding-top: .75rem; }
dt { color: var(--muted); font-size: .85rem; font-weight: 700; }
dd { margin: .15rem 0 0; font-weight: 600; }
.checkpoint-boundary { border-left: .25rem solid var(--accent); margin: 0; padding: .75rem 1rem; color: var(--muted); }
.checkpoint-footer { max-width: 48rem; margin: 0 auto; padding: 0 clamp(1rem, 4vw, 3rem) 2rem; border-top: 1px solid var(--accent); color: var(--muted); font-size: .85rem; }
.checkpoint-employment-boundary { margin: .5rem 0 0; color: var(--ink); font-weight: 600; }
@media (min-width: 641px) { .checkpoint-facts { grid-template-columns: 1fr 1fr; } }
@media screen and (prefers-color-scheme: dark) {
  :root { color-scheme: dark; --ink: #f3f6ff; --muted: #b8c4d8; --surface: #182235; --accent: #8eb2ff; --line: #5f718e; }
  html { background: #101521; }
  .checkpoint-card { box-shadow: 0 .5rem 2rem rgb(0 0 0 / .35); }
}
@page { size: auto; margin: 14mm; }
@media print { html { background: #fff; } .checkpoint-card { box-shadow: none; break-inside: avoid; page-break-inside: avoid; } .checkpoint-footer { break-inside: avoid; page-break-inside: avoid; } .skip-link { display: none; } }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation-duration: .01ms !important; transition-duration: .01ms !important; scroll-behavior: auto !important; } }
@media (prefers-contrast: more) { .checkpoint-card { border: 2px solid var(--ink); box-shadow: none; } .checkpoint-facts div { border-top: 2px solid var(--ink); } .checkpoint-boundary { border-left-width: .5rem; color: var(--ink); } .checkpoint-footer { border-top: 2px solid var(--ink); } }
@media (forced-colors: active) { .skip-link { background: Canvas; border-color: CanvasText; color: CanvasText; } .skip-link:focus-visible { outline: 2px solid Highlight; outline-offset: 2px; } .checkpoint-card { background: Canvas; color: CanvasText; border: 1px solid CanvasText; } .checkpoint-boundary { color: CanvasText; border: 1px solid CanvasText; border-left-width: .25rem; } .checkpoint-kicker { color: LinkText; } .checkpoint-footer { color: CanvasText; border-color: CanvasText; } }
```

### `plugins/professional-growth-coach/assets/private-recruiter-conversion-outcome-v1.css`

```css
:root { color-scheme: light dark; --ink: #172033; --muted: #536174; --surface: #fff; --accent: #315bd6; --line: #d9dfeb; }
* { box-sizing: border-box; }
html { font: 100%/1.5 system-ui, sans-serif; background: #f4f6fa; color: var(--ink); }
body { margin: 0; }
.skip-link { position: absolute; left: -10000px; top: auto; }
.skip-link:focus { left: 1rem; top: 1rem; padding: .5rem; background: var(--surface); color: var(--ink); }
main:focus-visible { outline: 3px solid var(--accent); outline-offset: 4px; }
.outcome-shell { max-width: 48rem; margin: 0 auto; padding: clamp(1rem, 4vw, 3rem); }
.outcome-card { background: var(--surface); border: 1px solid var(--line); border-radius: 1rem; padding: clamp(1.25rem, 4vw, 2.5rem); box-shadow: 0 .5rem 2rem rgb(23 32 51 / .08); }
.outcome-kicker { color: var(--accent); font-size: .8rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }
h1 { margin-top: .25rem; font-size: clamp(1.6rem, 4vw, 2.35rem); }
.outcome-facts { display: grid; gap: 1rem; margin: 2rem 0; }
.outcome-facts div { border-top: 1px solid var(--line); padding-top: .75rem; }
dt { color: var(--muted); font-size: .85rem; font-weight: 700; }
dd { margin: .15rem 0 0; font-weight: 600; }
.outcome-boundary { border-left: .25rem solid var(--accent); margin: 0; padding: .75rem 1rem; color: var(--muted); }
.outcome-footer { max-width: 48rem; margin: 0 auto; padding: 0 clamp(1rem, 4vw, 3rem) 2rem; border-top: 1px solid var(--accent); color: var(--muted); font-size: .85rem; }
.outcome-employment-boundary { margin: .5rem 0 0; color: var(--ink); font-weight: 600; }
@media (min-width: 641px) { .outcome-facts { grid-template-columns: 1fr 1fr; } }
@media screen and (prefers-color-scheme: dark) {
  :root { color-scheme: dark; --ink: #f3f6ff; --muted: #b8c4d8; --surface: #182235; --accent: #8eb2ff; --line: #5f718e; }
  html { background: #101521; }
  .outcome-card { box-shadow: 0 .5rem 2rem rgb(0 0 0 / .35); }
}
@page { size: auto; margin: 14mm; }
@media print { html { background: #fff; } .outcome-card { box-shadow: none; break-inside: avoid; page-break-inside: avoid; } .outcome-footer { break-inside: avoid; page-break-inside: avoid; } .skip-link { display: none; } }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation-duration: .01ms !important; transition-duration: .01ms !important; scroll-behavior: auto !important; } }
@media (prefers-contrast: more) { .outcome-card { border: 2px solid var(--ink); box-shadow: none; } .outcome-facts div { border-top: 2px solid var(--ink); } .outcome-boundary { border-left-width: .5rem; color: var(--ink); } .outcome-footer { border-top: 2px solid var(--ink); } }
@media (forced-colors: active) { .skip-link { background: Canvas; border-color: CanvasText; color: CanvasText; } .skip-link:focus-visible { outline: 2px solid Highlight; outline-offset: 2px; } .outcome-card { background: Canvas; color: CanvasText; border: 1px solid CanvasText; } .outcome-boundary { color: CanvasText; border: 1px solid CanvasText; border-left-width: .25rem; } .outcome-kicker { color: LinkText; } .outcome-footer { color: CanvasText; border-color: CanvasText; } }
```

### `plugins/professional-growth-coach/assets/executive-career-dossier-v2.css`

```css
.section-coverage-list { display: grid; gap: .75rem; margin: 0; padding: 0; list-style: none; }
.section-coverage-ledger, .coach-priorities { min-width: 0; }
.section-coverage-row { min-width: 0; overflow-wrap: anywhere; }
.section-coverage-row article { padding: 1rem; border: 1px solid var(--forest-soft); background: var(--surface); }
.section-coverage-facts { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .75rem 1rem; }
.section-coverage-facts dt, .section-coverage-facts dd { min-width: 0; }
.section-coverage-facts dd { margin: 0; }
.section-coverage-row h3 { margin: 0; }
.section-coverage-request { margin: 0; padding-left: .75rem; border-left: 4px solid var(--gold); }
.coach-priority-card { border-top: 4px solid var(--coral); }
.coach-template { margin: 1rem 0 0; padding: 1rem; border-left: 4px solid var(--forest); background: var(--paper); }
.coach-template h4 { margin: 0; }
.coach-template-list { margin: .5rem 0 0; padding-left: 1.25rem; }
.coach-template-field { display: block; font-weight: 700; }
.coach-template-blank { display: block; min-height: 1.5rem; border-bottom: 1px solid var(--line); }
.coach-template-boundary { margin: .75rem 0 0; color: var(--muted-text); font-size: .875rem; }
.market-evidence-available-card { border-top: 4px solid var(--forest); }

@media screen and (prefers-color-scheme: dark) {
  .section-coverage-row article { border-color: var(--forest); background: var(--surface); color: var(--ink); }
  .coach-template { background: var(--paper); color: var(--ink); }
}

@media (max-width: 640px) {
  .section-coverage-facts { grid-template-columns: 1fr; }
  .section-coverage-ledger, .section-coverage-list, .section-coverage-row, .section-coverage-row article, .coach-priorities, .coach-priority-card, .coach-template { min-width: 0; }
}

@media (prefers-reduced-motion: reduce) {
  .section-coverage-row article, .coach-priority-card, .coach-template { animation: none !important; transition: none !important; transform: none !important; }
}

@media print {
  .section-coverage-row, .section-coverage-row article, .coach-priority-card, .coach-template, .market-unavailable-card, .market-evidence-available-card { break-inside: avoid; page-break-inside: avoid; }
}

@media (forced-colors: active) {
  .section-coverage-row article, .coach-priority-card, .coach-template, .market-unavailable-card, .market-evidence-available-card { background: Canvas; color: CanvasText; border-color: CanvasText; }
  .coach-template-boundary { color: CanvasText; }
  .section-coverage-request, .coach-template { border-left-color: Highlight; }
  .coach-priority-card { border-top-color: Highlight; }
  main:focus-visible { outline-color: Highlight; }
}

@media (prefers-contrast: more) {
  .section-coverage-row article, .coach-priority-card, .coach-template, .market-unavailable-card, .market-evidence-available-card { border-width: 2px; }
  .section-coverage-request, .coach-template { border-left-width: 5px; }
  .coach-priority-card { border-top-width: 5px; }
}
```

### `plugins/professional-growth-coach/assets/career-market-learning-dossier-v1.css`

```css
.market-summary,
.market-summary-card,
.market-vacancy-section,
.market-matrix-section,
.market-matrix-group,
.market-recurrence,
.gap-closure-route { min-width: 0; }

.market-summary-card,
.market-matrix-group,
.market-recurrence,
.gap-closure-route {
  padding: clamp(1rem, 2.5vw, 1.5rem);
  border: 1px solid var(--forest-soft);
  background: var(--surface);
}

.market-summary-card { border-top: 4px solid var(--gold); }
.market-summary-heading { font-family: var(--serif); font-size: 1.35rem; font-weight: 700; }
.market-limitation { padding-left: 1rem; border-left: 4px solid var(--gold); }
.market-learning-state { margin: .75rem 0 0; padding: .65rem .85rem; border-left: 4px solid var(--gold); color: var(--muted-text); }
.market-next-safe-action { margin: .75rem 0 0; padding: .65rem .85rem; border-left: 4px solid var(--forest); color: var(--muted-text); overflow-wrap: anywhere; }
.market-vacancy-section,
.market-matrix-section,
.market-recurrence,
.gap-closure-route { margin-top: 1rem; }

.vacancy-alignment-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 12rem), 1fr));
  gap: .75rem;
}

.vacancy-alignment-card {
  min-width: 0;
  padding: 1rem;
  border: 1px solid var(--forest-soft);
  border-top: 4px solid var(--forest);
  background: var(--surface);
}

.vacancy-alignment-card h3 { margin: .2rem 0 0; font-size: 1.1rem; }
.vacancy-key-label,
.vacancy-employer { margin: 0; }
.vacancy-key-label { color: var(--forest); font-weight: 800; }
.vacancy-employer { font-size: .875rem; }
.vacancy-alignment-score { margin: .8rem 0 0; color: var(--forest); font-family: var(--serif); font-size: 1.5rem; font-weight: 700; }
.vacancy-score-boundary { margin: .65rem 0 0; font-size: .875rem; }
.vacancy-evidence-coverage { margin: .75rem 0 0; font-size: .9rem; }
.vacancy-qualitative-band { margin: .35rem 0 0; color: var(--forest); font-weight: 700; }

.market-vacancy-key { margin: .5rem 0 1rem; padding-left: 1.5rem; }
.market-vacancy-key-item + .market-vacancy-key-item { margin-top: .35rem; }
.market-matrix {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
  font-size: .925rem;
}

.market-matrix caption { padding-bottom: .75rem; text-align: left; font-weight: 700; }
.market-matrix th,
.market-matrix td {
  min-width: 0;
  padding: .65rem;
  border-bottom: 1px solid var(--muted);
  hyphens: auto;
  overflow-wrap: anywhere;
  text-align: left;
  vertical-align: top;
}

.market-matrix th { color: var(--forest); }
.market-matrix .visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  margin: -1px;
  padding: 0;
  overflow: hidden;
  clip: rect(0 0 0 0);
  clip-path: inset(50%);
  border: 0;
}

.market-matrix-state-cell { border-left: 2px solid var(--muted); }
.matrix-state-symbol { display: inline-block; width: 1.35em; font-weight: 800; }
.matrix-state-text { font-weight: 600; }

.recurrence-list { margin-top: .75rem; }
.recurrence-row {
  display: grid;
  grid-template-columns: minmax(10rem, 1fr) minmax(8rem, .65fr) auto;
  gap: 1rem;
  align-items: center;
  padding: .75rem 0;
  border-bottom: 1px solid var(--muted);
}

.recurrence-progress { margin-top: 0; }
.recurrence-fraction { font-family: var(--serif); font-size: 1.15rem; font-weight: 700; }
.gap-closure-route { border-left: 4px solid var(--coral); }
.gap-closure-route ol { margin-bottom: 0; padding-left: 1.5rem; }
.gap-closure-route li + li { margin-top: .5rem; }

@media screen and (prefers-color-scheme: dark) {
  .market-summary-card,
  .vacancy-alignment-card,
  .market-matrix-group,
  .market-recurrence,
  .gap-closure-route { border-color: var(--line); background: var(--surface); color: var(--ink); }
  .market-limitation { border-left-color: var(--gold); background: var(--paper); }
  .market-learning-state { border-left-color: var(--gold); }
  .market-matrix th,
  .vacancy-key-label,
  .vacancy-alignment-score { color: var(--forest); }
  .market-matrix-state-cell,
  .recurrence-row { border-color: var(--line); }
}

@media (max-width: 680px) {
  .vacancy-alignment-grid { grid-template-columns: 1fr; }
  .market-matrix,
  .market-matrix tbody,
  .market-matrix tr,
  .market-matrix th,
  .market-matrix td { display: block; width: 100%; }
  .market-matrix thead {
    position: absolute;
    width: 1px;
    height: 1px;
    margin: -1px;
    padding: 0;
    overflow: hidden;
    clip: rect(0 0 0 0);
    clip-path: inset(50%);
    border: 0;
  }
  .market-matrix tr { padding: .75rem 0; border-bottom: 1px solid var(--muted); }
  .market-matrix th,
  .market-matrix td { border-bottom: 0; }
  .market-matrix td {
    display: grid;
    grid-template-columns: minmax(0, .45fr) minmax(0, 1fr);
    gap: .5rem;
    border-left: 0;
  }
  .market-matrix td::before { content: attr(data-label); color: var(--forest); font-weight: 700; }
  .recurrence-row { grid-template-columns: 1fr; gap: .35rem; }
}

@media print {
  .market-summary { font-size: 10.5pt; }
  .vacancy-alignment-card,
  .market-matrix-row,
  .recurrence-row,
  .learning-signal-route-row,
  .gap-closure-route { break-inside: avoid; page-break-inside: avoid; }
  .market-summary-card { break-inside: avoid; page-break-inside: avoid; }
  .market-vacancy-key { break-inside: avoid; page-break-inside: avoid; break-after: avoid; page-break-after: avoid; }
  .market-matrix { display: table; width: 100%; table-layout: fixed; }
  .market-matrix thead {
    display: table-header-group;
    position: static;
    width: auto;
    height: auto;
    margin: 0;
    overflow: visible;
    clip: auto;
    clip-path: none;
  }
  .market-matrix tbody { display: table-row-group; }
  .market-matrix tr { display: table-row; }
  .market-matrix th,
  .market-matrix td { display: table-cell; width: auto; padding: .35rem; }
  .market-matrix td::before { content: none; }
}

@media (forced-colors: active) {
  .market-summary-card,
  .vacancy-alignment-card,
  .market-matrix-group,
  .market-matrix-state-cell,
  .market-recurrence,
  .recurrence-row,
  .gap-closure-route { background: Canvas; color: CanvasText; border-color: CanvasText; }
  .market-limitation,
  .market-learning-state,
  .market-next-safe-action,
  .gap-closure-route { border-left-color: Highlight; }
  .matrix-state-symbol,
  .market-matrix th,
  .market-matrix td::before,
  .vacancy-key-label,
  .vacancy-alignment-score { color: CanvasText; }
  .vacancy-alignment-progress,
  .recurrence-progress { border: 1px solid CanvasText; background: Canvas; color: Highlight; }
  .vacancy-alignment-progress::-webkit-progress-bar,
  .recurrence-progress::-webkit-progress-bar { background: Canvas; }
  .vacancy-alignment-progress::-webkit-progress-value,
  .recurrence-progress::-webkit-progress-value,
  .vacancy-alignment-progress::-moz-progress-bar,
  .recurrence-progress::-moz-progress-bar { background: Highlight; }
  .vacancy-qualitative-band { color: CanvasText; }
  .market-learning-state,
  .market-next-safe-action,
  .decide-now-summary,
  .decide-now-target,
  .decision-trace-boundary { color: CanvasText; }
}

@media (prefers-contrast: more) {
  .market-summary-card,
  .vacancy-alignment-card,
  .market-matrix-group,
  .market-recurrence,
  .gap-closure-route { border-width: 2px; }
  .market-learning-state { border-left-width: 5px; }
  .matrix-state-symbol { text-decoration: underline; text-decoration-thickness: .12em; }
}

.decide-now, .decide-now-grid, .decide-now-card { min-width: 0; }
.decide-now-card { padding: 1rem; border: 1px solid var(--forest-soft); background: var(--surface); overflow-wrap: anywhere; }
.decide-now-card h3, .decide-now-card h4 { margin-top: 0; }
.decide-now-summary { margin-top: -.5rem; color: var(--muted-text); }
.decide-now-navigation ul, .decide-now-list, .decide-now-recurrence { margin: .5rem 0 0; padding-left: 1.25rem; }
.decide-now-navigation a { color: inherit; text-decoration-thickness: .12em; text-underline-offset: .15em; }
.decide-now-rank { display: inline-grid; min-width: 1.5rem; place-items: center; margin-right: .25rem; border-radius: 999px; background: var(--coral); color: var(--paper); font-weight: 700; }
.decide-now-target { color: var(--muted-text); }
.decide-now-facts { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: .5rem 1rem; }
.decide-now-facts dd { margin: 0; font-weight: 700; }
.decide-now-authorization { border-left: 4px solid var(--gold); }
.decide-now-market { border-top: 4px solid var(--forest); }
.decide-now-signal { display: inline-block; min-width: 11rem; }
@media screen and (prefers-color-scheme: dark) {
  .decide-now-card { border-color: var(--forest); background: var(--surface); color: var(--ink); }
}
@media (max-width: 640px) {
  .decide-now, .decide-now-grid, .decide-now-card { min-width: 0; }
  .decide-now-signal { min-width: 0; }
}
@media (prefers-reduced-motion: reduce) {
  .decide-now-card { animation: none !important; transition: none !important; transform: none !important; }
}
@media print {
  .decide-now-card { break-inside: avoid; page-break-inside: avoid; }
}
@media (forced-colors: active) {
  .decide-now-card { background: Canvas; color: CanvasText; border-color: CanvasText; }
  .decide-now-rank { background: Highlight; color: HighlightText; }
  .decide-now-market { border-top-color: Highlight; }
  .decide-now-authorization { border-left-color: Highlight; }
}
@media (prefers-contrast: more) {
  .decide-now-card { border-width: 2px; }
  .decide-now-market { border-top-width: 5px; }
  .decide-now-authorization { border-left-width: 5px; }
}

.learning-decision,
.learning-decision-grid,
.learning-decision-card { min-width: 0; }
.learning-decision { margin-top: 1rem; }
.learning-decision-intro,
.learning-decision-boundary,
.learning-decision-sample { max-width: 72ch; }
.learning-decision-sample { color: var(--muted-text); }
.learning-decision-grid { align-items: stretch; }
.learning-decision-card {
  border-top: 4px solid var(--coral);
  overflow-wrap: anywhere;
}
.learning-decision-card p { margin-block: .7rem 0; }
.learning-decision-proof {
  margin-top: .85rem;
  padding: .75rem;
  border-left: 3px solid var(--gold);
  background: var(--paper);
}
.learning-decision-proof h4 { margin: 0; font-size: 1rem; }
.learning-decision-proof p { margin-top: .45rem; }
.learning-signal-route-row {
  min-width: 0;
  padding: .6rem 0;
}
.learning-signal-route-row + .learning-signal-route-row {
  margin-top: .2rem;
  padding-top: .8rem;
  border-top: 1px solid var(--muted);
}
.learning-signal-route-row:last-child { padding-bottom: 0; }
.learning-signal-route-row > strong { display: block; color: var(--forest); }
.learning-signal-route-row p { margin-top: .35rem; }
.learning-decision-header {
  display: flex;
  align-items: flex-start;
  gap: .7rem;
}
.learning-decision-header h3 { margin: 0; }
.learning-decision-rank {
  display: inline-grid;
  flex: 0 0 auto;
  min-width: 1.6rem;
  min-height: 1.6rem;
  place-items: center;
  border-radius: 999px;
  background: var(--coral);
  color: var(--paper);
  font-weight: 800;
}
.learning-decision-role { color: var(--muted-text); }
.learning-decision-boundary {
  margin-top: 1rem;
  color: var(--muted-text);
  font-size: .875rem;
}

.decision-trace {
  min-width: 0;
  margin-top: 1rem;
  padding: 1rem;
  border: 1px solid var(--forest-soft);
  border-left: 4px solid var(--coral);
  background: var(--paper);
  overflow-wrap: anywhere;
}
.decision-trace-title { margin: 0 0 .75rem; }
.decision-trace-steps {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: .75rem;
  margin: 0;
  padding-left: 1.25rem;
}
.decision-trace-step { min-width: 0; padding-left: .25rem; }
.decision-trace-step-label {
  display: block;
  color: var(--forest);
  font-size: .8125rem;
  font-weight: 800;
  letter-spacing: .06em;
  text-transform: uppercase;
}
.decision-trace-step p { margin: .55rem 0 0; }
.decision-trace-evidence-list,
.decision-trace-evidence-list li { min-width: 0; }
.decision-trace-evidence-list { margin: .55rem 0 0; padding-left: 1.1rem; }
.decision-trace-evidence-list li + li { margin-top: .5rem; }
.decision-trace-evidence-state { color: var(--forest); font-weight: 700; }
.decision-trace-evidence-paraphrase { display: block; }
.decision-trace .coach-template { margin-top: .55rem; padding: .75rem; background: var(--surface); }
.decision-trace .coach-template h5 { margin: 0; font-size: 1rem; }
.decision-trace .coach-template-list { margin-top: .55rem; }
.decision-trace-boundary { margin: 1rem 0 0; color: var(--muted-text); font-size: .875rem; }

@media screen and (prefers-color-scheme: dark) {
  .decision-trace { border-color: var(--forest); background: var(--surface); color: var(--ink); }
  .decision-trace .coach-template { background: var(--paper); }
  .decision-trace-step-label,
  .decision-trace-evidence-state { color: var(--forest); }
}

@media (max-width: 640px) {
  .decision-trace-steps { grid-template-columns: minmax(0, 1fr); }
  .decision-trace { padding: .85rem; }
}

@media print {
  .decision-trace,
  .decision-trace-step,
  .decision-trace .coach-template { break-inside: avoid; page-break-inside: avoid; }
}

@media (forced-colors: active) {
  .decision-trace,
  .decision-trace .coach-template { background: Canvas; color: CanvasText; border-color: CanvasText; }
  .decision-trace { border-left-color: Highlight; }
  .decision-trace-step-label,
  .decision-trace-evidence-state { color: CanvasText; }
}

@media (prefers-reduced-motion: reduce) {
  .decision-trace,
  .decision-trace * { animation: none !important; transition: none !important; transform: none !important; }
}

@media screen and (prefers-color-scheme: dark) {
  .learning-decision-card { border-color: var(--forest); background: var(--surface); color: var(--ink); }
  .learning-decision-proof { background: var(--paper); }
  .learning-decision-rank { background: var(--coral); color: var(--paper); }
  .learning-signal-route-row + .learning-signal-route-row { border-color: var(--line); }
  .learning-signal-route-row > strong { color: var(--forest); }
}

@media (max-width: 640px) {
  .learning-decision,
  .learning-decision-grid,
  .learning-decision-card { min-width: 0; }
  .learning-decision-header { align-items: flex-start; }
  .learning-signal-route-row { padding: .5rem 0; }
  .learning-signal-route-row + .learning-signal-route-row {
    margin-top: .1rem;
    padding-top: .65rem;
  }
}

@media (prefers-reduced-motion: reduce) {
  .learning-decision-card { animation: none !important; transition: none !important; transform: none !important; }
}

@media print {
  .learning-decision-card { break-inside: avoid; page-break-inside: avoid; }
  .learning-decision-boundary { font-size: 9.5pt; }
}

@media (forced-colors: active) {
  .learning-decision-card,
  .learning-decision-proof,
  .learning-signal-route-row { background: Canvas; color: CanvasText; border-color: CanvasText; }
  .learning-signal-route-row + .learning-signal-route-row { border-color: CanvasText; }
  .learning-signal-route-row > strong { color: CanvasText; }
  .learning-decision-rank { background: Highlight; color: HighlightText; }
  .learning-decision-sample,
  .learning-decision-role,
  .learning-decision-boundary { color: CanvasText; }
}

@media (prefers-contrast: more) {
  .learning-decision-card { border-width: 2px; }
}
```

### `plugins/professional-growth-coach/assets/career-learning-eligibility-v1.css`

```css
.weekly-decision {
  min-width: 0;
  border-top: 4px solid var(--coral);
  overflow-wrap: anywhere;
}

.weekly-decision > h3 { margin-bottom: .75rem; }
.weekly-decision-vacancy { margin: 0; font-family: var(--serif); font-size: 1.15rem; }
.weekly-decision-label {
  display: block;
  margin-bottom: .2rem;
  color: var(--forest);
  font-family: var(--sans);
  font-size: .78rem;
  font-weight: 800;
  letter-spacing: .06em;
  text-transform: uppercase;
}
.weekly-decision-facts {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: .75rem;
  min-width: 0;
  margin-top: .9rem;
}
.weekly-decision-facts:empty { display: none; }
.weekly-decision-signal,
.weekly-decision-recurrence { min-width: 0; margin: 0; }
.weekly-decision-choices { min-width: 0; margin-top: 1rem; }
.weekly-decision-choices h4 { margin: 0; font-size: 1rem; }
.weekly-decision-choices ol { margin: .55rem 0 0; padding-left: 1.4rem; }
.weekly-decision-choice { min-width: 0; overflow-wrap: anywhere; }
.weekly-decision-choice + .weekly-decision-choice { margin-top: .45rem; }
.weekly-decision-evidence {
  margin: 1rem 0 0;
  padding: .75rem .9rem;
  border-left: 4px solid var(--forest);
  background: var(--paper);
}
.weekly-decision-action {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: .75rem;
  min-width: 0;
  margin-top: 1rem;
}
.weekly-decision-action p { min-width: 0; margin: 0; }
.weekly-decision-boundary { margin: 1rem 0 0; color: var(--muted-text); font-size: .875rem; }
.weekly-decision-secondary { border-style: dashed; }

@media screen and (prefers-color-scheme: dark) {
  .weekly-decision { border-color: var(--coral); background: var(--surface); color: var(--ink); }
  .weekly-decision-evidence { border-color: var(--forest); background: var(--paper); color: var(--ink); }
  .weekly-decision-label { color: var(--forest); }
  .weekly-decision-choice { border-color: var(--line); }
  .weekly-decision-boundary { color: var(--ink); }
  .weekly-decision-secondary { border-color: var(--line); background: var(--surface); color: var(--ink); }
}

@media (max-width: 680px) {
  .weekly-decision,
  .weekly-decision-facts,
  .weekly-decision-action,
  .weekly-decision-choices,
  .weekly-decision-choice { min-width: 0; overflow-wrap: anywhere; }
  .weekly-decision-facts,
  .weekly-decision-action { grid-template-columns: minmax(0, 1fr); }
}

@media print {
  .weekly-decision { break-inside: avoid; page-break-inside: avoid; }
  .weekly-decision-choice { break-inside: avoid; page-break-inside: avoid; }
  .weekly-decision-boundary { font-size: 9.5pt; }
}

@media (forced-colors: active) {
  .weekly-decision,
  .weekly-decision-evidence,
  .weekly-decision-secondary { background: Canvas; color: CanvasText; border-color: CanvasText; }
  .weekly-decision { border-top-color: Highlight; }
  .weekly-decision-evidence { border-left-color: Highlight; }
  .weekly-decision-label,
  .weekly-decision-boundary { color: CanvasText; }
}

@media (prefers-reduced-motion: reduce) {
  .weekly-decision,
  .weekly-decision * { animation: none !important; transition: none !important; transform: none !important; }
}
```

### `plugins/professional-growth-coach/assets/learning-proof-sprint-v1.css`

```css
:root {
  --paper: #f6f4ee;
  --surface: #ffffff;
  --ink: #1b1c1a;
  --forest: #173e30;
  --forest-soft: #dce5e0;
  --coral: #b9513a;
  --coral-soft: #f6e0da;
  --decision-term: #dfbf70;
  --line: #6f8175;
  --muted: #46534d;
  --measure: 72ch;
  --serif: Georgia, "Times New Roman", Times, serif;
  --sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
}

* { box-sizing: border-box; }

html { color-scheme: light; background: var(--paper); }

.learning-proof-sprint-document {
  margin: 0;
  background: var(--paper);
  color: var(--ink);
  font-family: var(--sans);
  font-size: 16px;
  line-height: 1.55;
  overflow-wrap: anywhere;
}

.learning-proof-sprint-document :focus-visible {
  outline: 3px solid var(--coral);
  outline-offset: 3px;
}

.learning-proof-sprint-document .skip-link {
  position: fixed;
  z-index: 10;
  top: .5rem;
  left: .5rem;
  transform: translateY(-200%);
  padding: .75rem 1rem;
  background: var(--surface);
  border: 1px solid var(--forest);
  color: var(--forest);
  font-weight: 700;
}

.learning-proof-sprint-document .skip-link:focus { transform: none; }

.learning-proof-sprint-document .sprint-shell {
  width: min(960px, calc(100% - 2rem));
  margin-inline: auto;
  padding-block: 2rem 3rem;
}

.learning-proof-sprint-document .sprint-header {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 1.5rem;
  padding-block: 0 1.5rem;
  border-bottom: 1px solid var(--forest);
}

.learning-proof-sprint-document .sprint-kicker,
.learning-proof-sprint-document .sprint-label {
  margin: 0;
  color: var(--forest);
  font-size: .8125rem;
  font-weight: 700;
  letter-spacing: .09em;
  text-transform: uppercase;
}

.learning-proof-sprint-document h1,
.learning-proof-sprint-document h2,
.learning-proof-sprint-document h3,
.learning-proof-sprint-document h4 { font-family: var(--serif); }

.learning-proof-sprint-document h1 {
  max-width: 18ch;
  margin: .2rem 0 0;
  font-size: clamp(2rem, 6vw, 3.25rem);
  font-style: italic;
  line-height: 1.04;
}

.learning-proof-sprint-document h2,
.learning-proof-sprint-document h3,
.learning-proof-sprint-document h4 { margin: 0; line-height: 1.16; }

.learning-proof-sprint-document h2 { color: var(--forest); font-size: clamp(1.35rem, 3vw, 1.85rem); }
.learning-proof-sprint-document h3 { font-size: clamp(1.15rem, 2.2vw, 1.45rem); }
.learning-proof-sprint-document h4 { font-size: 1rem; }

.learning-proof-sprint-document .sprint-intro {
  max-width: var(--measure);
  margin: .75rem 0 0;
  color: var(--muted);
}

.learning-proof-sprint-document .sprint-status {
  flex: 0 0 auto;
  margin: 0;
  padding: .45rem .7rem;
  border: 1px solid var(--forest);
  background: var(--forest-soft);
  color: var(--forest);
  font-size: .875rem;
  font-weight: 700;
  text-align: center;
}

.learning-proof-sprint-document .sprint-plan,
.learning-proof-sprint-document .sprint-start,
.learning-proof-sprint-document .sprint-timeline-section,
.learning-proof-sprint-document .sprint-handoffs-section { padding-top: 2rem; }

.learning-proof-sprint-document .section-heading { margin-bottom: 1rem; }
.learning-proof-sprint-document .section-heading h2 { margin-top: .2rem; }

.learning-proof-sprint-document .sprint-plan-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1px;
  border: 1px solid var(--line);
  background: var(--line);
}

.learning-proof-sprint-document .sprint-plan-grid > div {
  min-width: 0;
  padding: 1rem;
  background: var(--surface);
}

.learning-proof-sprint-document .sprint-plan-grid > div:last-child { grid-column: 1 / -1; }

.learning-proof-sprint-document .sprint-start {
  padding-bottom: .25rem;
}

.learning-proof-sprint-document .sprint-start-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1px;
  border: 1px solid var(--forest);
  background: var(--forest);
}

.learning-proof-sprint-document .sprint-start-grid > div {
  min-width: 0;
  padding: 1rem;
  background: var(--forest-soft);
}

.learning-proof-sprint-document .sprint-start-grid > div:first-child,
.learning-proof-sprint-document .sprint-start-grid > div:nth-child(3) { grid-column: span 2; }

.learning-proof-sprint-document dt,
.learning-proof-sprint-document .field-label {
  color: var(--muted);
  font-size: .8125rem;
  font-weight: 700;
  letter-spacing: .03em;
}

.learning-proof-sprint-document dd { margin: .35rem 0 0; }

.learning-proof-sprint-document .sprint-timeline {
  position: relative;
  display: grid;
  gap: 1rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.learning-proof-sprint-document .sprint-timeline::before {
  position: absolute;
  top: 1rem;
  bottom: 1rem;
  left: 1.4rem;
  width: 2px;
  background: var(--forest);
  content: "";
}

.learning-proof-sprint-document .sprint-day {
  position: relative;
  display: grid;
  grid-template-columns: 3rem minmax(0, 1fr);
  gap: 1rem;
  min-width: 0;
}

.learning-proof-sprint-document .sprint-day-marker {
  z-index: 1;
  display: grid;
  place-items: center;
  align-self: start;
  width: 2.8rem;
  height: 2.8rem;
  border: 2px solid var(--forest);
  border-radius: 50%;
  background: var(--paper);
  color: var(--forest);
  font-weight: 800;
}

.learning-proof-sprint-document .sprint-day-card,
.learning-proof-sprint-document .sprint-handoff {
  min-width: 0;
  padding: 1rem;
  border: 1px solid var(--line);
  background: var(--surface);
  box-shadow: 0 1px 0 rgb(23 62 48 / 10%);
}

.learning-proof-sprint-document .sprint-day-card > * + *,
.learning-proof-sprint-document .sprint-handoff > * + * { margin-top: .9rem; }

.learning-proof-sprint-document .sprint-day-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 1rem;
  border-bottom: 1px solid var(--forest-soft);
  padding-bottom: .65rem;
}

.learning-proof-sprint-document .sprint-day-label,
.learning-proof-sprint-document .handoff-index {
  margin: 0;
  color: var(--forest);
  font-size: .8125rem;
  font-weight: 800;
  letter-spacing: .06em;
  text-transform: uppercase;
}

.learning-proof-sprint-document .sprint-day-facts,
.learning-proof-sprint-document .sprint-handoff-facts { display: grid; gap: .75rem; margin: 0; }

.learning-proof-sprint-document .sprint-day-facts > div,
.learning-proof-sprint-document .sprint-handoff-facts > div { min-width: 0; }

.learning-proof-sprint-document .sprint-proof-check,
.learning-proof-sprint-document .sprint-acceptance {
  padding: .8rem;
  border-left: 4px solid var(--forest);
  background: var(--forest-soft);
}

.learning-proof-sprint-document .sprint-risk-check,
.learning-proof-sprint-document .sprint-blocked-claims {
  padding: .8rem;
  border-left: 4px solid var(--coral);
  background: var(--coral-soft);
}

.learning-proof-sprint-document .sprint-proof-check p,
.learning-proof-sprint-document .sprint-acceptance p,
.learning-proof-sprint-document .sprint-risk-check p,
.learning-proof-sprint-document .sprint-blocked-claims p,
.learning-proof-sprint-document .sprint-safe-action p { margin: .3rem 0 0; }

.learning-proof-sprint-document .sprint-safe-action {
  margin: 0;
  color: var(--forest);
  font-weight: 700;
}

.learning-proof-sprint-document .sprint-handoffs {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1rem;
  margin: 0;
  padding: 0;
  list-style: none;
  counter-reset: handoff;
}

.learning-proof-sprint-document .sprint-handoff { border-top: 4px solid var(--forest); }
.learning-proof-sprint-document .sprint-handoff:nth-child(2) { border-top-color: var(--decision-term); }
.learning-proof-sprint-document .sprint-handoff:nth-child(3) { border-top-color: var(--coral); }

.learning-proof-sprint-document .sprint-handoff-header {
  display: flex;
  align-items: baseline;
  gap: .75rem;
}

.learning-proof-sprint-document .sprint-boundary {
  margin-top: 2rem;
  padding: 1rem;
  border: 1px solid var(--coral);
  border-left-width: 4px;
  background: var(--coral-soft);
}

.learning-proof-sprint-document .sprint-boundary h2 { color: var(--ink); font-size: 1.2rem; }
.learning-proof-sprint-document .sprint-boundary p { max-width: var(--measure); margin: .45rem 0 0; }

.learning-proof-sprint-document .sprint-footer {
  width: min(960px, calc(100% - 2rem));
  margin-inline: auto;
  padding-block: 1rem 2rem;
  border-top: 1px solid var(--forest);
  color: var(--muted);
  font-size: .875rem;
}

.learning-proof-sprint-document .sprint-footer p { margin: .35rem 0 0; }

@media screen and (prefers-color-scheme: dark) {
  :root {
    color-scheme: dark;
    --paper: #101521;
    --surface: #182235;
    --ink: #f3f6ff;
    --muted: #b8c4d8;
    --line: #5f718e;
    --forest: #8fc9b0;
    --forest-soft: #223b35;
    --coral: #ff9f8d;
    --coral-soft: #3f282d;
    --decision-term: #f5d68a;
  }
  html,
  .learning-proof-sprint-document { background: var(--paper); color: var(--ink); }
}

@media (max-width: 640px) {
  .learning-proof-sprint-document .sprint-shell,
  .learning-proof-sprint-document .sprint-footer { width: min(100% - 1rem, 960px); }
  .learning-proof-sprint-document .sprint-header { align-items: start; flex-direction: column; }
  .learning-proof-sprint-document .sprint-status { text-align: left; }
  .learning-proof-sprint-document .sprint-plan-grid,
  .learning-proof-sprint-document .sprint-start-grid,
  .learning-proof-sprint-document .sprint-handoffs { grid-template-columns: 1fr; }
  .learning-proof-sprint-document .sprint-plan-grid > div:last-child { grid-column: auto; }
  .learning-proof-sprint-document .sprint-start-grid > div:first-child,
  .learning-proof-sprint-document .sprint-start-grid > div:nth-child(3) { grid-column: auto; }
  .learning-proof-sprint-document .sprint-day { grid-template-columns: 2.4rem minmax(0, 1fr); gap: .65rem; }
  .learning-proof-sprint-document .sprint-day-marker { width: 2.3rem; height: 2.3rem; }
  .learning-proof-sprint-document .sprint-timeline::before { left: 1.15rem; }
  .learning-proof-sprint-document .sprint-day-header { align-items: start; flex-direction: column; gap: .25rem; }
}

@media (prefers-reduced-motion: reduce) {
  .learning-proof-sprint-document *,
  .learning-proof-sprint-document *::before,
  .learning-proof-sprint-document *::after {
    animation: none !important;
    transition: none !important;
    scroll-behavior: auto !important;
  }
}

@media (forced-colors: active) {
  .learning-proof-sprint-document .skip-link { background: Canvas; border-color: CanvasText; color: CanvasText; }
  .learning-proof-sprint-document main:focus-visible { outline-color: Highlight; }
  .learning-proof-sprint-document .sprint-plan-grid,
  .learning-proof-sprint-document .sprint-start-grid,
  .learning-proof-sprint-document .sprint-day-card,
  .learning-proof-sprint-document .sprint-handoff,
  .learning-proof-sprint-document .sprint-boundary,
  .learning-proof-sprint-document .sprint-proof-check,
  .learning-proof-sprint-document .sprint-acceptance,
  .learning-proof-sprint-document .sprint-risk-check,
  .learning-proof-sprint-document .sprint-blocked-claims { background: Canvas; color: CanvasText; border-color: CanvasText; }
  .learning-proof-sprint-document .sprint-kicker,
  .learning-proof-sprint-document .sprint-label,
  .learning-proof-sprint-document .sprint-day-label,
  .learning-proof-sprint-document .sprint-safe-action,
  .learning-proof-sprint-document h2 { color: CanvasText; }
  .learning-proof-sprint-document .sprint-status { background: Canvas; color: CanvasText; border-color: CanvasText; }
  .learning-proof-sprint-document .sprint-timeline::before { background: CanvasText; }
  .learning-proof-sprint-document .sprint-day-marker { background: Canvas; color: CanvasText; border-color: CanvasText; }
  .learning-proof-sprint-document .sprint-footer { color: CanvasText; border-color: CanvasText; }
}

@media (prefers-contrast: more) {
  .learning-proof-sprint-document .sprint-day-card,
  .learning-proof-sprint-document .sprint-handoff,
  .learning-proof-sprint-document .sprint-boundary { border-width: 2px; box-shadow: none; }
  .learning-proof-sprint-document .sprint-label,
  .learning-proof-sprint-document .sprint-day-label { text-decoration: underline; text-decoration-thickness: .12em; }
}

@page { size: auto; margin: 14mm; }

@media print {
  .learning-proof-sprint-document { background: #fff; font-size: 11pt; }
  .learning-proof-sprint-document .skip-link { display: none !important; }
  .learning-proof-sprint-document .sprint-shell,
  .learning-proof-sprint-document .sprint-footer { width: auto; }
  .learning-proof-sprint-document .sprint-header { display: block; }
  .learning-proof-sprint-document .sprint-status { display: inline-block; margin-top: .75rem; }
  .learning-proof-sprint-document .sprint-plan-grid,
  .learning-proof-sprint-document .sprint-day-card,
  .learning-proof-sprint-document .sprint-handoff,
  .learning-proof-sprint-document .sprint-boundary,
  .learning-proof-sprint-document .sprint-footer { break-inside: avoid; page-break-inside: avoid; }
  .learning-proof-sprint-document .sprint-day-card,
  .learning-proof-sprint-document .sprint-handoff { box-shadow: none; }
  .learning-proof-sprint-document .sprint-start-grid { break-inside: avoid; page-break-inside: avoid; }
  .learning-proof-sprint-document .sprint-handoffs { grid-template-columns: 1fr; }
  .learning-proof-sprint-document .sprint-day-marker { background: #fff; }
}
```

### `plugins/professional-growth-coach/assets/private-first-interview-conversion-board-v1.css`

```css
:root {
  --paper: #f6f4ee;
  --surface: #fff;
  --ink: #1b1c1a;
  --muted: #536158;
  --forest: #173e30;
  --forest-soft: #dce5e0;
  --coral: #b9513a;
  --coral-soft: #f6e0da;
  --gold: #dfbf70;
  --line: #6f8175;
  --serif: Georgia, "Times New Roman", Times, serif;
  --sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
}
* { box-sizing: border-box; }
html { color-scheme: light; background: var(--paper); }
body { margin: 0; color: var(--ink); background: var(--paper); font: 16px/1.55 var(--sans); overflow-wrap: anywhere; }
.board-shell { width: min(920px, calc(100% - 2rem)); margin-inline: auto; }
.board-shell :focus-visible { outline: 3px solid var(--coral); outline-offset: 3px; }
.skip-link { position: fixed; z-index: 2; left: .5rem; top: .5rem; transform: translateY(-200%); padding: .75rem 1rem; background: var(--surface); border: 1px solid var(--forest); color: var(--forest); font-weight: 700; }
.skip-link:focus { transform: none; }
.board-header { display: flex; align-items: end; justify-content: space-between; gap: 1rem; padding: 2rem 0 1rem; border-bottom: 1px solid var(--forest); }
.board-kicker, .board-label { margin: 0; color: var(--forest); font-size: .8125rem; font-weight: 700; letter-spacing: .09em; text-transform: uppercase; }
h1, h2, h3 { font-family: var(--serif); }
h1 { margin: .2rem 0 0; font-size: clamp(2rem, 6vw, 3.25rem); font-style: italic; line-height: 1.04; }
h2 { margin: 0; color: var(--forest); font-size: clamp(1.35rem, 3vw, 1.85rem); line-height: 1.16; }
h3 { margin: 0; font-size: 1.12rem; line-height: 1.2; }
.board-state { display: inline-flex; align-items: center; min-height: 2.25rem; padding: .4rem .75rem; border: 1px solid currentColor; color: var(--forest); font-size: .875rem; font-weight: 700; text-align: center; }
.board-main { padding: 1.5rem 0 3rem; }
.board-main > section + section { margin-top: 1.5rem; }
.board-decision { padding: clamp(1.15rem, 3vw, 2rem); background: var(--forest); border-left: 4px solid var(--gold); color: #fff; }
.board-decision h2 { color: #fff; }
.board-decision p { max-width: 72ch; }
.board-decision dl, .board-facts { display: grid; grid-template-columns: minmax(10rem, .35fr) minmax(0, 1fr); gap: .55rem 1rem; margin: 1rem 0 0; }
.board-decision dt { color: var(--gold); font-weight: 700; }
.board-decision dd, .board-facts dd { margin: 0; }
.board-boundary { margin: 1rem 0 0; padding: .85rem 1rem; background: var(--coral-soft); border: 1px solid var(--coral); color: var(--ink); font-weight: 650; }
.board-approval-boundary { margin-top: 1.5rem; padding: 1rem; background: var(--coral-soft); border: 2px solid var(--coral); }
.board-approval-boundary h2 { color: var(--ink); }
.board-approval-boundary ul { columns: 3; margin: .5rem 0 0; padding-left: 1.25rem; }
.board-sequence ol, .board-week-list, .board-review-list, .board-ladder-list, .board-proof-list, .board-risk-list { display: grid; gap: 1rem; margin: 1rem 0 0; padding: 0; list-style: none; }
.board-sequence ol { grid-template-columns: repeat(4, 1fr); }
.board-sequence li, .board-proof-card, .board-risk-card, .board-rehearsal, .board-day, .board-branch, .board-review { min-width: 0; padding: 1rem; background: var(--surface); border: 1px solid var(--line); }
.board-sequence li { border-top: 4px solid var(--forest); }
.board-number { display: block; color: var(--coral); font-size: .8rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }
.board-proof-list { grid-template-columns: repeat(2, 1fr); }
.board-proof-card { border-left: 4px solid var(--forest); }
.board-risk-list { grid-template-columns: repeat(2, 1fr); }
.board-risk-card { border-left: 4px solid var(--coral); }
.board-risk-card dl { margin: .75rem 0 0; }
.board-risk-card dt { margin-top: .6rem; color: var(--muted); font-size: .8rem; font-weight: 700; }
.board-risk-card dd { margin: .1rem 0 0; }
.board-rehearsal { background: var(--forest-soft); border-left: 4px solid var(--forest); }
.board-rehearsal p { max-width: 72ch; }
.board-week-list, .board-review-list, .board-ladder-list { grid-template-columns: repeat(2, 1fr); }
.board-day { border-top: 4px solid var(--forest); }
.board-day strong, .board-review strong, .board-branch strong { color: var(--forest); }
.board-day dl, .board-review dl, .board-branch dl { display: grid; gap: .55rem; margin: .8rem 0 0; }
.board-day dt, .board-review dt, .board-branch dt { color: var(--muted); font-size: .8rem; font-weight: 700; }
.board-day dd, .board-review dd, .board-branch dd { margin: 0; }
.board-branch { border-left: 4px solid var(--gold); }
.board-footer { padding: 1rem max(1rem, calc((100% - 920px) / 2)) 2rem; border-top: 1px solid var(--forest); color: var(--muted); font-size: .88rem; }
.board-footer p { margin: .4rem 0 0; }
@media (max-width: 640px) {
  .board-header { display: block; }
  .board-state { margin-top: 1rem; }
  .board-sequence ol, .board-proof-list, .board-risk-list, .board-week-list, .board-review-list, .board-ladder-list { grid-template-columns: 1fr; }
  .board-decision dl, .board-facts { grid-template-columns: 1fr; gap: .25rem; }
  .board-decision dt { margin-top: .6rem; }
}
@media screen and (prefers-color-scheme: dark) {
  :root { color-scheme: dark; --paper: #101521; --surface: #182235; --ink: #f3f6ff; --muted: #b8c4d8; --forest: #8fc9b0; --forest-soft: #244337; --coral: #ff9b83; --coral-soft: #4a2829; --gold: #f2d28a; --line: #5f718e; }
  .board-decision { color: var(--ink); }
  .board-decision h2 { color: var(--ink); }
}
@media print {
  html, body { background: #fff; }
  .board-shell { width: 100%; }
  .board-header, .board-decision, .board-sequence, .board-proof, .board-risks, .board-rehearsal, .board-week, .board-ladder, .board-reviews, .board-boundary, .board-footer { break-inside: avoid; page-break-inside: avoid; }
  .board-decision, .board-boundary { color: #000; border: 1px solid #000; background: #fff; }
  .board-approval-boundary { border: 2px solid #000; background: #fff; color: #000; }
  .skip-link { display: none; }
}
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation-duration: .01ms !important; transition-duration: .01ms !important; scroll-behavior: auto !important; } }
@media (forced-colors: active) {
  .skip-link, .board-decision, .board-sequence li, .board-proof-card, .board-risk-card, .board-rehearsal, .board-day, .board-branch, .board-review { background: Canvas; color: CanvasText; border-color: CanvasText; }
  .skip-link:focus-visible { outline: 2px solid Highlight; }
  .board-decision h2, .board-decision dt, .board-decision dd, .board-kicker, .board-label, .board-approval-boundary h2, h2, strong { color: CanvasText; }
}
```

### `plugins/professional-growth-coach/assets/private-vacancy-application-packet-v1.css`

```css
:root {
  color-scheme: light dark;
  --paper: #f6f4ee;
  --surface: #ffffff;
  --ink: #1b1c1a;
  --muted: #55615c;
  --forest: #173e30;
  --forest-soft: #dce5e0;
  --coral: #b9513a;
  --coral-soft: #f6e0da;
  --line: #b8c7c0;
  --focus: #0b6e4f;
  --sans: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  --serif: Georgia, "Times New Roman", serif;
  --measure: 72ch;
  --radius: 0.75rem;
}

* {
  box-sizing: border-box;
}

html {
  background: var(--paper);
  color: var(--ink);
  font-family: var(--sans);
  line-height: 1.55;
  text-size-adjust: 100%;
}

.private-vacancy-packet-document {
  margin: 0;
  min-width: 20rem;
  background: var(--paper);
}

a {
  color: var(--forest);
}

.skip-link {
  position: absolute;
  z-index: 10;
  top: 0.5rem;
  left: 0.5rem;
  padding: 0.65rem 0.85rem;
  border: 2px solid var(--focus);
  background: var(--surface);
  color: var(--ink);
  transform: translateY(-180%);
}

.skip-link:focus {
  transform: translateY(0);
}

:focus-visible {
  outline: 3px solid var(--focus);
  outline-offset: 3px;
}

.packet-shell {
  width: min(920px, calc(100% - 2rem));
  margin-inline: auto;
}

.packet-header {
  padding-block: 2.5rem 1.25rem;
}

.packet-kicker,
.packet-eyebrow,
.packet-status-label {
  margin: 0;
  color: var(--forest);
  font-size: 0.76rem;
  font-weight: 750;
  letter-spacing: 0.09em;
  text-transform: uppercase;
}

h1,
h2,
h3,
p,
dl,
ol,
ul {
  margin-top: 0;
}

h1,
h2,
h3 {
  color: var(--ink);
  font-family: var(--serif);
  line-height: 1.14;
}

h1 {
  max-width: 22ch;
  margin-bottom: 0.75rem;
  font-size: clamp(2rem, 7vw, 3.5rem);
}

h2 {
  margin-bottom: 0.9rem;
  font-size: clamp(1.35rem, 4vw, 1.85rem);
}

h3 {
  margin-bottom: 0.6rem;
  font-size: 1.12rem;
}

.packet-subtitle,
.packet-note,
.packet-meta {
  max-width: var(--measure);
  color: var(--muted);
}

.packet-readiness,
.packet-section,
.packet-approval,
.packet-suppressed {
  margin-bottom: 1rem;
  padding: clamp(1rem, 3vw, 1.5rem);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--surface);
}

.packet-readiness {
  border-width: 2px;
  border-left-width: 0.65rem;
}

.packet-readiness.is-ready {
  border-color: var(--forest);
}

.packet-readiness.is-revise,
.packet-readiness.is-stop {
  border-color: var(--coral);
}

.packet-readiness.is-revise .packet-status-label,
.packet-readiness.is-stop .packet-status-label,
.packet-warning {
  color: var(--coral);
}

.packet-summary-grid,
.packet-card-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.85rem;
}

.packet-card-grid {
  margin: 0;
  padding: 0;
  list-style: none;
}

.packet-requirement-card,
.packet-draft-card {
  padding: 1rem;
  border: 1px solid var(--line);
  border-radius: calc(var(--radius) - 0.15rem);
  background: var(--paper);
}

.packet-requirement-card p:last-child,
.packet-draft-card p:last-child,
.packet-section > :last-child,
.packet-readiness > :last-child,
.packet-approval > :last-child,
.packet-suppressed > :last-child {
  margin-bottom: 0;
}

dl {
  margin-bottom: 0;
}

.packet-summary-grid div,
.packet-detail-list div {
  min-width: 0;
}

.packet-detail-list div + div {
  margin-top: 0.75rem;
}

dt {
  color: var(--muted);
  font-size: 0.78rem;
  font-weight: 750;
  letter-spacing: 0.055em;
  text-transform: uppercase;
}

dd {
  margin: 0.18rem 0 0;
  overflow-wrap: anywhere;
}

.packet-list {
  padding-left: 1.35rem;
}

.packet-list li + li {
  margin-top: 0.55rem;
}

.packet-table-region {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.92rem;
}

caption {
  padding-bottom: 0.7rem;
  color: var(--muted);
  text-align: left;
}

th,
td {
  padding: 0.7rem;
  border: 1px solid var(--line);
  text-align: left;
  vertical-align: top;
}

th {
  background: var(--forest-soft);
  color: var(--ink);
}

.packet-boundary {
  padding-left: 1rem;
  border-left: 0.4rem solid var(--coral);
}

.packet-footer {
  padding-block: 1rem 3rem;
  color: var(--muted);
  font-size: 0.86rem;
}

.packet-footer strong {
  color: var(--ink);
}

@media screen and (prefers-color-scheme: dark) {
  :root {
    --paper: #111714;
    --surface: #18211d;
    --ink: #f3f0e8;
    --muted: #bdc7c2;
    --forest: #91c6ad;
    --forest-soft: #253b32;
    --coral: #f29a83;
    --coral-soft: #4c2a23;
    --line: #60736a;
    --focus: #f5b49f;
  }
}

@media (forced-colors: active) {
  :root {
    --paper: Canvas;
    --surface: Canvas;
    --ink: CanvasText;
    --muted: CanvasText;
    --forest: LinkText;
    --forest-soft: Canvas;
    --coral: MarkText;
    --coral-soft: Canvas;
    --line: CanvasText;
    --focus: Highlight;
  }

  .packet-readiness,
  .packet-boundary {
    forced-color-adjust: auto;
  }
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    scroll-behavior: auto !important;
    transition-duration: 0.01ms !important;
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
  }
}

@media (max-width: 640px) {
  .packet-shell {
    width: min(100% - 1rem, 920px);
  }

  .packet-header {
    padding-top: 1.5rem;
  }

  .packet-summary-grid,
  .packet-card-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  th,
  td {
    padding: 0.55rem;
  }
}

@media print {
  @page {
    margin: 18mm 14mm 24mm;
  }

  :root {
    color-scheme: light;
    --paper: #ffffff;
    --surface: #ffffff;
    --ink: #000000;
    --muted: #2d2d2d;
    --forest: #173e30;
    --forest-soft: #edf2ef;
    --coral: #8a3425;
    --line: #66736d;
  }

  body {
    min-width: 0;
  }

  .skip-link {
    display: none;
  }

  .packet-shell {
    width: auto;
  }

  .packet-header {
    padding-top: 0;
  }

  .packet-readiness,
  .packet-section,
  .packet-approval,
  .packet-suppressed,
  .packet-requirement-card,
  .packet-draft-card,
  table,
  tr {
    break-inside: avoid;
    page-break-inside: avoid;
  }

  thead {
    display: table-header-group;
  }

  .packet-footer {
    position: fixed;
    right: 0;
    bottom: -16mm;
    left: 0;
    padding: 0.35rem 0;
    border-top: 1px solid var(--line);
    background: #ffffff;
  }

  .packet-footer::before {
    content: attr(data-print-private) " · " attr(data-print-boundary);
    display: block;
    color: #000000;
    font-weight: 700;
  }
}
```
