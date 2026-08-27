import json
import os
import re
import time
import random
import logging
import urllib.request
from pathlib import Path
from datetime import timedelta
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
LOCAL_MODEL = os.getenv("LOCAL_MODEL", "qwen3.5-4b")
USE_LOCAL = os.getenv("USE_LOCAL", "false").lower() == "true"
LOCAL_RETRIES = int(os.getenv("LOCAL_RETRIES", "2"))
LOCAL_TEMPERATURE = float(os.getenv("LOCAL_TEMPERATURE", "0.40"))
# Keep local requests compact so Qwen3.5 4B Q_K_S does not burn the full budget
# on reasoning instead of emitting the JSON payload. Raised from 1024 to 2048
# alongside the extended (6-14 turn) fraud transcripts: with LLM_BATCH_SIZE=1
# each call is a single case, so this is comfortably ahead of the ~800-1000
# tokens a 14-turn transcript + structured fields actually needs, leaving
# margin for occasional hidden reasoning without being wastefully large.
LOCAL_MAX_TOKENS = int(os.getenv("LOCAL_MAX_TOKENS", "4096"))
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
                                "maxItems": 14,
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

TRANSCRIPT_VISION = """Write realistic payment-fraud and scam transcripts for a prototype fraud-detection project.
Keep every case grounded in the playbook vision: short, believable consumer payment scenarios that show
how an attacker pressures a target into a transfer, credential handoff, card payment, crypto move, gift
card purchase, or remote-access action. Avoid generic call-center roleplay, avoid legal or medical drama,
and avoid mention of training, prompts, policy, or model behavior.

Fraud transcripts must follow these rules:
- Between 6 and 14 turns -- shorter for quick refusals, longer where more back-and-forth persuasion or verification fits naturally.
- Speakers alternate between attacker and target.
- The attacker should sound specific, urgent, and operationally plausible.
- The target should show hesitation, verification attempts, refusal, or compliance that matches the labeled outcome.
- The transcript should make the requested action and final outcome obvious from the dialogue itself.

Benign transcripts must follow these rules:
- Exactly 4 turns.
- Speakers alternate customer and agent.
- The dialogue should be routine account or support conversation with no fraud pressure.
- Keep it realistic, concise, and clearly non-fraudulent.
"""


# CHANGED (bugfix): the judge call (_judge_final_turn) needs a tiny {"matches": bool,
# "reason": str} response, but it was calling call_structured() with no schema
# argument at all -- which meant it silently inherited LOCAL_RESPONSE_FORMAT (the
# FRAUD schema, requiring a "cases" array with a full 6-10 turn transcript) under
# USE_LOCAL=true. LM Studio's strict json_schema mode cannot produce a
# {"matches": ...} object while being told the schema requires "cases", so nearly
# every judge call failed outright -- which is why validate_fraud_case's judge
# fallback was rejecting good transcripts (~18/19 of all fraud rejections in one
# observed run were exactly this failure, not real content problems). This gives the
# judge its own minimal schema so it can actually succeed.
LOCAL_JUDGE_RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "outcome_judge_result",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "matches": {"type": "boolean"},
                "reason": {"type": "string"},
            },
            "required": ["matches", "reason"],
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
    print("Models available to this key (only ones supporting generateContent):")
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


def _structured_local(system, prompt, max_tokens, retries, response_format=None):
    # Qwen3-family models reason by default. In LM Studio that reasoning is returned
    # separately as `reasoning_content`; it can consume the entire token budget and
    # leave `message.content` empty. `/no_think` is the Qwen chat-template control
    # token for a non-reasoning response, which is the appropriate mode for this
    # bounded JSON-generation task.
    # CHANGED (bugfix): response_format now defaults to the FRAUD schema only when the
    # caller doesn't specify one, instead of _always_ reading the module-level
    # LOCAL_RESPONSE_FORMAT global. Previously every local call -- fraud, benign, and
    # judge alike -- was forced through LOCAL_FRAUD_RESPONSE_FORMAT (attacker/target
    # speakers, 6-10 turns) because LOCAL_BENIGN_RESPONSE_FORMAT was defined but never
    # actually wired to anything. That is why 100% of benign transcripts were coming
    # back with attacker/target speakers repeated instead of alternating customer/agent
    # turns, and failing validate_benign_case's turn-count/speaker check every time.
    if response_format is None:
        response_format = LOCAL_RESPONSE_FORMAT
    local_system = (
        system
        + "\n/no_think\nRespond with ONLY the JSON object, no markdown fences, no other text."
    )
    last_error = None
    local_retries = max(1, min(retries, LOCAL_RETRIES))
    for attempt in range(local_retries):
        try:
            local_prompt = (
                prompt
                + "\n\nReturn only valid JSON. Do not add explanations, markdown, or reasoning."
                + " Keep each case concise and self-contained."
                + " Make each case feel distinct: vary the opening, pressure style, wording,"
                + " and ending so cases do not read like repeats."
                + " /no_think"
            )
            resp = _local_client.chat.completions.create(
                model=LOCAL_MODEL, max_tokens=max_tokens, temperature=LOCAL_TEMPERATURE,
                response_format=response_format,
                messages=[{"role": "system", "content": local_system},
                          # This LM Studio Qwen3.5 template ignores the system-level
                          # control token, so repeat it as the final user instruction.
                          {"role": "user", "content": local_prompt}],
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


def call_structured(system: str, prompt: str, max_tokens: int = 4096, retries: int = 4,
                     local_response_format=None):
    """Returns a parsed dict, or None if every attempt failed (caller supplies the fallback).

    local_response_format: only consumed by the "local" (LM Studio) provider, which is
    the only path that requires a fixed JSON-schema object per call site. Gemini/
    Anthropic/OpenAI paths use response_mime_type="application/json" or
    response_format={"type": "json_object"} generically and don't need a schema
    argument here. Defaults to the fraud schema (LOCAL_RESPONSE_FORMAT) inside
    _structured_local when omitted, preserving prior behavior for existing callers
    that don't pass this."""
    if ACTIVE_PROVIDER == "local":
        return _structured_local(system, prompt, max_tokens, retries, response_format=local_response_format)
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
    "tax authority overdue payment notice",
    "utility disconnection final notice",
    "employer payroll correction request",
    "romance relationship financial help",
    "lottery or prize claim fee",
    "subscription auto-renewal dispute",
    "cryptocurrency exchange account freeze",
    "government benefit re-verification",
    "landlord or rental deposit refund",
]

