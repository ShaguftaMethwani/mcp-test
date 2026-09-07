---
name: Studio Intelligence & MCP Architecture
colors:
  surface: '#0b1326'
  surface-dim: '#0b1326'
  surface-bright: '#31394d'
  surface-container-lowest: '#060e20'
  surface-container-low: '#131b2e'
  surface-container: '#171f33'
  surface-container-high: '#222a3d'
  surface-container-highest: '#2d3449'
  on-surface: '#dae2fd'
  on-surface-variant: '#c7c4d7'
  inverse-surface: '#dae2fd'
  inverse-on-surface: '#283044'
  outline: '#908fa0'
  outline-variant: '#464554'
  surface-tint: '#c0c1ff'
  primary: '#c0c1ff'
  on-primary: '#1000a9'
  primary-container: '#8083ff'
  on-primary-container: '#0d0096'
  inverse-primary: '#494bd6'
  secondary: '#d0bcff'
  on-secondary: '#3c0091'
  secondary-container: '#571bc1'
  on-secondary-container: '#c4abff'
  tertiary: '#4edea3'
  on-tertiary: '#003824'
  tertiary-container: '#00885d'
  on-tertiary-container: '#000703'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#e1e0ff'
  primary-fixed-dim: '#c0c1ff'
  on-primary-fixed: '#07006c'
  on-primary-fixed-variant: '#2f2ebe'
  secondary-fixed: '#e9ddff'
  secondary-fixed-dim: '#d0bcff'
  on-secondary-fixed: '#23005c'
  on-secondary-fixed-variant: '#5516be'
  tertiary-fixed: '#6ffbbe'
  tertiary-fixed-dim: '#4edea3'
  on-tertiary-fixed: '#002113'
  on-tertiary-fixed-variant: '#005236'
  background: '#0b1326'
  on-background: '#dae2fd'
  surface-variant: '#2d3449'
typography:
  display-hero:
    fontFamily: Plus Jakarta Sans
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
    letterSpacing: -0.025em
  display-hero-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
    letterSpacing: -0.02em
  headline-xl:
    fontFamily: Plus Jakarta Sans
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 22px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.015em
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Geist
    fontSize: 15px
    fontWeight: '400'
    lineHeight: 24px
    letterSpacing: -0.005em
  body-md:
    fontFamily: Geist
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 20px
    letterSpacing: 0em
  body-sm:
    fontFamily: Geist
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 18px
    letterSpacing: 0.005em
  label-md:
    fontFamily: Geist
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Geist
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 14px
    letterSpacing: 0.04em
  code-md:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 18px
    letterSpacing: 0em
  code-sm:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '400'
    lineHeight: 16px
    letterSpacing: 0em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  layout-margin-desktop: 1.5rem
  layout-margin-tablet: 1rem
  layout-margin-mobile: 0.75rem
  panel-gutter: 0.75rem
  stack-xxs: 0.125rem
  stack-xs: 0.25rem
  stack-sm: 0.5rem
  stack-md: 0.75rem
  stack-lg: 1rem
  stack-xl: 1.5rem
  stack-2xl: 2rem
  stack-3xl: 3rem
---

## Brand & Style

The design system projects precision, engineering rigor, and deep algorithmic clarity. Tailored for enterprise product managers, AI engineers, and technical support leads navigating high-throughput intelligence pipelines and Model Context Protocol (MCP) toolchains, the aesthetic combines the high-density utility of Linear and Retool with the restrained editorial luxury of Stripe and Claude Workbench.

The emotional signature is focused, decisive, and calm under high data volume. Every surface serves comprehension: translucent backing surfaces minimize visual weight, razor-sharp 1px micro-borders establish distinct functional enclosures, and luminous violet/indigo accents delineate AI synthesis and automated action states from static human records.

### Visual Style Characteristics
- **Studio Glass & Precision Tones:** Deep slate-zinc foundations layered with semi-transparent surfaces (`backdrop-blur-md`) that anchor multi-pane operational workspaces without visual heaviness.
- **Architectural Micro-Borders:** 1px borders with controlled alpha channels create clean boundary contrast without heavy containment outlines.
- **Computational Luster:** Targeted luminous radial flares and indigo edge highlights signify active agent computation, MCP payload execution, and synthesis streaming.
- **Utilitarian Balance:** Geometric display headings paired with high-legibility sans body typography and strict tabular monospace data arrays for token streams, latency meters, and JSON RPC schemas.

