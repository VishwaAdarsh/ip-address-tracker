---
name: IP Pulse
colors:
  surface: '#0f131b'
  surface-dim: '#0f131b'
  surface-bright: '#353941'
  surface-container-lowest: '#0a0e15'
  surface-container-low: '#181c23'
  surface-container: '#1c2027'
  surface-container-high: '#262a32'
  surface-container-highest: '#31353d'
  on-surface: '#dfe2ed'
  on-surface-variant: '#bac9cc'
  inverse-surface: '#dfe2ed'
  inverse-on-surface: '#2d3038'
  outline: '#849396'
  outline-variant: '#3b494c'
  surface-tint: '#00daf3'
  primary: '#c3f5ff'
  on-primary: '#00363d'
  primary-container: '#00e5ff'
  on-primary-container: '#00626e'
  inverse-primary: '#006875'
  secondary: '#93ccff'
  on-secondary: '#003351'
  secondary-container: '#3198dc'
  on-secondary-container: '#002c47'
  tertiary: '#a8ffd2'
  on-tertiary: '#003824'
  tertiary-container: '#5be9ad'
  on-tertiary-container: '#006645'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#9cf0ff'
  primary-fixed-dim: '#00daf3'
  on-primary-fixed: '#001f24'
  on-primary-fixed-variant: '#004f58'
  secondary-fixed: '#cce5ff'
  secondary-fixed-dim: '#93ccff'
  on-secondary-fixed: '#001d31'
  on-secondary-fixed-variant: '#004b73'
  tertiary-fixed: '#6ffbbe'
  tertiary-fixed-dim: '#4edea3'
  on-tertiary-fixed: '#002113'
  on-tertiary-fixed-variant: '#005236'
  background: '#0f131b'
  on-background: '#dfe2ed'
  surface-variant: '#31353d'
typography:
  headline-xl:
    fontFamily: Space Grotesk
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-xl-mobile:
    fontFamily: Space Grotesk
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-lg:
    fontFamily: Space Grotesk
    fontSize: 22px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.015em
  headline-sm:
    fontFamily: Space Grotesk
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 22px
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Inter
    fontSize: 15px
    fontWeight: '400'
    lineHeight: 22px
  body-md:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  telemetry-display:
    fontFamily: JetBrains Mono
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 32px
    letterSpacing: -0.03em
  telemetry-metric:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 18px
    letterSpacing: -0.02em
  label-code:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
    letterSpacing: 0.02em
  label-caps:
    fontFamily: Inter
    fontSize: 10px
    fontWeight: '700'
    lineHeight: 12px
    letterSpacing: 0.06em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 12px
  gutter-desktop: 16px
  margin: 16px
  margin-desktop: 24px
  space-xs: 4px
  space-sm: 8px
  space-md: 12px
  space-lg: 16px
  space-xl: 24px
  space-2xl: 32px
---

## Brand & Style

This design system establishes an ultra-precise, mission-critical operations aesthetic bridging high-fidelity cybersecurity intelligence with financial-terminal analytical density. It serves network engineers, SecOps analysts, and infrastructure architects monitoring global routing tables, ASN telemetry, and threat surfaces in real time.

The design movement synthesizes **Modern Technical Minimalism** with **Tactile Instrumentalism**:
- Deep, light-absorbing obsidian foundations that mitigate eye fatigue during protracted 24/7 monitoring cycles.
- Hairline structural framing (1px precision borders) delineating modular metric arrays and multi-tenant telemetry panels.
- Highly purposeful chromatic luminescence: vivid electric cyan highlights critical network conduits, while tactical status indicators (emerald, amber, crimson) command rapid cognitive triage without ambient visual noise.
- Laser-focused data density, offering immediate scanability through monospaced telemetry figures, micro-pill indicators, and strictly budgeted elevation planes.

## Colors

The palette operates under a strict dark-mode-first taxonomy optimized for high-contrast legible instrumentation.

