# H.37 Form submission and Enter-key rules

Generate/Defend forms should submit on Enter where native form semantics allow.

Exception:

- multiline transcript content areas are not user-editable anyway.
- controls inside a select popover should not trigger the parent form accidentally.

Use:

```html
<form onSubmit={handleSubmit(...)} />
```

and a real submit button.

Do not manually listen for every Enter key unless the primitive interaction requires it.

---

