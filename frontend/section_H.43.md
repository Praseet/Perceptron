# H.43 No fake “live” indicators

A green pulsing dot does not make a system live.

For `System status`, the status should be derived from actual backend/demo state.

In demo mode, “Online” means:

```text
the demo data source is available
```

not:

```text
the production inference stack is running
```

If you choose to show additional status text in demo mode, use something honest such as:

```text
Demo · 1.06M tx
```

but do not clutter the judge-facing nav unless necessary.

---

