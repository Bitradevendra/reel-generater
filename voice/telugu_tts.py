#!/usr/bin/env python3
"""
Telugu TTS using Meta MMS (Python 3.13 compatible)
Works offline with Transformers library and PyTorch
"""

import os
import sys
import numpy as np
import warnings
from pathlib import Path
from typing import Optional, Tuple

warnings.filterwarnings("ignore")

# Import transformers and torch
try:
    import torch
    from transformers import pipeline
    print("[OK] Transformers and PyTorch loaded successfully")
except ImportError as e:
    print(f"[ERROR] Required packages missing: {e}")
    print("Install with: pip install --upgrade transformers torch scipy")
    sys.exit(1)


class TeluguTTSMMS:
    """Telugu Text-to-Speech using Meta's MMS model"""
    
    def __init__(self, device: str = "cpu"):
        """
        Initialize Telugu TTS with Meta MMS model
        
        Args:
            device: "cpu" or "cuda" (GPU if available)
        """
        self.device = device if torch.cuda.is_available() else "cpu"
        self.model = None
        self.sample_rate = None
        self.load_model()
    
    def load_model(self) -> bool:
        """Load the MMS Telugu TTS model"""
        try:
            print("[INFO] Loading Meta MMS Telugu model (first run may take 2-3 min)...")
            
            # Initialize the TTS pipeline
            # facebook/mms-tts-tel is the Telugu model
            self.model = pipeline(
                "text-to-speech",
                model="facebook/mms-tts-tel",
                device=self.device
            )
            
            # MMS model has specific sample rate
            self.sample_rate = 16000
            
            print("[OK] Telugu TTS model loaded successfully!")
            return True
        
        except Exception as e:
            print(f"[ERROR] Failed to load model: {e}")
            return False
    
    def synthesize(self, text: str) -> Optional[Tuple[np.ndarray, int]]:
        """
        Synthesize Telugu text to speech
        
        Args:
            text: Telugu text to synthesize
            
        Returns:
            Tuple of (audio_array, sample_rate) or None if failed
        """
        if not self.model:
            print("[ERROR] Model not loaded")
            return None
        
        if not text or not text.strip():
            print("[WARN] Empty text provided")
            return None
        
        try:
            print(f"[INFO] Synthesizing Telugu: '{text[:50]}{'...' if len(text) > 50 else ''}'")
            
            # Generate speech
            output = self.model(text)
            
            # Extract audio array - the model returns a dict with "audio" key
            if isinstance(output, dict) and "audio" in output:
                audio = output["audio"]
            else:
                audio = output
            
            # Convert to numpy if needed
            if isinstance(audio, list):
                audio = np.array(audio, dtype=np.float32)
            elif isinstance(audio, torch.Tensor):
                audio = audio.cpu().numpy().astype(np.float32)
            else:
                audio = np.array(audio, dtype=np.float32)
            
            # Flatten if needed
            if audio.ndim > 1:
                audio = audio.flatten()
            
            # Normalize
            if audio.max() > 1.0:
                audio = audio / audio.max()
            
            print(f"[OK] Generated audio: {len(audio)} samples at {self.sample_rate}Hz")
            return audio, self.sample_rate
        
        except Exception as e:
            print(f"[ERROR] Synthesis failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def synthesize_to_file(self, text: str, output_path: str) -> bool:
        """
        Synthesize and save to WAV file
        
        Args:
            text: Telugu text
            output_path: Path to save WAV file
            
        Returns:
            True if successful
        """
        result = self.synthesize(text)
        if result is None:
            return False
        
        audio, sample_rate = result
        
        try:
            from scipy.io import wavfile
            
            # Convert to int16
            audio_int16 = np.int16(audio * 32767)
            
            # Create output directory if needed
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Save WAV file
            wavfile.write(output_path, sample_rate, audio_int16)
            print(f"[OK] Saved: {output_path}")
            return True
        
        except Exception as e:
            print(f"[ERROR] Failed to save file: {e}")
            return False


# Quick test
if __name__ == "__main__":
    print("\n" + "="*60)
    print("Telugu TTS Test (Meta MMS)")
    print("="*60)
    
    tts = TeluguTTSMMS()
    
    if tts.model:
        # Test Telugu text
        telugu_text = "నమస్కారం, ఎలా ఉన్నారు?"
        
        print(f"\nTest text: {telugu_text}")
        result = tts.synthesize(telugu_text)
        
        if result:
            audio, sr = result
            print(f"[OK] Audio generated: {len(audio)} samples")
            
            # Save test file
            tts.synthesize_to_file(telugu_text, "telugu_test.wav")
        else:
            print("[FAIL] Synthesis failed")
    
    print("\n" + "="*60)
