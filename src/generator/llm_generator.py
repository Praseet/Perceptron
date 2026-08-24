import json
import os
import time
import random
import logging
import urllib.request
from pathlib import Path
from datetime import timedelta
from google import genai
import numpy as np
from dotenv import load_dotenv

from openai import OpenAI



load_dotenv()

logger = logging.getLogger("llm_generator")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

GEMINI_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
LOCAL_BASE_URL = os.getenv("LOCAL_BASE_URL", "http://localhost:1234/v1")
LOCAL_MODEL = os.getenv("LOCAL_MODEL", "qwen2.5-7b-instruct")
USE_LOCAL = os.getenv("USE_LOCAL", "false").lower() == "true"
LOCAL_RETRIES = int(os.getenv("LOCAL_RETRIES", "2"))
LOCAL_TEMPERATURE = float(os.getenv("LOCAL_TEMPERATURE", "0.2"))
# Qwen3.5 can emit hidden reasoning even when instructed not to. 768 tokens is
# too little for a three-case structured batch when that happens, whereas 2048
# leaves room for both the occasional reasoning and the final JSON response.
LOCAL_MAX_TOKENS = int(os.getenv("LOCAL_MAX_TOKENS", "2048"))
_local_client = OpenAI(
    base_url=LOCAL_BASE_URL,
    api_key="lm-studio",
)

# LM Studio's OpenAI-compatible server accepts JSON Schema mode (rather than
# OpenAI's older `json_object` response format). Fraud and benign data have
# deliberately separate contracts: sharing a minimal schema was the reason
# fraud-outcome fields silently disappeared and defaulted to `True` downstream.
LOCAL_FRAUD_RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "fraud_transcript_batch",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "cases": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "case_id": {"type": "string"},
                            "transcript": {
                                "type": "array",
                                "minItems": 6,
                                "maxItems": 10,
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "speaker": {"type": "string", "enum": ["attacker", "target"]},
                                        "text": {"type": "string"},
                                    },
                                    "required": ["speaker", "text"],
                                    "additionalProperties": False,
                                },
                            },
                            "transaction_attempted": {"type": "boolean"},
                            "transaction_completed": {"type": "boolean"},
                            "credential_shared": {"type": "boolean"},
                            "requested_action": {
                                "type": "string",
                                "enum": [
                                    "bank_transfer", "card_payment", "crypto_transfer", "gift_card",
                                    "one_time_code", "password", "remote_access", "personal_information", "none",
                                ],
                            },
                            "target_outcome": {
                                "type": "string",
                                "enum": [
                                    "refused", "deferred_for_verification", "engaged_no_action",
                                    "credential_shared", "payment_attempted", "payment_completed",
                                ],
                            },
                            "urgency_level": {"type": "string", "enum": ["low", "medium", "high"]},
                            "pretext_category": {"type": "string"},
                            "contact_channel": {"type": "string", "enum": ["phone", "sms", "email", "chat"]},
                        },
                        "required": [
                            "case_id", "transcript", "transaction_attempted", "transaction_completed",
                            "credential_shared", "requested_action", "target_outcome", "urgency_level",
                            "pretext_category", "contact_channel",
                        ],
                        "additionalProperties": False,
                    },
                },
            },
            "required": ["cases"],
            "additionalProperties": False,
        },
    },
}

LOCAL_RESPONSE_FORMAT = LOCAL_FRAUD_RESPONSE_FORMAT

LOCAL_BENIGN_RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "benign_transcript_batch",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "cases": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "case_id": {"type": "string"},
                            "transcript": {
                                "type": "array",
                                "minItems": 4,
                                "maxItems": 4,
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "speaker": {"type": "string", "enum": ["customer", "agent"]},
                                        "text": {"type": "string"},
                                    },
                                    "required": ["speaker", "text"],
                                    "additionalProperties": False,
                                },
                            },
                        },
                        "required": ["case_id", "transcript"],
                        "additionalProperties": False,
                    },
                },
            },
            "required": ["cases"],
            "additionalProperties": False,
        },
    },
}


class LocalResponseError(ValueError):
    """A local-model response that retrying unchanged cannot repair."""

