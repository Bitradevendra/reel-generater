# Agent Setup Guide

This file is for coding agents and IDE assistants that receive this repository and need to set it up on a Windows machine. Follow this file before modifying app behavior.

## Objective

Make the project runnable from a fresh clone on Windows. Do not assume large local assets were committed. Recreate them using documented downloads/builds.

Primary repo:

```text
https://github.com/Bitradevendra/reel-generater.git
```

## Non-Negotiable Rules

- Do not commit `venv/`, caches, generated videos, logs, model binaries, or downloaded `.gguf` files.
- Do not vendor the raw `script/llama.cpp` directory into the parent repo. It is a Git submodule.
- Do not replace `script/model.gguf` in `config.yaml` with a machine-specific absolute path.
- Keep setup commands Windows PowerShell compatible.
- If a model download fails, report the failing URL/model name and the exact command that failed.
- If you change setup docs, test or at least syntax-check the commands you touched.

## Expected Local-Only Assets

These are intentionally not stored in Git:

```text
venv/
output/
outputs/
*.gguf
voice/models/
language_converter/.hf_cache/
script/.cache/
script/llama.cpp/build/
*.log
```

They are recreated during setup.

## Fresh Windows Setup

Run in PowerShell.

### 1. Install system dependencies

```powershell
winget install --id Git.Git -e
winget install --id Python.Python.3.11 -e
winget install --id Kitware.CMake -e
winget install --id Google.Chrome -e
winget install --id Microsoft.VisualStudio.2022.BuildTools -e --override "--quiet --wait --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
```

Open a new PowerShell window after installing these.

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### 2. Clone with submodules

```powershell
cd $env:USERPROFILE\Downloads
git clone --recurse-submodules https://github.com/Bitradevendra/reel-generater.git
cd reel-generater
git submodule update --init --recursive
```

### 3. Create venv and install Python dependencies

```powershell
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
pip install --prefer-binary -r requirements.txt
```

### 4. Build llama.cpp CLI fallback

```powershell
cd script\llama.cpp
cmake -S . -B build -G "Visual Studio 17 2022" -A x64
cmake --build build --config Release
cd ..\..
```

Verify:

```powershell
Test-Path .\script\llama.cpp\build\bin\Release\llama-cli.exe
```

Expected: `True`.

### 5. Download the GGUF script model

```powershell
cd script
python get_deepseek.py
cd ..
```

The required file is:

```text
script/model.gguf
```

If the automatic downloader fails, manually download a GGUF model from one of:

```text
https://huggingface.co/bartowski/deepseek-r1-distill-qwen-7b-gguf
https://huggingface.co/QuantFactory/Phi-3-5-mini-instruct-GGUF
```

Then rename it to `model.gguf` and place it in `script/`.

### 6. Preload voice models

English sherpa-onnx VITS VCTK:

```powershell
python -c "from core.voice_engine import synthesize_speech; synthesize_speech('Voice setup test.', 'output/setup/english_test.wav', language='en')"
```

Expected files:

```text
voice/models/en/vits-vctk.onnx
voice/models/en/tokens.txt
voice/models/en/lexicon.txt
```

Telugu Facebook MMS TTS:

```powershell
python -c "from transformers import VitsModel, AutoTokenizer; AutoTokenizer.from_pretrained('facebook/mms-tts-tel'); VitsModel.from_pretrained('facebook/mms-tts-tel'); print('Telugu MMS model ready')"
```

This uses the Hugging Face cache, not `voice/models/te`.

### 7. Preload translation model

Translation uses Facebook NLLB:

```powershell
python -c "from transformers import AutoModelForSeq2SeqLM, AutoTokenizer; AutoTokenizer.from_pretrained('facebook/nllb-200-distilled-600M', src_lang='eng_Latn'); AutoModelForSeq2SeqLM.from_pretrained('facebook/nllb-200-distilled-600M', use_safetensors=True); print('NLLB translation model ready')"
```

### 8. Verify Chrome/Selenium image scraping

```powershell
python -c "from selenium import webdriver; from selenium.webdriver.chrome.options import Options; o=Options(); o.add_argument('--headless=new'); d=webdriver.Chrome(options=o); print('Chrome started'); d.quit(); print('Chrome/Selenium ready')"
```

## Full Verification Checklist

Run from repo root with venv active:

```powershell
python --version
python -c "import torch, transformers, sherpa_onnx, moviepy, selenium, yaml; print('Python packages ready')"
Test-Path .\script\model.gguf
Test-Path .\script\llama.cpp\build\bin\Release\llama-cli.exe
Test-Path .\voice\models\en\vits-vctk.onnx
python -c "from transformers import AutoTokenizer; AutoTokenizer.from_pretrained('facebook/mms-tts-tel'); AutoTokenizer.from_pretrained('facebook/nllb-200-distilled-600M', src_lang='eng_Latn'); print('HF tokenizers ready')"
```

Expected:

- Python is `3.11.x`.
- Imports succeed.
- All `Test-Path` checks return `True`.
- Hugging Face tokenizers load.

## Run The App

```powershell
.\venv\Scripts\Activate.ps1
python main.py
```

## Important Architecture Notes

- `core/script_engine.py` tries `llama-cpp-python` first, then falls back to compiled `llama-cli.exe`, then can fall back to Ollama if enabled.
- `config.yaml` must keep `script.model_path` as `script/model.gguf` for portable setup.
- English voice uses `core.voice_engine` and auto-downloads sherpa-onnx VITS files into `voice/models/en`.
- Telugu voice in the main pipeline uses `facebook/mms-tts-tel` through Transformers/Hugging Face cache.
- Translation uses `facebook/nllb-200-distilled-600M`.
- Image scraping uses Selenium and Chrome.
- Video rendering uses MoviePy and `imageio-ffmpeg`.

## Known Risks To Report

Report these clearly instead of silently changing project behavior:

- `llama-cpp-python` wheel build failure.
- Visual Studio C++ Build Tools missing or incomplete.
- Hugging Face download/network failure.
- Low disk space for `.gguf`, NLLB, or MMS models.
- Chrome/Selenium driver mismatch.
- GPU-specific PyTorch or CUDA mismatch.

## Git Hygiene

Before committing, run:

```powershell
git status -sb
git diff --stat
```

Make sure no generated or model files are staged:

```powershell
git diff --cached --name-only
```

If any of these appear staged, unstage them:

```text
venv/
output/
outputs/
*.gguf
voice/models/
language_converter/.hf_cache/
script/llama.cpp/build/
*.log
```

Use normal commits for docs/setup fixes. Keep `script/llama.cpp` as a submodule pointer, not copied source.