# ---------- CHANGED: batched fraud-case generation ----------
# One call now produces BATCH_SIZE independent cases instead of one call per case.

TARGET_PERSONAS = [
    "an older adult who is not very tech-savvy and tends to trust authority figures",
    "a busy professional who is distracted and answers on autopilot between tasks",
    "a cautious person who has read about scams before and gets suspicious quickly",
    "a young adult who is anxious about doing something wrong and eager to comply fast",
    "a skeptical person who pushes back hard and asks pointed verification questions",
    "a parent who is preoccupied with childcare and answers quickly without full attention",
    "a small-business owner who is used to vendor and supplier calls and lowers their guard for anything sounding official",
    "someone less familiar with local bank procedures who defers to anyone who sounds official",
    "a person under financial stress who is more receptive to urgent money-related requests",
    "a confident, tech-savvy person who questions technical details but can still be swayed by specific-sounding jargon",
]

# CHANGED (was): BATCH_SYSTEM previously hard-coded "transaction_attempted MUST be
# true for every generated case" and explicitly forbade refusal/hesitation endings.
# That is what was diagnosed as the root cause of the LM Studio reasoning-budget
# failure: a persona like "cautious ... gets suspicious quickly" pulls directly
# against a mandatory-compliance instruction with zero valid escape outcome, so the
# model has to reason its way through that contradiction on every single case before
# it can commit to JSON -- which is exactly the multi-thousand-token internal debate
# observed in the LM Studio log, ending in finish_reason='length' before any content
# was emitted. The fix is state-conditioned generation: the OUTCOME is decided in
# Python *before* the call (see _assign_outcomes below) and handed to the model as a
# fact to dramatize, not a puzzle to solve. This removes the ambiguity the model was
# spending its reasoning budget on, independent of any LM Studio setting.
OUTCOME_STATES = [
    "refused",
    "deferred_for_verification",
    "engaged_no_action",
    "credential_shared",
    "payment_attempted",
    "payment_completed",
]
# Deliberately skewed toward outcomes useful to this project, not a claim about
# real-world social-engineering success rates. Every state stays genuinely present.
# Slightly favor transaction-producing endings so the downstream tabular model
# actually sees enough ai_impersonation examples after the temporal split.
OUTCOME_WEIGHTS = [0.10, 0.10, 0.08, 0.15, 0.28, 0.29]

OUTCOME_GUIDANCE = {
    "refused": (
        "The target must end the conversation by clearly refusing to comply -- e.g. "
        "hanging up, stating they will not do this, or explicitly declining. No "
        "money, credentials, or codes are shared. This is a valid, common, and "
        "REQUIRED outcome for this case -- do not soften it into hesitation."
    ),
    "deferred_for_verification": (
        "The target must end the conversation by declining to act NOW and instead "
        "saying they will verify independently first -- e.g. 'I'll call the bank "
        "directly' or 'I'll check this myself and call you back.' No money, "
        "credentials, or codes are shared in this conversation."
    ),
    "engaged_no_action": (
        "The target stays engaged, asks questions, may seem uncertain, but the "
        "conversation ends WITHOUT the target taking any concrete action -- no "
        "money sent, no credentials or codes given, no explicit refusal either. "
        "The conversation simply ends inconclusively (e.g. gets cut off, target "
        "says they need to think about it with no firm refusal or agreement)."
    ),
    "credential_shared": (
        "The target ends the conversation by providing or clearly agreeing to "
        "provide a LOGIN-STYLE authentication credential -- a password, PIN, "
        "security-question answer, or one-time code -- but does NOT explicitly "
        "send money or authorize a payment in this conversation. Do NOT use this "
        "outcome for a full payment card number, CVV, or expiry date: disclosing "
        "complete card details is payment-card compromise, not a login-credential "
        "handover -- use 'payment_attempted' or 'payment_completed' for that "
        "content instead, since a usable card number is functionally the same as "
        "an authorized transaction attempt."
    ),
    "payment_attempted": (
        "The target ends the conversation by clearly agreeing to send money, "
        "authorize a payment, or make a transfer -- e.g. 'Okay, I'll make the "
        "transfer now.' The conversation ends at the point of agreement/attempt; "
        "it does not need to state the transfer definitely succeeded."
    ),
    "payment_completed": (
        "The target ends the conversation by both agreeing to AND confirming "
        "completion of a payment or transfer -- e.g. 'Okay, I've just sent it' or "
        "'Done, the transfer went through.' The final message must show completed "
        "action, not just intent."
    ),
}

