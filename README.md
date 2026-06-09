# Reel Generator

Local reel generation project with script generation, translation, voice, image scraping, subtitles, and video composition.

## Clone And Setup

Run these commands in PowerShell:

```powershell
git clone --recurse-submodules https://github.com/Bitradevendra/reel-generater.git
cd reel-generater

python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

If you already cloned without submodules, run:

```powershell
git submodule update --init --recursive
```

## Build llama.cpp

The project uses `script/llama.cpp` as a pinned Git submodule. Build `llama-cli` like this:

```powershell
cd script\llama.cpp
cmake -B build
cmake --build build --config Release
cd ..\..
```

After the build, the executable should exist here:

```text
script\llama.cpp\build\bin\Release\llama-cli.exe
```

## Download The Script Model

Download one GGUF model and save it as `script\model.gguf`.

Recommended:

```powershell
cd script
python get_deepseek.py
cd ..
```

Manual option:

- Download a GGUF model from `https://huggingface.co/QuantFactory/Phi-3-5-mini-instruct-GGUF`
- Rename it to `model.gguf`
- Put it at `script\model.gguf`

## Run

```powershell
python main.py
```

Generated files are written to local output folders, which are ignored by Git.

## Notes

Large local-only files are not committed:

- `venv/`
- generated `output/` and `outputs/`
- HuggingFace caches
- downloaded GGUF model files
- built binaries and local model folders

They are recreated by the setup commands above.
