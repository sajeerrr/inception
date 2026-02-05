from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

class GrammarCorrector:
    def __init__(self):
        # google/flan-t5-base is excellent at following instructions like "Fix grammar" 
        # and is lightweight (250M params) so it won't crash.
        self.model_name = "google/flan-t5-base"
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.load_model()
        
    def load_model(self):
        print(f"Loading Grammar Corrector {self.model_name} on {self.device}...")
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name, low_cpu_mem_usage=True)
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
            # Instruction for Flan-T5
            input_text = f"Fix grammar and improve flow: {text}"
            
            inputs = self.tokenizer(input_text, return_tensors="pt")
            if self.device == "cuda":
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs, 
                    max_length=256,
                    num_beams=5,             # Beam search for better quality
                    early_stopping=True,
                    repetition_penalty=1.2
                )
            
            corrected_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Basic sanity check: if it returns empty, return original
            if not corrected_text:
                return text
                
            return corrected_text
            
        except Exception as e:
            print(f"Grammar Correction Error: {e}")
            return text
