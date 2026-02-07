from transformers import AutoProcessor
import sys

try:
    print("Attempting local load...")
    proc = AutoProcessor.from_pretrained("openai/whisper-medium", local_files_only=True)
    print("Success local!")
except Exception as e:
    print(f"Failed local: {e}")
    try:
        print("Attempting online load...")
        proc = AutoProcessor.from_pretrained("openai/whisper-medium")
        print("Success online!")
    except Exception as e2:
        print(f"Failed online: {e2}")
