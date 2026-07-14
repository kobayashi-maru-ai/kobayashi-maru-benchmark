# Design System Inspired by a Scientific Starship Mission Terminal

## 1. Visual Theme & Atmosphere

Kobayashi is a scientific instrument, not a game and not a weapons console. The
interface should feel like an independent research terminal aboard a deep-space
mission: calm under pressure, information-dense, auditable, and exact. Its visual
metaphor is a mission-status board built from segmented rails, labelled channels,
and flat instrument surfaces. It may evoke retro-futurist starship interfaces but
must never copy protected screen layouts, insignia, typefaces, or terminology.

The chrome is dark and quiet so evidence remains primary. Warm amber identifies
the active path, coral marks uncertainty or danger, orchid separates secondary
channels, and mineral green indicates verified state. Decoration must encode
structure or state; there are no ornamental glows, star fields, or fake telemetry.

**Key Characteristics:**

- Deep mineral navy foundation with warm ivory text; never pure black or white.
- Condensed technical display type, humanist scientific body type, mono only for data.
- Segmented status rails and asymmetric instrument bars instead of generic cards.
- Left-aligned, audit-first information hierarchy with tabular numeric alignment.
- Asymmetric capsule controls: rounded leading edge, precise squared trailing edge.
- Flat surfaces separated by hue, 1px rules, and spacing; no decorative shadows.
- Desktop mission rail becomes a horizontal status strip on small screens.
- Motion communicates initialization and state changes, with reduced-motion parity.

## 2. Color Palette & Roles

### Primary

| Token | Hex | Role |
|---|---:|---|
| `--ink-950` | `#0B1118` | Page foundation; tinted near-black |
| `--ivory-050` | `#F3EEDF` | Primary text; warm near-white |
| `--amber-400` | `#EFB45F` | Active channel, primary action, focus |
| `--amber-700` | `#8C5426` | Amber text/border on pale contexts |

### Surface & Background

| Token | Hex | Named role |
|---|---:|---|
| `--surface-0` | `#0B1118` | Canvas |
| `--surface-1` | `#111A24` | Primary instrument surface |
| `--surface-2` | `#182431` | Raised grouping surface |
| `--surface-3` | `#223140` | Hover/selected dark surface |
| `--surface-inverse` | `#E9E1CE` | Light evidence panel |
| `--surface-inverse-strong` | `#D8CEB8` | Light selected panel |

### Neutrals & Text

| Token | Hex | Role |
|---|---:|---|
| `--text-primary` | `#F3EEDF` | Headings and essential content |
| `--text-secondary` | `#B9B6AA` | Supporting copy; ≥4.5:1 on surfaces |
| `--text-muted` | `#8F948F` | Nonessential metadata only |
| `--text-on-light` | `#17202A` | Text on ivory panels |
| `--text-on-accent` | `#16120D` | Text on amber/coral controls |
| `--border-subtle` | `#354452` | Structural dividers |
| `--border-strong` | `#62717D` | Selected/interactive outlines |
| `--disabled` | `#687078` | Disabled foreground only |

### Semantic & Accent

| Token | Hex | Usage rule |
|---|---:|---|
| `--coral-400` | `#E47B6C` | Warning, provisional, destructive context |
| `--coral-700` | `#8E3F38` | Coral text on pale surfaces |
| `--orchid-400` | `#B8A3D9` | Secondary channel and method links |
| `--green-400` | `#78B69B` | Verified/success only, always paired with text |
| `--red-400` | `#E26868` | Error only, never used as sole signal |
| `--focus` | `#FFD38B` | 3px focus-visible ring with 3px offset |
| `--link` | `#F0C47D` | Inline links on dark surfaces |

### Extended Color Spectrum

Campaign and data-visualization use may derive low-chroma 100/300/500/700
steps from amber, coral, orchid, and green. Product UI may use only the named
tokens above. Charts must combine hue with labels, shapes, or line patterns.

### Gradient System

No UI gradients. Use adjacent solid segments, rules, or stepped color fields.
Never use gradient text, blurred color blooms, or glow as hierarchy.

## 3. Typography Rules

### Font Family

- Display/headings: `"Barlow Condensed", "Arial Narrow", sans-serif`.
- Body/body-medium: `"IBM Plex Sans", "Noto Sans", sans-serif`.
- Data/code only: `"IBM Plex Mono", "SFMono-Regular", Consolas, monospace`.
- Spanish and English share identical families; fall back through `Noto Sans`.
- Fonts are self-hosted WOFF2 with `font-display: swap`; no runtime font request.

### Hierarchy

