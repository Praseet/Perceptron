# H.27 Visual style anti-pattern audit

Search the final source tree for:

```text
backdrop-blur
bg-gradient
from-purple-
via-pink-
to-orange-
hover:scale
hover:-translate
translate-y on hover
shadow-
emoji characters
console.log
TODO(Phase
```

Also search for raw color literals outside the canonical token file.

Any hit must be inspected.

A search hit is not automatically a bug if it lives in:

- a code comment,
- an external test fixture,
- a documentation example.

But visual source code hits are presumptively a defect.

---

