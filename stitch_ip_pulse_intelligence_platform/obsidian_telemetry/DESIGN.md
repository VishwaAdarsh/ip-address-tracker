---
name: Obsidian Telemetry
colors:
  surface: '#0f131c'
  surface-dim: '#0f131c'
  surface-bright: '#353942'
  surface-container-lowest: '#0a0e16'
  surface-container-low: '#181c24'
  surface-container: '#1c2028'
  surface-container-high: '#262a33'
  surface-container-highest: '#31353e'
  on-surface: '#dfe2ee'
  on-surface-variant: '#bbc9cf'
  inverse-surface: '#dfe2ee'
  inverse-on-surface: '#2c3039'
  outline: '#859399'
  outline-variant: '#3c494e'
  surface-tint: '#47d6ff'
  primary: '#a5e7ff'
  on-primary: '#003543'
  primary-container: '#00d2ff'
  on-primary-container: '#00566a'
  inverse-primary: '#00677f'
  secondary: '#7bd0ff'
  on-secondary: '#00354a'
  secondary-container: '#00a6e0'
  on-secondary-container: '#00374d'
  tertiary: '#69f6b9'
  on-tertiary: '#003824'
  tertiary-container: '#48d99e'
  on-tertiary-container: '#005b3d'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#b6ebff'
  primary-fixed-dim: '#47d6ff'
  on-primary-fixed: '#001f28'
  on-primary-fixed-variant: '#004e60'
  secondary-fixed: '#c4e7ff'
  secondary-fixed-dim: '#7bd0ff'
  on-secondary-fixed: '#001e2c'
  on-secondary-fixed-variant: '#004c69'
  tertiary-fixed: '#6ffbbe'
  tertiary-fixed-dim: '#4edea3'
  on-tertiary-fixed: '#002113'
  on-tertiary-fixed-variant: '#005236'
  background: '#0f131c'
  on-background: '#dfe2ee'
  surface-variant: '#31353e'
typography:
  display-lg:
    fontFamily: Space Grotesk
    fontSize: 48px
    fontWeight: '600'
    lineHeight: 56px
    letterSpacing: -0.03em
  display-lg-mobile:
    fontFamily: Space Grotesk
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Space Grotesk
    fontSize: 32px
    fontWeight: '500'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Space Grotesk
    fontSize: 24px
    fontWeight: '500'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Space Grotesk
    fontSize: 24px
    fontWeight: '500'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Space Grotesk
    fontSize: 18px
    fontWeight: '500'
    lineHeight: 26px
    letterSpacing: 0em
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 26px
    letterSpacing: -0.01em
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 22px
    letterSpacing: 0em
  body-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
    letterSpacing: 0.01em
  label-data-lg:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.02em
  label-data-md:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
    letterSpacing: 0.03em
  label-ui:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.02em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1.5rem
  gutter-mobile: 1rem
  margin: 3rem
  margin-mobile: 1.25rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style

This design system expresses a state of calm authority, precision, and architectural purity for deep-tier internet infrastructure and cybersecurity intelligence. It rejects the hyper-dense, chaotic terminal overload typical of legacy SOC interfaces in favor of a quiet, executive-grade analytical clarity: "Less information, better presentation."

### Brand Persona & Tone
- **Sovereign & Quiet:** Unhurried, deliberate, and free of panic-inducing noise. It frames complex network telemetry into crystalline, actionable insights.
- **Architectural Precision:** Every coordinate, Autonomous System Number (ASN), and CIDR block is rendered with scientific rigor and pristine visual weight.
- **Target Audience:** Principal network engineers, CISOs, threat intelligence researchers, and infrastructure architects who value rapid signal over dense noise.

### Design Movement: Dark-Mode Spatial Minimalism
The aesthetic bridges spatial depth and pure geometric minimalism. Monochromatic dark obsidian planes sit in spatial layers, punctuated by precise hairline strokes and a singular, electric cyan signal light. Surfaces do not shout; they quietly support data hierarchy via subtle luminance steps, tactile glass blurs, and expansive breathing room.

## Colors

