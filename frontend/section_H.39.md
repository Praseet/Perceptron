# H.39 Command palette behavior

Keyboard shortcut:

```text
Ctrl+K
Cmd+K
```

Must:

- work from any page,
- not break text editing behavior,
- not steal focus from normal text input shortcuts when the input is actively handling the same combination,
- focus the search field when opened,
- close on Escape,
- restore focus to a sensible element.

Groups:

```text
Go to page
Attacks
Actions
```

Attacks are fetched/cached once through TanStack Query.

---

