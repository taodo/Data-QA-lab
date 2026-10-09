# Data QA Lab design system

Task 18 targets React 19 + TypeScript + Vite with the existing plain CSS approach.
Nexus direction: near-black, orange, thin borders, deliberate typography and
layered bento surfaces. No Nexus screenshot or HTML asset was available in the
request or repository; this is an interpretation, not pixel-perfect reproduction.

## Tokens and scope

| Role | Token/value | Use |
|---|---|---|
| Background | `#0d0e10` | Discovery pages only |
| Surface | `--surface: #171615` | Cards, overview, illustration |
| Raised surface | `--surface-raised: #201d1a` | Warm layered surfaces |
| Text | `--ink: #f7f4f0` | Headings/body emphasis |
| Secondary text | `--muted: #b7b2ac` | Supporting copy |
| Accent | `--accent: #ff8a4c` | CTA, technical labels, highlights |
| On accent | `--on-accent: #1b100a` | Dark CTA text |
| Divider | `--line: #38332f` | Decorative thin borders |
| Focus | `--focus: #ff9f6e` | 3px outline, 4px offset |
| Control boundary | `#74685b` | Inputs, secondary controls |

Tokens live in frontend/src/discovery.css. `.discovery` wraps landing, catalog,
subjects and course overview. Learning/editor/pipeline/account surfaces retain
their existing light theme. The distinct dark navigation and visible focus
styles are shared. Do not apply discovery surface overrides to `.player-main`.
PASS/FAIL/SUCCESS/UNKNOWN/RUNNING and related statuses retain explicit text;
green/red alone never communicate a result. The landing example is labelled
illustrative and is never live telemetry.

## Typography, space and layout

- Existing local system sans stack: Inter if already installed, ui-sans-serif,
  system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif. Vietnamese
  uses system glyph support. No font/CDN fetches; no serif lesson/editor text.
- Heading size uses clamp; hero about 42–76px, section titles 30–44px. Body about
  16px, line-height 1.6. Discovery tokens: section labels 14px/600/1.4 with .06em
  tracking, small card labels 13px/.03em, metadata/captions 14px and card titles
  21px. Labels sit 12–16px above headings. Essential text stays the same size on
  mobile; reflow instead of shrinking to fit.
- Monospace only for identifiers, code, stage numbers and technical labels.
- Spacing rhythm: 8/12/16/20/24/32/40/48/56/64/88px. Cards use 20–28px padding,
  8–16px radii, 1px borders; shadows are restrained and used for hierarchy.
- Max content 1360px with adaptive gutters. Hero two columns → one at 800px;
  bento three columns → stacked; course grid existing three/two/one columns.
- Navigation wraps in document flow; never overlays content with pinned sections.
  At small widths search/navigation span a row and account controls wrap.
- The existing positioned header owns an isolated stacking context. An open
  disclosure uses layer 1 above normal positioned siblings, so the later account
  summary cannot paint through Subjects. The bounded panel scrolls at 70dvh/32rem
  and fits the viewport. Native summary keyboard toggling remains; Escape closes
  and restores trigger focus, outside pointer/Tab exit dismiss without focus theft.
- Mobile pipeline evidence stacks Source → Transform → Target vertically, with
  readable 14px labels and 16px key values. The example is always illustrative.
- Essential content reflows; table/code scrolling stays within the workspace.
  Test both locales at 375/768/1024/1440px; do not hide overflow to mask defects.

## Components and interaction

- Primary: orange fill/dark text, 48px discovery target; secondary: outlined
  surface/white text. Shared header controls at least 44px high.
- Cards keep separate real links, clear titles, metadata, availability, progress
  and SIMULATED/IMPORTED disclosure for cloud exercises. No fake logos or claims.
- Course card bodies use flex columns and automatic space above the CTA, aligning
  buttons per row without fixed description heights. Subject links expose the
  current page and show an underline plus filled background. Generic
  "FOUNDATION TO ADVANCED" card claims are removed; overview uses hands-on learning.
- All nine covers use distinct authored inline SVG schematics: SQL reconciliation,
  ETL transformation, API contract, Fabric lakehouse connections, ADF dependencies,
  OneLake shortcuts, Azure services, Databricks notebooks and Synapse warehouse
  aggregates. Reuse the same visual in overview. Fixed cover space avoids shifts;
  inline SVG has no network load or image dependency. Decorative beside titles;
  cover links have the course name. No external assets, attribution/license need,
  official logos, endorsement or claim of live provider integration.
- Course introductions retain the full-width native button with aria-expanded,
  first open/second closed, and the existing keyboard behavior.
- Navigation uses anchors, actions use buttons; form labels and skip link remain.
- Hover uses short color/border transitions, with no essential hover-only content.
- Landing accent pulse is decorative CSS, 4 seconds × 2 cycles. No listeners,
  loops, canvas or dependency; reduced motion disables all platform animations
  and transitions. All text is visible before animation and after it stops.
- English is the first-visit/invalid-preference fallback; explicit ENG/VIE local
  storage preferences persist. No browser-language/location selection. SQL,
  identifiers, written answers and stored learning records are not translated.

## UI UX Pro Max provenance

[Upstream](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill), inspected
2026-10-09. Installed project-locally via documented `uipro init --ai codex`, using
the npm package `ui-ux-pro-max-cli@2.15.0` in data/generated/task18-20261009/tools.
The generated Codex skill is `.agents/skills/ui-ux-pro-max/SKILL.md`, SHA-256
`e5baf9400d4347e5ed3eb1f6b99cd0b9ba545b8b0e507aabb2b87397bbf73ea1`.
No global install, instruction replacement or production dependency.

Installer also created six unrelated bundled skills; inspected and removed only
those newly created directories. The retained skill is ignored in Git and
`.agents`/`.codex` are excluded from Docker build context. CLI/cache stay on D.
Upstream README mentioned --dry-run but package 2.15.0 does not support it;
inspected --help/output/files instead. No force or overwrite flags used.

Queries: design-system "education data QA developer learning dark bento orange"
returned children's typography and was rejected. Refined "developer tool dark
bento" gave suitable dark developer guidance, but its FAQ pattern and green
palette were not applied. User orange/educational scope takes precedence. React
stack guidance for semantics/labels plus skill contrast, focus, wrapping and
reduced-motion rules inform implementation. No HTML/Tailwind scaffold, font
imports, testimonials, pricing or certifications from generated suggestions.

## Verification

See docs/TASK_18_PROGRESS.md for observed commands/results and screenshot paths.
Accessibility checks are focused behavior/contrast/layout checks, not a claim of
formal WCAG certification or a full screen-reader audit. External-device demo
verification remains user-operated; no tunnel is started.
