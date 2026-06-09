#!/usr/bin/env python3
"""
Model Setup Helper
Helps users download and configure TTS models
"""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
MODELS_DIR = BASE_DIR / "models"

def print_menu():
    """Print setup menu."""
    print("\n" + "="*60)
    print("  TTS MODEL SETUP HELPER")
    print("="*60)
    print("\n[AVAILABLE MODELS]")
    print("  [1] English VITS VCTK (Official - Recommended)")
    print("  [2] English LibriTTS VITS (Backup option)")
    print("  [3] Custom Model (Bring your own ONNX + tokens.txt)")
    print("  [4] View current models")
    print("  [5] Clear all models")
    print("  [0] Exit")
    return input("\nSelect option [0-5]: ").strip()

def show_models():
    """Show currently downloaded models."""
    print("\n[CURRENT MODELS]")
    
    en_dir = MODELS_DIR / "en"
    te_dir = MODELS_DIR / "te"
    
    # Check English models
    if en_dir.exists():
        onnx_files = list(en_dir.glob("*.onnx"))
        token_files = list(en_dir.glob("tokens.txt"))
        if onnx_files and token_files:
            print(f"✓ English: {onnx_files[0].name}")
        else:
            print("✗ English: Incomplete model (missing .onnx or tokens.txt)")
    else:
        print("✗ English: Not downloaded")
    
    # Check Telugu models
    if te_dir.exists():
        onnx_files = list(te_dir.glob("*.onnx"))
        token_files = list(te_dir.glob("tokens.txt"))
        if onnx_files and token_files:
            print(f"✓ Telugu: {onnx_files[0].name}")
        else:
            print("✗ Telugu: Incomplete model (missing .onnx or tokens.txt)")
    else:
        print("✗ Telugu: Not downloaded")

def add_custom_model():
    """Add custom model files."""
    print("\n[ADD CUSTOM MODEL]")
    
    lang = input("Language code (en/te): ").strip().lower()
    if lang not in ["en", "te"]:
        print("Invalid language code")
        return
    
    model_dir = MODELS_DIR / lang
    model_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\nPlace your model files in: {model_dir}")
    print("Required files:")
    print("  - model.onnx (or language-specific name like vits-vctk.onnx)")
    print("  - tokens.txt")
    
    print("\nHow to get models:")
    print("1. Download ONNX TTS models from:")
    print("   - Hugging Face: https://huggingface.co/models")
    print("   - Model Zoo: https://github.com/pytorch/hub")
    print("2. Extract model.onnx and tokens.txt files")
    print("3. Copy them to the directory shown above")
    print("4. Rename model.onnx to vits-vctk.onnx (for English)")
    print("      or libritts-vits.onnx (for alternate English)")
    
    input("\nPress Enter after copying model files...")
    
    # Verify files
    onnx_files = list(model_dir.glob("*.onnx"))
    token_files = list(model_dir.glob("tokens.txt"))
    
    if onnx_files and token_files:
        print(f"✓ Model files found for {lang}")
        print(f"  Model: {onnx_files[0].name}")
        print(f"  Tokens: tokens.txt")
    else:
        print("✗ Model files not found")
        if not onnx_files:
            print("  Missing: *.onnx file")
        if not token_files:
            print("  Missing: tokens.txt file")

def clear_models():
    """Clear all downloaded models."""
    import shutil
    
    response = input("\nClear ALL models? This cannot be undone [y/N]: ").strip()
    if response.lower() != 'y':
        print("Cancelled")
        return
    
    try:
        en_dir = MODELS_DIR / "en"
        te_dir = MODELS_DIR / "te"
        
        if en_dir.exists():
            shutil.rmtree(en_dir)
            print("✓ Cleared English models")
        
        if te_dir.exists():
            shutil.rmtree(te_dir)
            print("✓ Cleared Telugu models")
        
        print("Models cleared. Run main.py to re-download.")
    except Exception as e:
        print(f"Error: {e}")

def main():
    """Main menu loop."""
    while True:
        choice = print_menu()
        
        if choice == "1":
            print("\nTo download English VITS VCTK model:")
            print("Run: python main.py")
            print("Select English option [1]")
            print("Models will download automatically on first use")
        
        elif choice == "2":
            print("\nTo use LibriTTS VITS model:")
            print("Run: python main.py")
            print("Select option [2]")
            print("Models will download automatically on first use")
        
        elif choice == "3":
            add_custom_model()
        
        elif choice == "4":
            show_models()
        
        elif choice == "5":
            clear_models()
        
        elif choice == "0":
            print("\n✓ Goodbye!")
            break
        
        else:
            print("Invalid choice")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✓ Interrupted")
        sys.exit(0)
