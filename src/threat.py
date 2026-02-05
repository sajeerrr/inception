import os

class ThreatDetector:
    def __init__(self, keywords_file="data/threat_words.txt"):
        self.keywords = set()
        self.load_keywords(keywords_file)

    def load_keywords(self, filepath):
        """Loads threat keywords from a file."""
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                self.keywords = {line.strip().lower() for line in f if line.strip()}
        else:
            print(f"Warning: Threat keywords file not found at {filepath}")

    def detect(self, text):
        """
        Scans the text for threat keywords.
        Returns (is_threat, detected_words_list)
        """
        if not text:
            return False, []
            
        lower_text = text.lower()
        detected = []
        
        # Simple keyword matching
        # In a more advanced version, we might use regex or lemmatization
        for word in self.keywords:
            # Check for word boundaries to avoid partial matches (e.g. "danger" in "endangered" might be okay, but let's stick to simple inclusion for now or improve with boundaries)
            # For simplicity in this offline MVP, we'll check if the word exists in the string.
            # A better approach for exact word matching:
            if word in lower_text.split(): # Basic tokenization
                 detected.append(word)
            elif word in lower_text: # Fallback for multi-word phrases if any
                 # Check if it's a phrase in the list
                 if ' ' in word:
                     detected.append(word)

        return len(detected) > 0, list(set(detected))
