import sys
import os

print(f"Python Executable: {sys.executable}")
print(f"CWD: {os.getcwd()}")
print("sys.path:")
for p in sys.path:
    print(f"  {p}")

try:
    import customtkinter
    print(f"SUCCESS: customtkinter found at {customtkinter.__file__}")
except ImportError as e:
    print(f"FAILURE: {e}")
    
    # Check if it's installed via pip freeze
    try:
        import subprocess
        print("\nPip Freeze:")
        subprocess.run([sys.executable, "-m", "pip", "freeze"], check=False)
    except Exception as e2:
        print(f"Pip error: {e2}")