### Palette Architecture
- **Primary Conduits (`#00E5FF` & `#0284C7`):** Electric Cyan functions as the primary visual beacon for active selections, focused network traces, primary metrics, and acute telemetry triggers. Sky Blue provides supporting depth for secondary interactions and structural breadcrumbs.
- **Verification & Health (`#10B981`):** Emerald denotes verified BGP announcements, secure DNSSEC chains, pristine latency targets, and certified clean upstream providers.
- **Alert States (`#F59E0B` & `#EF4444`):** Amber captures latency jitter, stale route propagation, and degraded edge nodes. Crimson indicates BGP hijacks, RPKI invalid states, DDoS saturation, and immediate critical anomalies.
- **Foundational Neutrals (`#090D14`, `#0F172A`, `#131F33`, `#1E293B`):** 
  - Canvas Root: `#090D14`
  - Layer 1 Panel Surface: `#0F172A`
  - Layer 2 Raised Tile / Popover: `#131F33`
  - Structural Divider / Border: `#1E293B`
  - Data Dimmed Text: `#64748B`
  - High-Contrast Terminal Text: `#F8FAFC`

## Typography

The typographic hierarchy distinguishes operational narratives from technical data streams through a dual-engine font pairing.

- **Primary Interface (Inter):** Applied across global structural elements, alerts, descriptions, and interaction labels. Chosen for optical clarity at low micro-scales (`12px`-`13px`) against ultra-dark backdrops.
- **Structural Display (Space Grotesk):** Anchors module titles, panel headers, and intelligence summaries with an engineered, low-contrast geometric form.
- **Telemetry & Infrastructure Notation (JetBrains Mono):** Dedicated to all network-specific values: IPv4/IPv6 blocks, Autonomous System Numbers (e.g., `AS13335`), CIDR notations, round-trip times (`ms`), packet losses, and hex payloads. Zero-ambiguity glyphs (slashed zeros, clear l/1/I separations) prevent operational oversight.
- **Tabular Alignment:** All numerical listings utilize `font-feature-settings: "tnum" 1` to guarantee vertical decimal and digit alignment across dynamic table updates.

## Layout & Spacing

The layout model favors dense, spatial efficiency reminiscent of high-frequency trading terminals, while preserving explicit visual separation between autonomous monitoring modules.

### Grid Engine
- **Desktop (≥ 1440px):** 16-column flexible layout with a persistent 64px collapsed/expanded system utility rail. Gutter: `16px`. Outer canvas margin: `24px`.
- **Medium Screens / Tablet (768px - 1439px):** 8-column layout with a horizontal sub-navigation bar replacing vertical rails. Gutter: `12px`. Outer margin: `16px`.
- **Mobile Handheld (< 768px):** 4-column single-stack flow. Metrics panels convert to horizontally swiping telemetry strips with sticky top-level severity summaries. Margin: `12px`.

### Density Controls
- **Internal Card & Module Padding:** Default to compact boundaries (`space-md` / 12px) to maximize above-the-fold telemetry density.
- **Table Row Ergonomics:** Table cells enforce an explicit vertical height of `32px` (dense) or `40px` (standard), paired with `space-sm` inline gap spacing for status badges and mono IP nodes.

## Elevation & Depth

Visual depth avoids thick drop-shadows, which muddy dark screens. Depth is created through surface luminance tiering, subtle top-edge illumination, and tactical atmospheric glows.

- **Level 0 (Canvas Base):** Solid `#090D14`. Used exclusively for application viewport backdrops and inactive canvas real-estate.
- **Level 1 (Card & Module Shells):** Tinted obsidian `#0F172A` bordered with 1px solid `#1E293B`. Top border features an optional subtle inset highlight (`inset 0 1px 0 0 rgba(255, 255, 255, 0.05)`).
- **Level 2 (Active Inspections / Flyouts / Drawers):** Raised charcoal `#131F33` with backdrop-filter blur (`backdrop-filter: blur(12px)` when layered over network graphs). Outline stays sharp: 1px `#334155`.
- **Level 3 (Modals / Emergency Overlays):** `#0F172A` with a high-contrast boundary (`#00E5FF` at 30% alpha) supported by an ambient drop shadow: `0 16px 32px -8px rgba(0, 0, 0, 0.75)`.
- **Conduit Glows:** Critical anomaly indicators and active traceroute paths implement a targeted luminescent blur: `box-shadow: 0 0 12px rgba(0, 229, 255, 0.25)` for primary status, and `0 0 12px rgba(239, 68, 68, 0.35)` for severe outage events. Ambient glows must never exceed a 16px spread radius.

## Shapes

The design system uses a controlled **Soft-Technical** shape language (roundedness scale `1`), reinforcing industrial precision:

