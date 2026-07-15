# Kobayashi Research Dossier Design System

## 1. Visual Theme & Atmosphere

Kobayashi should feel like a serious benchmark paper made interactive: restrained,
editorial, dark, and inspectable. The information architecture may take cues from
research organizations such as ARC Prize—narrow reading measure, compact capsule
navigation, small categorical labels, strong tables—but must remain an original
composition with Kobayashi’s own language and identity.

The memorable element is the tension between a quiet scientific document and an
original deep-space research terminal. Its interface language uses sparse system
rails, instrument grids, clipped corners, and measured status colour. The logo may suggest a long-range starship,
but it must not reproduce a Star Trek vessel, Starfleet delta, franchise typeface,
registry number, or protected insignia.

Key characteristics:

- Near-black research canvas with warm off-white type.
- Narrow editorial reading column; wider evidence and leaderboard sections.
- Small mono labels and link lists; normal prose never defaults to monospace.
- Square data marks, thin rules, and compact technical readouts rather than ornamental chrome.
- Yellow indicates research navigation; red indicates provisional evidence.
- No fake telemetry: every technical readout must expose real protocol or result data.
- No glow, glass cards, decorative dashboards, or giant metrics.

## 2. Color Palette & Roles

| Token | Value | Role |
|---|---:|---|
| `--bg` | `#090A0B` | Main canvas; never pure black |
| `--surface` | `#111315` | Code, expanded prompts, quiet grouping |
| `--surface-raised` | `#17191C` | Hover and selected surfaces |
| `--text` | `#EDEDE8` | Primary warm near-white |
| `--paper` | `#D9D9D2` | Long-form evidence text |
| `--muted` | `#A2A39E` | Supporting copy |
| `--faint` | `#6E706D` | Metadata only |
| `--line` | `#2B2D30` | Standard rule |
| `--line-strong` | `#484B4F` | Interactive/section boundary |
| `--yellow` | `#F4C430` | Research category and active path |
| `--red` | `#EF5B4D` | Provisional, warning, review required |
| `--blue` | `#5D8CFF` | Logo mark only or selected data series |
| `--green` | `#54C98A` | Verified state only |
| `--focus` | `#FFDA5A` | 3px keyboard focus ring |

Use colour sparsely. A section gets one semantic accent, never a rainbow border.
Charts and diagrams must pair colour with text, shape, or position.

## 3. Typography Rules

- Space Grotesk is the body and display family, weights 400–700.
- IBM Plex Mono is reserved for IDs, prompts, settings, labels, commands, and data.
- Body copy is 16–17px with 1.6–1.7 line height and a maximum width near 47rem.
- Page titles use `clamp(3rem, 7vw, 5.7rem)`, weight 500, tight tracking.
- Section titles use `clamp(2rem, 4vw, 3.5rem)`, weight 500.
- Category labels are 10–12px mono uppercase with modest tracking.
- Never use all-caps for paragraphs or use monospace as a substitute for hierarchy.

## 4. Component Stylings

- Header: 80px, transparent near-black, thin bottom rule, compact wordmark.
- Wordmark: the original KM exploration-starship emblem plus the compact two-line
  name; the same mark anchors the hero, footer, favicon, and social preview.
- Segmented navigation: one thin outline, 4 equal sections, clipped terminal corners, no shadows.
- Links list: simple underlined mono links prefixed with a yellow chevron.
- Buttons: rare; rectangular or fully pill-shaped, minimum 44px target.
- Tables: collapsed rules, mono headers, left-aligned evidence, tabular numerals.
- Prompt disclosures: native `details/summary`, one rule per row, no card shell.
- Code: flat dark surface, 1px rule, mono type, horizontal scroll when required.
- Provisional notice: red label and red horizontal rules, always explanatory text.
- Logo: original KM/starship mark, readable at 32px, no franchise elements.

## 5. Layout Principles

- Global width: `min(100% - 2rem, 77rem)`.
- Reading width: 47rem.
- Evidence/leaderboard width: 68–77rem.
- Use a long vertical research-document flow, not dashboard tiles.
- Section spacing varies from 4rem to 7rem; related text stays tightly grouped.
- Heroes are informative document headers, not marketing splash screens.
- The leaderboard may break wider than prose but remains in the same reading flow.
- Exact prompts and judge instructions live on a dedicated protocol route.

## 6. Depth & Elevation

Depth comes from spacing, tone, and rules. Product surfaces use no box shadows.
The sticky header may use a restrained 12px backdrop blur solely to preserve
legibility over scrolling content. Expanded evidence may invert to a warm paper
surface. Never use glow, glassmorphism, floating panels, or layered card stacks.

## 7. Do's and Don'ts

Do:

- Lead with methodology and disclosure.
- Keep ES and EN scores separate.
- Show coverage, verification, judge agreement, and review rate beside scores.
- Publish exact prompt and judge text verbatim.
- Use native semantic HTML, visible focus, and 44px touch targets.
- Preserve an original KM identity even when taking layout cues from ARC Prize.

Do not:

- Copy ARC Prize code, logo, wording, task graphics, or exact page composition.
- Copy the Enterprise, Starfleet insignia, LCARS, registry numbers, or Trek fonts.
- Present provisional results as verified or as a general ethics score.
- Use cyan/purple AI gradients, gradient text, glow, or ornamental sparklines.
- Wrap every paragraph in a card or repeat giant number/stat blocks.
- Hide methodology, caveats, or critical controls on mobile.

## 8. Responsive Behavior

- At 52rem, header content stacks and navigation remains horizontally available.
- Capability rows become a single reading column; illustrations stay present.
- At 40rem, leaderboard rows become labelled two-column records.
- Protocol summaries keep ID, language, and suite visible without truncating access.
- Code blocks scroll horizontally; prose never creates page-level overflow.
- Tables remain scrollable when their meaning depends on columns.
- `prefers-reduced-motion` disables entrance and transition effects.

## 9. Agent Prompt Guide

When generating or editing Kobayashi UI, describe it as:

> An original dark research dossier for an auditable AI benchmark. Use a narrow
> editorial reading column, compact capsule navigation, mono evidence labels,
> warm off-white prose, thin rules, yellow research markers, red provisional
> markers, and wide transparent data tables. Pair it with an original KM
> long-range-starship emblem that does not reproduce any existing franchise asset.

Required checks before shipping:

1. Exact prompts and scoring rules match the Python protocol export.
2. Provisional and incomplete results are explicit.
3. Keyboard focus, contrast, mobile layout, and reduced motion are verified.
4. No protected Star Trek or ARC Prize brand asset has been copied.
5. The page reads like a research publication, not a generic AI dashboard.
