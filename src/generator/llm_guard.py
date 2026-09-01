"""Lightweight LLM availability guard for rule_generator.py (speed/efficiency fix).

When either LLM target is >0, rule_generator probes the endpoint once, cheaply,
BEFORE importing llm_generator (which raises RuntimeError at import when no
provider is configured) or issuing any generation call。 Endpoint unreachable:
the LLM sections are skipped entirely (pure rule-based output; rule-based fallback
tops up ai_impersonation organically). Remote providers (gemini/anthropic/openai)

can't be probed without burning a paid generation call, so their guard is a key-
presence check only; the local (LM Studio) path gets a real GET /models probe.
"""
import os
import urllib.request


def probe_llm(timeout: float = 2.0) -> bool:
    """True if the active LLM provider is reachable enough to bother issuing calls."""

    use_local = os.getenv("USE_LOCAL", "false").lower() == "true"
    if use_local:
        base = os.getenv("LOCAL_BASE_URL", "http://localhost:1234/v1").rstrip("/") or "http://localhost:1234/v1"
        try:
            with urllib.request.urlopen(base + "/models", timeout=timeout) as resp:
                return 200 <= resp.status < 300
        except Exception:
            return False
    return bool(
        os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
        or os.getenv("ANTHROPIC_API_KEY")
        or os.getenv("OPENAI_API_KEY")
    )