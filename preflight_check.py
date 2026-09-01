"""Dependency preflight helper for start.cmd (P1).

5-phased preflight:
  Phase 1: venv + usable Python runtime
  Phase 2: Python packages (requirements.txt parsed, import-name mapped)
  Phase 3: Frontend packages (package.json + node_modules)
  Phase 4: Data/model artifacts (run_pipeline.py train.py anomaly.py)
  Phase 5: frontend/.env file

Exit codes: 0 = READY, 1 = python problem, 2 = python deps missing,
            3 = frontend deps failed, 4 = artifacts/data-pipeline failed,
            5 = general preflight failure (backend import smoke, etc.)
Uses --install [--yes] to auto-fix; without those flags just checks.
"""
from __future__ import annotations

import importlib
import shutil
import subprocess
import sys
import time as _time
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# mapping: package name -> import module used at runtime.
IMPORT_NAMES = {
    "scikit-learn": "sklearn",
    "imbalanced-learn": "imblearn",
    "python-dotenv": "dotenv",
    "pillow": "PIL",
    "pydantic-core": "pydantic_core",
    "typing-inspection": "typing_inspection",
    "annotated-types": "annotated_types",
    "sklearn-compat": "sklearn_compat",
    "httpx2": "httpx",
    "httpcore2": "httpcore",
    "fonttools": "fontTools",
    "python-dateutil": "dateutil",
    "python-multipart": "multipart",
    "pyyaml": "yaml",
}

CRITICAL_IMPORTS = [
    "numpy", "pandas", "scipy", "sklearn", "xgboost", "shap", "joblib",
    "fastapi", "uvicorn", "pydantic", "dotenv",
]

def _config_artifact_paths():
    """Import X_TEST_PKL, XGB_TIER1_JSON, ISO_FOREST_TIER2_JOBLAB from src/config.py.
    Returns (x_test_pkl, xgb_json, iso_forest_joblib) as strings, or None if config
    cannot be imported (caller falls back to literals)."""
    try:
        import sys as _sys
        _sys.path.insert(0, str(ROOT))
        from src.config import X_TEST_PKL, XGB_TIER1_JSON, ISO_FOREST_TIER2_JOBLIB
        return str(X_TEST_PKL), str(XGB_TIER1_JSON), str(ISO_FOREST_TIER2_JOBLIB)
    except Exception:
        return None


# Artifact paths: use config-driven values for the three spec-required paths,
# keep static literals for the remaining ones (not exposed as config constants).
_cfg = _config_artifact_paths()
if _cfg:
    _X_TEST, _XGB_JSON, _ISO_JOBLIB = _cfg
else:
    _X_TEST = "data/processed/X_test.pkl"
    _XGB_JSON = "models_artifacts/xgboost_tier1.json"
    _ISO_JOBLIB = "models_artifacts/isolation_forest_tier2.joblib"

ARTIFACTS = [
    _XGB_JSON,
    _ISO_JOBLIB,
    "models_artifacts/isolation_forest_config.json",
    "models_artifacts/metrics_manifest.json",
    _X_TEST,
    "data/processed/test_df.pkl",
]


def log(msg):
    print(msg, flush=True)


def python_path() -> Path | None:
    venv = ROOT / ".venv" / "Scripts" / "python.exe"
    return venv if venv.exists() else None


def check_python() -> tuple[bool, str, Path | None]:
    py = python_path()
    if py is not None:
        try:
            r = subprocess.run([str(py), "--version"], capture_output=True,
                               text=True, timeout=20)
            if r.returncode == 0:
                return True, r.stdout.strip() or r.stderr.strip(), py
            return False, f"venv python broken rc={r.returncode}", py
        except Exception as exc:
            return False, f"venv python error: {exc}", py
    for launcher in (["py", "-3"], ["python"]):
        if shutil.which(launcher[0]):
            try:
                r = subprocess.run(launcher + ["--version"],
                                   capture_output=True, text=True, timeout=20)
                if r.returncode == 0:
                    return True, r.stdout.strip(), None
            except Exception:
                pass
    return False, "no usable Python runtime found", None


