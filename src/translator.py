from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

class OfflineTranslator:
    def __init__(self):
        # Using NLLB-200 Distilled 600M (Recommended for Kashmiri)
        self.model_name = "facebook/nllb-200-distilled-600M"
        self.load_model()
        
    def load_model(self):
        print(f"Loading NLLB Translation model {self.model_name}...")
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
            print("NLLB model loaded.")
        except Exception as e:
            print(f"Error loading NLLB model: {e}")
            
    def translate(self, text, src_lang, tgt_lang):
        """
        Translates text using NLLB.
        src_lang/tgt_lang should be simple codes ('ks', 'en', 'hi')
        """
        if not text or not text.strip(): 
            return ""
        
        # Map to NLLB codes
        code_map = {
            "ks": "kas_Arab", 
            "en": "eng_Latn",
            "hi": "hin_Deva"
        }
        
        nllb_src = code_map.get(src_lang)
        nllb_tgt = code_map.get(tgt_lang)
        
        if not nllb_src or not nllb_tgt:
            return text
            
        try:
            # Set source language
            self.tokenizer.src_lang = nllb_src
            
            inputs = self.tokenizer(text, return_tensors="pt")
            
            # Generate with target language
            # Fix: lang_code_to_id is not always available properties
            forced_bos_token_id = self.tokenizer.convert_tokens_to_ids(nllb_tgt)
            
            # Generate
            translated_tokens = self.model.generate(
                **inputs, 
                forced_bos_token_id=forced_bos_token_id, 
                max_length=512
            )
            
            result = self.tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)[0]
            return result
            
        except Exception as e:
            print(f"Translation Error: {e}")
            return text
