# RasterScope Design System

## Direction

RasterScope is a remote-sensing light table translated into software. Satellite imagery is the working material; the interface behaves like a precise instrument around it. The visual world combines mineral paper, graphite annotations, map legends, acetate overlays, and restrained cartographic signals.

The product is an operational workbench, not a marketing dashboard. Dense information is acceptable when hierarchy stays explicit and the imagery remains dominant.

## Visual Principles

1. Image before chrome: the comparison stage receives the majority of the viewport.
2. Measurement before decoration: lines, labels, and color exist to explain evidence.
3. One signal at a time: green marks action and selection; amber marks uncertainty or caution.
4. Flat physicality: use rules, tonal steps, and typographic weight instead of floating cards.
5. Quiet confidence: no gradients, glass, glow, ornamental maps, or ambient animation.

## Composition

- Desktop shell: 80 px navigation rail, flexible comparison stage, 360–400 px analysis rail.
- Compact top toolbar aligns scenario, layer, opacity, and export controls.
- Comparison stage uses an image pair with a draggable vertical reveal and immediate overlay controls.
- Analysis rail is a continuous ruled column, not a stack of cards.
- Model Lab replaces the comparison stage with a metrics canvas and keeps the shell stable.
- At tablet widths, the analysis rail becomes a bottom sheet in document flow.
- At phone widths, the nav becomes a top bar, comparison becomes stacked, and the table gains a semantic compact view rather than horizontal page scrolling.

## Color

All implementation colors use OKLCH tokens.

- Paper: `oklch(97% 0.009 105)` — warm mineral near-white.
- Paper raised: `oklch(94% 0.012 105)`.
- Ink: `oklch(20% 0.012 135)` — green-tinted graphite.
- Secondary ink: `oklch(42% 0.012 135)`.
- Rule: `oklch(82% 0.012 115)`.
- Action: `oklch(48% 0.130 145)` — cartographic green.
- Focus: `oklch(56% 0.180 145)`.
- Warning: `oklch(64% 0.130 75)` — amber, reserved for uncertainty.
- Error: `oklch(52% 0.150 28)`.

Land-cover classes use a separate categorical palette. Every class is paired with a text label or pattern; color is never the only cue.

## Typography

- Display and UI headings: Manrope variable, upright, 700.
- Body and controls: Source Sans 3 variable, 400/600.
- Measurements and tables: IBM Plex Mono, 400/500, tabular numerals.
- Minimum body size is 16 px; compact labels never fall below 12 px and are not body copy.
- Headings use sentence case and never italics.

## Shape and Rules

- Radius scale: 0, 4, 8, and 12 px; most panels remain square or 4 px.
- Controls may use 6–8 px corners; pills are reserved for compact status filters.
- Use 1 px rules and one low-elevation shadow only for popovers.
- The draggable divider is a crisp rule with a 44 px accessible handle.

## Interaction

- Primary interactions: scenario selection, layer visibility, opacity, divider drag, pixel inspection, tab navigation, uploads, and report export.
- Controls implement default, hover, focus-visible, active, disabled, loading, error, and success states where applicable.
- Focus rings appear instantly with at least 3:1 contrast.
- Motion is limited to 120–220 ms opacity/transform changes. Divider movement directly follows input and is not eased.
- Reduced-motion mode removes spatial transitions.
- Successful export is acknowledged inline next to the action; errors explain recovery in place.

## Voice

Use short operational labels: “Compare dates”, “Show uncertainty”, “Inspect pixel”, “Export report”. Explain limitations directly. Avoid inflated AI language, certainty claims, and decorative technical jargon.

## Reference

The approved composition reference is `docs/design/rasterscope-ui-direction.png`. It is a quality bar only; its example geography and metrics must never ship as product evidence.