def parse_requirements() -> list[str]:
    req = ROOT / "requirements.txt"
    if not req.exists():
        return []
    pkgs = []
    for line in req.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        name = line.split("==")[0].split(">=")[0].split("<")[0].strip()
        if name:
            pkgs.append(name)
    return pkgs


def import_name_for(dist: str) -> str:
    if dist in IMPORT_NAMES:
        return IMPORT_NAMES[dist]
    return dist.lower().replace("-", "_")
def check_deps(py: Path | None) -> tuple[bool, list[str]]:
    missing = []
    req = ROOT / "requirements.txt"
    if not req.exists():
        return False, ["requirements.txt missing"]
    for dist in parse_requirements():
        mod = import_name_for(dist)
        if dist in ("cython",):
            continue
        try:
            if py is not None:
                r = subprocess.run(
                    [str(py), "-c",
                     f"import importlib; importlib.import_module('{mod}')"],
                    capture_output=True, text=True, timeout=30)
                if r.returncode != 0:
                    missing.append(f"{dist} (import `{mod}`)")
            else:
                importlib.import_module(mod)
        except Exception:
            missing.append(f"{dist} (import `{mod}`)")
    return (not missing), missing


def check_node() -> tuple[bool, str, str, str]:
    node = shutil.which("node")
    npm = shutil.which("npm")
    pkg = ROOT / "frontend" / "package.json"
    if not node:
        return False, "node", "missing", ""
    ver = subprocess.run([node, "--version"], capture_output=True,
                         text=True, timeout=15).stdout.strip()
    if not npm:
        return False, "npm", "missing", ""
    if not pkg.exists():
        return False, "frontend/package.json", "missing", ""
    lock = ROOT / "frontend" / "package-lock.json"
    lock_state = "lockfile" if lock.exists() else "no-lockfile"
    return True, node, ver, lock_state



def check_artifacts() -> list[str]:
    return [a for a in ARTIFACTS if not (ROOT / a).exists()]


def ensure_frontend_env(py: Path | None = None, auto: bool = False) -> bool:
    """Phase 5: ensure frontend/.env exists with the API base URL.
    If `auto` is True (--yes), write it without prompting.
    Returns True if the file exists (or was created)."""
    env = ROOT / "frontend" / ".env"
    if env.exists():
        return True
    # Default to the dev backend URL
    content = "VITE_API_BASE_URL=http://127.0.0.1:8000/api\n"
    if auto:
        log("[Phase 5] creating frontend/.env ...")
        env.write_text(content, encoding="utf-8")
        return env.exists()
    # Not auto — prompt the user
    ans = input("[Phase 5] frontend/.env is missing. Create it with default dev API URL? [Y/n] ").strip().lower()
    if ans in ("", "y", "yes"):
        log("[Phase 5] writing frontend/.env ...")
        env.write_text(content, encoding="utf-8")
        return env.exists()
    log("[Phase 5] skipping .env creation (frontend may not launch API correctly)")
    return False


def check_import_smoke(py: Path | None) -> bool:
    """Lightweight: verify the 4 most critical third-party packages import
    in a fresh subprocess. Does NOT load the full FastAPI app (that takes
    ~25s on first run and the start.cmd health check covers it).
    """
    progs = [
        "import fastapi, uvicorn, xgboost, sklearn; print('OK')",
    ]
    for code in progs:
        try:
            runner = [py] if py is not None else [sys.executable]
            r = subprocess.run(runner + ["-c", code], capture_output=True,
                               text=True, timeout=60, cwd=str(ROOT))
            if r.returncode != 0 or "OK" not in r.stdout:
                return False
        except Exception:
            return False
    return True


