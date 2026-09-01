"""Run full data pipeline sequentially: rule_generator -> engineering -> anti_leakage.

Usage:
    python run_pipeline.py                # regenerate raw + features + validate
    python run_pipeline.py --no-generate  # reuse existing raw, only features + validate
"""
import subprocess, sys, time
from pathlib import Path

start = time.time()
SKIP_GENERATE = "--no-generate" in sys.argv

def run(name, cmd):
    print(f"[{name}] starting...", flush=True)
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True)
    dt = time.time() - t0
    print(f"[{name}] done in {dt:.1f}s rc={r.returncode}", flush=True)
    if r.stdout:
        lines = r.stdout.strip().splitlines()
        print(f"[{name}] stdout tail:", flush=True)
        print("\n".join(lines[-14:]), flush=True)
    if r.stderr:
        lines = r.stderr.strip().splitlines()
        print(f"[{name}] stderr tail:", flush=True)
        print("\n".join(lines[-6:]), flush=True)
    if r.returncode != 0:
        raise SystemExit(f"[{name}] FAILED rc={r.returncode}")

# Clear stale artifacts before each run (avoids Windows file-lock/Errno 22).
# With --no-generate the raw CSV is kept so engineering can reuse it.
stale = ["data/processed/transactions_features.pkl"]
if not SKIP_GENERATE:
    stale = ["data/raw/transactions.csv", "data/raw/generation_log.csv",
             "data/raw/transactions.parquet"] + stale
for p in stale:
    q = Path(p)
    if q.exists():
        q.unlink()
        print(f"[cleanup] removed {p}", flush=True)

if SKIP_GENERATE:
    raw_csv = Path("data/raw/transactions.csv")
    if not raw_csv.exists():
        raise SystemExit("[--no-generate] data/raw/transactions.csv not found -- run a full pipeline first.")
    print("[skip] --no-generate: reusing existing raw data", flush=True)
else:
    run("rule_generator", [sys.executable, "-W", "ignore", "src/generator/rule_generator.py"])

run("engineering",   [sys.executable, "-W", "ignore", "src/features/engineering.py"])
run("anti_leakage",  [sys.executable, "-W", "ignore", "src/generator/anti_leakage.py"])
run("train",         [sys.executable, "-W", "ignore", "src/models/train.py"])
run("evaluate",      [sys.executable, "-W", "ignore", "src/models/evaluate.py"])

print(f"PIPELINE OK in {time.time()-start:.1f}s", flush=True)