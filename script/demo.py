#!/usr/bin/env python3
"""
Reel Script Generator - Demo & Quick Start
============================================
"""

import os
import sys
import io

# Fix Windows encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def main():
    print("=" * 70)
    print("[*] REEL SCRIPT GENERATOR DEMO")
    print("=" * 70)
    print()
    
    # Verify model
    if not os.path.exists("model.gguf"):
        print("[-] Error: model.gguf not found")
        print("[*] Download from: https://huggingface.co/bartowski/deepseek-r1-distill-qwen-7b-gguf")
        return
    
    size_gb = os.path.getsize("model.gguf") / (1024**3)
    print(f"[+] Model found: model.gguf ({size_gb:.2f} GB)")
    
    # Check libraries
    try:
        import ctransformers
        print("[+] ctransformers: ready")
    except:
        print("[-] ctransformers: NOT installed")
        return
    
    try:
        import torch
        print(f"[+] PyTorch: ready ({torch.__version__})")
    except:
        print("[-] PyTorch: NOT installed")
    
    print()
    print("=" * 70)
    print("[*] RUNNING INTERACTIVE GENERATOR")
    print("=" * 70)
    print()
    print("[*] Example input for demo:")
    print("    Topic: What is Artificial Intelligence")  
    print("    Type: 1 (Technology)")
    print("    Duration: 15 seconds")
    print("    Audience: 2 (Common people)")
    print()
    print("-" * 70)
    print()
    
    # Import and run main
    try:
        from main import main as generator_main
        generator_main()
    except Exception as e:
        print(f"[-] Error: {e}")
        print()
        print("[*] Try running directly:")
        print("    python main.py")

if __name__ == "__main__":
    main()