ACTIVE_PROVIDER = "local" if USE_LOCAL else "gemini" if GEMINI_KEY else "anthropic" if ANTHROPIC_KEY else "openai" if OPENAI_KEY else None
if ACTIVE_PROVIDER is None:
    raise RuntimeError("No LLM API key detected in .env. Set GEMINI_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY, or USE_LOCAL=true.")


def list_gemini_models():
    """
    Diagnostic helper, not called automatically. A 404 on generateContent almost
    always means GEMINI_MODEL doesn't match what this specific key can actually call
    -- the fix is to ask the API directly rather than guess another model string.
    Run this from a shell:  python -c "from llm_generator import list_gemini_models; list_gemini_models()"
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_KEY}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    print(f"Models available to this key (only ones supporting generateContent):")
    for m in data.get("models", []):
        if "generateContent" in m.get("supportedGenerationMethods", []):
            print(f"  {m['name']}")
    print("\nSet GEMINI_MODEL in .env to one of the names above, WITHOUT the 'models/' prefix.")


def _sleep_for_retry(attempt, exc):
    wait = 2 * (attempt + 1) if "429" in str(exc) else 0.5 ** (attempt + 1)
    time.sleep(wait + random.uniform(0, 1))


# ---------- structured call: returns a parsed dict, provider-specific JSON mode ----------
# CHANGED: every provider path now logs the real exception (type + message) on every
# failed attempt instead of silently swallowing it. This is what was hiding the actual
# 429/401/permission error behind the fallback data.

def _structured_gemini(system, prompt, max_tokens, retries):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_KEY}"
    payload = {"systemInstruction": {"parts": [{"text": system}]},
               "contents": [{"role": "user", "parts": [{"text": prompt}]}],
               "generationConfig": {"responseMimeType": "application/json", "temperature": 1.0, "maxOutputTokens": max_tokens}}
    last_error = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                          headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return json.loads(data["candidates"][0]["content"]["parts"][0]["text"])
        except Exception as exc:
            last_error = exc
            hint = ""
            if "404" in str(exc):
                hint = (f" -- a 404 here almost always means GEMINI_MODEL='{GEMINI_MODEL}' is not a "
                        f"valid model name for this key. Run: python -c "
                        f"\"from llm_generator import list_gemini_models; list_gemini_models()\" "
                        f"to see which model names this key can actually use, then set GEMINI_MODEL "
                        f"in .env to one of those.")
                logger.warning("Gemini structured call failed (attempt %d/%d): %s: %s%s",
                                attempt + 1, retries, type(exc).__name__, exc, hint)
                break  # retrying a bad model name won't fix itself; stop wasting attempts
            logger.warning("Gemini structured call failed (attempt %d/%d): %s: %s%s",
                            attempt + 1, retries, type(exc).__name__, exc, hint)
            _sleep_for_retry(attempt, exc)
    logger.error("Gemini structured call exhausted all retries. Last error: %s: %s",
                 type(last_error).__name__, last_error)
    return None


def _structured_anthropic(system, prompt, max_tokens, retries):
    from anthropic import Anthropic
    client = Anthropic(api_key=ANTHROPIC_KEY)
    last_error = None
    for attempt in range(retries):
        try:
            resp = client.messages.create(model=ANTHROPIC_MODEL, max_tokens=max_tokens, temperature=1.0,
                                           system=system + "\nRespond with ONLY the JSON object, no markdown fences, no other text.",
                                           messages=[{"role": "user", "content": prompt}])
            text = resp.content[0].text.strip()
            text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            return json.loads(text)
        except Exception as exc:
            last_error = exc
            logger.warning("Anthropic structured call failed (attempt %d/%d): %s: %s",
                            attempt + 1, retries, type(exc).__name__, exc)
            _sleep_for_retry(attempt, exc)
    logger.error("Anthropic structured call exhausted all retries. Last error: %s: %s",
                 type(last_error).__name__, last_error)
    return None


def _structured_openai(system, prompt, max_tokens, retries):
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_KEY)
    last_error = None
    for attempt in range(retries):
        try:
            resp = client.chat.completions.create(
                model=OPENAI_MODEL, max_tokens=max_tokens, temperature=1.0,
                response_format={"type": "json_object"},
                messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            )
            return json.loads(resp.choices[0].message.content)
        except Exception as exc:
            last_error = exc
            logger.warning("OpenAI structured call failed (attempt %d/%d): %s: %s",
                            attempt + 1, retries, type(exc).__name__, exc)
            _sleep_for_retry(attempt, exc)
    logger.error("OpenAI structured call exhausted all retries. Last error: %s: %s",
                 type(last_error).__name__, last_error)
    return None


def _structured_local(system, prompt, max_tokens, retries):
    # Qwen3-family models reason by default. In LM Studio that reasoning is returned
    # separately as `reasoning_content`; it can consume the entire token budget and
    # leave `message.content` empty. `/no_think` is the Qwen chat-template control
    # token for a non-reasoning response, which is the appropriate mode for this
    # bounded JSON-generation task.
    local_system = (
        system
        + "\n/no_think\nRespond with ONLY the JSON object, no markdown fences, no other text."
    )
    last_error = None
    local_retries = max(1, min(retries, LOCAL_RETRIES))
    for attempt in range(local_retries):
        try:
            resp = _local_client.chat.completions.create(
                model=LOCAL_MODEL, max_tokens=max_tokens, temperature=LOCAL_TEMPERATURE,
                response_format=LOCAL_RESPONSE_FORMAT,
                messages=[{"role": "system", "content": local_system},
                          # This LM Studio Qwen3.5 template ignores the system-level
                          # control token, so repeat it as the final user instruction.
                          {"role": "user", "content": prompt + "\n/no_think"}],
            )
            message = resp.choices[0].message
            text = (message.content or "").strip()
            if not text:
                reasoning = getattr(message, "reasoning_content", None)
                finish_reason = resp.choices[0].finish_reason
                raise LocalResponseError(
                    "LM Studio returned no final content "
                    f"(finish_reason={finish_reason!r}, reasoning_tokens={'present' if reasoning else 'absent'}). "
                    "Ensure the loaded model supports JSON mode and that /no_think is honored."
                )
            text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            start, end = text.find("{"), text.rfind("}")
            if start != -1 and end != -1:
                text = text[start:end + 1]
            return json.loads(text)
        except Exception as exc:
            last_error = exc
            logger.warning("Local (LM Studio) structured call failed (attempt %d/%d): %s: %s",
                            attempt + 1, local_retries, type(exc).__name__, exc)
            status_code = getattr(exc, "status_code", None)
            if isinstance(exc, LocalResponseError):
                logger.error("Local model produced reasoning only; not retrying the same request.")
                break
            if status_code is not None and 400 <= status_code < 500 and status_code != 429:
                logger.error("Local request was rejected by LM Studio; not retrying a non-transient %s error.",
                             status_code)
                break
            _sleep_for_retry(attempt, exc)
    logger.error("Local structured call exhausted all retries. Last error: %s: %s",
                 type(last_error).__name__, last_error)
    return None


def call_structured(system: str, prompt: str, max_tokens: int = 2048, retries: int = 4):
    """Returns a parsed dict, or None if every attempt failed (caller supplies the fallback)."""
    if ACTIVE_PROVIDER == "local":
        return _structured_local(system, prompt, max_tokens, retries)
    if ACTIVE_PROVIDER == "gemini":
        return _structured_gemini(system, prompt, max_tokens, retries)
    if ACTIVE_PROVIDER == "anthropic":
        return _structured_anthropic(system, prompt, max_tokens, retries)
    return _structured_openai(system, prompt, max_tokens, retries)


TRANSCRIPT_PATH = Path("data/raw/transcripts.jsonl")
TRANSCRIPT_PATH.parent.mkdir(parents=True, exist_ok=True)

PRETEXTS = [
    "bank security team callback",
    "courier delivery fee",
    "technical support contact",
    "family emergency payment request",
    "investment opportunity urgency",
]

# ---------- CHANGED: batched fraud-case generation ----------
# One call now produces BATCH_SIZE independent cases instead of one call per case.

TARGET_PERSONAS = [
    "an older adult who is not very tech-savvy and tends to trust authority figures",
    "a busy professional who is distracted and answers on autopilot between tasks",
    "a cautious person who has read about scams before and gets suspicious quickly",
    "a young adult who is anxious about doing something wrong and eager to comply fast",
    "a skeptical person who pushes back hard and asks pointed verification questions",
]

BATCH_SYSTEM = """You are a synthetic conversational data generator for an Authorized Push Payment (APP)
fraud research benchmark.

