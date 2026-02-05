from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

class GrammarCorrector:
    def __init__(self):
        # vennify/t5-base-grammar-correction is a robust choice for grammar fixing
        self.model_name = "vennify/t5-base-grammar-correction"
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.load_model()
        
    def load_model(self):
        print(f"Loading Grammar Corrector {self.model_name} on {self.device}...")
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
            self.model.to(self.device)
            print("Grammar Corrector loaded.")
        except Exception as e:
            print(f"Error loading Grammar Corrector: {e}")
            self.model = None
            
    def correct(self, text):
        """
        Corrects grammar and style of the input text.
        """
        if not text or not text.strip():
            return text
            
        if not self.model:
            return text
            
        try:
            # T5 expects a prefix for the task
            input_text = f"grammar: {text}"
            
            inputs = self.tokenizer(input_text, return_tensors="pt")
            if self.device == "cuda":
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs, 
                    max_length=256,
                    num_beams=5,             # Beam search for better quality
                    early_stopping=True
                )
            
            corrected_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Basic sanity check: if it returns empty, return original
            if not corrected_text:
                return text
                
            return corrected_text
            
        except Exception as e:
            print(f"Grammar Correction Error: {e}")
            return text
