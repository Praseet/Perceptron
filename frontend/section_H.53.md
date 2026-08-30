# H.53 Cline debugging order for charts

When a chart is blank:

1. log/inspect data shape,
2. verify all required numeric values are finite,
3. verify axis keys match exact response fields,
4. verify container width/height is non-zero,
5. verify the chart library is imported only in the page that needs it,
6. inspect accessibility layer,
7. only then adjust chart props.

Do not invent chart data just to make the graph render.

---

