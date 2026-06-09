#!/usr/bin/env python3

import os
import webbrowser
import sys

def main():
    print("\n" + "=" * 70)
    print("🎬 DEEPSEEK MODEL CHECKER")
    print("=" * 70 + "\n")
    
    model_path = "model.gguf"
    
    if os.path.exists(model_path):
        size_gb = os.path.getsize(model_path) / (1024**3)
        print(f"✓ Model found: {model_path}")
        print(f"✓ Size: {size_gb:.2f} GB")
        print(f"\n✓ Ready! Run: python main.py\n")
        return
    
    print(f"✗ Model not found: {model_path}\n")
    print("=" * 70)
    print("QUICK FIX - Choose an option:")
    print("=" * 70)
    print("\n1️⃣  OPEN DOWNLOAD PAGE (browser)")
    print("    Link: https://huggingface.co/bartowski/deepseek-r1-distill-qwen-7b-gguf")
    print("\n2️⃣  VIEW DOWNLOAD INSTRUCTIONS")
    print("    Run: type DOWNLOAD_DEEPSEEK.md (in repo)")
    print("\n3️⃣  TRY RETRY DOWNLOAD NOW")
    print("    Run: python get_deepseek.py")
    print("\n4️⃣  USE ALTERNATIVE LIGHTWEIGHT MODEL")
    print("    Download Phi-3.5 instead (2.3 GB, faster)")
    print("\nEnter choice (1-4): ", end="", flush=True)
    
    try:
        choice = input().strip()
        
        if choice == "1":
            print("\nOpening browser...")
            webbrowser.open("https://huggingface.co/bartowski/deepseek-r1-distill-qwen-7b-gguf")
        elif choice == "2":
            os.system("type DOWNLOAD_DEEPSEEK.md" if sys.platform == "win32" else "cat DOWNLOAD_DEEPSEEK.md")
        elif choice == "3":
            os.system("python get_deepseek.py")
        elif choice == "4":
            print("\nAlternative: Phi-3.5 Mini (faster, 2.3 GB)")
            print("Link: https://huggingface.co/QuantFactory/Phi-3-5-mini-instruct-GGUF")
        else:
            print("Invalid choice")
    except KeyboardInterrupt:
        print("\n\nCancelled.")

if __name__ == "__main__":
    main()
