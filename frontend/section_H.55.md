# H.55 Testing contract for URL handoffs

Automate:

```text
/identify?attack_id=SE-001
```

and assert:

```text
drawer open
SE-001 visible
```

Automate:

```text
/generate?attack_id=SE-001
```

and assert:

```text
attack field pre-selected
```

Automate:

```text
/loop?prefill=1cycle
```

and assert:

```text
max cycles = 1
```

Do not assert internal React state directly if the same behavior can be observed from the DOM.

---

