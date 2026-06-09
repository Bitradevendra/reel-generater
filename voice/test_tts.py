#!/usr/bin/env python3
"""
Test script for running the TTS application with pre-defined inputs
"""

import subprocess
import sys
import os
import time

def test_tts():
    """Run TTS application with test inputs, with better handling"""
    
    # More elaborate test: select English, type text, then exit
    test_inputs = "1\n1\nHello world, this is offline text to speech synthesis\nn\nn\n0\n"
    
    print("=" * 70)
    print("  OFFLINE TTS SYSTEM - COMPREHENSIVE TEST")
    print("=" * 70)
    print("\nStarting TTS application test...\n")
    
    # Run the application with test inputs
    try:
        process = subprocess.Popen(
            [sys.executable, "main.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.getcwd(),
            text=True,
            bufsize=1  # Line buffering
        )
        
        # Send inputs 
        stdout, stderr = process.communicate(input=test_inputs, timeout=120)
        
        # Print combined output
        print(stdout)
        
        # Filter verbose warnings for display
        if stderr:
            stderr_clean = "\n".join([
                line for line in stderr.split("\n")
                if "unknown token" not in line.lower() and not line.strip().startswith("D:\\")
            ])
            if stderr_clean.strip():
                print("\n[STDERR]")
                print(stderr_clean)
        
        print("\n" + "=" * 70)
        print("  TEST RESULTS")
        print("=" * 70)
        
        # Check for success indicators
        success_count = 0
        total_tests = 0
        
        tests = [
            ("[OK] Generated audio", "Audio synthesis"),
            ("[OK] Saved:", "Audio file saved"),
            ("[MODEL INITIALIZATION]", "Model initialization"),
            ("[OK] Model loaded", "Model loading"),
            ("22050", "Sample rate"),
        ]
        
        for test_str, test_name in tests:
            total_tests += 1
            if test_str in stdout:
                print(f"  [PASS] {test_name}")
                success_count += 1
            else:
                print(f"  [FAIL] {test_name}")
        
        print(f"\nResult: {success_count}/{total_tests} tests passed")
        
        # Check if audio files were created
        import pathlib
        outputs = list(pathlib.Path("outputs").glob("*.wav"))
        if outputs:
            print(f"  [PASS] Generated audio files: {len(outputs)}")
            for wav_file in sorted(outputs)[-3:]:  # Show last 3
                size_kb = wav_file.stat().st_size / 1024
                print(f"         └─ {wav_file.name} ({size_kb:.1f} KB)")
        else:
            print(f"  [FAIL] No audio files generated")
        
        print("\n" + "=" * 70)
        
        return success_count >= 4  # At least 4 core tests must pass
        
    except subprocess.TimeoutExpired:
        print("[FAIL] Test timed out after 120 seconds")
        return False
    except Exception as e:
        print(f"[FAIL] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = test_tts()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Test cancelled by user")
        sys.exit(1)