| Role | Size | Weight | Line Height | Letter Spacing | Notes |
|---|---:|---:|---:|---:|---|
| Display | `clamp(3.5rem, 9vw, 7.5rem)` | 600 | 0.84 | `-0.035em` | Landing statement only |
| H1 | `clamp(2.75rem, 6vw, 5.5rem)` | 600 | 0.9 | `-0.025em` | One per page |
| H2 | `clamp(2rem, 4vw, 3.5rem)` | 600 | 0.95 | `-0.015em` | Major channel title |
| H3 | `1.5rem` | 600 | 1.05 | `0` | Panel heading |
| Body | `1rem` | 400 | 1.65 | `0` | Max measure 68ch |
| Body Medium | `1rem` | 500 | 1.55 | `0` | Emphasis and table model name |
| Link | `1rem` | 600 | 1.5 | `0.01em` | Underline offset 0.2em |
| Link Small | `0.875rem` | 600 | 1.45 | `0.02em` | Metadata actions |
| Button | `0.9375rem` | 600 | 1 | `0.075em` | Uppercase, short labels |
| Button Small | `0.8125rem` | 600 | 1 | `0.08em` | Filters only |
| Caption | `0.8125rem` | 500 | 1.45 | `0.04em` | Scientific captions |
| Small | `0.75rem` | 500 | 1.4 | `0.06em` | Status labels |
| Tiny | `0.6875rem` | 600 | 1.3 | `0.09em` | Channel identifiers |

### Principles

Barlow Condensed creates decisive mission-channel hierarchy; IBM Plex Sans keeps
methodology and evidence humane and legible. IBM Plex Mono appears only where
alignment matters: scores, hashes, commands, timestamps, and sample identifiers.
Tabular numerals are mandatory for metrics. Body copy is never condensed or mono.

## 4. Component Stylings

### Buttons

- Primary: amber background, `--text-on-accent`, `border-radius: 999px 4px 4px 999px`,
  min-height 44px, padding `0 20px`; hover uses `#F7C879`, pressed translates 1px.
- Primary on Dark: same as Primary; no glow or shadow.
- Secondary: transparent, 1px `--border-strong`, ivory text, same asymmetric radius.
- Disabled: `--surface-2` background and `--disabled` text; no opacity-only state.
- Icon Button: 44×44px target, 20px icon, 1px border, `radius-2`; always has `aria-label`.
- All controls use `120ms` color/transform transitions and the `--focus` ring.

### Cards & Containers

Use cards only for independently comparable runs or samples. Default background is
`--surface-1`, border 1px `--border-subtle`, radius `4px`, and padding 24px. No box
shadow. Hoverable run rows change to `--surface-2` and expose an amber end-cap; they
never lift. Interior groups use rules and spacing instead of nested cards.

### Inputs & Forms

Inputs use `--surface-0`, ivory text, 1px `--border-strong`, 4px radius, min-height
44px, and 12px/14px padding. Placeholder uses `--text-secondary`. Focus uses a 3px
`--focus` ring. Errors use red border plus a textual explanation below connected by
`aria-describedby`. State transition is 120ms; labels are always visible.

### Navigation

Desktop navigation is a 72px top command bar plus an optional 16px segmented rail.
Content maxes at 1240px. Logo/wordmark stays left; Results, Method, Run locally, and
external repositories sit right. Active state is an amber underline and explicit
`aria-current`. Below 720px the links become a horizontally scrollable command strip,
not a hamburger; critical destinations remain visible.

### Image Treatment

The product uses diagrams and evidence screenshots, not decorative stock images.
Images use square corners or 4px radius, 1px border, descriptive alt text, explicit
dimensions, AVIF/WebP where applicable, and lazy loading below the fold. Never add
space photography, star fields, fake planets, or model portraits as filler.

### Promotional Banners / Snackbars / Toasts

Status banners are flat segmented bars: 4px amber/coral/green leading segment,
`--surface-2` body, 16px padding, Tiny label plus Body text. Toasts sit at bottom-right,
max-width 420px, no shadow, border `--border-strong`, and remain until read for errors.

## 5. Layout Principles

### Spacing System

| Token | Value | Use |
|---|---:|---|
| `--space-1` | `4px` | Hairline relationships |
| `--space-2` | `8px` | Label-to-value |
| `--space-3` | `12px` | Compact controls |
| `--space-4` | `16px` | Default inline gap |
| `--space-5` | `24px` | Panel padding |
| `--space-6` | `32px` | Component separation |
| `--space-7` | `48px` | Section subgroups |
| `--space-8` | `64px` | Section boundary |
| `--space-9` | `96px` | Major page rhythm |
| `--space-10` | `144px` | Hero breathing room |

### Grid & Container

Maximum shell width is 1440px; evidence content width is 1240px; prose is 68ch.
Desktop uses 12 columns with 24px gutters, tablet 8 columns with 20px gutters,
mobile 4 columns with 16px gutters. Page padding is `clamp(16px, 4vw, 48px)`.
The hero uses an asymmetric 7/5 split; leaderboard uses full width; methodology
uses a 4-column rail plus 8-column prose.

### Whitespace Philosophy

Dense evidence gets compact internal rhythm; major conceptual shifts receive 64–144px.
Do not apply one universal padding to every section. Empty space signals a new channel,
while 1px rules and 8–24px gaps group related telemetry.

### Border Radius Scale

| Value | Context |
|---:|---|
| `0px` | Rules, tables, segmented rails |
| `4px` | Panels, inputs, code blocks |
| `12px` | Rare callout/end-cap geometry |
| `999px 4px 4px 999px` | Primary and secondary action controls |

## 6. Depth & Elevation

