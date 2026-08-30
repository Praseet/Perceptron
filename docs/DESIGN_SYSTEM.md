# Fraud Model Frontend - Design System (2026)

> **Source of truth for all UI decisions.** A light-mode, data-dense design system inspired by Datadog, Stripe, and Notion.

---

## 1. Design Philosophy

**Professional SaaS dashboard for fraud analysts.** This is a tool users live in 8+ hours/day.

| Principle | What It Means | Reference |
|-----------|---------------|-----------|
| **Light Mode Default** | Clean white/gray surfaces, crisp hierarchy. Easy on eyes during long sessions. | Datadog, Stripe |
| **Data Density First** | Table layouts, compact metrics, information-rich. Not hero cards or marketing layouts. | Datadog, Elastic |
| **Functional Over Decorative** | Every pixel serves a purpose. Subtle shadows, restrained animations. | Stripe, Notion |
| **Professional Trust** | No AI-purple gradients or "edgy" aesthetics. Trust through clarity. | Stripe, PagerDuty |
| **Accessible Contrast** | WCAG AA minimum. Light mode requires more care with contrast ratios. | All platforms |

---

## 2. Color System

### 2.1 Core Palette

```css
/* Surfaces - White to subtle gray hierarchy */
--color-bg-base: #FFFFFF;     /* Card backgrounds, main surfaces */
--color-bg-subtle: #FAFBFC;   /* Page background */
--color-bg-muted: #F3F4F6;    /* Hover states, subtle fills */
--color-bg-hover: #E5E7EB;    /* Interactive hover */
--color-bg-active: #D1D5DB;   /* Active/pressed states */

/* Foreground - Crisp black hierarchy */
--color-fg-primary: #111827;   /* Headings, primary text */
--color-fg-secondary: #4B5563; /* Body text, labels */
--color-fg-muted: #9CA3AF;     /* Captions, placeholders */
--color-fg-disabled: #D1D5DB;  /* Disabled states */

/* Borders - Subtle, professional */
--color-border-default: #E5E7EB;  /* Default borders */
--color-border-strong: #D1D5DB;  /* Hover/focus borders */
--color-border-focus: #6366F1;    /* Focus rings */

/* Brand Accent - Deep Indigo */
--color-accent: #4F46E5;         /* Primary actions */
--color-accent-hover: #4338CA;   /* Hover state */
--color-accent-subtle: #EEF2FF;  /* Light accent backgrounds */
```

### 2.2 Risk Spectrum

| Level | Score | Color | Background |
|-------|-------|-------|------------|
| Critical | 90-100 | `#DC2626` | `#FEF2F2` |
| High | 70-89 | `#EA580C` | `#FFF7ED` |
| Medium | 40-69 | `#D97706` | `#FFFBEB` |
| Low | 10-39 | `#16A34A` | `#F0FDF4` |
| Minimal | 0-9 | `#2563EB` | `#EFF6FF` |

---

## 3. Typography

| Element | Size | Weight | Notes |
|---------|------|--------|-------|
| Page Title | 1.125rem (18px) | 600 | "text-lg font-semibold" |
| Section Title | 0.875rem (14px) | 600 | "text-sm font-semibold" |
| Body | 0.875rem (14px) | 400 | Default text |
| Caption | 0.75rem (12px) | 400 | Secondary info |
| Micro | 0.6875rem (11px) | 500 | Labels, badges |
| Monospace | Same sizes | 400 | IDs, code, amounts |

**Font Stack:** `"Inter", "SF Pro Display", system-ui, sans-serif`

---

## 4. Spacing & Radius

### Spacing Scale
```
xs: 4px    - Tight internal spacing
sm: 8px    - Component internal padding
md: 12px   - Default gaps
lg: 16px   - Section spacing
xl: 24px   - Major section gaps
```

### Border Radius
```
sm: 4px    - Badges, small elements
md: 6px    - Buttons, inputs
lg: 8px    - Cards, panels
```

---

## 5. Components

### 5.1 Cards

```html
<div class="card p-4">
  <!-- Content -->
</div>
```

- White background with subtle gray border
- 8px radius
- Optional hover effect: `card-hover`

### 5.2 Buttons

```html
<!-- Primary -->
<button class="btn btn-primary">Action</button>

<!-- Secondary -->
<button class="btn btn-secondary">Action</button>

<!-- Ghost -->
<button class="btn btn-ghost">Action</button>

<!-- Sizes -->
<button class="btn btn-sm">Small</button>
<button class="btn btn-lg">Large</button>
```

### 5.3 Risk Badges

```html
<!-- Score badge -->
<span class="badge" style="background: var(--color-risk-critical-bg); color: var(--color-risk-critical)">
  <span class="w-1.5 h-1.5 rounded-full" style="background: var(--color-risk-critical)"></span>
  87
</span>
```

### 5.4 Tables

```html
<table class="w-full">
  <thead>
    <tr class="border-b border-[var(--color-border-default)]">
      <th class="table-header table-cell text-left">Column</th>
    </tr>
  </thead>
  <tbody>
    <tr class="table-border-bottom table-row-hover">
      <td class="table-cell">Data</td>
    </tr>
  </tbody>
</table>
```

---

## 6. Layout System

### Page Structure
- **Sidebar:** 240px fixed width
- **Header:** 56px height
- **Content padding:** 24px horizontal, 20px vertical
- **Card gap:** 16-24px

### Grid
```html
<div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
  <div class="lg:col-span-8">Main content (table)</div>
  <div class="lg:col-span-4">Sidebar (stats)</div>
</div>
```

---

## 7. Animations

### Timing
| Duration | Use Case |
|----------|----------|
| 150ms | Micro-interactions (hover) |
| 200ms | Standard transitions |
| 250ms | Entrance animations |

### Utilities
```css
.animate-fade-in-up { animation: fadeInUp 250ms ease-out forwards; }
.stagger-in > * { animation: fadeInUp 300ms ease-out backwards; }
```

---

## 8. Accessibility

| Requirement | Implementation |
|-------------|---------------|
| WCAG AA Contrast | All text = 4.5:1 minimum |
| Focus Visible | 2px `--color-accent` outline |
| Reduced Motion | `@media (prefers-reduced-motion: reduce)` |
| Color Independence | Risk badges always include text or icon |

---

## 9. Anti-Patterns

| Avoid | Instead |
|-------|---------|
| Dark mode | Light mode with subtle grays |
| Large hero cards | Table-first data density |
| Purple/cyan gradients | Single indigo accent |
| Oversized badges | Small inline badges with dots |
| Heavy shadows | Crisp borders, minimal shadows |
| Monospace dominance | Sans-serif body, mono for data |

---

*Last updated: 2026-08-29 | Version: 3.0.0*