BATCH_SYSTEM = """You are a synthetic conversational data generator for an Authorized Push Payment (APP)
fraud research benchmark.

You will be given a list of (pretext, persona, assigned_outcome, case_id) quadruples.

For EACH quadruple, generate one realistic synthetic scam conversation between:

- Attacker: impersonating a bank, courier, technical support agent, family member,
  investment representative, or another trusted authority, based on the given pretext.
- Target: a victim whose reactions are consistent with the given persona.

CRITICAL: each case has an assigned_outcome. The conversation's ending is NOT a free
choice -- it is a fact you are dramatizing, not a decision you make. The persona
describes HOW the target behaves along the way (how much they question, resist, or
comply); the assigned_outcome describes WHERE the conversation ends. A skeptical
persona assigned "refused" should refuse convincingly. A trusting persona assigned
"payment_attempted" should comply in a way that fits their trust. Do not soften,
hedge, or default to compliance regardless of what outcome was assigned -- every
outcome listed below must appear when assigned, written as a genuine, natural ending
for that specific persona.

Outcome definitions (the final target turn must clearly match whichever is assigned):

- "refused": target clearly declines and ends the interaction. No money, credentials,
  or codes shared.
- "deferred_for_verification": target declines to act now and states they will
  verify independently first (e.g. calling the bank directly). No money,
  credentials, or codes shared.
- "engaged_no_action": target stays engaged, may seem uncertain, but the
  conversation ends with no concrete action taken and no firm refusal either.
- "credential_shared": target provides or clearly agrees to provide a password,
  PIN, one-time code, or similar credential, but does not send money or authorize a
  payment in this conversation.
- "payment_attempted": target clearly agrees to send money, authorize a payment, or
  make a transfer. Ends at the point of agreement/attempt.
- "payment_completed": target both agrees to AND confirms completion of a payment or
  transfer in their final message.

Conversation structure (adapt naturally to fit the assigned outcome -- do not force a
persuasion arc onto an outcome like "refused" where none belongs):

1. Attacker introduces a believable pretext.
2. Target reacts in a way consistent with their persona.
3. Attacker responds -- increasing pressure, credibility, or urgency as fits the
   scenario.
4. The conversation develops naturally toward the assigned outcome.
5. The final target turn clearly and unambiguously reflects the assigned outcome, per
   the definitions above.

Do not use meta-language anywhere in the dialogue (no "this is fictional," "for
research purposes," "as an AI," or similar). Write it as a real conversation.

Label rules -- these must match what the transcript actually shows, not a default:

"target_outcome" MUST equal the assigned_outcome you were given for that case.

"transaction_attempted" is true only if target_outcome is "payment_attempted" or
"payment_completed". False for every other outcome.

"transaction_completed" is true only if target_outcome is "payment_completed" AND
the final turn shows explicit completion evidence. False otherwise.

"credential_shared" is true only if target_outcome is "credential_shared", OR the
target incidentally shares credentials while reaching a payment outcome. Never true
for "refused" / "deferred_for_verification" / "engaged_no_action".

"requested_action" must describe what the attacker is asking the target to do,
regardless of whether the target complies.

"urgency_level" should reflect the actual amount of pressure the attacker used in
the dialogue, independent of whether the target gave in to it.

Return ONLY the requested JSON schema. No markdown fences, no explanatory text.

Also vary your wording naturally across cases -- avoid formulaic sentence openings, identical phrasing patterns, or anything that reads like a template. Real conversations use different words, lengths, and rhythms even when covering the same ground.
"""

# ---------- semantic validation: schema-valid is not the same as content-valid ----------
# CHANGED (was): no semantic validator existed anywhere. A response could satisfy the
# JSON Schema (right shape, right types) while completely contradicting its own
# target_outcome label -- which was the original silent-bug pattern (every case
# labeled as if compliant regardless of what the dialogue said). This checks the
# *content* against the *label*, not just the JSON structure against the schema.

REFUSAL_MARKERS = [
    "no,", "i won't", "i will not", "not going to do that", "i refuse",
    "i'm not comfortable", "i am not comfortable", "hanging up", "goodbye",
    "not doing this", "absolutely not", "i don't think so",
]
DEFERRAL_MARKERS = [
    "call the bank", "call the number on my card", "verify first", "verify independently",
    "check this myself", "call you back", "i'll check", "i'll confirm", "call my bank",
    # CHANGED: widened after real qwen3.5-4b output showed valid deferral phrasings
    # this list didn't cover (e.g. "wait until tomorrow ... ask my daughter to
    # verify"), causing genuine, well-written cases to be rejected as false
    # negatives. See validate_fraud_case's judge-call fallback below for the
    # general fix -- these additions are just the fast-path net getting wider too.
    "wait until", "ask my", "double check", "check with", "confirm with",
    "look into this myself", "reach out to", "contact them directly",
    "check my bank app", "log in directly", "check for alerts myself",
]
PAYMENT_ATTEMPT_MARKERS = [
    "i'll send", "i'll make the transfer", "i'll transfer", "i'll authorize",
    "sending the money", "i'll pay", "okay, i'll", "i'll do it now", "making the payment",
    "i'll complete the payment", "i'll wire", "sending it now", "i'll do the transfer",
    "i'll go ahead and", "let me send", "i'll process the payment",
]
PAYMENT_COMPLETED_MARKERS = [
    "i've sent", "i have sent", "it's done", "just sent", "went through",
    "i've transferred", "i have transferred", "payment is complete", "i've paid",
    "transfer is complete", "sent it", "it's sent", "all done", "just paid",
    "money is on its way", "transfer went through",
]
CREDENTIAL_MARKERS = [
    "here's my", "here is my", "the code is", "my password is", "my pin is",
    "one-time code", "otp is", "i'll give you the code", "here's the code",
    "the number is", "sending you the code", "here's my code",
]
META_LANGUAGE_MARKERS = [
    "this is fictional", "for research purposes", "as an ai", "this is a simulation",
    "hypothetical scenario", "this is just an example", "for training purposes",
]

# CHANGED: CREDENTIAL_MARKERS' generic phrases ("here's my", "the number is") match
# a PIN/password handover and a full payment-card handover equally -- they only
# detect THAT something was disclosed, not WHAT. Real qwen3.5-4b output confirmed
# this: a full card number + CVV + expiry got accepted under "credential_shared"
# (see CHANGELOG), which is wrong -- a usable card number is payment-card
# compromise, not a login credential, and belongs under payment_attempted /
# payment_completed instead. This is a targeted content check for that one gap,
# not a general rewrite of the outcome taxonomy.
CARD_NUMBER_PATTERN = re.compile(r"(?:\d[ -]?){13,19}")
CARD_CONTEXT_MARKERS = ["cvv", "cvc", "expiry", "exp date", "expiration date", "card number"]

