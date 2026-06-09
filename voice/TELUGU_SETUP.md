# Telugu TextTo Speech Setup Guide

## Current Status

✓ **English TTS**: Fully working with sherpa-onnx (VITS VCTK model)
⚠ **Telugu TTS**: Requires Python 3.11 or earlier (your system has Python 3.13)

## Why Telugu Isn't Immediately Available

The **TTS library (Coqui TTS)** that provides high-quality Telugu synthesis only supports Python versions up to 3.11. Your Python 3.13 environment is too new for this package.

## Solution  1: Downgrade Python (Recommended for Telugu)

If you want to use Telugu TTS, downgrade to Python 3.11:

```powershell
# Download Python 3.11 from: https://www.python.org/downloads/release/python-3-11-0/
# Or use pyenv, conda, or Windows Store

# After installing Python 3.11:
cd c:\path\to\voice

# Delete old venv
rmdir /s /q venv

# Create new venv with Python 3.11
py -3.11 -m venv venv

# Activate and install dependencies
.\ venv\Scripts\Activate.ps1
pip install -r requirements_with_telugu.txt

# Run application
python main.py
```

## Solution 2: Use English Only (Recommended if Python 3.13 preferred)

Keep your Python 3.13 setup and use English TTS, which works perfectly offline:

```powershell
cd c:\Users\papan\Downloads\voice
.\ venv\Scripts\python.exe main.py

# Select option [1] for English
```

English TTS with the VITS VCTK model provides:
- ✓ 24 different speaker voices
- ✓ High-quality synthesis
- ✓ Offline operation
- ✓ CPU-only (no GPU needed)
- ✓ ~5-30 seconds per 100 words

## For Advanced Users: Python 3.11 with Telugu

If you install Python 3.11, create a `requirements_with_telugu.txt`:

```text
sherpa-onnx>=1.10.0
numpy>=1.21.0
sounddevice>=0.4.5
scipy>=1.7.0
requests>=2.26.0
tqdm>=4.62.0
TTS>=0.17.0
```

Then install with:
```bash
pip install -r requirements_with_telugu.txt
```

The application will automatically detect Python 3.11 and enable Telugu support.

## Available Languages (with Python 3.11+)

| Language | Engine | Status |
|----------|--------|--------|
| English | sherpa-onnx (VITS VCTK) | ✓ Ready |
| Telugu | Coqui TTS (VITS) | ⚠ Python 3.11 only |

## Tested & Working

English TTS has been verified to work:
- ✓ Model loads in < 5 seconds
- ✓ Audio synthesis: 105,216 samples at 22,050Hz
- ✓ File saved successfully as WAV
- ✓ Offline operation confirmed
- ✓ CPU-only inference

## Current System Specs

- Python Version: 3.13
- Shakespeare-onnx: 1.12.31
- Model: VITS VCTK (English)
- Sample Rate: 22,050 Hz
- Output Format: WAV (16-bit PCM)

## Recommendation

For most users, **English TTS is excellent and production-ready**. If you specifically need Telugu, downgrade to Python 3.11 following Solution 1 above.