## Colors

The color architecture is optimized for sustained focus in high-density, multi-pane dark workspaces. The foundation utilizes deep slate-zinc neutral scales, ensuring pure contrast without harsh ocular fatigue.

### Palette Architecture
- **Primary Indigo (`#6366F1`) & Electric Violet (`#8B5CF6`):** The operational core. Indigo governs primary state changes, execution triggers, active pipeline nodes, and MCP transport connections. Electric Violet designates generative AI synthesis, LLM stream markers, and autonomous query orchestration.
- **Emerald Functional (`#10B981`):** Applied exclusively to deterministic verification: automated approval thresholds, verified MCP tools, healthy pipeline latency, and resolved ticket resolutions.
- **Amber Warning (`#F59E0B`):** Flags friction signals: customer fee confusion anomalies, churn-risk sentiments, context-window saturation, and MCP rate limits.
- **Rose Destructive (`#F43F5E`):** Reserved for agent execution halts, tool invocation failures, unhandled exceptions, and critical sentiment dips.
- **Base Surfaces (`#0F172A`, `#0B0F19`, `#020617`):** Scaled depth tiers ranging from deep workspace canvas (`#020617`) to elevated workbench panels (`#0B0F19`) and inspect flyouts (`#0F172A`).
- **Micro-Border Alpha:** Surfaces utilize dynamic border states (`rgba(255, 255, 255, 0.08)` to `rgba(99, 102, 241, 0.35)`) to communicate panel focus without introducing opaque layout friction.

## Typography

Typography establishes an uncompromising hierarchy between structural navigation, AI synthesis summaries, and low-level execution payloads.

- **Headlines (Plus Jakarta Sans):** Geometric clarity with refined letter spacing. Scaled for clean section delineation in workbench dashboards, contextual sheets, and pipeline headers.
- **Body & Controls (Geist):** Neutral, technical, and engineered for dense SaaS information density. Highly legible at 12px and 13px across complex data grids and multi-turn agent logs.
- **Telemetry & Payload Code (JetBrains Mono):** Dedicated to MCP JSON-RPC statements, tool schemas, token usage counters, and latency measurements. Ensures strict column alignment in side-by-side verification consoles.

## Layout & Spacing

The structural layout uses a responsive dual-pane and three-pane studio layout model based on a strict 4px/8px modular scale.

### Workbench Architecture
- **Primary Canvas Grid:** Fixed collapsible left rail (navigation and pipelines, 240px default / 64px collapsed), fluid central execution workbench (minimum 540px), and an interactive inspect/debug rail (380px default) on desktop displays (≥ 1280px).
- **Responsive Adaptations:**
  - **Desktop (≥ 1280px):** Multi-pane split view active. Center workbench and inspect drawer sit side-by-side with synchronized scrolling.
  - **Tablet (768px - 1279px):** Central workbench occupies dominant view. The inspect drawer shifts into a slide-over sheet anchored right. Left rail auto-collapses into an icon-only dock.
  - **Mobile (< 768px):** Single vertical stream. Pipeline steps convert to a horizontal scroll pill-track. Panels stack sequentially with top app bar navigation and bottom contextual toolbars.
- **Rhythm & Padding:** Layout containers adopt internal 16px (`stack-lg`) or 20px padding with 12px (`panel-gutter`) separation between discrete floating cards.

## Elevation & Depth

Depth is established through calibrated dark tonal tiers, micro-borders, and diffused ambient indigo light cones rather than heavy, muddy drop shadows.

### Surface Tiers
- **Tier 0 (Root Void - `#020617`):** The global backdrop beneath all floating viewports.
- **Tier 1 (Base Panel - `#0B0F19` with 90% opacity & `backdrop-blur-md`):** Main content areas, table shells, and pipeline tracks. Framed by a 1px border of `rgba(255, 255, 255, 0.06)`.
- **Tier 2 (Interactive Modules & Cards - `#111827`):** Context modules, prompt editors, and payload containers. Outlined by `rgba(255, 255, 255, 0.1)`. Ambient shadow: `0 4px 20px -2px rgba(0, 0, 0, 0.5)`.
- **Tier 3 (Modals, Context Sheets, Floating Command Menus - `#1E293B`):** High-level overlays. Bordered by `rgba(99, 102, 241, 0.25)`. Ambient shadow: `0 12px 36px -4px rgba(0, 0, 0, 0.7), 0 0 24px -2px rgba(99, 102, 241, 0.15)`.