def _discloses_full_card_data(text: str) -> bool:
    """True if `text` contains a card-number-shaped digit run alongside a
    CVV/expiry-style marker -- i.e. enough to attempt a charge, not just a
    login credential. Deliberately narrow (both signals required) so it
    doesn't flag an OTP or account-number-only disclosure, which is exactly
    what credential_shared is meant to cover."""
    if not CARD_NUMBER_PATTERN.search(text):
        return False
    return any(marker in text for marker in CARD_CONTEXT_MARKERS)

# ---------- adaptive fallback: an LLM judge for cases the keyword lists can't ----------
# CHANGED: keyword matching alone proved too brittle against a live model's actual
# range of phrasing -- real qwen3.5-4b output included valid, unambiguous outcome
# evidence (e.g. "I'll wait until tomorrow ... ask my daughter to verify") that no
# fixed phrase list will ever fully anticipate, causing good cases to be rejected as
# false negatives (confirmed directly against a real generation log). Rather than
# permanently chasing an ever-growing phrase list, the keyword lists now serve as a
# FAST PASS (skip the extra call when there's a confident, unambiguous match) and an
# LLM judge call is the fallback for anything the keyword lists don't confidently
# resolve either way. This adapts to new phrasing automatically -- no manual list
# maintenance required going forward.
JUDGE_SYSTEM = """You are a strict validator for synthetic fraud-scenario transcripts.
You will be given one conversation's final target turn, plus the outcome that turn is
supposed to demonstrate. Decide whether the final turn CLEARLY and UNAMBIGUOUSLY
demonstrates that specific outcome -- not a nearby or softer version of it.

Outcome definitions:
- "refused": target clearly declines and ends the interaction.
- "deferred_for_verification": target declines to act now and will verify independently
  first (any way of expressing "I'll check/confirm this through another channel before
  doing anything" counts, however it's phrased).
- "engaged_no_action": target stays engaged/uncertain but takes no concrete action and
  does not firmly refuse either.
- "credential_shared": target provides or clearly agrees to provide a password, PIN,
  code, or similar credential.
- "payment_attempted": target clearly agrees to send money, authorize a payment, or
  make a transfer (agreement/attempt, not necessarily confirmed completion).
- "payment_completed": target both agrees to AND confirms a payment or transfer is done.

Return ONLY this JSON object, no markdown fences, no other text:
{"matches": true or false, "reason": "one short sentence"}
"""


def _judge_final_turn(final_target_text: str, assigned_outcome: str) -> tuple[bool, str]:
    """Fallback for cases the keyword fast-path can't confidently resolve. Makes one
    small structured call (cheap: single short-answer JSON, no transcript generation)
    asking whether the final turn matches the assigned outcome. On any call failure,
    fails closed (treated as non-matching) -- an unreachable judge must never cause a
    case to be silently accepted."""
    prompt = (
        f'assigned_outcome: "{assigned_outcome}"\n'
        f'final target turn: "{final_target_text}"\n\n'
        "Does this final turn clearly demonstrate the assigned outcome?"
    )
    result = call_structured(JUDGE_SYSTEM, prompt, max_tokens=300, retries=2,
                              local_response_format=LOCAL_JUDGE_RESPONSE_FORMAT)
    if result is None or "matches" not in result:
        return False, "judge call failed or returned no usable response (failing closed)"
    return bool(result["matches"]), str(result.get("reason", ""))


