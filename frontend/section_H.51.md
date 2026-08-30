# H.51 Cline debugging order for broken shadcn components

When a generated shadcn primitive looks wrong:

1. inspect the generated source,
2. identify its data attributes/variants,
3. replace its default color/radius/spacing values with AFL tokens,
4. preserve the interaction/accessibility implementation,
5. do not delete its semantic roles just to make styling easier.

Current shadcn documentation emphasizes that the component source is owned by the project and can be modified. citeturn423138search2

---

