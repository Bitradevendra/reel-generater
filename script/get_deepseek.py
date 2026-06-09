#!/usr/bin/env python3

import subprocess
import os
import sys

def download_with_aria2(url, filename):
    """Download using aria2c (fastest method)"""
    try:
        cmd = [
            "aria2c",
            "-x", "16",  # 16 connections
            "-k", "1M",  # 1MB chunk size
            "-o", filename,
            url
        ]
        print("📥 Downloading with aria2c (fastest)...")
        subprocess.run(cmd, check=True)
        return True
    except:
        return False

def download_with_curl(url, filename):
    """Download using curl"""
    try:
        cmd = ["curl", "-L", "-o", filename, url]
        print("📥 Downloading with curl...")
        subprocess.run(cmd, check=True)
        return True
    except:
        return False

def download_with_wget(url, filename):
    """Download using wget"""
    try:
        cmd = ["wget", "-O", filename, url]
        print("📥 Downloading with wget...")
        subprocess.run(cmd, check=True)
        return True
    except:
        return False

def download_with_powershell(url, filename):
    """Download using PowerShell"""
    try:
        ps_cmd = f"""
$url = '{url}'
$outfile = '{filename}'
$ProgressPreference = 'Continue'
try {{
    (New-Object System.Net.WebClient).DownloadFile($url, $outfile)
    Write-Host "Download complete"
}} catch {{
    Write-Host "Error: $($_.Exception.Message)"
    exit 1
}}
"""
        print("📥 Downloading with PowerShell...")
        subprocess.run(["powershell", "-Command", ps_cmd], check=True)
        return True
    except:
        return False

def main():
    print("=" * 70)
    print("🎬 DEEPSEEK MODEL DOWNLOADER")
    print("=" * 70)
    print()
    
    # DeepSeek R1 model options
    models = [
        {
            "name": "DeepSeek R1 Distill Qwen 7B (Q4 - FASTEST)",
            "size": "~4.7 GB",
            "urls": [
                "https://huggingface.co/bartowski/deepseek-r1-distill-qwen-7b-gguf/resolve/main/deepseek-r1-distill-qwen-7b-Q4_K_M.gguf",
                "https://ollama.ai/library/deepseek-r1",
            ]
        },
        {
            "name": "DeepSeek R1 Distill Qwen 7B (Q5 - BEST QUALITY)",
            "size": "~6.2 GB",
            "urls": [
                "https://huggingface.co/bartowski/deepseek-r1-distill-qwen-7b-gguf/resolve/main/deepseek-r1-distill-qwen-7b-Q5_K_M.gguf",
            ]
        },
        {
            "name": "DeepSeek R1 Distill Qwen 7B (Q3 - SMALLEST)",
            "size": "~3.3 GB",
            "urls": [
                "https://huggingface.co/bartowski/deepseek-r1-distill-qwen-7b-gguf/resolve/main/deepseek-r1-distill-qwen-7b-Q3_K_M.gguf",
            ]
        }
    ]
    
    if os.path.exists("model.gguf"):
        size = os.path.getsize("model.gguf") / (1024**3)
        print(f"✓ Model already exists: model.gguf ({size:.2f} GB)")
        return
    
    print("Available DeepSeek Models:\n")
    for i, model in enumerate(models, 1):
        print(f"{i}. {model['name']}")
        print(f"   Size: {model['size']}\n")
    
    while True:
        try:
            choice = int(input("Select model (1-3) [default: 1]: ").strip() or "1")
            if 1 <= choice <= 3:
                selected = models[choice - 1]
                break
        except ValueError:
            pass
        print("Invalid choice, enter 1-3")
    
    print(f"\nSelected: {selected['name']}")
    print(f"Size: {selected['size']}")
    print("\nInitiating download...")
    print("This will take 10-60 minutes depending on your connection.\n")
    
    # Try multiple download methods
    for i, url in enumerate(selected['urls'], 1):
        print(f"\n--- Attempt {i} ---")
        print(f"URL: {url}\n")
        
        # Try in order: aria2c > curl > wget > powershell
        if download_with_aria2(url, "model.gguf"):
            break
        elif download_with_curl(url, "model.gguf"):
            break
        elif download_with_wget(url, "model.gguf"):
            break
        elif download_with_powershell(url, "model.gguf"):
            break
        else:
            print(f"✗ Attempt {i} failed, trying next URL...\n")
            continue
    
    # Verify download
    if os.path.exists("model.gguf"):
        size = os.path.getsize("model.gguf") / (1024**3)
        if size > 1:  # Verify it's a real file
            print("\n" + "=" * 70)
            print("✓ DOWNLOAD COMPLETE!")
            print("=" * 70)
            print(f"\n✓ Model saved: model.gguf ({size:.2f} GB)")
            print("\nNow run: python main.py")
            return
    
    print("\n✗ Download failed or incomplete")
    print("\n📌 MANUAL DOWNLOAD OPTION:")
    print("\nIf automatic download fails, download manually:")
    for i, model in enumerate(models, 1):
        print(f"\n{i}. {model['name']}")
        print(f"   {model['urls'][0]}")
    
    print("\nThen save as: model.gguf in this folder")

if __name__ == "__main__":
    main()