def create_venv() -> Path | None:
    """Create .venv using the py launcher (or python) if missing."""
    import subprocess as _s
    venv = ROOT / ".venv" / "Scripts" / "python.exe"
    if venv.exists():
        return venv
    for launcher in (["py", "-3"], ["python"]):
        if shutil.which(launcher[0]):
            log(f"[install] creating .venv with {launcher[0]} ...")
            try:
                r = _s.run(launcher + ["-m", "venv", str(ROOT / ".venv")],
                           capture_output=True, text=True, timeout=300)
                if r.returncode == 0 and venv.exists():
                    log("[install] .venv created")
                    return venv
            except Exception as exc:
                log(f"[install] venv creation failed: {exc}")
    return None


def install_python_deps(py: Path) -> bool:
    """pip install -r requirements.txt into the given venv, printing '*'
    progress every 2s so the launcher shows visible progress (Section 27.6)."""
    import time as _time

    req = ROOT / "requirements.txt"
    if not req.exists():
        log("[install] requirements.txt not found -- cannot install")
        return False
    log("[install] installing Python dependencies (this can take a while)...")
    try:
        proc = subprocess.Popen(
            [str(py), "-m", "pip", "install", "-q", "-r", str(req)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            cwd=str(ROOT),
        )
        while proc.poll() is None:
            print("*", end="", flush=True)
            _time.sleep(2.0)
        print(flush=True)
        return proc.returncode == 0
    except Exception as exc:
        print(flush=True)
        log(f"[install] pip install failed: {exc}")
        return False


def install_frontend_deps() -> bool:
    """npm install (or npm ci when a lockfile exists), printing '*' progress."""
    import time as _time

    pkg = ROOT / "frontend" / "package.json"
    if not pkg.exists():
        log("[install] frontend/package.json not found -- cannot install")
        return False
    lock = ROOT / "frontend" / "package-lock.json"
    cmd = "npm ci" if lock.exists() else "npm install"
    log(f"[install] running `{cmd}` in frontend/ ...")
    try:
        proc = subprocess.Popen(
            cmd.split(), cwd=str(ROOT / "frontend"),
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        while proc.poll() is None:
            print("*", end="", flush=True)
            _time.sleep(2.0)
        print(flush=True)
        return proc.returncode == 0
    except Exception as exc:
        print(flush=True)
        log(f"[install] {cmd} failed: {exc}")
        return False


def main() -> int:
    want_install = "--install" in sys.argv
    auto_yes = "--yes" in sys.argv
    log("=== AFL preflight (5 phases) ===")

    # ---- Phase 1: Python runtime ----
    log("[Phase 1/5] Python runtime")
    py_ok, py_info, py_path = check_python()
    log(f"Python        : {'OK' if py_ok else 'MISSING'}  ({py_info})")
    if not py_ok:
        if want_install and py_path is None:
            log("[Phase 1] creating .venv ...")
            py_path = create_venv()
            if py_path is None:
                log("manual fix:  py -3 -m venv .venv")
                log("then:        .venv\\Scripts\\python.exe -m pip install -r requirements.txt")
                return 1
            py_ok = True
        elif not want_install and py_path is None:
            log("manual fix:  py -3 -m venv .venv")
            log("then:        .venv\\Scripts\\python.exe -m pip install -r requirements.txt")
            return 1

    # ---- Phase 2: Python deps ----
    log("[Phase 2/5] Python dependencies")
    deps_ok, missing_deps = check_deps(py_path)
    log(f"Python deps   : {'OK' if deps_ok else 'MISSING: ' + (', '.join(missing_deps[:8])) + ('...' if len(missing_deps) > 8 else '')}")
    if not deps_ok:
        if want_install:
            if not auto_yes:
                ans = input("[Phase 2] Install missing Python deps now? [Y/n] ").strip().lower()
                if ans and ans != "y" and ans != "yes":
                    log("Skipping Python deps install at user request.")
                    return 2
            if install_python_deps(py_path):
                log("[Phase 2] python deps installed. re-checking...")
                deps_ok, missing_deps = check_deps(py_path)
                log(f"Python deps   : {'OK' if deps_ok else 'STILL MISSING: ' + ', '.join(missing_deps[:8])}")
                if not deps_ok:
                    return 2
            else:
                log("[Phase 2] python dependency install FAILED")
                return 2

    # ---- Phase 3: Frontend deps ----
    log("[Phase 3/5] Frontend dependencies")
    node_ok, node_bin, node_ver, lock_state = check_node()
    log(f"Node/npm      : {'OK' if node_ok else 'MISSING'} ({node_ver or 'n/a'} {lock_state or 'n/a'})")
    fe_installed = (ROOT / "frontend" / "node_modules").exists()
    log(f"Frontend deps : {'OK' if fe_installed else 'MISSING (frontend/node_modules)'}")
    if not fe_installed:
        if want_install and node_ok:
            if not auto_yes:
                ans = input("[Phase 3] Install frontend (npm ci/install) now? [Y/n] ").strip().lower()
                if ans and ans != "y" and ans != "yes":
                    log("Skipping frontend deps install at user request.")
                    return 3
            if install_frontend_deps():
                log("[Phase 3] frontend deps installed. re-checking...")
                fe_installed = (ROOT / "frontend" / "node_modules").exists()
                if not fe_installed:
                    return 3
            else:
                log("[Phase 3] frontend dependency install FAILED")
                return 3

    # ---- Phase 4: Data/model artifacts ----
    log("[Phase 4/5] Data/model artifacts")
    if py_ok and deps_ok:
        missing_artifacts = check_artifacts()
        log(f"Artifacts     : {'OK' if not missing_artifacts else 'MISSING: ' + ', '.join(missing_artifacts)}")
        if missing_artifacts:
            log("Phase 4 requires running the ML pipeline to generate model artifacts.")
            log("Required steps: src/generator/llm_generator.py + run_pipeline.py")
            if want_install:
                if not auto_yes:
                    ans = input("[Phase 4] Run training/pipeline now to generate artifacts? [Y/n] ").strip().lower()
                    if ans and ans != "y" and ans != "yes":
                        log("Skipping pipeline generation at user request.")
                        return 4
                log("[Phase 4] running run_pipeline.py ...")
                try:
                    proc = subprocess.Popen(
                        [str(py_path), str(ROOT / "run_pipeline.py")] if py_path
                        else [sys.executable, str(ROOT / "run_pipeline.py")],
                        cwd=str(ROOT),
                    )
                    while proc.poll() is None:
                        print("*", end="", flush=True)
                        _time.sleep(2.0)
                    print(flush=True)
                    if proc.returncode == 0:
                        log("[Phase 4] pipeline complete. re-checking artifacts...")
                        missing_artifacts = check_artifacts()
                        log(f"Artifacts     : {'OK' if not missing_artifacts else 'STILL MISSING: ' + ', '.join(missing_artifacts)}")
                    else:
                        log("[Phase 4] pipeline exited with code " + str(proc.returncode))
                except Exception as exc:
                    log(f"[Phase 4] pipeline run failed: {exc}")
            return 4
    else:
        log("Artifacts     : SKIPPED (python or deps missing)")

    # ---- Phase 5: Frontend .env ----
    log("[Phase 5/5] Frontend environment")
    env_ok = ensure_frontend_env(py_path, auto=auto_yes)
    log(f"Frontend .env : {'OK' if env_ok else 'MISSING'}")

    # ---- Backend import smoke ----
    smoke_ok = True
    if py_ok and deps_ok:
        smoke_ok = check_import_smoke(py_path)
        log(f"Backend import: {'OK' if smoke_ok else 'FAIL'}")
    else:
        log("Backend import: SKIPPED")

    ok = py_ok and deps_ok and node_ok and fe_installed and env_ok and smoke_ok
    log("=== " + ("ENVIRONMENT READY" if ok else "ENVIRONMENT NOT READY") + " ===")
    return 0 if ok else 5


if __name__ == "__main__":
    sys.exit(main())
