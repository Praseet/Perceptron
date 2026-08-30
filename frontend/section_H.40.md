# H.40 Command palette actions

Exactly the three named actions:

```text
Run the loop
Generate a random attack
Predict a random transaction
```

Recommended routes:

```text
Run the loop
→ /loop?prefill=1cycle

Generate a random attack
→ /generate?attack_id=<chosen generator-backed id>

Predict a random transaction
→ /defend
```

If a random transaction fixture is available, load it after navigation.

Do not invent a new `/random` route.

---

