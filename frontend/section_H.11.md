# H.11 Error boundaries

Because `React.lazy()` can propagate rejected module-loading errors to an Error Boundary, the router/app shell should include a small error boundary around routed page content. React's lazy documentation explicitly describes rejected dynamic imports being thrown for the nearest Error Boundary to handle. citeturn957766search0

### Required behavior

If a feature chunk fails to load:

```text
Page title:
"Page failed to load"

Explanation:
"The requested feature could not be loaded."

Action:
"Reload page"
```

The error boundary must not expose a stack trace to the judge.

Log the technical detail only through the existing error pathway appropriate for the environment.

---