You will be given a list of (pretext, persona, case_id) triples.

For EACH triple, generate one realistic synthetic scam conversation between:

- Attacker: impersonating a bank, courier, technical support agent, family member,
  investment representative, or another trusted authority.
- Target: a victim matching the given persona.

IMPORTANT:
These cases are being generated specifically to create fraudulent TRANSACTION EVENTS.

Therefore, the conversation MUST end with the target actually attempting or agreeing
to perform the requested financial/security action.

The target may initially hesitate, question the attacker, or express suspicion,
but the attacker must successfully persuade the target by the end.

Conversation structure:

1. Attacker introduces a believable pretext.
2. Target initially reacts naturally and may question the request.
3. Attacker responds and increases credibility, urgency, or pressure.
4. Target may continue to hesitate or ask for clarification.
5. Attacker addresses the objection.
6. The conversation must end with the target clearly agreeing to perform
   an action such as:
   - sending money
   - authorizing a payment
   - making a bank transfer
   - sending a one-time verification code
   - providing credentials that directly enable the fraudulent transaction.

The final target message MUST show clear compliance or attempted compliance.

Examples of valid final target behavior:

- "Okay, I'll make the transfer now."
- "Fine, I'll authorize the payment."
- "I'll enter the code now."
- "Okay, I'm sending the money."
- "I'll complete the payment through the link."
- "All right, I'm giving you the verification code."

