# H.38 Query cache and URL-state separation

Use Zustand only for the three deliberate cross-cutting values already specified:

```text
commandPaletteOpen
dataSource
lastGeneratedTransactionId
```

If Phase 8 requires the complete generated transaction object for the cross-page handoff, the documented one-field exception is:

```text
lastGeneratedTransaction
```

Use URL state for:

```text
attack_id
prefill=1cycle
```

Use local feature state for:

```text
filters
drawer open
selected row
form dirty state
active stream
cycle timeline
```

Use TanStack Query cache for:

```text
server data
```

Do not put server response collections into Zustand.

---

