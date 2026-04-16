import json
import re
import time

from src.config import MAX_RETRIES, MODEL_NAME, SYSTEM_PROMPT, client, _generation_config
from src.logger import setup_logger

logger = setup_logger("analyzer")


def analyze_transcript(dialogue: str) -> dict:
    """
    Analyze a preprocessed transcript dialogue string using Google Gemini.
    Retries up to MAX_RETRIES times with exponential backoff on failure.

    Args:
        dialogue: Clean formatted string from preprocessor.py, e.g.:
                  "Agent: हाँ सर राहुल बात कर रहा हूँ\\nCustomer: अच्छा..."

    Returns:
        Normalized dict with keys:
            summary, key_takeaways, intent, customer_objection,
            agent_resolution, call_rating
        On total failure, returns an error dict with 'error' key.
    """
    if not dialogue or not dialogue.strip():
        return {
            "error": "empty_dialogue",
            "last_error": "Preprocessor returned empty dialogue — check raw segments.",
        }

    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"TRANSCRIPT:\n{dialogue}"
    )

    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.debug(f"Gemini API call — attempt {attempt}/{MAX_RETRIES}")

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=_generation_config,
            )
            raw_text = (response.text or "").strip()

            # Strip markdown fences robustly (handles ```json, nested
            # backticks in values, missing closing fence, extra text)
            fence_match = re.search(
                r"```(?:json)?\s*([\s\S]*?)\s*```", raw_text
            )
            if fence_match:
                raw_text = fence_match.group(1).strip()
            elif raw_text.startswith("```"):
                # Opening fence with no closing fence
                raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text).strip()

            result = json.loads(raw_text)
            normalized = _normalize_result(result)
            logger.debug(f"Analysis successful — intent={normalized['intent']}, rating={normalized['call_rating']}")
            return normalized

        except json.JSONDecodeError as e:
            last_error = f"JSON parse error: {e}"
            logger.warning(f"Attempt {attempt} — {last_error}")

        except Exception as e:
            last_error = str(e)
            # Check for rate limit error (429)
            if "429" in last_error or "quota" in last_error.lower() or "rate" in last_error.lower() or "RESOURCE_EXHAUSTED" in last_error:
                # Free-tier Gemini recommends ~35s retry delay — respect it
                wait = min(35 * attempt, 60)  # 35s, 60s, 60s, ...
                logger.warning(f"Attempt {attempt} — Rate limited (429). Waiting {wait}s before retry...")
                time.sleep(wait)
            else:
                logger.warning(f"Attempt {attempt} — Error: {last_error}")
                # Small pause only for non-rate-limit errors
                if attempt < MAX_RETRIES:
                    time.sleep(1)

    logger.error(f"All {MAX_RETRIES} attempts failed. Last error: {last_error}")
    return {
        "error": "analysis_failed_after_retries",
        "attempts": MAX_RETRIES,
        "last_error": last_error,
    }


def _normalize_result(result: dict) -> dict:
    """
    Validate and clean each field from the raw LLM JSON response.
    Applies fallback defaults for any missing or invalid values.

    Args:
        result: Raw dict parsed from Gemini JSON response

    Returns:
        Cleaned and validated dict with all 6 required fields.
    """

    # --- summary ---
    summary = str(result.get("summary", "")).strip()
    if not summary:
        summary = "Summary not available"

    # --- key_takeaways ---
    key_takeaways = result.get("key_takeaways", [])
    if isinstance(key_takeaways, str):
        # Handle pipe-separated string fallback
        key_takeaways = [p.strip() for p in key_takeaways.split("|") if p.strip()]
    if not isinstance(key_takeaways, list):
        key_takeaways = []
    key_takeaways = [str(item).strip() for item in key_takeaways if str(item).strip()]
    # Ensure at least 1 item
    if not key_takeaways:
        key_takeaways = ["No key takeaways captured"]

    # --- intent ---
    VALID_INTENTS = {"high", "medium", "low"}
    intent = str(result.get("intent", "low")).strip().lower()
    if intent not in VALID_INTENTS:
        logger.warning(f"Invalid intent '{intent}' — defaulting to 'low'")
        intent = "low"

    # --- customer_objection ---
    customer_objection = str(result.get("customer_objection", "")).strip()
    if not customer_objection:
        customer_objection = "Not captured"

    # --- agent_resolution ---
    agent_resolution = str(result.get("agent_resolution", "")).strip()
    if not agent_resolution:
        agent_resolution = "Agent resolution not captured"

    # --- call_rating ---
    raw_rating = result.get("call_rating", 3)
    try:
        call_rating = int(float(str(raw_rating)))
        if call_rating < 1 or call_rating > 5:
            raise ValueError("Out of range")
    except (ValueError, TypeError):
        logger.warning(f"Invalid call_rating '{raw_rating}' — defaulting to 3")
        call_rating = 3

    return {
        "summary": summary,
        "key_takeaways": key_takeaways,
        "intent": intent,
        "customer_objection": customer_objection,
        "agent_resolution": agent_resolution,
        "call_rating": call_rating,
    }