def validate_fraud_case(case: dict, assigned_outcome: str, use_judge_fallback: bool = True) -> tuple[bool, str]:
    """Checks a single parsed case against its assigned_outcome. Returns
    (is_valid, reason). reason is empty on success, otherwise names the specific
    failing check so rejection logs are actionable instead of a bare 'invalid'.

    use_judge_fallback=True (default) means a keyword-list non-match falls through to
    _judge_final_turn instead of an immediate rejection -- this is what makes
    validation adapt to phrasing the fixed lists don't cover. Set False only for pure
    offline/unit testing where no LLM call should happen."""
    transcript = case.get("transcript")
    if not isinstance(transcript, list):
        return False, "transcript missing or not a list"
    if len(transcript) > 14:
        return False, f"transcript has too many turns ({len(transcript)} > 14)"

    speakers = [t.get("speaker") for t in transcript]
    if any(s not in ("attacker", "target") for s in speakers):
        return False, f"transcript contains an unexpected speaker value: {speakers}"
    for i in range(1, len(speakers)):
        if speakers[i] == speakers[i - 1]:
            return False, f"transcript speakers do not alternate at turn {i}"

    full_text = " ".join(t.get("text", "") for t in transcript).lower()
    for marker in META_LANGUAGE_MARKERS:
        if marker in full_text:
            return False, f"meta-language leakage detected ('{marker}')"

    if case.get("target_outcome") != assigned_outcome:
        return False, (
            f"target_outcome '{case.get('target_outcome')}' does not match "
            f"assigned outcome '{assigned_outcome}'"
        )

    # Only the FINAL target turn is authoritative for outcome evidence -- a
    # conversation can dip through refusal-sounding language mid-way and still
    # resolve to compliance (or vice versa), so checking any earlier turn would
    # produce false rejections/acceptances on a perfectly valid transcript.
    target_turns = [t for t in transcript if t.get("speaker") == "target"]
    if not target_turns:
        return False, "no target turns in transcript"
    final_target_text = target_turns[-1].get("text", "").lower()

    outcome_checks = {
        "refused": REFUSAL_MARKERS,
        "deferred_for_verification": DEFERRAL_MARKERS,
        "credential_shared": CREDENTIAL_MARKERS,
        "payment_attempted": PAYMENT_ATTEMPT_MARKERS,
        "payment_completed": PAYMENT_COMPLETED_MARKERS,
    }
    if assigned_outcome in outcome_checks:
        markers = outcome_checks[assigned_outcome]
        keyword_match = any(m in final_target_text for m in markers)
        if not keyword_match:
            # CHANGED: a keyword miss no longer means an instant rejection. Fixed
            # phrase lists can't keep pace with a generative model's actual range of
            # wording (confirmed against real qwen3.5-4b output that used valid but
            # unlisted phrasings). Fall through to the adaptive judge before
            # rejecting -- this is what lets validation keep up with new phrasing
            # without manual list maintenance every time a new failure surfaces.
            if use_judge_fallback:
                judge_match, judge_reason = _judge_final_turn(final_target_text, assigned_outcome)
                if not judge_match:
                    return False, (
                        f"final target turn does not demonstrate '{assigned_outcome}' "
                        f"(keyword fast-path missed, judge also rejected: {judge_reason})"
                    )
            else:
                return False, (
                    f"final target turn does not contain evidence matching "
                    f"'{assigned_outcome}' (checked against {len(markers)} known phrasings, "
                    f"judge fallback disabled)"
                )
    # "engaged_no_action" has no positive marker set by design -- a keyword hit for
    # a DIFFERENT outcome is a signal, not an automatic rejection, since a stray
    # matching phrase doesn't always mean the outcome is wrong in substance. The
    # judge gets the final say when the fast-path signal is ambiguous.
    else:
        for other_outcome, markers in outcome_checks.items():
            if any(m in final_target_text for m in markers):
                if use_judge_fallback:
                    judge_match, judge_reason = _judge_final_turn(final_target_text, "engaged_no_action")
                    if not judge_match:
                        return False, (
                            f"assigned 'engaged_no_action' but final turn matches "
                            f"'{other_outcome}' evidence and judge agrees it does not "
                            f"demonstrate engaged_no_action: {judge_reason}"
                        )
                else:
                    return False, (
                        f"assigned 'engaged_no_action' but final turn matches "
                        f"'{other_outcome}' evidence -- outcome label does not match content"
                    )
                break

    # CHANGED: CREDENTIAL_MARKERS' generic phrasing let a full card-number +
    # CVV/expiry handover pass validation as "credential_shared" (confirmed
    # against real qwen3.5-4b output -- see CHANGELOG). That content is
    # payment-card compromise, not a login-credential handover, and it was
    # silently costing generation yield too, since materialize_llm_transaction
    # can never turn a credential_shared case into a transaction by design.
    # Reject here so it retries into a more accurate outcome instead of
    # reaching transcripts.jsonl mislabeled.
    if assigned_outcome == "credential_shared" and _discloses_full_card_data(final_target_text):
        return False, (
            "assigned 'credential_shared' but final target turn discloses full "
            "payment-card data (card number + CVV/expiry) -- that is payment-card "
            "compromise, not a login-credential handover; should be "
            "'payment_attempted' or 'payment_completed' instead"
        )

    expected_attempted = assigned_outcome in ("payment_attempted", "payment_completed")
    if bool(case.get("transaction_attempted")) != expected_attempted:
        return False, (
            f"transaction_attempted={case.get('transaction_attempted')} inconsistent "
            f"with outcome '{assigned_outcome}' (expected {expected_attempted})"
        )

    expected_completed = assigned_outcome == "payment_completed"
    if bool(case.get("transaction_completed")) != expected_completed:
        return False, (
            f"transaction_completed={case.get('transaction_completed')} inconsistent "
            f"with outcome '{assigned_outcome}' (expected {expected_completed})"
        )

    if case.get("transaction_completed") and not case.get("transaction_attempted"):
        return False, "transaction_completed=True but transaction_attempted=False"

    if assigned_outcome in ("refused", "deferred_for_verification", "engaged_no_action"):
        if case.get("credential_shared"):
            return False, f"credential_shared=True is invalid for outcome '{assigned_outcome}'"

    return True, ""


def _assign_outcomes(case_ids: list[str], rng_random=random) -> dict[str, str]:
    """Picks one outcome state per case_id, weighted by OUTCOME_WEIGHTS. Returns a
    dict of case_id -> outcome so the caller can pair it with the case's other
    identifying fields before building the prompt."""
    return {
        cid: rng_random.choices(OUTCOME_STATES, weights=OUTCOME_WEIGHTS, k=1)[0]
        for cid in case_ids
    }


def _fallback_case(pretext: str, case_id: str, assigned_outcome: str = "refused") -> dict:
    """Used ONLY for the pre-generation placeholder shape when constructing a
    rejection record -- never returned as if it were a real accepted case. A
    rejected/failed case must never silently default to transaction_attempted=True;
    that was the original fabrication bug. This placeholder is always
    non-transacting regardless of assigned_outcome, since it exists to be logged as
    rejected, not materialized."""
    return {
        "case_id": case_id,
        "transcript": [
            {"speaker": "attacker", "text": f"Hello, this is regarding an urgent matter about {pretext} on your account."},
            {"speaker": "target", "text": f"Wait, who is this? I wasn't expecting a call about {pretext}."},
            {"speaker": "attacker", "text": "This is time-sensitive -- your account will be locked if we don't act now."},
            {"speaker": "target", "text": "I'm not comfortable doing this without verifying first. I'll call the number on my card."},
        ],
        "target_outcome": "deferred_for_verification",
        "transaction_attempted": False,
        "transaction_completed": False,
        "credential_shared": False,
        "amount_multiplier": float(np.random.uniform(4.0, 9.0)),
        "urgency_level": "medium",
        "pretext_category": pretext,
    }


