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

All implementation colors use OKLCH tokens, and every surface token is defined twice: once for the
light scheme and once under `prefers-color-scheme: dark`. No rule in `styles.css` is scheme-specific.

Two things deliberately do not invert. The navigation rail owns `--color-chrome`, a separate pair, so
it stays dark in both schemes and keeps reading as chrome rather than as content. The divider between
the two images is a fixed near-white rule with a dark outer stroke, because it separates two
photographs and has to stay visible over both.

- Paper: `oklch(97% 0.009 105)` — warm mineral near-white.
- Paper raised: `oklch(94% 0.012 105)`.
- Ink: `oklch(20% 0.012 135)` — green-tinted graphite.
- Secondary ink: `oklch(42% 0.012 135)`.
- Rule: `oklch(82% 0.012 115)`.
- Action: `oklch(48% 0.130 145)` — cartographic green.
- Focus: `oklch(56% 0.180 145)`.
- Warning: `oklch(64% 0.130 75)` — amber, reserved for uncertainty.
- Error: `oklch(52% 0.150 28)`.

### Materials

Surfaces that float over imagery — the toolbar, the date badges, the divider handle and the pixel
readout — are translucent with `backdrop-filter`, so the working material keeps travelling under the
chrome instead of being cut off by an opaque strip. Everything else stays flat.

`prefers-reduced-transparency` and `prefers-contrast: more` resolve those materials to solid surfaces
at the token layer, so no component needs to know either setting exists.

Land-cover classes use a separate categorical palette. Every class is paired with a text label or pattern; color is never the only cue.

## Typography

- Tracking is size-specific, never one value across the scale: `-0.03em` at display size, `-0.022em`
  for page titles, `-0.014em` for section headings, `0` for body, `+0.02em` for micro labels. A fixed
  `letter-spacing` is wrong somewhere on the scale.
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
- Motion is limited to 90–220 ms opacity/transform changes. Feedback lands on pointer-down, not on
  release.
- Divider movement is written straight to a CSS custom property on the frame, so it tracks the
  pointer within the frame of the input rather than waiting for a render pass. It is 1:1 and not
  eased, it keeps the offset from wherever the handle was grabbed, and it clamps at the edges rather
  than projecting momentum — a scrub control has no snap points to be thrown towards.
- The one exception is the double-click recentre, which runs a critically damped spring
  (`frontend/src/lib/spring.ts`) rather than a CSS transition, because a transition cannot be grabbed
  mid-flight. Pressing the handle during the return stops the spring and continues from its live
  value.
- Reduced-motion mode removes spatial transitions and replaces them with short cross-fades.
- Successful export is acknowledged inline next to the action; errors explain recovery in place.

## Voice

Use short operational labels: “Compare dates”, “Show uncertainty”, “Inspect pixel”, “Export report”. Explain limitations directly. Avoid inflated AI language, certainty claims, and decorative technical jargon.

## Reference

The approved composition reference is `docs/design/rasterscope-ui-direction.png`. It is a quality bar only; its example geography and metrics must never ship as product evidence.

