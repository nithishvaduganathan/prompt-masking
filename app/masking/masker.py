"""
Privacy-Preserving Prompt Masking Module
Detects and masks sensitive personal information in user queries
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field


@dataclass
class MaskingResult:
    """Result of masking operation containing masked text and mappings"""
    original_text: str
    masked_text: str
    mappings: Dict[str, str] = field(default_factory=dict)
    detected_entities: List[str] = field(default_factory=list)


class PromptMasker:
    """
    Main class for masking and unmasking sensitive information in prompts
    Uses regex patterns and optional NER for detecting sensitive data
    """
    
    def __init__(self, use_spacy: bool = False):
        """
        Initialize the PromptMasker
        
        Args:
            use_spacy: Whether to use spaCy NER for additional entity detection
        """
        self.use_spacy = use_spacy
        self.nlp = None
        
        if use_spacy:
            try:
                import spacy
                # Try to load the model, fallback to not using spacy if not available
                try:
                    self.nlp = spacy.load("en_core_web_sm")
                except OSError:
                    print("Warning: spaCy model not found. Using regex-only mode.")
                    self.use_spacy = False
            except ImportError:
                print("Warning: spaCy not installed. Using regex-only mode.")
                self.use_spacy = False
        
        # Mental health and disease patterns
        self.mental_health_terms = [
            r'\b(depression|depressed|anxiety|anxious|panic attack|ptsd|bipolar|schizophrenia|'
            r'ocd|adhd|eating disorder|anorexia|bulimia|addiction|suicidal|self-harm|'
            r'mental health|mental illness|psychiatric|psychological condition)\b'
        ]
        
        self.disease_patterns = [
            r'\b(diabetes|cancer|hiv|aids|covid|coronavirus|tuberculosis|hepatitis|'
            r'heart disease|hypertension|asthma|copd|alzheimer|parkinson|epilepsy|'
            r'arthritis|multiple sclerosis|lupus|crohn|celiac)\b'
        ]
        
        # Contact information patterns
        self.email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        # Phone number patterns (various formats)
        self.phone_patterns = [
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # 123-456-7890 or 1234567890
            r'\b\(\d{3}\)\s*\d{3}[-.]?\d{4}\b',  # (123) 456-7890
            r'\+\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}\b'  # +1-234-567-8900
        ]
        
        # Personal information patterns
        self.age_pattern = r'\b(?:age|aged|year old|years old|yr old|yrs old)[\s:]+(\d{1,3})\b|\b(\d{1,3})[\s-]?(?:year|yr)[\s-]?old\b'
        self.gender_pattern = r'\b(male|female|man|woman|boy|girl|transgender|non-binary|gender)\b'
        
        # Location patterns (cities, states, countries)
        self.location_pattern = r'\b(New York|Los Angeles|Chicago|Houston|Phoenix|Philadelphia|San Antonio|San Diego|Dallas|San Jose|Austin|Jacksonville|Fort Worth|Columbus|Indianapolis|Charlotte|San Francisco|Seattle|Denver|Washington|Boston|Nashville|Baltimore|Oklahoma City|Louisville|Portland|Las Vegas|Milwaukee|Albuquerque|Tucson|Fresno|Sacramento|Kansas City|Mesa|Atlanta|Omaha|Colorado Springs|Raleigh|Miami|Long Beach|Virginia Beach|Oakland|Minneapolis|Tulsa|Tampa|Arlington|New Orleans|Wichita|Cleveland|Bakersfield|Aurora|Anaheim|Honolulu|Santa Ana|Riverside|Corpus Christi|Lexington|Stockton|Henderson|Saint Paul|St. Paul|Cincinnati|St. Louis|Pittsburgh|Greensboro|Lincoln|Anchorage|Plano|Orlando|Irvine|Newark|Durham|Chula Vista|Toledo|Fort Wayne|St. Petersburg|Laredo|Jersey City|Chandler|Madison|Lubbock|Scottsdale|Reno|Buffalo|Gilbert|Glendale|North Las Vegas|Winston-Salem|Chesapeake|Norfolk|Fremont|Garland|Irving|Hialeah|Richmond|Boise|Spokane|Baton Rouge)\b|\b(California|Texas|Florida|New York|Pennsylvania|Illinois|Ohio|Georgia|North Carolina|Michigan|Alabama|Alaska|Arizona|Arkansas|Colorado|Connecticut|Delaware|Hawaii|Idaho|Indiana|Iowa|Kansas|Kentucky|Louisiana|Maine|Maryland|Massachusetts|Minnesota|Mississippi|Missouri|Montana|Nebraska|Nevada|New Hampshire|New Jersey|New Mexico|North Dakota|Oklahoma|Oregon|Rhode Island|South Carolina|South Dakota|Tennessee|Utah|Vermont|Virginia|Washington|West Virginia|Wisconsin|Wyoming)\b|\b(USA|United States|America|UK|United Kingdom|England|Canada|Australia|Germany|France|Italy|Spain|India|China|Japan|Mexico|Brazil)\b'
        
        # Counter for generating unique placeholders
        self.counters = {
            'MENTAL_HEALTH': 0,
            'DISEASE': 0,
            'EMAIL': 0,
            'PHONE': 0,
            'NAME': 0,
            'AGE': 0,
            'GENDER': 0,
            'LOCATION': 0
        }
    
    def reset_counters(self):
        """Reset all counters for a new masking session"""
        for key in self.counters:
            self.counters[key] = 0
    
    def _generate_placeholder(self, entity_type: str) -> str:
        """Generate a unique placeholder token for an entity type"""
        placeholder = f"[{entity_type}_{self.counters[entity_type]}]"
        self.counters[entity_type] += 1
        return placeholder
    
    def mask_text(self, text: str) -> MaskingResult:
        """
        Mask sensitive information in the provided text
        
        Args:
            text: The original text containing potential sensitive information
            
        Returns:
            MaskingResult object containing masked text and mappings
        """
        self.reset_counters()
        masked_text = text
        mappings = {}
        detected_entities = []
        
        # Apply regex-based masking in specific order
        # 1. Mental health conditions
        for pattern in self.mental_health_terms:
            matches = list(re.finditer(pattern, masked_text, re.IGNORECASE))
            for match in reversed(matches):  # Reverse to maintain positions
                original = match.group(0)
                placeholder = self._generate_placeholder('MENTAL_HEALTH')
                mappings[placeholder] = original
                detected_entities.append(f"MENTAL_HEALTH: {original}")
                masked_text = masked_text[:match.start()] + placeholder + masked_text[match.end():]
        
        # 2. Diseases
        for pattern in self.disease_patterns:
            matches = list(re.finditer(pattern, masked_text, re.IGNORECASE))
            for match in reversed(matches):
                original = match.group(0)
                placeholder = self._generate_placeholder('DISEASE')
                mappings[placeholder] = original
                detected_entities.append(f"DISEASE: {original}")
                masked_text = masked_text[:match.start()] + placeholder + masked_text[match.end():]
        
        # 3. Email addresses
        matches = list(re.finditer(self.email_pattern, masked_text))
        for match in reversed(matches):
            original = match.group(0)
            placeholder = self._generate_placeholder('EMAIL')
            mappings[placeholder] = original
            detected_entities.append(f"EMAIL: {original}")
            masked_text = masked_text[:match.start()] + placeholder + masked_text[match.end():]
        
        # 4. Phone numbers
        for pattern in self.phone_patterns:
            matches = list(re.finditer(pattern, masked_text))
            for match in reversed(matches):
                original = match.group(0)
                placeholder = self._generate_placeholder('PHONE')
                mappings[placeholder] = original
                detected_entities.append(f"PHONE: {original}")
                masked_text = masked_text[:match.start()] + placeholder + masked_text[match.end():]
        
        # 5. Age
        matches = list(re.finditer(self.age_pattern, masked_text, re.IGNORECASE))
        for match in reversed(matches):
            original = match.group(0)
            placeholder = self._generate_placeholder('AGE')
            mappings[placeholder] = original
            detected_entities.append(f"AGE: {original}")
            masked_text = masked_text[:match.start()] + placeholder + masked_text[match.end():]
        
        # 6. Locations (before person names to avoid false positives)
        matches = list(re.finditer(self.location_pattern, masked_text, re.IGNORECASE))
        for match in reversed(matches):
            original = match.group(0)
            placeholder = self._generate_placeholder('LOCATION')
            mappings[placeholder] = original
            detected_entities.append(f"LOCATION: {original}")
            masked_text = masked_text[:match.start()] + placeholder + masked_text[match.end():]
        
        # 7. Gender terms
        matches = list(re.finditer(self.gender_pattern, masked_text, re.IGNORECASE))
        for match in reversed(matches):
            original = match.group(0)
            placeholder = self._generate_placeholder('GENDER')
            mappings[placeholder] = original
            detected_entities.append(f"GENDER: {original}")
            masked_text = masked_text[:match.start()] + placeholder + masked_text[match.end():]
        
        # 8. Use spaCy for person names if enabled
        if self.use_spacy and self.nlp:
            doc = self.nlp(masked_text)
            # Process in reverse order to maintain positions
            person_entities = [(ent.start_char, ent.end_char, ent.text) 
                             for ent in doc.ents if ent.label_ == "PERSON"]
            for start, end, text in reversed(person_entities):
                placeholder = self._generate_placeholder('NAME')
                mappings[placeholder] = text
                detected_entities.append(f"NAME: {text}")
                masked_text = masked_text[:start] + placeholder + masked_text[end:]
        
        return MaskingResult(
            original_text=text,
            masked_text=masked_text,
            mappings=mappings,
            detected_entities=detected_entities
        )
    
    def unmask_text(self, masked_text: str, mappings: Dict[str, str]) -> str:
        """
        Unmask text by replacing placeholders with original values
        
        Args:
            masked_text: Text containing placeholders
            mappings: Dictionary mapping placeholders to original values
            
        Returns:
            Unmasked text with original values restored
        """
        unmasked_text = masked_text
        
        # Sort placeholders by their position in the text to replace in order
        # Replace all placeholders with their original values
        for placeholder, original in mappings.items():
            unmasked_text = unmasked_text.replace(placeholder, original)
        
        return unmasked_text


def mask_prompt(text: str, use_spacy: bool = False) -> MaskingResult:
    """
    Convenience function to mask a prompt
    
    Args:
        text: Original text to mask
        use_spacy: Whether to use spaCy NER
        
    Returns:
        MaskingResult object
    """
    masker = PromptMasker(use_spacy=use_spacy)
    return masker.mask_text(text)


def unmask_response(masked_text: str, mappings: Dict[str, str]) -> str:
    """
    Convenience function to unmask a response
    
    Args:
        masked_text: Text with placeholders
        mappings: Mapping of placeholders to original values
        
    Returns:
        Unmasked text
    """
    masker = PromptMasker()
    return masker.unmask_text(masked_text, mappings)