def _call_batch_for_outcomes(system_prompt: str, quadruples: list[tuple[str, str, str, str]], max_tokens: int) -> dict:
    """Factors out the repair-retry call shape shared by the main batch call and the
    single-case repair retry: builds the prompt from (pretext, persona, outcome,
    case_id) quadruples and returns the parsed response (or None on failure)."""
    prompt_lines = "\n".join(
        f"- pretext: '{p}', persona: '{persona}', assigned_outcome: '{o}', case_id: '{c}'"
        for p, persona, o, c in quadruples
    )
    prompt = (
        "You are generating synthetic APP-fraud transcripts for a prototype benchmark.\n"
        "Use only the instructions in this request. Do not rely on any external file.\n"
        "Keep each case realistic, on-vision, and concise enough for a local Qwen 3.5 4B model.\n"
        "Do not include commentary, analysis, or markdown.\n\n"
        f"Generate one synthetic scam conversation for each of these cases:\n{prompt_lines}"
    )
    # Explicit rather than relying on _structured_local's implicit fraud-schema
    # default -- every call site should now name its own schema so a future new
    # call path can't silently inherit the wrong one the way benign/judge did.
    return call_structured(system_prompt, prompt, max_tokens=max_tokens,
                            local_response_format=LOCAL_FRAUD_RESPONSE_FORMAT)


def generate_llm_case_batch(pretext_case_pairs, max_tokens: int | None = None):
    """
    Generates len(pretext_case_pairs) cases in a single API call instead of one call per
    case. pretext_case_pairs: list of (pretext, case_id) tuples.
    Returns: dict of case_id -> params for every ACCEPTED case only. A rejected or
    unrecoverable case is simply absent from the returned dict -- callers must treat a
    missing case_id as "skip this transaction," not assume every requested case_id is
    present.

    CHANGED: state-conditioned generation replaces forced-outcome generation. Each
    case is assigned one of six outcome states in Python before the call
    (_assign_outcomes), the LLM dramatizes that assigned state rather than choosing
    freely, and every returned case is semantically validated (validate_fraud_case)
    against its assigned outcome -- not just checked for JSON-schema validity. An
    invalid case gets exactly one individual repair retry with the same assigned
    outcome; if still invalid, it is logged with its specific rejection_reason and
    excluded from the returned dict. This never fabricates a placeholder transaction
    for a failed case -- rejection is a valid terminal state, not an error to paper
    over with invented data.
    """
    # 6-14 turn transcripts with 5+ structured fields need more room than the old
    # fixed 4-turn format did. LOCAL_MAX_TOKENS already accounts for hidden reasoning
    # separately from this output budget.
    max_tokens = max_tokens if max_tokens is not None else (LOCAL_MAX_TOKENS if ACTIVE_PROVIDER == "local" else 1536)

    case_ids = [c for _, c in pretext_case_pairs]
    outcomes = _assign_outcomes(case_ids)
    personas = {c: random.choice(TARGET_PERSONAS) for c in case_ids}
    quadruples = [(p, personas[c], outcomes[c], c) for p, c in pretext_case_pairs]

    parsed = _call_batch_for_outcomes(BATCH_SYSTEM, quadruples, max_tokens)

    model_name = {"gemini": GEMINI_MODEL, "anthropic": ANTHROPIC_MODEL, "openai": OPENAI_MODEL, "local": LOCAL_MODEL}[ACTIVE_PROVIDER]
    n_requested = len(pretext_case_pairs)

    if parsed is None or "cases" not in parsed:
        logger.error(
            "Batch of %d cases returned no usable response from %s (model=%s). "
            "See the WARNING lines above for the real exception. Every case in this "
            "batch will be rejected and logged (not fabricated).", n_requested, ACTIVE_PROVIDER, model_name,
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

    # CHANGED: validate every returned case against its assigned outcome. A case
    # that fails validation gets exactly one individual repair retry (same assigned
    # outcome, single-case call) -- if it's still invalid, it is REJECTED: logged
    # with its specific reason and excluded from `results` entirely. It is never
    # patched with a deterministic placeholder and never defaults
    # transaction_attempted to True. `rule_generator.py`'s caller loop must treat a
    # missing case_id in the returned dict as "skip this transaction."
    results = {}
    n_accepted = 0
    n_rejected = 0
    for pretext, case_id in pretext_case_pairs:
        assigned_outcome = outcomes[case_id]
        case = by_id.get(case_id)

        if case is None:
            record = {
                "case_id": case_id, "pretext": pretext, "transcript": "",
                "accepted": False, "assigned_outcome": assigned_outcome,
                "rejection_reason": "case_id absent from model response (batch under-return)",
                "label": 1,
            }
            with TRANSCRIPT_PATH.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            n_rejected += 1
            continue

        is_valid, reason = validate_fraud_case(case, assigned_outcome)

        if not is_valid:
            # Single individual repair retry, same assigned outcome, single-case call.
            logger.warning(
                "Case %s failed validation (%s) -- attempting one repair retry.",
                case_id, reason,
            )
            repair_quad = [(pretext, personas[case_id], assigned_outcome, case_id)]
            repaired = _call_batch_for_outcomes(BATCH_SYSTEM, repair_quad, max_tokens)
            repaired_case = None
            if repaired and "cases" in repaired:
                repaired_by_id = {c["case_id"]: c for c in repaired.get("cases", []) if "case_id" in c}
                repaired_case = repaired_by_id.get(case_id)
            if repaired_case is not None:
                is_valid, reason = validate_fraud_case(repaired_case, assigned_outcome)
                if is_valid:
                    case = repaired_case

        if not is_valid:
            transcript_lines = [
                f"{t.get('speaker','unknown')}: {t.get('text','')}"
                for t in (case.get("transcript", []) if isinstance(case, dict) else [])
            ]
            record = {
                "case_id": case_id, "pretext": pretext,
                "transcript": "\n".join(transcript_lines),
                "accepted": False, "assigned_outcome": assigned_outcome,
                "rejection_reason": reason, "label": 1,
            }
            with TRANSCRIPT_PATH.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            logger.error("Case %s rejected after repair retry: %s", case_id, reason)
            n_rejected += 1
            continue

        transcript_lines = [f"{t.get('speaker','unknown')}: {t.get('text','')}" for t in case.get("transcript", [])]
        params = {
            "transaction_attempted": bool(case.get("transaction_attempted", False)),
            "transaction_completed": bool(case.get("transaction_completed", False)),
            "credential_shared": bool(case.get("credential_shared", False)),
            "target_outcome": str(case.get("target_outcome", assigned_outcome)),
            "amount_multiplier": float(case.get("amount_multiplier", np.random.uniform(4.0, 8.0))),
            "urgency_level": str(case.get("urgency_level", "medium")),
            # CHANGED: pretext_category used to trust the model's own free-text echo
            # of the pretext (case.get("pretext_category", pretext)). Observed real
            # output showed the same input pretext coming back as three different
            # strings across calls (e.g. "government_benefit_verification" vs
            # "government_benefit_re-verification" vs the literal input string) --
            # the model is generating this field, not copying it. Since the input
            # `pretext` is already known ground truth, use it directly so every case
            # from the same PRETEXTS entry groups identically downstream (this field
            # is read by impersonation_diagnostics.py's categorical value_counts).
            "pretext_category": pretext,
            "fallback": False,
            "label": 1,
        }
        record = {
            "case_id": case_id, "pretext": pretext,
            "transcript": "\n".join(transcript_lines),
            "accepted": True, "assigned_outcome": assigned_outcome, **params,
        }
        with TRANSCRIPT_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        results[case_id] = params
        n_accepted += 1

    logger.info(
        "Batch summary: %d/%d cases accepted, %d rejected.",
        n_accepted, len(pretext_case_pairs), n_rejected,
    )

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
    "updating a mailing address",
    "asking how to redeem a loyalty reward",
    "checking current account balance",
    "asking about branch operating hours",
    "requesting a replacement debit card for wear and tear",
    "clarifying a line item on a recent statement",
    "asking about international transaction fees",
    "updating a phone number on file",
    "asking how to set up a recurring bill payment",
]

