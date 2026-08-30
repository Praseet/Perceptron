# H.41 Accessibility of dynamic updates

For dynamic values such as:

```text
probability
prediction label
loop cycle metrics
connection state
```

do not put `aria-live="assertive"` on everything.

Use:

```text
polite
```

for ordinary progress.

Reserve assertive announcements for genuinely urgent state changes only.

The page must remain pleasant for screen-reader users during a multi-event loop run.

---

