# H.50 Cline debugging order for missing Tailwind classes

If a class does nothing:

1. confirm the class appears as a complete literal string in source,
2. confirm Tailwind v4 is scanning the file,
3. inspect generated CSS,
4. prefer static mapping,
5. switch to a canonical CSS variable if the value is runtime-driven.

Tailwind's documentation explicitly states that string interpolation does not generate dynamic utility classes. citeturn889556search1

---

