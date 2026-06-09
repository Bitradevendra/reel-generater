#!/usr/bin/env python3
"""
Telugu TTS using Meta's MMS (Massively Multilingual Speech)
============================================================

Simplest working solution for Python 3.13+
Installation: pip install transformers>=4.33 torch scipy

Working with:
- Python 3.13+
- Offline processing (no API calls)
- Natural quality Telugu voice
- ~150MB model download
"""

import sys
import os
from pathlib import Path
from datetime import datetime

def main():
    print("\n" + "="*70)
    print("TELUGU TTS - Meta MMS (Python 3.13+)")
    print("="*70)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print(f"ERROR: Python 3.8+ required. You have {sys.version}")
        return False
    
    print(f"Python Version: {sys.version.split()[0]}")
    
    # Import required packages
    print("\n[1/4] Checking dependencies...")
    try:
        import torch
        import scipy
        from transformers import VitsModel, AutoTokenizer
        print("  ✓ All dependencies available")
    except ImportError as e:
        print(f"  ✗ Missing: {e}")
        print("\nInstall required packages:")
        print("  pip install transformers>=4.33 torch scipy")
        return False
    
    # Load models
    print("\n[2/4] Loading Telugu tokenizer...")
    try:
        tokenizer = AutoTokenizer.from_pretrained("facebook/mms-tts-tel")
        print("  ✓ Tokenizer loaded")
    except Exception as e:
        print(f"  ✗ Error loading tokenizer: {e}")
        return False
    
    print("\n[3/4] Loading MMS Telugu TTS model (~150MB)...")
    try:
        model = VitsModel.from_pretrained("facebook/mms-tts-tel")
        model.eval()
        print("  ✓ Model loaded successfully")
        print(f"    Sample Rate: {model.config.sampling_rate}Hz")
    except Exception as e:
        print(f"  ✗ Error loading model: {e}")
        return False
    
    # Prepare for synthesis
    print("\n[4/4] Ready for synthesis")
    print("-" * 70)
    
    # Test texts
    test_samples = [
        "నమస్కారం",  # Hello
        "ఈ సిస్టమ్ చాలా సરળమైనది",  # This system is very simple
        "భారతదేశం ఆశీర్వాదం",  # India is blessed
    ]
    
    # Create outputs directory
    output_dir = Path("telugu_tts_outputs")
    output_dir.mkdir(exist_ok=True)
    
    # Synthesize samples
    for idx, text in enumerate(test_samples, 1):
        try:
            print(f"\n[Sample {idx}/3]")
            print(f"Text: {text}")
            
            # Tokenize
            inputs = tokenizer(text, return_tensors="pt")
            
            # Generate speech
            print("Synthesizing...", end=" ", flush=True)
            with torch.no_grad():
                output = model(**inputs).waveform
            
            # Save to WAV
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = output_dir / f"telugu_sample_{idx}_{timestamp}.wav"
            
            waveform = output.cpu().numpy().squeeze()
            sample_rate = model.config.sampling_rate
            
            import scipy.io.wavfile
            scipy.io.wavfile.write(output_path, rate=sample_rate, data=waveform)
            
            duration = len(waveform) / sample_rate
            print(f"Done!")
            print(f"  Saved: {output_path}")
            print(f"  Duration: {duration:.2f} seconds")
            
        except Exception as e:
            print(f"  Error: {e}")
    
    print("\n" + "="*70)
    print("✓ Telugu TTS synthesis complete!")
    print(f"Outputs saved to: {output_dir.absolute()}")
    print("="*70)
    
    return True


def interactive_mode():
    """Interactive text input mode."""
    print("\n" + "="*70)
    print("INTERACTIVE TELUGU TTS")
    print("="*70)
    print("\nYou can now type Telugu text to synthesize.")
    print("Type 'quit' to exit.\n")
    
    # Load model once
    try:
        from transformers import VitsModel, AutoTokenizer
        import torch
        import scipy.io.wavfile
        
        tokenizer = AutoTokenizer.from_pretrained("facebook/mms-tts-tel")
        model = VitsModel.from_pretrained("facebook/mms-tts-tel")
        model.eval()
        sample_rate = model.config.sampling_rate
        
        output_dir = Path("telugu_tts_outputs")
        output_dir.mkdir(exist_ok=True)
        
        while True:
            text = input("\nEnter Telugu text (or 'quit'): ").strip()
            
            if text.lower() == 'quit':
                print("Exiting...")
                break
            
            if not text:
                print("Empty text, skipping...")
                continue
            
            try:
                print("Synthesizing...", end=" ", flush=True)
                
                inputs = tokenizer(text, return_tensors="pt")
                with torch.no_grad():
                    output = model(**inputs).waveform
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = output_dir / f"telugu_{timestamp}.wav"
                
                waveform = output.cpu().numpy().squeeze()
                scipy.io.wavfile.write(output_path, rate=sample_rate, data=waveform)
                
                duration = len(waveform) / sample_rate
                print(f"Done!")
                print(f"  Saved: {output_path}")
                print(f"  Duration: {duration:.2f} seconds")
                
            except Exception as e:
                print(f"Error: {e}")
    
    except Exception as e:
        print(f"Error loading model: {e}")
        return False
    
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Telugu TTS with Meta MMS for Python 3.13+"
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive mode (type Telugu text to synthesize)"
    )
    parser.add_argument(
        "--text", "-t",
        type=str,
        help="Synthesize single Telugu text"
    )
    
    args = parser.parse_args()
    
    # Run appropriate mode
    if args.interactive:
        interactive_mode()
    elif args.text:
        # Single text synthesis
        try:
            from transformers import VitsModel, AutoTokenizer
            import torch
            import scipy.io.wavfile
            from pathlib import Path
            
            tokenizer = AutoTokenizer.from_pretrained("facebook/mms-tts-tel")
            model = VitsModel.from_pretrained("facebook/mms-tts-tel")
            model.eval()
            
            inputs = tokenizer(args.text, return_tensors="pt")
            with torch.no_grad():
                output = model(**inputs).waveform
            
            output_dir = Path("telugu_tts_outputs")
            output_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = output_dir / f"telugu_{timestamp}.wav"
            
            waveform = output.cpu().numpy().squeeze()
            scipy.io.wavfile.write(
                output_path, 
                rate=model.config.sampling_rate, 
                data=waveform
            )
            
            print(f"✓ Saved: {output_path}")
        except Exception as e:
            print(f"Error: {e}")
    else:
        # Default: run test samples
        success = main()
        sys.exit(0 if success else 1)
