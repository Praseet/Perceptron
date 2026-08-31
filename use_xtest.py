#!/usr/bin/env python3
"""Replace TEST_DF[MODEL_COLS] with X_TEST in business + confusion paths
since X_TEST is the pre-engineered numeric matrix."""
from pathlib import Path
target = Path(r"D:/Projects/fraud_model/src/api/main.py")
src = target.read_text(encoding="utf-8")
# Be careful: only replace the specific cases. In _confusion:
src = src.replace(
    "    X = TEST_DF[MODEL_COLS]\n    y = TEST_DF[\"is_fraud\"].to_numpy()\n    proba = XGB_MODEL.predict_proba(X)\n    for thr in (0.30, 0.50, 0.70, 0.90):",
    "    X = X_TEST\n    y = TEST_DF[\"is_fraud\"].to_numpy()\n    proba = XGB_MODEL.predict_proba(X)[:, 1]\n    for thr in (0.30, 0.50, 0.70, 0.90):",
)
src = src.replace(
    "    X = TEST_DF[MODEL_COLS]\n    proba = XGB_MODEL.predict_proba(X)\n    preds = (proba >= 0.5).astype(int)\n    for ftype, grp in df.groupby(\"fraud_type\"):",
    "    X = X_TEST\n    proba = XGB_MODEL.predict_proba(X)[:, 1]\n    preds = (proba >= 0.5).astype(int)\n    for ftype, grp in df.groupby(\"fraud_type\"):",
)
target.write_text(src, encoding="utf-8")
print("Patched business + confusion")

import ast
ast.parse(src)
print("Syntax OK")