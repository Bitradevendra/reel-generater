# Reel Generator

Windows-first local reel generator for script generation, voice, image scraping, subtitles, and video composition.

This repository includes `llama.cpp` as a Git submodule pinned to the same source commit used in the local project. Large generated files, model files, virtual environments, caches, and build outputs are not committed; the commands below recreate them.

## One-Time Windows Setup

Open PowerShell as Administrator and paste this:

```powershell
winget install --id Git.Git -e
winget install --id Python.Python.3.11 -e
winget install --id Kitware.CMake -e
winget install --id Microsoft.VisualStudio.2022.BuildTools -e --override "--quiet --wait --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
```

Close PowerShell, open a new PowerShell window, then continue.

If script activation is blocked, run this once:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## Clone The Project

```powershell
cd $env:USERPROFILE\Downloads
git clone --recurse-submodules https://github.com/Bitradevendra/reel-generater.git
cd reel-generater
```

If you already cloned without `--recurse-submodules`, run:

```powershell
git submodule update --init --recursive
```

## Create Python Environment

```powershell
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
pip install --prefer-binary -r requirements.txt
```

## Build llama.cpp

```powershell
cd script\llama.cpp
cmake -S . -B build -G "Visual Studio 17 2022" -A x64
cmake --build build --config Release
cd ..\..
```

Confirm the executable exists:

```powershell
Test-Path .\script\llama.cpp\build\bin\Release\llama-cli.exe
```

It should print:

```text
True
```

## Download The LLM Model

Recommended automatic download:

```powershell
cd script
python get_deepseek.py
cd ..
```

The model file must end up here:

```text
script\model.gguf
```

Manual download option:

1. Open `https://huggingface.co/QuantFactory/Phi-3-5-mini-instruct-GGUF`
2. Download one `.gguf` file.
3. Rename it to `model.gguf`.
4. Move it into the `script` folder.

## Run The App

From the repository root:

```powershell
.\venv\Scripts\Activate.ps1
python main.py
```

Generated videos and temporary files are written under `output/`.

## Quick Full Paste

Use this after the one-time Windows setup is already installed:

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
python main.py
```

## What Is Not Stored In GitHub

These are intentionally recreated locally:

- `venv/`
- `output/` and `outputs/`
- `*.gguf` model files
- HuggingFace caches
- built `llama.cpp` binaries
- local voice model folders
- logs and temporary files

## Troubleshooting

### `git submodule` folder is empty

```powershell
git submodule update --init --recursive
```

### `cmake` is not recognized

Close PowerShell and open a new one after installing CMake. If it still fails, reinstall:

```powershell
winget install --id Kitware.CMake -e
```

### Build tools are missing

Install Visual Studio Build Tools with C++ tools:

```powershell
winget install --id Microsoft.VisualStudio.2022.BuildTools -e --override "--quiet --wait --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
```

### `model.gguf not found`

Run:

```powershell
cd script
python get_deepseek.py
cd ..
```

Or manually place a GGUF model at:

```text
script\model.gguf
```

### Python package install fails

Make sure Python 3.11 is active:

```powershell
python --version
```

Then retry:

```powershell
python -m pip install --upgrade pip setuptools wheel
pip install --prefer-binary -r requirements.txt
```
