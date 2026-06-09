try:
    import torch
    print("[OK] PyTorch version:", torch.__version__)
except ImportError as e:
    print("[FAIL] PyTorch:", e)

try:
    import transformers
    print("[OK] Transformers version:", transformers.__version__)
except ImportError as e:
    print("[FAIL] Transformers:", e)

try:
    import torchaudio
    print("[OK] Torchaudio available")
except ImportError as e:
    print("[FAIL] Torchaudio:", e)

print("\nAttempting to import Telugu TTS module...")
try:
    from telugu_tts import TeluguTTSMMS
    print("[OK] Telugu TTS module imported!")
except Exception as e:
    print("[FAIL] Telugu TTS import:", e)
