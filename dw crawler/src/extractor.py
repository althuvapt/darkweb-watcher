import re
import spacy
from typing import Dict, List, Set
import logging

logger = logging.getLogger(__name__)

class IntelligenceExtractor:
    def __init__(self):
        try:
            # We use the small model to keep memory footprint low
            self.nlp = spacy.load("en_core_web_sm")
        except Exception as e:
            logger.error(f"Failed to load spaCy model: {e}")
            self.nlp = None

        # Basic RegEx patterns for dark web artifacts
        self.patterns = {
            "btc_addresses": re.compile(r'\b(1[a-km-zA-HJ-NP-Z1-9]{25,34}|3[a-km-zA-HJ-NP-Z1-9]{25,34}|bc1[a-zA-HJ-NP-Z0-9]{39,59})\b'),
            "xmr_addresses": re.compile(r'\b4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}\b'),
            "emails": re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),
            "pgp_keys": re.compile(r'-----BEGIN PGP PUBLIC KEY BLOCK-----[\s\S]*?-----END PGP PUBLIC KEY BLOCK-----')
        }

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract structured intelligence from raw text."""
        entities = {
            "btc_addresses": list(set(self.patterns["btc_addresses"].findall(text))),
            "xmr_addresses": list(set(self.patterns["xmr_addresses"].findall(text))),
            "emails": list(set(self.patterns["emails"].findall(text))),
            "pgp_keys": [] # Taking a simpler approach for PGP since it spans lines
        }

        # Handle multiline PGP keys
        for match in self.patterns["pgp_keys"].finditer(text):
            entities["pgp_keys"].append(match.group(0))

        # NLP Named Entity Recognition (Persons, Organizations, Locations)
        if self.nlp and text:
            try:
                # Limit text size for NLP to prevent massive memory usage on huge pages
                doc = self.nlp(text[:100000])
                nlp_entities = {"PERSON": set(), "ORG": set(), "GPE": set()}
                
                for ent in doc.ents:
                    if ent.label_ in nlp_entities:
                        # Clean up basic whitespace/newlines from entities
                        clean_text = ent.text.strip().replace('\n', ' ')
                        if len(clean_text) > 2: # Ignore tiny artifacts
                            nlp_entities[ent.label_].add(clean_text)

                entities["nlp_persons"] = list(nlp_entities["PERSON"])
                entities["nlp_organizations"] = list(nlp_entities["ORG"])
                entities["nlp_locations"] = list(nlp_entities["GPE"])
            except Exception as e:
                logger.error(f"NER Extraction failed: {e}")
                entities["nlp_persons"] = []
                entities["nlp_organizations"] = []
                entities["nlp_locations"] = []
        
        return entities