- **Metric Cards, Modals, Panels, and Viewports:** `rounded-sm` (4px) to `rounded-md` (6px). Corners are clipped crisp to maximize viewport real estate and echo server rack equipment hardware.
- **Buttons, Segmented Switchers, & Inputs:** Strict 4px radius (`0.25rem`). Maintains functional clarity across data-entry forms and ASN search filters.
- **Telemetry Chips & Badges:** Distinct pill-shaped perimeter (`rounded-full` / 9999px) applied to network state indicators, IP tags, and severity badges to immediately isolate them from square structural components.

## Components

### Buttons
- **Primary Terminal Trigger:** Background solid `#00E5FF`, label `#090D14` (Inter bold 12px), radius 4px, height 32px. Hover: brightness(110%) with `0 0 8px rgba(0, 229, 255, 0.4)`. Focus: 2px offset cyan focus ring.
- **Secondary / Ghost Outline:** Background transparent, 1px border `#1E293B`, text `#F8FAFC`. Hover: border `#00E5FF`, text `#00E5FF`, background `rgba(0, 229, 255, 0.04)`.
- **Destructive Action:** Background `rgba(239, 68, 68, 0.1)`, 1px border `#EF4444`, text `#EF4444`. Hover: background `#EF4444`, text `#FFFFFF`.

### Analytical Metric Cards
- Base surface `#0F172A` wrapped in 1px `#1E293B`.
- Header: micro uppercase `label-caps` in `#64748B` accompanied by a pulsing status indicator (green/amber/red).
- Center: `telemetry-display` in `#F8FAFC` paired with a miniature sparkline or delta pill (`+12.4ms` in `#EF4444` or `-4.2%` in `#10B981`).
- Footer: contextual subline in `label-code` citing authoritative upstream collectors.

### Status Chips & Badges
- Pill geometry (`rounded-full`), height 20px, inline padding 8px.
- **Verified / Clean:** Background `rgba(16, 185, 129, 0.1)`, border `1px solid rgba(16, 185, 129, 0.3)`, text `#10B981`, font `label-code`.
- **Warning / Degraded:** Background `rgba(245, 158, 11, 0.1)`, border `1px solid rgba(245, 158, 11, 0.3)`, text `#F59E0B`, font `label-code`.
- **High Risk / Critical:** Background `rgba(239, 68, 68, 0.15)`, border `1px solid rgba(239, 68, 68, 0.5)`, text `#EF4444`, font `label-code`, accompanied by a solid 4px dot indicator.

### Input Fields & Global Filters
- Height 36px. Background `#090D14`, border 1px solid `#1E293B`, text `#F8FAFC`, font `label-code`.
- Left-adorned with search, CIDR, or protocol icons in `#64748B`.
- Focus state: border `#00E5FF`, subtle box-shadow `0 0 0 1px #00E5FF`, background `#0F172A`.
- Clear/reset trigger embedded on the far right using hotkey notation (`[ESC]`, `[⌘K]`) styled with `label-code` at 9px.

### Data Tables & Stream Lists
- Header: height 28px, background `#090D14`, text `#64748B`, uppercase 10px tracking.
- Row: height 36px, alternate row background `#0F172A` and `rgba(15, 23, 42, 0.5)`, border-bottom 1px solid `#1E293B`.
- Hover state: background `#131F33` with an accent 2px vertical indicator on the far-left border in `#00E5FF`.

### Checkboxes & Radio Selectors
- Checkbox: 14px × 14px, 2px radius, border 1px solid `#334155`, background `#090D14`. Checked: background `#00E5FF`, border `#00E5FF`, checkmark icon in `#090D14`.
- Radio: 14px outer circle, border 1px solid `#334155`. Selected: border `#00E5FF`, center dot 6px `#00E5FF`.

### Specialized IP Pulse Elements
- **BGP AS Path Visualizer:** Node links rendered with 1px SVG arcs in `#1E293B`, transitions illuminated in `#00E5FF` when inspecting route hops, with intermediary IXP nodes tagged via 18px height mini-chips.
- **Raw Hex / Packet Stream Viewer:** Inset dark panel (`#05080E`) with an explicit monospace 11px font, gutter line numbering in `#334155`, and syntax-highlighted payload segments using cyan, emerald, and crimson.