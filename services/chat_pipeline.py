"""
Chat Pipeline — Orchestration Service
Flow: User message → TinyLlama detects PII → Regex safety-net → Mask →
      Gemini gets ONLY masked prompt → Unmask response → Return to user.
"""

import json
import logging
from services.masking_service import masker
from services.local_llm import ollama_client
from services.gemini_client import gemini_client
from storage.conversation_store import conversation_store

logger = logging.getLogger(__name__)


def process_message(
    user_message: str,
    conversation_id: str | None = None,
    masking_enabled: bool = True,
) -> dict:
    """
    Full pipeline for a single user message.

    1. Create / reuse conversation
    2. TinyLlama scans user message for PII (primary detection)
    3. Regex patterns also scan for PII (safety net)
    4. Merge both results and build masked prompt with placeholders
    5. Send ONLY the masked prompt to Gemini
    6. Unmask Gemini's response (replace placeholders with originals)
    7. Persist both versions
    8. Return clean response + masking metadata
    """

    # ---- 1. Conversation --------------------------------------------------
    if conversation_id is None:
        title = user_message[:60] + ("…" if len(user_message) > 60 else "")
        conversation_id = conversation_store.create_conversation(title)

    # ---- 2–4. Masking (only if enabled) ------------------------------------
    import uuid
    msg_id = uuid.uuid4().hex
    mapping = {}
    masked_text = user_message  # Default: no masking

    if masking_enabled:
        # 2. TinyLlama PII detection (PRIMARY)
        llm_pii_items = []
        try:
            llm_pii_items = ollama_client.detect_pii(user_message)
            logger.info(
                "TinyLlama found %d PII item(s): %s",
                len(llm_pii_items),
                [i["value"] for i in llm_pii_items],
            )
        except Exception as exc:
            logger.warning("TinyLlama PII detection failed, falling back to regex only: %s", exc)

        # 3. Regex PII detection (SAFETY NET)
        masked_text, regex_mapping, msg_id = masker.mask(user_message)
        logger.info(
            "Regex masking found %d item(s): %s",
            len(regex_mapping),
            list(regex_mapping.keys()),
        )

        # 4. Merge TinyLlama results into the mapping
        mapping = dict(regex_mapping)

        for item in llm_pii_items:
            val = item["value"]
            pii_type = item.get("type", "SENSITIVE").upper().replace(" ", "_")
            if val in mapping.values():
                continue
            if val in masked_text:
                counter = sum(1 for k in mapping if pii_type in k) + 1
                placeholder = f"[MASKED_{pii_type}_{counter}]"
                masked_text = masked_text.replace(val, placeholder)
                mapping[placeholder] = val

        masker.store_mapping(msg_id, mapping)
    else:
        logger.info("Masking DISABLED — sending original prompt directly to Gemini")

    total_masked = len(mapping)
    logger.info(
        "=== MASKING SUMMARY === %d total items masked", total_masked
    )
    if total_masked > 0:
        logger.info("Original:  %s", user_message)
        logger.info("Masked:    %s", masked_text)
    else:
        logger.info("No sensitive data detected — sending original message to Gemini")

    # ---- 5. Build masked conversation history ----------------------------
    history_rows = conversation_store.get_messages(conversation_id)
    masked_history = []
    for row in history_rows:
        role = row["role"]
        # Always use the masked version for cloud history
        text = row.get("masked_content") or row["content"]
        masked_history.append({"role": role, "text": text})

    # ---- 6. Send ONLY masked prompt to Gemini ----------------------------
    # If nothing was masked, the original text goes to Gemini (it's safe)
    prompt_for_gemini = masked_text if total_masked > 0 else user_message
    masked_response = gemini_client.generate_response(prompt_for_gemini, masked_history)

    # ---- 7. Unmask Gemini's response -------------------------------------
    # Replace any placeholders in the response with the original values
    clean_response = masker.unmask(masked_response, msg_id)

    # ---- 8. Persist both versions ----------------------------------------
    conversation_store.add_message(
        conversation_id, "user", user_message, masked_text, json.dumps(mapping)
    )
    conversation_store.add_message(
        conversation_id, "assistant", clean_response, masked_response, ""
    )

    # ---- 9. Return result ------------------------------------------------
    return {
        "response": clean_response,
        "conversation_id": conversation_id,
        "masking_info": {
            "items_masked": total_masked,
            "placeholders": list(mapping.keys()),
            "masked_prompt": masked_text if total_masked > 0 else None,
        },
    }