### Intelligence Glow
When an agent or MCP workflow node is actively computing, the container border transitions dynamically from neutral white-alpha to a 1px ring of `rgba(99, 102, 241, 0.6)` paired with a soft internal gradient wash (`radial-gradient(ellipse at top, rgba(99, 102, 241, 0.12), transparent 70%)`).

## Shapes

The design system employs **Level 2 (Rounded)** curvature. This geometry provides an architectural, tool-grade feel: crisp enough to convey mathematical precision, yet smoothed at intersections to avoid brutalist edge fatigue.

### Corner Radii Guidelines
- **Base Components (Inputs, Buttons, Badges, Tabs):** `0.5rem` (`rounded-md` / 8px). Delivers compact, tactile interaction targets.
- **Structural Containers (Workflow Cards, Data Tables, Payload Blocks):** `1rem` (`rounded-lg` / 16px). Creates clear grouping boundaries for complex internal layouts.
- **Overlay Shells (Sheets, Flyouts, Large Dialogs):** `1.5rem` (`rounded-xl` / 24px). Softens dominant edge intersections on viewport perimeters.
- **Micro-Pills (Status Indicators, Filter Tags, MCP Method Badges):** Standardized pill rounding (`9999px`) reserved purely for compact state tags.

## Components

### Buttons & Actions
- **Primary Studio Button:** Solid `#6366F1` background, white text (`Geist` 13px weight 500), `rounded-md` (8px). Subtle top highlight border (`inset 0 1px 0 rgba(255, 255, 255, 0.25)`) and hover transition to `#4F46E5`.
- **Secondary / Ghost Button:** Transparent background, `rgba(255, 255, 255, 0.08)` border, text `#E2E8F0`. On hover: surface transitions to `rgba(255, 255, 255, 0.05)` with `rgba(255, 255, 255, 0.16)` border.
- **Tool / MCP Action Button:** High-density 28px height, `JetBrains Mono` 11px label, subtle indigo tint for agent-triggered operations.

### Data Inputs & Code Editors
- **Text & Prompt Fields:** Surface `#090D16`, 1px border `rgba(255, 255, 255, 0.08)`, text `#F8FAFC`. Active focus states apply an electric violet glow ring (`0 0 0 1px #6366F1`, `0 0 12px rgba(99, 102, 241, 0.25)`).
- **JSON / Code Editor Panes:** Embedded background `#030712`, inset micro-borders, with syntax highlighting optimized for prompt tokens, variable chips, and JSON-RPC method arguments.

### Pipeline Nodes & Stepper Visualizations
- **Pipeline Edge Connections:** 1.5px orthogonal path lines tinted `rgba(255, 255, 255, 0.12)`. When active, animated stroke dashes move along the vector path in `#6366F1`.
- **Node Cards:** Surface `#0F172A`, 8px padding, containing node icon, node title, execution duration (`JetBrains Mono`), and state badge (Pending, Active, Verified, Blocked).

### Status Chips & Badges
- **Approval / Healthy:** Background `rgba(16, 185, 129, 0.1)`, text `#34D399`, border `1px solid rgba(16, 185, 129, 0.2)`.
- **Alert / Anomaly:** Background `rgba(245, 158, 11, 0.1)`, text `#FBBF24`, border `1px solid rgba(245, 158, 11, 0.2)`.
- **Agent Active:** Background `rgba(99, 102, 241, 0.12)`, text `#A5B4FC`, border `1px solid rgba(99, 102, 241, 0.3)`.

### Cards & Flyout Drawers
- **Studio Cards:** Multi-layer zinc backdrop with header divider border (`1px solid rgba(255, 255, 255, 0.06)`). Contextual actions grouped top-right in segmented button bars.
- **Dual-Pane Splitter:** Drag handles are minimal 1px visual seams with centered 4-dot grips that illuminate violet on hover.