The palette is anchored by impenetrable void tones, illuminated strictly by high-frequency signal beams. High-contrast white and muted slate create an effortless typographical hierarchy, while semantic status colors are applied with clinical discipline.

### Palette Architecture
- **Canvas & Surface Base:** Deep obsidian navy (`#0b0f17`) for base canvas backgrounds, rising to slate-infused obsidian (`#0f1420`) for elevated card planes and navigation docks.
- **Primary Signal (`#00d2ff`):** Electric Cyan. Reserved for active network states, focused elements, and primary call-to-action interactions. Carries an aura glow in active states.
- **Secondary Telemetry (`#38bdf8`):** Sky Blue. Used for secondary active controls, selected filters, interactive hover transitions, and telemetry metrics.
- **Neutral Structure:**
  - `Primary Text`: `#f8fafc` (Pure crisp white with faint slate undertone; maximum legibility).
  - `Secondary/Muted Text`: `#94a3b8` (Balanced slate gray; secondary labels, metadata, and inactive icons).
  - `Borders & Rules`: `#1e2638` (Structural borders) and `rgba(255, 255, 255, 0.07)` (Interior hairline separators).
- **Functional Semantics (Minimal Dosage):**
  - `Safe / Verified`: `#10b981` (Emerald green).
  - `Attention / Warning`: `#f59e0b` (Warm amber).
  - `Critical / Threat`: `#ef4444` (Vivid crimson).
  *Rule of use:* Semantic hues must never dominate card backgrounds; they appear strictly as hairline indicator pips, pill labels, or micro-graphs.

## Typography

The typographic system creates an intentional friction between humanist geometric display forms and unyielding machine precision.

### Typographic Hierarchy & Roles
- **Headings & Key Metrics (`Space Grotesk`):** Delivers a technical yet modern geometric cadence. Used for page titles, high-level metrics, and section headers. High-range tracking is slightly compressed to preserve density.
- **Product Body & Descriptions (`Inter`):** Handles all standard UI language, long-form threat analysis, explanatory tooltips, and system notifications. Ensures maximum legibility across extended viewing sessions.
- **Machine Telemetry & Network Identity (`JetBrains Mono`):** Strictly quarantined to infrastructure representations. This includes IPv4/IPv6 addresses, CIDR notation blocks, ASN tags, DNS record types, geographic coordinates, and cryptographic hashes. Never use monospaced fonts for narrative explanations or standard button labels.

## Layout & Spacing

The spatial philosophy is founded on intentional roominess and structural discipline. We eliminate cognitive fatigue by separating metric panels with deliberate breathing room rather than boxing every visual artifact into tight borders.

### Grid Architecture
- **Desktop (1200px+):** 12-column fluid grid system with `1.5rem` (24px) gutters and generous `3rem` (48px) canvas margins. Maximum container width caps at `1440px` to maintain focused visual scanning.
- **Tablet (768px – 1199px):** 8-column layout with `1.25rem` (20px) gutters and `2rem` (32px) margins.
- **Mobile (Up to 767px):** 4-column layout with `1rem` (16px) gutters and `1.25rem` (20px) safe-area outer margins. Complex data rows reflow into vertical, expandable card structures.

### Spacing Principles
- Never pack data clusters tightly against card perimeters. Internal card padding strictly enforces `space-lg` (24px) on desktop to guarantee an airy, pristine framing.
- Macro spacing between distinct intelligence modules relies on `space-xl` (40px) to make visual transitions obvious without needing heavy divider lines.

## Elevation & Depth

Visual hierarchy relies on structural luminance and ethereal light dissipation rather than physical drop shadows.

### Surface Tiers
- **Layer 0 (Infinite Canvas):** Deepest ground (`#0b0f17`). The foundational void behind all components.
- **Layer 1 (Card & Module Ground):** `#0f1420` paired with an ultra-fine border (`1px solid #1e2638`).
- **Layer 2 (Floating Modals, Flyouts & Menus):** Semi-transparent `#131b2c` combined with `backdrop-filter: blur(16px)` and an internal hairline border of `rgba(255, 255, 255, 0.08)`.

