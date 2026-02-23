"""
Ollama / TinyLlama Local LLM Client
Primary PII detection engine — uses TinyLlama to identify and mask
sensitive/personal data in user prompts before they reach the cloud model.
"""

import requests
import json
import re
import logging

from config import Config

logger = logging.getLogger(__name__)


class OllamaClient:
    """Thin wrapper around the Ollama REST API for PII masking."""

    def __init__(self, base_url: str | None = None, model: str | None = None):
        self.base_url = (base_url or Config.OLLAMA_URL).rstrip("/")
        self.model = model or Config.LOCAL_MODEL

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def check_health(self) -> bool:
        """Return True if Ollama is reachable and the model is available."""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if resp.status_code != 200:
                return False
            models = [m["name"] for m in resp.json().get("models", [])]
            return any(
                self.model in m or m.startswith(self.model) for m in models
            )
        except Exception as exc:
            logger.warning("Ollama health-check failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Primary PII Detection via TinyLlama
    # ------------------------------------------------------------------

    def detect_pii(self, text: str) -> list[dict]:
        """
        Ask TinyLlama to identify ALL personally identifiable and sensitive
        information in the given text.

        Returns a list of dicts: [{"value": "exact text", "type": "NAME|EMAIL|..."}]
        """
        prompt = (
            "You are a privacy protection assistant. Your ONLY job is to find "
            "personally identifiable information (PII) and sensitive data in the text below.\n\n"
            "Look for these types:\n"
            "- NAME: Person names (first, last, full names)\n"
            "- EMAIL: Email addresses\n"
            "- PHONE: Phone numbers\n"
            "- SSN: Social security numbers\n"
            "- CREDIT_CARD: Credit/debit card numbers\n"
            "- ADDRESS: Physical addresses\n"
            "- DOB: Dates of birth\n"
            "- ID_NUMBER: Aadhaar, PAN, passport, license numbers\n"
            "- ORGANIZATION: Company/organization names that are private\n"
            "- MEDICAL: Medical conditions or records\n"
            "- FINANCIAL: Bank account numbers, salary amounts\n"
            "- PASSWORD: Passwords or secret keys\n\n"
            "RULES:\n"
            "1. Output ONLY a valid JSON array\n"
            "2. Each item must have \"value\" (exact text from input) and \"type\" (category)\n"
            "3. If NO sensitive data found, output exactly: []\n"
            "4. Do NOT include any explanation, only the JSON array\n\n"
            f"Text to analyze:\n\"{text}\"\n\n"
            "JSON output:"
        )

        try:
            resp = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1, "num_predict": 512},
                },
                timeout=60,
            )
            resp.raise_for_status()
            raw = resp.json().get("response", "").strip()

            logger.info("TinyLlama raw PII response: %s", raw[:500])

            # Clean up markdown code blocks if present
            raw = raw.strip()
            if raw.startswith("```"):
                raw = re.sub(r'^```\w*\n?', '', raw)
                raw = re.sub(r'\n?```$', '', raw)
            raw = raw.strip()

            # Try to find a JSON array in the response
            match = re.search(r'\[.*\]', raw, re.DOTALL)
            if match:
                raw = match.group(0)

            items = json.loads(raw)
            if isinstance(items, list):
                valid = [
                    i for i in items
                    if isinstance(i, dict) and "value" in i and "type" in i
                    and i["value"].strip()  # Non-empty value
                    and i["value"] in text   # Value must actually exist in text
                ]
                logger.info("TinyLlama detected %d PII items: %s", len(valid), valid)
                return valid

        except (json.JSONDecodeError, requests.RequestException) as exc:
            logger.warning("TinyLlama PII detection failed: %s", exc)

        return []

    # ------------------------------------------------------------------
    # Generic generate
    # ------------------------------------------------------------------

    def generate(self, prompt: str, **kwargs) -> str:
        """Send a generic generation request to Ollama."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            **kwargs,
        }
        resp = requests.post(
            f"{self.base_url}/api/generate", json=payload, timeout=60
        )
        resp.raise_for_status()
        return resp.json().get("response", "")


# Module-level singleton
ollama_client = OllamaClient()
