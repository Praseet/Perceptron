# H.46 Cline “do not overfit to the screenshot” rule

Screenshots are a validation mechanism, not a substitute for semantics.

Do not write brittle code such as:

```text
absolute position everything
hardcode text widths
fix table by magic pixel offset
set 1px negative margins to align icons
```

Use:

```text
flex
grid
normal flow
consistent gaps
max widths
intrinsic content sizing
```

Only use absolute positioning for genuinely layered UI elements such as:

```text
chart marker
status dot
drawer close icon where appropriate
```

---

