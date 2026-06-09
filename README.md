# Reel Generator

Windows-first local reel generator for scripts, translation, voice, image scraping, subtitles, and final reel video composition.

Coding agents and IDE assistants should read `AGENTS.md` before setup or edits.

This repo keeps source code in GitHub and recreates heavy local assets during setup:

- `script/llama.cpp` is included as a pinned Git submodule.
- LLM `.gguf` files are downloaded locally.
- Facebook NLLB translation model downloads from Hugging Face on first setup/use.
- Facebook MMS Telugu TTS model downloads from Hugging Face on first setup/use.
- English sherpa-onnx VITS voice model downloads on first setup/use.
- Generated videos, caches, logs, model files, and virtual environments are ignored by Git.

I cannot promise every Windows PC will work without troubleshooting, because GPU drivers, Visual Studio C++ tools, Python wheels, internet access, and Hugging Face availability can vary. The commands below are the intended full setup path for a fresh Windows machine.

## 1. Install Windows Requirements

Open PowerShell as Administrator and paste:

```powershell
winget install --id Git.Git -e
winget install --id Python.Python.3.11 -e
winget install --id Kitware.CMake -e
winget install --id Google.Chrome -e
winget install --id Microsoft.VisualStudio.2022.BuildTools -e --override "--quiet --wait --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
```

Close PowerShell, open a new PowerShell window, then allow local venv activation:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## 2. Clone With llama.cpp

```powershell
cd $env:USERPROFILE\Downloads
git clone --recurse-submodules https://github.com/Bitradevendra/reel-generater.git
cd reel-generater
```

If `script\llama.cpp` is empty:

```powershell
git submodule update --init --recursive
```

## 3. Create Python Environment

```powershell
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
pip install --prefer-binary -r requirements.txt
```

This installs the main project dependencies, including:

- `torch`
- `transformers`
- `sentencepiece`
- `accelerate`
- `sherpa-onnx`
- `moviepy`
- `imageio-ffmpeg`
- `selenium`
- `webdriver-manager`
- `llama-cpp-python`

## 4. Build llama.cpp CLI

```powershell
cd script\llama.cpp
cmake -S . -B build -G "Visual Studio 17 2022" -A x64
cmake --build build --config Release
cd ..\..
```

Confirm:

```powershell
Test-Path .\script\llama.cpp\build\bin\Release\llama-cli.exe
```

Expected output:

```text
True
```

## 5. Download Script LLM Model

Automatic option:

```powershell
cd script
python get_deepseek.py
cd ..
```

The file must exist here:

```text
script\model.gguf
```

Manual option:

1. Download a `.gguf` model from Hugging Face.
2. Rename it to `model.gguf`.
3. Put it in `script\model.gguf`.

Recommended model links:

- `https://huggingface.co/bartowski/deepseek-r1-distill-qwen-7b-gguf`
- `https://huggingface.co/QuantFactory/Phi-3-5-mini-instruct-GGUF`

## 6. Download Voice Models

English voice model, sherpa-onnx VITS VCTK:

```powershell
python -c "from core.voice_engine import synthesize_speech; synthesize_speech('Voice setup test.', 'output/setup/english_test.wav', language='en')"
```

This downloads these files under `voice\models\en`:

```text
voice\models\en\vits-vctk.onnx
voice\models\en\tokens.txt
voice\models\en\lexicon.txt
```

Telugu voice model, Facebook MMS:

```powershell
python -c "from transformers import VitsModel, AutoTokenizer; AutoTokenizer.from_pretrained('facebook/mms-tts-tel'); VitsModel.from_pretrained('facebook/mms-tts-tel'); print('Telugu MMS model ready')"
```

The Telugu MMS files are cached by Hugging Face under your Windows user cache. They are not stored inside this GitHub repo.

## 7. Download Translation Model

Translation uses:

```text
facebook/nllb-200-distilled-600M
```

Pre-download it:

```powershell
python -c "from transformers import AutoModelForSeq2SeqLM, AutoTokenizer; AutoTokenizer.from_pretrained('facebook/nllb-200-distilled-600M', src_lang='eng_Latn'); AutoModelForSeq2SeqLM.from_pretrained('facebook/nllb-200-distilled-600M', use_safetensors=True); print('NLLB translation model ready')"
```

This model is large, roughly 1.2 GB or more depending on cache files.

## 8. Prepare Browser Image Scraping

Chrome is installed in step 1. The Python package `webdriver-manager` downloads the matching ChromeDriver automatically.

Quick check:

```powershell
python -c "from selenium import webdriver; from selenium.webdriver.chrome.options import Options; o=Options(); o.add_argument('--headless=new'); d=webdriver.Chrome(options=o); print(d.title); d.quit(); print('Chrome/Selenium ready')"
```

## 9. Verify Setup

Run these from the repository root with the venv active:

```powershell
python --version
python -c "import torch, transformers, sherpa_onnx, moviepy, selenium, yaml; print('Python packages ready')"
Test-Path .\script\model.gguf
Test-Path .\script\llama.cpp\build\bin\Release\llama-cli.exe
Test-Path .\voice\models\en\vits-vctk.onnx
```

Expected:

- Python should be `3.11.x`.
- Package check should print `Python packages ready`.
- All `Test-Path` commands should print `True`.

## 10. Run Reel Generator

```powershell
.\venv\Scripts\Activate.ps1
python main.py
```

Generated videos and temporary files are written under:

```text
output/
```

## One Big Copy-Paste Setup

Use this after step 1 Windows requirements are installed:

```powershell
cd $env:USERPROFILE\Downloads
git clone --recurse-submodules https://github.com/Bitradevendra/reel-generater.git
cd reel-generater
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
pip install --prefer-binary -r requirements.txt
cd script\llama.cpp
cmake -S . -B build -G "Visual Studio 17 2022" -A x64
cmake --build build --config Release
cd ..\..
cd script
python get_deepseek.py
cd ..
python -c "from core.voice_engine import synthesize_speech; synthesize_speech('Voice setup test.', 'output/setup/english_test.wav', language='en')"
python -c "from transformers import VitsModel, AutoTokenizer; AutoTokenizer.from_pretrained('facebook/mms-tts-tel'); VitsModel.from_pretrained('facebook/mms-tts-tel'); print('Telugu MMS model ready')"
python -c "from transformers import AutoModelForSeq2SeqLM, AutoTokenizer; AutoTokenizer.from_pretrained('facebook/nllb-200-distilled-600M', src_lang='eng_Latn'); AutoModelForSeq2SeqLM.from_pretrained('facebook/nllb-200-distilled-600M', use_safetensors=True); print('NLLB translation model ready')"
python -c "import torch, transformers, sherpa_onnx, moviepy, selenium, yaml; print('Python packages ready')"
python main.py
```

## Important Config Paths

The default config uses:

```yaml
script:
  model_path: "script/model.gguf"

voice:
  english:
    model_dir: "voice/models/en"
  telugu:
    model_name: "facebook/mms-tts-tel"

translation:
  model_name: "facebook/nllb-200-distilled-600M"
```

## What Is Not Pushed To GitHub

These are intentionally local:

- `venv/`
- `output/` and `outputs/`
- `*.gguf`
- Hugging Face caches
- `voice/models/`
- built `llama.cpp` binaries
- logs and temp files

## Troubleshooting

### `model.gguf not found`

Run:

```powershell
cd script
python get_deepseek.py
cd ..
```

### `llama-cli.exe` not found

Run:

```powershell
cd script\llama.cpp
cmake -S . -B build -G "Visual Studio 17 2022" -A x64
cmake --build build --config Release
cd ..\..
```

### Translation model fails to download

Check internet access and retry:

```powershell
python -c "from transformers import AutoModelForSeq2SeqLM, AutoTokenizer; AutoTokenizer.from_pretrained('facebook/nllb-200-distilled-600M', src_lang='eng_Latn'); AutoModelForSeq2SeqLM.from_pretrained('facebook/nllb-200-distilled-600M', use_safetensors=True)"
```

### Telugu TTS fails to download

Retry:

```powershell
python -c "from transformers import VitsModel, AutoTokenizer; AutoTokenizer.from_pretrained('facebook/mms-tts-tel'); VitsModel.from_pretrained('facebook/mms-tts-tel')"
```

### English TTS model fails

Retry:

```powershell
python -c "from core.voice_engine import synthesize_speech; synthesize_speech('Voice setup test.', 'output/setup/english_test.wav', language='en')"
```

### `cmake` is not recognized

Close PowerShell and open a new one. If still missing:

```powershell
winget install --id Kitware.CMake -e
```

### Visual C++ build tools missing

```powershell
winget install --id Microsoft.VisualStudio.2022.BuildTools -e --override "--quiet --wait --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
```

### Selenium or ChromeDriver fails

Update Chrome:

```powershell
winget upgrade --id Google.Chrome -e
```

Then retry the Selenium check.