| Level | Treatment | Use |
|---|---|---|
| 0 | `--surface-0`, no border/shadow | Page canvas |
| 1 | `--surface-1` + 1px subtle border | Evidence panel |
| 2 | `--surface-2` + strong top rule | Sticky command bar, selected panel |
| 3 | `--surface-3` + 1px strong border | Popover/toast only |

Elevation is flat. Never use decorative box shadows, glass blur, or glow. Depth comes
from explicit surface lightness, borders, and overlap only where interaction requires it.

**Decorative Depth:** segmented rails may overlap a panel edge by 4–12px; an ivory
evidence sheet may interrupt the dark canvas; a 1px scan rule may traverse a section.
These treatments never imply clickability and are hidden from assistive technology.

## 7. Do's and Don'ts

### Do

- Use `--amber-400` sparingly for the current action or channel.
- Pair every status color with a word, icon, or pattern.
- Align every score and percentage with tabular numerals.
- Preserve separate ES and EN tracks everywhere.
- Label provisional, incomplete, and human-review states explicitly.
- Use segmented bars to encode structure, never as empty ornament.
- Keep body copy in IBM Plex Sans at 1rem/1.65 and ≤68ch.
- Give every interactive target at least 44×44px and a `--focus` ring.
- Use native semantic tables, details, links, and headings before custom widgets.
- Honor `prefers-reduced-motion` with no spatial movement.

### Don't

- Do not copy LCARS screens, Starfleet marks, franchise names, or proprietary fonts.
- Do not use cyan-on-black neon, purple-blue gradients, glow, or star-field backgrounds.
- Do not imply that a provisional score is verified or morally authoritative.
- Do not combine Spanish and English into a single score.
- Do not hide incomplete coverage behind a numeric rank.
- Do not place every section inside a rounded card or nest cards.
- Do not use monospace for paragraphs or headings as shorthand for “technical.”
- Do not use pure `#000000`/`#FFFFFF`, generic gray, or opacity-only disabled states.
- Do not animate width, height, padding, margin, or continuous background effects.
- Do not rely on hover, color, or tiny tooltips for essential information.

## 8. Responsive Behavior

### Breakpoints

| Context | Width | Behavior |
|---|---:|---|
| Mobile | `0–479px` | 4 columns; horizontal command strip; run rows become labelled blocks |
| Small Tablet | `480–719px` | 4 columns; compact status rail; two-up metadata where possible |
| Tablet | `720–959px` | 8 columns; full navigation; hero stacks 5/3 |
| Small Desktop | `960–1199px` | 12 columns; vertical mission rail; full table |
| Desktop | `1200–1439px` | 12 columns; 1240px evidence width |
| Large Desktop | `≥1440px` | 1440px shell; whitespace grows, type/data density stays fixed |

### Touch Targets

All controls are at least 44×44px. At `pointer: coarse`, compact filters gain 4px
vertical padding. Hover is enhancement only; pressed and focus states carry parity.

### Collapsing Strategy

Navigation becomes horizontally scrollable rather than hidden. Tables switch to
semantic labelled rows below 720px while preserving model, language, score, coverage,
and verification. Secondary metrics move into native `<details>` blocks. No critical
action or benchmark caveat is removed on mobile.

### Image Behavior

Diagrams use `max-width: 100%` and retain labels at 200% zoom. Art-directed images
may use `<picture>`; evidence screenshots scale without cropping. Decorative rails
recompose from vertical to horizontal instead of shrinking.

## 9. Agent Prompt Guide

### Quick Color Reference

- Canvas → `#0B1118`
- Primary surface → `#111A24`
- Raised surface → `#182431`
- Primary text → `#F3EEDF`
- Secondary text → `#B9B6AA`
- Active/primary → `#EFB45F`
- Provisional/warning → `#E47B6C`
- Secondary channel → `#B8A3D9`
- Verified/success → `#78B69B`
- Focus ring → `#FFD38B`

### Example Component Prompts

- “Build a leaderboard row using flat `--surface-1`, tabular scores, an amber end-cap,
  explicit ES/EN and provisional labels, and no shadow or nested card.”
- “Build a run-detail evidence sheet on `--surface-inverse` with IBM Plex Sans body,
  IBM Plex Mono identifiers, 1px rules, and a visible human-review banner.”
- “Build a mission command bar with Results, Method, Run locally, GitHub, and Hugging
  Face; preserve all destinations in a horizontal mobile strip.”
- “Build a method diagram from solid segmented rails using amber, orchid, and coral;
  label every stage and provide an equivalent ordered list for screen readers.”
- “Build a filter group with asymmetric capsule controls, 44px targets, roving or
  native keyboard behavior, and the `#FFD38B` focus-visible ring.”

### Iteration Guide

1. Change one component family at a time and name the exact DESIGN.md token used.
2. Restate the no-gradient, no-glow, no-shadow rule during visual refinement.
3. Test hierarchy with the squint test, then test keyboard and 200% zoom.
4. Verify ES/EN separation and provisional labelling after every data-layout change.
5. Compare at 375px, 768px, 1024px, and 1440px before adding a breakpoint.
6. Check reduced motion and contrast before polishing animation or decoration.
