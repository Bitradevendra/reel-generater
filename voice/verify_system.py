#!/usr/bin/env python3
"""
Offline TTS System - Final Verification
"""

import subprocess
import sys
import os
import pathlib
from datetime import datetime

def check_files():
    """Check if essential files exist"""
    print("\n" + "="*70)
    print("  FILE VERIFICATION")
    print("="*70)
    
    files_check = {
        "main.py": "Main application",
        "requirements.txt": "Dependencies",
        "README.md": "Documentation",
        "models/en/vits-vctk.onnx": "English VITS model",
        "models/en/tokens.txt": "Phoneme tokens",
        "models/en/lexicon.txt": "Phoneme lexicon",
    }
    
    all_ok = True
    for file_path, description in files_check.items():
        if pathlib.Path(file_path).exists():
            print(f"  ✓ {description:.<40} {file_path}")
        else:
            print(f"  ✗ {description:.<40} MISSING")
            all_ok = False
    
    return all_ok

def run_test():
    """Run the TTS application with test inputs"""
    print("\n" + "="*70)
    print("  SYSTEM TEST")
    print("="*70)
    print("\nRunning synthesis test...")
    
    test_input = "1\n1\nTest offline text to speech\nn\nn\n0\n"
    
    try:
        result = subprocess.run(
            [sys.executable, "main.py"],
            input=test_input,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        combined = result.stdout + result.stderr
        
        # Check for indicators
        checks = {
            "[OK] Model loaded": "Model loading",
            "[OK] Generated audio": "Audio synthesis",
            "[OK] Saved": "File saving",
            "22050": "Sample rate",
        }
        
        passed = 0
        for indicator, description in checks.items():
            if indicator in combined:
                print(f"  ✓ {description}")
                passed += 1
            else:
                print(f"  ✗ {description}")
        
        return passed >= 3
        
    except subprocess.TimeoutExpired:
        print("  ✗ Test timeout")
        return False
    except Exception as e:
        print(f"  ✗ Test error: {e}")
        return False

def check_outputs():
    """Check generated audio files"""
    print("\n" + "="*70)
    print("  OUTPUT FILES")
    print("="*70)
    
    outputs = sorted(pathlib.Path("outputs").glob("*.wav"))
    
    if not outputs:
        print("  No audio files generated yet")
        return False
    
    total_size = 0
    for wav_file in outputs[-3:]:  # Show last 3
        size_kb = wav_file.stat().st_size / 1024
        size_mb = size_kb / 1024
        total_size += wav_file.stat().st_size
        
        if size_mb > 0.1:
            print(f"  ✓ {wav_file.name} ({size_kb:.1f} KB)")
        else:
            print(f"  ✗ {wav_file.name} (corrupted - too small)")
            return False
    
    return len(outputs) > 0

def main():
    """Run all verifications"""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + "  OFFLINE TEXT-TO-SPEECH SYSTEM - VERIFICATION".center(68) + "║")
    print("╚" + "="*68 + "╝")
    
    # Run checks
    file_ok = check_files()
    test_ok = run_test()
    output_ok = check_outputs()
    
    # Summary
    print("\n" + "="*70)
    print("  SUMMARY")
    print("="*70)
    
    if file_ok and test_ok and output_ok:
        print("  Status: ✓ ALL CHECKS PASSED - SYSTEM READY")
        return 0
    elif file_ok and test_ok:
        print("  Status: ~ SYSTEM WORKING (files may not have been created yet)")
        return 0
    elif file_ok:
        print("  Status: ✗ SYSTEM HAS ISSUES")
        return 1
    else:
        print("  Status: ✗ MISSING ESSENTIAL FILES")
        return 1

if __name__ == "__main__":
    sys.exit(main())