Do NOT end the conversation with:

- refusal
- "I'll verify later"
- "I'll call the bank"
- hesitation without action
- "maybe later"
- hanging up
- asking for more proof without eventually complying.

Label rules:

"transaction_attempted" MUST be true for every generated case.

"transaction_completed" should be true only when the final target messages
clearly indicate that the transaction was actually completed.
Otherwise set it to false.

"credential_shared" should be true if the target actually provides or agrees
to provide credentials, a password, OTP, or similar authentication information.

"target_outcome" should normally be one of:
- "payment_attempted"
- "payment_completed"
- "credential_shared"

"requested_action" must describe what the attacker is asking the target to do.

"urgency_level" should reflect the actual amount of pressure used.

Return ONLY the requested JSON schema.
"""


def _fallback_case(pretext: str, case_id: str) -> dict:
    return {
        "case_id": case_id,
        "transcript": [
            {"speaker": "attacker", "text": f"Urgent security notice regarding your account for {pretext}."},
            {"speaker": "target", "text": "Wait, who is this? I wasn't expecting a call about that."},
            {"speaker": "attacker", "text": "This is time-sensitive -- your account will be locked if we don't act now."},
            {"speaker": "target", "text": "I'm not comfortable doing this without verifying first. I'll call the number on my card."},
        ],
        "transaction_attempted": False,
        "amount_multiplier": float(np.random.uniform(4.0, 9.0)),
        "urgency_level": "medium",
        "pretext_category": pretext,
    }


def generate_llm_case_batch(pretext_case_pairs, max_tokens: int | None = None):
    """
    Generates len(pretext_case_pairs) cases in a single API call instead of one call per
    case. pretext_case_pairs: list of (pretext, case_id) tuples.
    Returns: dict of case_id -> params (same shape generate_llm_case used to return per-case).
    Saves every case's transcript to transcripts.jsonl, same as before.

    CHANGED: on total failure this logs the real error and marks every case in the batch
    "fallback": true (as before) -- but now you'll actually see WHY in the console instead
    of silently getting an all-placeholder dataset.
    """
    # 6-10 turn transcripts with 5 structured fields need more room than the old fixed
    # 4-turn format did. 768 was sized for that shorter shape; 1536 gives headroom for
    # a 3-case batch of the new longer transcripts without inflating local's budget
    # (which already accounts for hidden reasoning separately).
    max_tokens = max_tokens if max_tokens is not None else (LOCAL_MAX_TOKENS if ACTIVE_PROVIDER == "local" else 1536)
    prompt_pairs = "\n".join(
        f"- pretext: '{p}', persona: '{random.choice(TARGET_PERSONAS)}', case_id: '{c}'"
        for p, c in pretext_case_pairs
    )
    prompt = f"Generate one synthetic scam conversation for each of these cases:\n{prompt_pairs}"

    parsed = call_structured(BATCH_SYSTEM, prompt, max_tokens=max_tokens)

    model_name = {"gemini": GEMINI_MODEL, "anthropic": ANTHROPIC_MODEL, "openai": OPENAI_MODEL, "local": LOCAL_MODEL}[ACTIVE_PROVIDER]
    n_requested = len(pretext_case_pairs)

    if parsed is None or "cases" not in parsed:
        # Hard failure: every retry raised. call_structured's own logging already
        # explained why (rate limit, auth, etc).
        logger.error(
            "Batch of %d cases returned no usable response from %s (model=%s). "
            "See the WARNING lines above for the real exception. Every case in this "
            "batch will be a placeholder.", n_requested, ACTIVE_PROVIDER, model_name,
        )
        by_id = {}
    else:
        by_id = {case["case_id"]: case for case in parsed.get("cases", []) if "case_id" in case}
        n_returned = len(by_id)
        if n_returned < n_requested:
            # CHANGED: this used to be the silent bug. A structurally valid response
            # (parsed is not None, "cases" key present) that is EMPTY or SHORT --
            # Gemini truncating mid-generation at maxOutputTokens, or the model just
            # dropping cases on a batched prompt -- fell through to individual
            # per-case WARNINGs with no batch-level signal, and worse, each of those
            # patched-in cases was tagged "fallback": False because only the
            # all-or-nothing is_fallback_batch flag controlled that field. Both are
            # fixed below: this is now an ERROR (loud, batch-level), and every
            # individual fallback is tracked and tagged correctly regardless of why
            # it happened.
            logger.error(
                "Batch of %d cases: %s (model=%s) only returned %d case(s) -- %d will "
                "be placeholders. This is NOT a request failure (the call succeeded and "
                "parsed as JSON); the model returned an incomplete 'cases' list. Common "
                "causes: max_tokens too low for this batch size (raise max_tokens or "
                "lower LLM_BATCH_SIZE), or the model dropping items on a batched prompt "
                "(lower LLM_BATCH_SIZE). Raw response for debugging: %s",
                n_requested, ACTIVE_PROVIDER, model_name, n_returned,
                n_requested - n_returned, json.dumps(parsed)[:800],
            )

    results = {}
    for pretext, case_id in pretext_case_pairs:
        case = by_id.get(case_id)
        is_fallback_case = case is None
        if is_fallback_case:
            case = _fallback_case(pretext, case_id)
        transcript_lines = [f"{t.get('speaker','unknown')}: {t.get('text','')}" for t in case.get("transcript", [])]
        params = {
            "transaction_attempted": bool(case.get("transaction_attempted", True)),
            "amount_multiplier": float(case.get("amount_multiplier", np.random.uniform(4.0, 8.0))),
            "urgency_level": str(case.get("urgency_level", "high")),
            "pretext_category": str(case.get("pretext_category", pretext)),
            "fallback": is_fallback_case,
            "label": 1,
        }
        record = {"case_id": case_id, "pretext": pretext, "transcript": "\n".join(transcript_lines), **params}
        with TRANSCRIPT_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        results[case_id] = params

    time.sleep(0.2)  # one sleep per BATCH, not per case
    return results


def generate_llm_case(pretext: str, case_id: str) -> dict:
    """Unchanged single-case entry point, kept for compatibility. Prefer
    generate_llm_case_batch() in new code -- this routes through it with a batch of 1, so
    it benefits from the error-logging fix above, but does not save on call count."""
    return generate_llm_case_batch([(pretext, case_id)])[case_id]


BENIGN_PRETEXTS = [
    "checking delivery status",
    "asking about a billing charge",
    "requesting a password reset",
    "asking about a subscription renewal date",
    "reporting a minor product defect",
]

BENIGN_BATCH_SYSTEM = """You are a synthetic conversational data generator for a customer-service benchmark.
You will be given a list of (topic, case_id) pairs. For EACH pair, generate one realistic, ORDINARY support conversation
between a Customer and an Agent about that topic -- no fraud, no urgency, no request to move money or share a one-time code.
Return utterances per case in this order: customer, agent, customer, agent. Generate 6-8 utterances per case.
Each utterance should normally contain 8-20 words.
Keep the conversation concise while preserving:
1. believable pretext
2. target hesitation
3. attacker persuasion
4. target compliance.
Vary wording and tone across cases.

