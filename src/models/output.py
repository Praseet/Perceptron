"""
Lightweight output helpers for model scripts.

Use these to keep terminal output consistent and easy to scan. The style
is plain and practical: section banners, key-value pairs, and minimal
decoration for quick visual parsing.
"""

from __future__ import annotations

import sys
from contextlib import contextmanager
from typing import Iterable, Optional, Sequence


def banner(title: str) -> None:
    """Print a section banner to visually separate phases."""
    print(f"\n{title}", flush=True)


def step(message: str) -> None:
    """Print a short progress or status message."""
    print(f"  {message}", flush=True)


def kv(label: str, value, *, indent: int = 0) -> None:
    """Print a key: value pair with clean alignment."""
    pad = "    " * indent  # 4 spaces per indent level
    # Truncate very long labels to maintain readability
    display_label = str(label)[:30]
    print(f"{pad}{display_label:<30}{value}", flush=True)


def table(
    headers: Sequence[str],
    rows: Iterable[Sequence],
    aligns: Optional[Sequence[str]] = None,
) -> None:
    """Print a simple fixed-width table for tabular data."""
    rows = list(rows)
    if not rows:
        print("  (no data)", flush=True)
        return
    
    # Calculate column widths
    widths = [len(str(h)) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))
    
    # Add padding between columns
    widths = [w + 2 for w in widths]  # 2 spaces padding
    
    aligns = aligns or ["l"] * len(headers)
    
    # Print header
    header_parts = []
    for h, w, a in zip(headers, widths, aligns):
        h_str = str(h)
        if a == "l":
            header_parts.append(h_str.ljust(w))
        else:
            header_parts.append(h_str.rjust(w))
    print("  " + "".join(header_parts), flush=True)
    
    # Print separator
    sep_parts = ["-" * w for w in widths]
    print("  " + "".join(sep_parts), flush=True)
    
    # Print rows
    for row in rows:
        row_parts = []
        for cell, w, a in zip(row, widths, aligns):
            cell_str = str(cell)
            if a == "l":
                row_parts.append(cell_str.ljust(w))
            else:
                row_parts.append(cell_str.rjust(w))
        print("  " + "".join(row_parts), flush=True)


@contextmanager
def phase(name: str):
    """Context manager that announces start and end of a phase."""
    banner(f"{name} »")
    try:
        yield
    finally:
        banner(f"« {name} completed")


def done(message: str = "Done.") -> None:
    print(f"\n✓ {message}", flush=True)


def warn(message: str) -> None:
    print(f"⚠  {message}", file=sys.stderr, flush=True)


def error(message: str) -> None:
    print(f"✗ {message}", file=sys.stderr, flush=True)


def info(message: str) -> None:
    print(f"ℹ  {message}", flush=True)
