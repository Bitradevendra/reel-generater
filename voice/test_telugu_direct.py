#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Direct Telugu TTS test with hardcoded text"""

import sys
sys.path.insert(0, '.')

from telugu_tts import TeluguTTSMMS
import os

print("\n" + "="*60)
print("Direct Telugu TTS Test")
print("="*60 + "\n")

# Initialize the model
print("[1] Loading Telugu TTS model...")
tts = TeluguTTSMMS(device="cpu")

if not tts.model:
    print("[ERROR] Model failed to load!")
    sys.exit(1)

print("[OK] Model loaded successfully!\n")

# Test texts
test_texts = [
    "నమస్కారం",  # Hello
    "మీరు ఎలా ఉన్నారు?",  # How are you?
    "ఆన్‍డ్‌రాయిడ్",  # Android
]

print("[2] Testing synthesis...\n")

for i, text in enumerate(test_texts, 1):
    print(f"Test {i}: '{text}'")
    result = tts.synthesize(text)
    
    if result:
        audio, sr = result
        print(f"  ✓ Generated {len(audio)} samples at {sr} Hz\n")
        
        # Save the audio
        output_path = f"outputs/telugu_test_{i}.wav"
        tts.synthesize_to_file(text, output_path)
        print(f"  ✓ Saved to {output_path}\n")
    else:
        print(f"  ✗ Failed!\n")

print("="*60)
print("Test complete!")
print("="*60)
