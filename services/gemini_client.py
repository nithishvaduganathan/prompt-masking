"""
Gemini 2.5 Flash Client
Sends masked prompts to Google's Gemini API and returns responses.
"""

import logging
from google import genai
from google.genai import types

from config import Config

logger = logging.getLogger(__name__)


class GeminiClient:
    """Wrapper around the Google GenAI SDK for Gemini 2.5 Flash."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or Config.GEMINI_API_KEY
        if not self.api_key:
            logger.warning("GEMINI_API_KEY is not set — cloud responses will fail.")
        self.client = genai.Client(api_key=self.api_key)
        self.model = Config.GEMINI_MODEL

    def generate_response(
        self,
        masked_prompt: str,
        conversation_history: list[dict] | None = None,
    ) -> str:
        """
        Send *masked_prompt* (with PII already replaced by placeholders)
        to Gemini and return the text response.

        conversation_history is a list of {"role": "user"|"model", "text": "..."}
        """
        if not self.api_key:
            return "[Error] Gemini API key not configured. Please set GEMINI_API_KEY in your .env file."

        try:
            # Build contents list from history + current message
            contents = []
            if conversation_history:
                for msg in conversation_history:
                    role = msg.get("role", "user")
                    if role == "assistant":
                        role = "model"
                    contents.append(
                        types.Content(
                            role=role,
                            parts=[types.Part.from_text(text=msg["text"])],
                        )
                    )

            # Add the current user message
            contents.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=masked_prompt)],
                )
            )

            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=8192,
                ),
            )

            return response.text or "[No response generated]"

        except Exception as exc:
            logger.error("Gemini API error: %s", exc, exc_info=True)
            return f"[Error] Failed to get response from Gemini: {exc}"


# Module-level singleton
gemini_client = GeminiClient()
