import torch
import soundfile as sf
from transformers import AutoProcessor, AutoModelForSpeechSeq2Seq
import numpy as np
import traceback

class SimpleSegment:
    """Wrapper to make dictionary behave like object with .text attribute, for GUI compatibility"""
    def __init__(self, text):
        self.text = text

class SpeechRecognizer:
    def __init__(self, model_size="medium"): 
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_id = "Muzaffar786/whisper-kashmiri"
        
        print(f"Loading Whisper-Kashmiri Model '{self.model_id}' on {self.device}...")
        
        try:
            # CRITICAL FIX: The fine-tuned model repo is missing tokenizer files, leading to a broken default tokenizer.
            # We must use the standard Whisper tokenizer (from openai/whisper-medium) which matches the model's vocab.
            print("Loading processor from 'openai/whisper-medium' (to fix tokenizer)...")
            self.processor = AutoProcessor.from_pretrained("openai/whisper-medium")
            
            print(f"Loading model from '{self.model_id}'...")
            self.model = AutoModelForSpeechSeq2Seq.from_pretrained(self.model_id)
            self.model.to(self.device)
            print("Whisper-Kashmiri model loaded (Direct + Fix).")
            
        except Exception as e:
            print(f"Failed to load Whisper-Kashmiri model: {e}")
            raise e

    def transcribe(self, audio_data, language=None):
        """
        Transcribes audio data using Muzaffar786/whisper-kashmiri.
        Input: numpy array (float32)
        """
        try:
            if isinstance(audio_data, np.ndarray):
                if audio_data.dtype != np.float32:
                    audio_data = audio_data.astype(np.float32)
                
                if len(audio_data) < 100:
                    return [], None

                print(f"DEBUG: Audio stats: max={np.max(audio_data):.3f} mean={np.mean(np.abs(audio_data)):.3f}", flush=True)

                inputs = self.processor(audio_data, sampling_rate=16000, return_tensors="pt")
                if self.device == "cuda":
                    inputs = {k: v.to(self.device) for k, v in inputs.items()}

                with torch.no_grad():
                    # Force Urdu language which maps to Kashmiri in this fine-tune often
                    generated_ids = self.model.generate(**inputs, language="ur")
                
                # Debug raw tokens
                print(f"DEBUG: generated_ids: {generated_ids[0].tolist()}", flush=True)
                
                # Decode WITH special tokens to see what is happening
                raw_text = self.processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
                print(f"DEBUG: Raw Text: '{raw_text}'", flush=True)

                text = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
                print(f"DEBUG: Clean Text: '{text}'", flush=True)
                
                # FORCE return raw text if clean is empty, so user sees something
                if not text.strip():
                    print("DEBUG: Clean text empty, returning raw text as fallback.", flush=True)
                    # Simple cleanup of common tags to make it readable
                    text = raw_text.replace("<|startoftranscript|>", "").replace("<|notimestamps|>", "").replace("<|ur|>", "").replace("<|transcribe|>", "")
                
                segment = SimpleSegment(text)
                return [segment], None
                
            return [], None

        except Exception as e:
            traceback.print_exc()
            print(f"Error in transcribe: {e}")
            return [], None
    # Note: translate_to_english handles by GUI via separate Translator class.


