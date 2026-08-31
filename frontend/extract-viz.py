#!/usr/bin/env python3
"""Phase 10 step 4a - extract key data from the visualizer HTML
report. The visualizer emits a `window.renderOptions` script with
the bundle data embedded; we parse out the top-N largest entries.
"""
import json
import re
from html import unescape
from pathlib import Path

p = Path(r"D:/Projects/fraud_model/frontend/dist/bundle-report.html")
html = p.read_text(encoding="utf-8", errors="replace")

# The data is embedded as JSON within a script tag.
m = re.search(r"<script[^>]*>\s*window\.renderOptions\s*=\s*(\{.*?\})\s*;?\s*</script>", html, re.DOTALL)
if not m:
    print("renderOptions not found; checking for other data shapes...")
    m2 = re.search(r"treeData\s*=\s*(\{.*?\})\s*;", html, re.DOTALL)
    print("treeData match:", bool(m2))
    raise SystemExit(1)

data = json.loads(unescape(m.group(1)))

# The structure is { tree: { name, children: [...] }, nodes: {...} }
def walk(node, depth=0, rows=None):
    if rows is None:
        rows = []
    if "groups" in node or "children" in node:
        kids = node.get("groups") or node.get("children") or []
        for k in kids:
            walk(k, depth + 1, rows)
    rows.append({
        "name": node.get("name", "?"),
        "rendered_bytes": node.get("renderedLength", 0),
        "gzip_bytes": node.get("gzipLength", 0),
        "depth": depth,
    })
    return rows

tree = data.get("tree") or data.get("graph") or data
rows = walk(tree)
rows.sort(key=lambda r: -r["rendered_bytes"])

print("Top 25 bundle entries by rendered bytes:")
print(f"{'name':<60} {'rendered':>12} {'gzip':>10}")
for r in rows[:25]:
    name = r["name"][:58]
    print(f"{name:<60} {r['rendered_bytes']:>12,} {r['gzip_bytes']:>10,}")