### Ambient Shadow & Glow
- **Quiet Depth:** `0 8px 32px -4px rgba(0, 0, 0, 0.45)`. Ambient, wide-spread, non-directional darkness for layered floating panels.
- **Signal Focus Ring:** Active interactive elements, focused inputs, and targeted network nodes cast an ambient cyan glow: `0 0 20px -2px rgba(0, 210, 255, 0.18)`. This mimics an energized optical display panel.

## Shapes

The design system standardizes on moderate, tailored radii to humanize technical content without turning playful or soft.

### Geometry Rules
- **Base Components (Inputs, Buttons, Chips):** `0.5rem` (8px) provides crisp architectural framing.
- **Surface Panels & Intelligence Cards:** `0.75rem` (12px) to `1rem` (16px) establishes clean, modern card boundaries (`rounded-lg` / `rounded-xl`).
- **Status Indicators & Micro-Chips:** Pill-shaped (`9999px`) purely for binary status dots, threat tags, and telemetry badges to contrast sharply with squared data modules.

## Components

### Buttons
- **Primary Signal Button:** Solid electric cyan (`#00d2ff`) background with deep obsidian (`#0b0f17`) bold text. Hover introduces a soft cyan bloom (`0 0 16px rgba(0, 210, 255, 0.35)`) and slight brightness shift.
- **Secondary Ghost Button:** Transparent background, `1px solid #1e2638`, with `#f8fafc` text. On hover: border transitions to `rgba(255, 255, 255, 0.2)` with an inner wash of `rgba(255, 255, 255, 0.03)`.
- **Destructive Action:** Low-saturation dark crimson background wash (`rgba(239, 68, 68, 0.12)`) with `#ef4444` border and text.

### Inputs & Global Search Bar
- **Form Inputs & IP Lookups:** Deep background (`#0b0f17`), framed with `#1e2638`. Padding `0.75rem 1rem`. Monospaced text where IP/domain input is expected.
- **Focus State:** Hairline border turns to `#00d2ff`, supported by an outer ambient cyan glow ring (`box-shadow: 0 0 0 3px rgba(0, 210, 255, 0.15)`). Zero jarring jumps.
- **Integrated Actions:** Inline action icons (e.g., "Copy IP", "Inspect CIDR") sit in the right gutter in `#94a3b8`, illuminating to `#00d2ff` on interaction.

### Cards & Intelligence Containers
- **Visual Stance:** `#0f1420` background with `1px solid #1e2638`. Radius set to `12px` or `14px`. Generous internal padding (`1.5rem`).
- **Header Structure:** Clean title in `Space Grotesk` with metadata tags on the opposing edge. Content areas are separated by an airy `1.5rem` gap rather than dividing lines.

### Chips & Telemetry Badges
- **Status Tags:** Compact, pill-shaped tags (`font-family: JetBrains Mono`, `font-size: 12px`).
  - *Safe:* Emerald tint (`rgba(16, 185, 129, 0.1)`) with `#10b981` text and dot indicator.
  - *Warning:* Amber tint (`rgba(245, 158, 11, 0.1)`) with `#f59e0b` text.
  - *High Risk:* Crimson tint (`rgba(239, 68, 68, 0.1)`) with `#ef4444` text.
- **Infrastructure Metadata Chips (ASN, Protocol):** Neutral `#131b2c` background, subtle `#1e2638` border, and `#94a3b8` monospaced text.

### Progressive Disclosure Accordions
- **Header:** Clean trigger row featuring asset titles, IP targets, and risk scores. An outline chevron indicator rotates 180 degrees smoothly on expand.
- **Content Panel:** Expands downward seamlessly over 200ms using an ease-out curve. Sub-telemetry data is cleanly chunked into 2-column or 3-column micro-grids.

### Tab Bars
- **Navigation Tabs:** Borderless, minimalist horizontal tracks. The active tab is indicated by a sharp, glowing `#00d2ff` bottom indicator bar (2px height) and white text; inactive tabs rest in `#94a3b8` without visible boundaries.