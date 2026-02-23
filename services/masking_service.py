"""
PII Masking Service
Detects and masks personally identifiable information using regex patterns.
Maintains a reversible mapping so responses can be unmasked.
"""

import re
import uuid
from collections import OrderedDict


# ---------------------------------------------------------------------------
# Regex patterns for common PII types
# ---------------------------------------------------------------------------

PII_PATTERNS = OrderedDict([
    ("EMAIL", re.compile(
        r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b'
    )),
    ("CREDIT_CARD", re.compile(
        r'\b(?:\d[ \-]*?){13,19}\b'
    )),
    ("SSN", re.compile(
        r'\b\d{3}[\s\-]?\d{2}[\s\-]?\d{4}\b'
    )),
    ("PHONE", re.compile(
        r'(?:\+?\d{1,3}[\s\-]?)?'
        r'(?:\(?\d{2,4}\)?[\s\-]?)'
        r'\d{3,4}[\s\-]?\d{3,4}\b'
    )),
    ("IP_ADDRESS", re.compile(
        r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    )),
    ("DATE_OF_BIRTH", re.compile(
        r'\b(?:0[1-9]|[12]\d|3[01])[\/\-\.](?:0[1-9]|1[0-2])[\/\-\.]\d{2,4}\b'
        r'|\b(?:0[1-9]|1[0-2])[\/\-\.](?:0[1-9]|[12]\d|3[01])[\/\-\.]\d{2,4}\b'
        r'|\b\d{4}[\/\-\.](?:0[1-9]|1[0-2])[\/\-\.](?:0[1-9]|[12]\d|3[01])\b'
    )),
    ("AADHAAR", re.compile(
        r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b'
    )),
    ("PAN", re.compile(
        r'\b[A-Z]{5}\d{4}[A-Z]\b'
    )),
    ("PASSPORT", re.compile(
        r'\b[A-Z]\d{7}\b'
    )),
])

# Common name prefixes/titles that hint at a following personal name
NAME_PREFIXES = re.compile(
    r"(?:(?:my name is|i(?:'?m| am)|call me|this is|mr\.?|mrs\.?|ms\.?|dr\.?)\s+)"
    r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})",
    re.IGNORECASE,
)

ADDRESS_PATTERN = re.compile(
    r'\b\d{1,5}\s+(?:[A-Za-z]+\s){1,4}'
    r'(?:Street|St|Avenue|Ave|Boulevard|Blvd|Road|Rd|Lane|Ln|Drive|Dr|Court|Ct|Way|Place|Pl)\b'
    r'(?:[,\s]+(?:[A-Za-z]+\s?)+)?'
    r'(?:[,\s]+[A-Z]{2}\s+\d{5}(?:\-\d{4})?)?',
    re.IGNORECASE,
)


class PIIMasker:
    """Detects, masks and unmasks PII in text strings."""

    def __init__(self):
        # mapping: message_id -> {placeholder: original}
        self._mappings: dict[str, dict[str, str]] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def mask(self, text: str, message_id: str | None = None) -> tuple[str, dict[str, str], str]:
        """
        Mask PII in *text*.

        Returns
        -------
        (masked_text, mapping_dict, message_id)
        """
        if message_id is None:
            message_id = uuid.uuid4().hex

        mapping: dict[str, str] = {}
        counters: dict[str, int] = {}
        masked_text = text

        # 1. Address (before shorter patterns to avoid partial matches)
        masked_text = self._apply_pattern(
            masked_text, ADDRESS_PATTERN, "ADDRESS", mapping, counters
        )

        # 2. Named regex patterns
        for pii_type, pattern in PII_PATTERNS.items():
            masked_text = self._apply_pattern(
                masked_text, pattern, pii_type, mapping, counters
            )

        # 3. Name detection via contextual prefixes
        masked_text = self._mask_names(masked_text, mapping, counters)

        # Store the mapping for later unmasking
        self._mappings[message_id] = mapping

        return masked_text, mapping, message_id

    def unmask(self, text: str, message_id: str) -> str:
        """Replace placeholders back with the original PII values."""
        mapping = self._mappings.get(message_id, {})
        result = text
        # Sort by longest placeholder first to avoid partial replacements
        for placeholder in sorted(mapping.keys(), key=len, reverse=True):
            result = result.replace(placeholder, mapping[placeholder])
        return result

    def get_mapping(self, message_id: str) -> dict[str, str]:
        return self._mappings.get(message_id, {})

    def store_mapping(self, message_id: str, mapping: dict[str, str]):
        self._mappings[message_id] = mapping

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _apply_pattern(
        text: str,
        pattern: re.Pattern,
        pii_type: str,
        mapping: dict[str, str],
        counters: dict[str, int],
    ) -> str:
        """Replace all matches of *pattern* with numbered placeholders."""
        def _replacer(match: re.Match) -> str:
            original = match.group(0)
            # Skip if already masked
            if original.startswith("[MASKED_"):
                return original
            # Avoid duplicate masking of the same value
            for placeholder, orig in mapping.items():
                if orig == original:
                    return placeholder
            counters[pii_type] = counters.get(pii_type, 0) + 1
            placeholder = f"[MASKED_{pii_type}_{counters[pii_type]}]"
            mapping[placeholder] = original
            return placeholder

        return pattern.sub(_replacer, text)

    @staticmethod
    def _mask_names(
        text: str,
        mapping: dict[str, str],
        counters: dict[str, int],
    ) -> str:
        """Detect names following known prefix phrases."""
        def _replacer(match: re.Match) -> str:
            full = match.group(0)
            name = match.group(1)
            for placeholder, orig in mapping.items():
                if orig == name:
                    return full.replace(name, placeholder)
            counters["NAME"] = counters.get("NAME", 0) + 1
            placeholder = f"[MASKED_NAME_{counters['NAME']}]"
            mapping[placeholder] = name
            return full.replace(name, placeholder)

        return NAME_PREFIXES.sub(_replacer, text)


# Module-level singleton for convenience
masker = PIIMasker()
