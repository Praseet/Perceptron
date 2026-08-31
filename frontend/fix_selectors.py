#!/usr/bin/env python3
"""Phase 11 - update identify.spec.ts selectors after Phase 10's
a11y fix removed role='grid' from the wrapper and put aria-label
on the <Table> element."""
from pathlib import Path
target = Path(r"D:/Projects/fraud_model/frontend/tests/e2e/identify.spec.ts")
src = target.read_text(encoding="utf-8")
n = src.count("[role=grid][aria-label='Attack list']")
src = src.replace(
    "[role=grid][aria-label='Attack list']",
    "[aria-label='Attack list']",
)
target.write_text(src, encoding="utf-8")
print(f"Updated {n} selectors")
print("Sample after edit:", src[src.find('aria-label'):src.find('aria-label')+50])