BENIGN_BATCH_SYSTEM = """You are a synthetic conversational data generator for a customer-service benchmark.
You will be given a list of (topic, case_id) pairs. For EACH pair, generate one realistic, ORDINARY support conversation
between a Customer and an Agent about that topic -- no fraud, no urgency, no request to move money or share a one-time
code, no impersonation, no persuasion arc, no escalating pressure. This is a routine, low-stakes support interaction:
the customer asks a normal question, the agent answers it helpfully, and the conversation resolves without drama.
Return exactly 4 utterances per case in this order: customer, agent, customer, agent.
Each utterance should normally contain 8-20 words.
Vary wording and tone across cases -- some customers are brief, some chatty, some slightly annoyed but never
manipulated or pressured into anything.

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


# CHANGED (was): the original prompt copy-pasted the fraud conversation's own shape
# ("hesitation -> persuasion -> compliance") into the benign class's instructions,
# which would teach a future transcript classifier the labels backwards -- the
# supposedly-negative class was structurally identical to the positive class. These
# markers catch that specific contamination pattern if it recurs.
BENIGN_CONTAMINATION_MARKERS = [
    "wire transfer", "one-time code", "verification code", "urgent", "immediately",
    "account will be locked", "act now", "send money", "gift card", "crypto",
    "password is", "pin is", "authorize the payment",
]


def validate_benign_case(case: dict) -> tuple[bool, str]:
    """Checks a single parsed benign case for structural validity and absence of
    fraud-shape contamination. Returns (is_valid, reason)."""
    transcript = case.get("transcript")
    if len(transcript) > 10:
        return False, f"transcript has too many turns ({len(transcript)} > 10)"

    speakers = [t.get("speaker") for t in transcript]
    if speakers != ["customer", "agent", "customer", "agent"]:
        return False, f"transcript speaker order must be customer/agent/customer/agent, got {speakers}"

    full_text = " ".join(t.get("text", "") for t in transcript).lower()
    for marker in META_LANGUAGE_MARKERS:
        if marker in full_text:
            return False, f"meta-language leakage detected ('{marker}')"
    for marker in BENIGN_CONTAMINATION_MARKERS:
        if marker in full_text:
            return False, f"fraud-shape contamination detected ('{marker}') -- not a genuinely benign transcript"

    return True, ""


def _fallback_benign_case(topic: str, case_id: str) -> dict:
    return {
        "case_id": case_id,
        "transcript": [
            {"speaker": "customer", "text": f"Hi, I had a question about {topic}."},
            {"speaker": "agent", "text": "Sure, happy to help with that."},
            {"speaker": "customer", "text": "That answers it, thanks."},
            {"speaker": "agent", "text": "Glad I could help -- anything else?"},
        ],
    }


def generate_benign_case_batch(topic_case_pairs, max_tokens: int | None = None):
    """Batched version of generate_benign_case: one call for the whole batch. Writes
    directly to transcripts.jsonl (these don't feed generation_log.csv or fraud_rows,
    same as the original).

    CHANGED: every returned case is validated (validate_benign_case) for structure
    and fraud-shape contamination before being accepted -- same reject-and-log
    discipline as the fraud path, no silent fabrication."""
    max_tokens = max_tokens if max_tokens is not None else (LOCAL_MAX_TOKENS if ACTIVE_PROVIDER == "local" else 1568)
    prompt_pairs = "\n".join(f"- topic: '{t}', case_id: '{c}'" for t, c in topic_case_pairs)
    prompt = (
        "You are generating synthetic benign customer-service transcripts for a prototype benchmark.\n"
        "Use only the instructions in this request. Do not rely on any external file.\n"
        "Keep the dialogue ordinary, short, and fully self-contained.\n"
        "Do not include fraud pressure, analysis, or markdown.\n\n"
        f"Generate one ordinary customer-service conversation for each of these cases:\n{prompt_pairs}"
    )

    # CHANGED (bugfix): explicitly request the benign schema (customer/agent, exactly
    # 4 turns) instead of silently inheriting the fraud schema through the old
    # always-on LOCAL_RESPONSE_FORMAT global. See _structured_local's comment for the
    # full failure mode this fixes.
    parsed = call_structured(BENIGN_BATCH_SYSTEM, prompt, max_tokens=max_tokens,
                              local_response_format=LOCAL_BENIGN_RESPONSE_FORMAT)

    if parsed is None or "cases" not in parsed:
        logger.error(
            "Benign batch of %d cases returned no usable response -- see WARNING lines "
            "above for the real error. Every case in this batch will be rejected and "
            "logged (not fabricated).", len(topic_case_pairs),
        )
        by_id = {}
    else:
        by_id = {case["case_id"]: case for case in parsed["cases"] if "case_id" in case}

    n_accepted = 0
    n_rejected = 0
    for topic, case_id in topic_case_pairs:
        case = by_id.get(case_id)
        if case is not None:
            is_valid, reason = validate_benign_case(case)
        else:
            is_valid, reason = False, "case_id absent from model response (batch under-return)"

        if is_valid:
            lines = [f"{t.get('speaker','unknown')}: {t.get('text','')}" for t in case.get("transcript", [])]
            record = {"case_id": case_id, "pretext": topic, "transcript": "\n".join(lines),
                       "label": 0, "accepted": True, "fallback": False}
            n_accepted += 1
        else:
            lines = [
                f"{t.get('speaker','unknown')}: {t.get('text','')}"
                for t in (case.get("transcript", []) if isinstance(case, dict) else [])
            ]
            record = {"case_id": case_id, "pretext": topic, "transcript": "\n".join(lines),
                       "label": 0, "accepted": False, "rejection_reason": reason}
            logger.warning("Benign case %s rejected: %s", case_id, reason)
            n_rejected += 1

        with TRANSCRIPT_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    logger.info(
        "Benign batch summary: %d/%d cases accepted, %d rejected.",
        n_accepted, len(topic_case_pairs), n_rejected,
    )

    time.sleep(0.2)


def generate_benign_case(topic: str, case_id: str) -> dict:
    """Unchanged single-case entry point, kept for compatibility."""
    generate_benign_case_batch([(topic, case_id)])
    return {"case_id": case_id, "pretext": topic}


def materialize_llm_transaction(u, utx, params, case_id, users, merchant_ids,
                                 cat_lookup, rng, new_tx_id, sim_start, sim_days,
                                 drop_stats=None):
    """
    Turns extracted conversation parameters into an actual transaction row.

    CHANGED: device_id, three_ds_result/three_ds_failures_before_result, and
    lat/lon used to be fixed constants (dev_{u}_0, "passed_first_try", home
    coords) for every single case. That meant `amount` was the *only* feature
    that varied for ai_impersonation -- the detector had nothing consistent to
    learn beyond "big purchase", which is why its per-fraud-type PR-AUC was
    far below every other fraud type. These three fields are now sampled,
    conditioned on params["urgency_level"] (already produced by the LLM but
    previously discarded after generation) since a high-pressure call is more
    plausibly linked to a new device/session or a fumbled 3DS attempt than a
    calm one.

    CHANGED: the three early-exit points below used to `return None` silently,
    so there was no way to tell whether a case was lost to "no transaction
    attempted", "landed too close to the simulation boundary", or "user had
    too little prior history at that random day" -- only the final surviving
    count was visible. They now report through `drop_stats`, an optional dict
    passed in by the caller and mutated in place (reason -> count), so the
    caller can print the real breakdown instead of guessing at it.
    """
    def _drop(reason):
        if drop_stats is not None:
            drop_stats[reason] = drop_stats.get(reason, 0) + 1
        return None

    if not params.get("transaction_attempted"):
        return _drop("transaction_not_attempted")

    urow = users.loc[u]
    target_day = rng.uniform(0.0, float(sim_days))
    start = sim_start + timedelta(days=float(target_day))
    if start >= sim_start + timedelta(days=sim_days) - timedelta(minutes=5):
        return _drop("too_close_to_sim_end")

    prior_tx = [r for r in utx if r[0] < start]
    if len(prior_tx) < 2:
        return _drop("insufficient_prior_history")

    m = int(rng.choice(merchant_ids))
    typical = float(np.mean([r[1] for r in prior_tx]))
    amount = float(typical * float(params.get("amount_multiplier", 1)))
    age = int(urow.account_age_days_at_start + target_day)

    urgency = str(params.get("urgency_level", "medium")).lower()

    # New/unfamiliar device: more likely under a high-pressure pretext (victim
    # walked through installing something or authorizing from a new session).
    new_device_prob = {"high": 0.30, "medium": 0.15, "low": 0.05}.get(urgency, 0.15)
    device_id = f"dev_{u}_new" if rng.random() < new_device_prob else f"dev_{u}_0"

    # 3DS friction: a calm, well-rehearsed scammer script still tends to pass
    # first try, but higher urgency raises the odds of a fumbled/retried step.
    friction_prob = {"high": 0.35, "medium": 0.20, "low": 0.08}.get(urgency, 0.20)
    if rng.random() < friction_prob:
        three_ds_result = "failed_then_passed"
        three_ds_failures = int(rng.integers(1, 3))
    else:
        three_ds_result = "passed_first_try"
        three_ds_failures = 0

    # Geo: usually still near home (most of these happen mid-conversation at
    # home), with a modest chance of being away from home / distracted.
    if rng.random() < 0.12:
        lat = urow.home_lat + rng.normal(0, 2.0)
        lon = urow.home_lon + rng.normal(0, 2.0)
    else:
        lat = urow.home_lat + rng.normal(0, 0.05)
        lon = urow.home_lon + rng.normal(0, 0.05)

    return {
        "transaction_id": new_tx_id(), "user_id": int(u), "timestamp": start,
        "amount": amount, "merchant_id": m, "merchant_category": cat_lookup[m],
        "device_id": device_id,
        "lat": float(lat), "lon": float(lon),
        "channel": "ecom", "account_age_days": age, "is_fraud": 1,
        "fraud_type": "ai_impersonation", "case_id": case_id, "ring_id": None,
        "three_ds_result": three_ds_result,
        "three_ds_failures_before_result": three_ds_failures,
    }