Return ONLY a JSON object with this exact schema -- a "cases" array with one entry per input pair, in the same order:
{
  "cases": [
    {
      "case_id": "<the case_id you were given>",
      "transcript": [
        {"speaker": "customer", "text": "..."},
        {"speaker": "agent", "text": "..."}
      ]
    }
  ]
}
"""


def _fallback_benign_case(topic: str, case_id: str) -> dict:
    return {
        "case_id": case_id,
        "transcript": [
            {"speaker": "customer", "text": f"Hi, I had a question about {topic}."},
            {"speaker": "agent", "text": "Sure, happy to help with that."},
        ],
    }


def generate_benign_case_batch(topic_case_pairs, max_tokens: int | None = None):
    """Batched version of generate_benign_case: one call for the whole batch. Writes
    directly to transcripts.jsonl (these don't feed generation_log.csv or fraud_rows,
    same as the original)."""
    max_tokens = max_tokens if max_tokens is not None else (LOCAL_MAX_TOKENS if ACTIVE_PROVIDER == "local" else 768)
    prompt_pairs = "\n".join(f"- topic: '{t}', case_id: '{c}'" for t, c in topic_case_pairs)
    prompt = f"Generate one ordinary customer-service conversation for each of these cases:\n{prompt_pairs}"

    parsed = call_structured(BENIGN_BATCH_SYSTEM, prompt, max_tokens=max_tokens)

    if parsed is None or "cases" not in parsed:
        logger.error(
            "Benign batch of %d cases returned no usable response -- see WARNING lines "
            "above for the real error. Using placeholder transcripts for this batch.",
            len(topic_case_pairs),
        )
        by_id = {c: _fallback_benign_case(t, c) for t, c in topic_case_pairs}
        is_fallback_batch = True
    else:
        by_id = {case["case_id"]: case for case in parsed["cases"] if "case_id" in case}
        for topic, case_id in topic_case_pairs:
            if case_id not in by_id:
                by_id[case_id] = _fallback_benign_case(topic, case_id)
        is_fallback_batch = False

    for topic, case_id in topic_case_pairs:
        case = by_id[case_id]
        lines = [f"{t.get('speaker','unknown')}: {t.get('text','')}" for t in case.get("transcript", [])]
        record = {"case_id": case_id, "pretext": topic, "transcript": "\n".join(lines),
                   "label": 0, "fallback": is_fallback_batch}
        with TRANSCRIPT_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    time.sleep(0.2)


def generate_benign_case(topic: str, case_id: str) -> dict:
    """Unchanged single-case entry point, kept for compatibility."""
    generate_benign_case_batch([(topic, case_id)])
    return {"case_id": case_id, "pretext": topic}


def materialize_llm_transaction(u, utx, params, case_id, users, merchant_ids,
                                 cat_lookup, rng, new_tx_id, sim_start, sim_days):
    """
    Turns extracted conversation parameters into an actual transaction row -- same
    schema, same leakage discipline as inject_impersonation_case in rule_generator.py.
    Unchanged from the original.
    """
    if not params.get("transaction_attempted"):
        return None

    urow = users.loc[u]
    target_day = rng.uniform(0.0, float(sim_days))
    start = sim_start + timedelta(days=float(target_day))
    if start >= sim_start + timedelta(days=sim_days) - timedelta(minutes=5):
        return None

    prior_tx = [r for r in utx if r[0] < start]
    if len(prior_tx) < 2:
        return None

    m = int(rng.choice(merchant_ids))
    typical = float(np.mean([r[1] for r in prior_tx]))
    amount = float(typical * float(params.get("amount_multiplier", 1)))
    age = int(urow.account_age_days_at_start + target_day)

    return {
        "transaction_id": new_tx_id(), "user_id": int(u), "timestamp": start,
        "amount": amount, "merchant_id": m, "merchant_category": cat_lookup[m],
        "device_id": f"dev_{u}_0",
        "lat": float(urow.home_lat + rng.normal(0, 0.05)),
        "lon": float(urow.home_lon + rng.normal(0, 0.05)),
        "channel": "ecom", "account_age_days": age, "is_fraud": 1,
        "fraud_type": "ai_impersonation", "case_id": case_id, "ring_id": None,
        "three_ds_result": "passed_first_try", "three_ds_failures_before_result": 0,
    }
