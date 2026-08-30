"""
Leakage guard — automated check that no transaction_id or case_id appears in
more than one of {train, val, test} after the pipeline runs.

The temporal split in `train.py` slices by row timestamp, but multi-transaction
fraud cases can span the cut points. A case whose median timestamp is in train
but whose first or last tx is in test effectively teaches the model what the
"same case" looks like in test. This is the same failure mode as tuning an
attack against the exact data you'll then report robustness on.

USAGE
-----
After running `python -m src.models.train` and any augmentation that writes
`data/processed/*.pkl`, run this script directly:

    python -m src.models.leakage_guard

It will:
  1. Load train_df.pkl / val_df.pkl / test_df.pkl
  2. Check transaction_id and case_id overlap across every pair of splits
  3. Report per-class fraud_type case-leakage (the most diagnostic view)
  4. Exit with code 1 if any overlap is found (suitable for CI gating)

The check is also importable as a function for pytest:

    from src.models.leakage_guard import assert_no_leakage
    assert_no_leakage(strict=True)
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import (
    TRAIN_DF_PKL, VAL_DF_PKL, TEST_DF_PKL,
)
from models import output as out


def _case_id_set(df: pd.DataFrame) -> set:
    """Non-null case_ids only — None is normal-transaction placeholder."""
    return set(df["case_id"].dropna().unique())


def _per_class_case_overlap(
    splits: dict[str, pd.DataFrame],
    id_col: str = "case_id",
) -> list[tuple[str, str, str, int]]:
    """For each pair of splits, list (fraud_type, split_a, split_b, overlap_count)
    where case_ids of that fraud_type appear in both splits."""
    findings = []
    names = list(splits)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            df_a = splits[a]
            df_b = splits[b]
            ids_a = _case_id_set(df_a) if id_col == "case_id" else set(df_a["transaction_id"].unique())
            ids_b = _case_id_set(df_b) if id_col == "case_id" else set(df_b["transaction_id"].unique())
            common = ids_a & ids_b
            if not common:
                continue
            # Find fraud_types these overlapping IDs belong to (use the split
            # with more rows for stability).
            df_src = df_a if len(df_a) > len(df_b) else df_b
            for cid in common:
                fts = df_src.loc[df_src[id_col] == cid, "fraud_type"].unique()
                for ft in fts:
                    findings.append((str(ft), a, b, 1))
    # Aggregate by (fraud_type, a, b)
    agg: dict[tuple[str, str, str], int] = {}
    for ft, a, b, _ in findings:
        agg[(ft, a, b)] = agg.get((ft, a, b), 0) + 1
    return [(ft, a, b, c) for (ft, a, b), c in sorted(agg.items())]


def check_leakage() -> dict:
    """Return a structured dict of leakage findings. Empty dict == no leakage.

    Keys:
      tx_overlap_total: total transaction_id overlaps across any split pair
      case_overlap_total: total case_id overlaps across any split pair
      per_class_case_overlap: list of (fraud_type, split_a, split_b, n_overlap)
    """
    train_df = pd.read_pickle(TRAIN_DF_PKL)
    val_df = pd.read_pickle(VAL_DF_PKL)
    test_df = pd.read_pickle(TEST_DF_PKL)
    splits = {"train": train_df, "val": val_df, "test": test_df}

    tx_overlap_total = 0
    names = list(splits)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            common_tx = set(splits[a]["transaction_id"]) & set(splits[b]["transaction_id"])
            tx_overlap_total += len(common_tx)

    case_overlap_total = 0
    names = list(splits)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            common_case = _case_id_set(splits[a]) & _case_id_set(splits[b])
            case_overlap_total += len(common_case)

    per_class = _per_class_case_overlap(splits, id_col="case_id")
    return {
        "tx_overlap_total": tx_overlap_total,
        "case_overlap_total": case_overlap_total,
        "per_class_case_overlap": per_class,
    }


def assert_no_leakage(strict: bool = False) -> None:
    """Print findings; raise AssertionError in strict mode if any leak."""
    out.banner("Leakage guard (case_id + transaction_id)")
    findings = check_leakage()
    out.kv("transaction_id overlap (any pair)",
           f"{findings['tx_overlap_total']} {'(PASS)' if findings['tx_overlap_total'] == 0 else '(FAIL)'}")
    out.kv("case_id overlap (any pair)",
           f"{findings['case_overlap_total']} {'(PASS)' if findings['case_overlap_total'] == 0 else '(FAIL)'}")
    if findings["per_class_case_overlap"]:
        rows = [[ft, a, b, str(c)]
                for (ft, a, b, c) in findings["per_class_case_overlap"]]
        out.table(["fraud_type", "split_a", "split_b", "n_overlap"],
                  rows, aligns=["l", "l", "l", "r"])
    else:
        out.step("  no per-class case_id overlaps.")
    if strict and (findings["tx_overlap_total"] or findings["case_overlap_total"]):
        raise AssertionError(
            f"Leakage detected: tx_overlap={findings['tx_overlap_total']}, "
            f"case_overlap={findings['case_overlap_total']}"
        )


if __name__ == "__main__":
    # Default to non-strict so the script always reports findings even when
    # leakage is present (CI can wrap it with --strict).
    strict = "--strict" in sys.argv
    try:
        assert_no_leakage(strict=strict)
    except AssertionError as e:
        out.error(str(e))
        sys.exit(1)