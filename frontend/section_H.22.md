# H.22 Accessibility checklist by component

## Navigation

- `<nav>` landmark
- visible focus
- current route indication
- keyboard activation
- mobile menu focus trap and restore

## Buttons

- native `<button>`
- accessible text
- disabled state correctly announced

## Inputs

- `<label for>` / matching `id`
- errors associated with `aria-describedby`
- invalid state with `aria-invalid`

## Tables

- semantic `<table>`
- `<caption>` or accessible heading
- `<th scope="col">`
- sortable headers announce sort state
- horizontal scroll container has an accessible name when needed

## Drawer/Sheet

- visible title
- description
- focus trap
- Escape
- return focus

## Charts

- title
- visible numeric summary
- accessibility layer where supported
- data not communicated exclusively by color

## Loop diagram

- accessible labels
- text-equivalent explanation
- no keyboard trap

React Flow's current accessibility implementation supports focusable nodes/edges and ARIA descriptions, so use those mechanisms rather than disabling keyboard accessibility globally. citeturn830860search0

---

