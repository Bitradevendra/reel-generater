# Offline Text-to-Speech CLI Application

A complete **100% local, offline** Text-to-Speech application built with Python using sherpa-onnx and VITS models.

## Features

✓ **Completely Offline** - No internet required after initial model download  
✓ **CPU-Only Inference** - Works on any machine without GPU  
✓ **Multi-language Support** - English and Telugu  
✓ **VITS Models** - High-quality neural speech synthesis  
✓ **Interactive CLI** - Easy-to-use menu interface  
✓ **Audio Playback** - Play generated audio directly  
✓ **Auto Model Download** - Automatically downloads models on first run  
✓ **File Input Support** - Read text from .txt files  
✓ **Timestamped Outputs** - Organized audio file naming  

## Project Structure

```
voice/
├── main.py                  # Main application
├── requirements.txt         # Python dependencies
│
├── models/                  # Model storage
│   ├── en/                  # English VITS VCTK model
│   │   ├── vits-vctk.onnx
│   │   └── tokens.txt
│   └── te/                  # Telugu VITS model
│       ├── model.onnx
│       └── tokens.txt
│
└── outputs/                 # Generated audio files
    ├── output_20260321_170000.wav
    └── output_20260321_170015.wav
```

## Installation

### 1. Install Python Dependencies

```bash
cd voice
pip install -r requirements.txt
```

**Required packages:**
- `sherpa-onnx` - Offline TTS and ASR framework
- `numpy` - Numerical computing
- `sounddevice` - Audio playback
- `scipy` - Scientific computing (WAV file writing)
- `requests` - Model downloading
- `tqdm` - Progress bars

### 2. Run the Application

```bash
python main.py
```

**On first run:**
- Application automatically detects missing models
- Downloads ~200MB of VITS models (English + Telugu)
- Models are cached in `voice/models/`
- Subsequent runs use cached models (instant startup)

## Usage Guide

### Interactive Menu

```
==================================================
  TEXT-TO-SPEECH (OFFLINE)
==================================================

[SELECT LANGUAGE]
  [1] English (VITS VCTK)
  [2] Telugu (VITS)
  [0] Exit

Enter choice [0-2]: 1
```

### Input Methods

**Option 1: Type Text**
```
[INPUT METHOD]
  [1] Type text
  [2] Load from file
  [0] Back to language selection

Enter choice [0-2]: 1

[TYPE TEXT]
Enter text to synthesize: Hello, this is offline text to speech
```

**Option 2: Load from File**
```
Enter choice [0-2]: 2
Enter file path (.txt): path/to/your/file.txt
```

### Output

- Audio files saved to `voice/outputs/`
- Filename format: `output_YYYYMMDD_HHMMSS.wav`
- Example: `output_20260321_170000.wav`

### Playback

```
[PLAYBACK]
Play audio now? [y/n]: y

Playing audio at 22050Hz...
✓ Playback complete

Replay? [y/n]: y
```

## Technical Details

### TTS Engine Specifications

| Feature | Specification |
|---------|---|
| Engine | sherpa-onnx |
| Model Architecture | VITS (Variational Inference with adversarial learning) |
| Inference | CPU-only, ONNX Runtime |
| Sample Rate | 22,050 Hz |
| Language Support | English, Telugu |
| Model Size | ~100-150MB per language |

### English Model

- **Model**: vits-vctk
- **Dataset**: VCTK (Voice Conversion Toolkit)
- **Speakers**: Multi-speaker (24 speakers)
- **Quality**: High-quality synthesis
- **File**: `models/en/vits-vctk.onnx`

### Telugu Model

- **Model**: VITS (Indian English)
- **Offline Processing**: Complete TTS chain runs locally
- **Quality**: Natural speech synthesis
- **File**: `models/te/model.onnx`

## Performance Characteristics

### System Requirements

**Minimum:**
- CPU: Dual-core processor
- RAM: 2GB
- Storage: 500MB (models + app)
- OS: Windows, macOS, Linux

**Recommended:**
- CPU: Quad-core or better
- RAM: 4GB+
- Storage: 1GB SSD
- Modern OS version

### Speed

- **Startup**: <1 second (models cached)
- **Synthesis**: 5-30 seconds per 100 words (CPU dependent)
- **Playback**: Real-time streaming

### Memory Usage

- **Idle**: ~50MB
- **During Synthesis**: ~300-500MB
- **Peak**: Model + audio buffers

## Troubleshooting

### Issue: "sherpa_onnx not installed"

**Solution:**
```bash
pip install -r requirements.txt
```

### Issue: "Model file not found"

**Solution:**
- Delete `models/` directory
- Run `python main.py` to re-download models
- Check internet connection during download

### Issue: "No audio output / Device not found"

**Solution:**
```bash
# Check available audio devices
python -c "import sounddevice as sd; print(sd.query_devices())"

# Or use system audio settings to ensure speakers are enabled
```

### Issue: Slow synthesis

**Cause:** CPU-based inference takes time  
**Solution:**
- Synthesis speed depends on CPU performance
- 5-30 seconds per 100 words is normal
- Longer texts take longer to process

### Issue: "Connection timeout" during model download

**Solution:**
- Check internet connection
- Try again - downloads are resumable
- Manually download models if needed

## Advanced Usage

### Batch Processing

Create a text file with lines of text:

```
hello world
how are you
offline synthesis
```

**Run in application:**
1. Select Input Method → Load from file
2. Enter file path
3. Process and save output

### Multiple Languages

Process both English and Telugu in one session:
1. Select English → Synthesize → Save
2. Continue → Select Telugu → Synthesize → Save

### Custom Audio Processing

Modify `save_audio()` in `main.py`:

```python
# Change audio format
wavfile.write(str(filepath), sample_rate, audio_int16)

# Add audio effects if needed
from scipy.signal import butter, sosfilt
```

## Model Management

### Check Downloaded Models

```bash
# List English models
ls voice/models/en/

# List Telugu models
ls voice/models/te/

# Check file sizes
du -h voice/models/
```

### Clear Models and Re-download

```bash
# Remove cached models
rm -rf voice/models/en
rm -rf voice/models/te

# Re-run application to download fresh models
python main.py
```

### Offline Model Setup

If you have models offline:

1. Place ONNX model file as `model.onnx`
2. Place tokens file as `tokens.txt`
3. Copy to respective language directory:
   - English: `voice/models/en/`
   - Telugu: `voice/models/te/`

## API-Free Architecture

This application is **completely API-free and offline**:

- ✗ No cloud TTS APIs
- ✗ No internet-dependent services
- ✗ No external API rate limits
- ✓ All processing on local machine
- ✓ Models run with ONNX Runtime
- ✓ CPU-only inference

## Output Audio Specifications

All generated audio files (`output_*.wav`):

- **Format**: WAV (Waveform Audio File)
- **Sample Rate**: 22,050 Hz
- **Bit Depth**: 16-bit PCM
- **Channels**: Mono
- **Encoding**: Uncompressed
- **Quality**: CD-quality audio

## File Naming Convention

```
output_YYYYMMDD_HHMMSS.wav

Where:
  YYYY = Year (e.g., 2026)
  MM = Month (01-12)
  DD = Day (01-31)
  HH = Hour (00-23)
  MM = Minute (00-59)
  SS = Second (00-59)

Example: output_20260321_170000.wav
         (March 21, 2026 at 17:00:00)
```

## Dependencies Explained

| Package | Purpose | Version |
|---------|---------|---------|
| sherpa-onnx | TTS + ASR inference | ≥1.10.0 |
| numpy | Array operations | ≥1.21.0 |
| sounddevice | Audio playback | ≥0.4.5 |
| scipy | WAV file I/O | ≥1.7.0 |
| requests | Model downloading | ≥2.26.0 |
| tqdm | Progress bars | ≥4.62.0 |

## License

This application uses:
- sherpa-onnx: Apache 2.0
- VITS models: CC0 / Open source
- VCTK dataset: Creative Commons

## Support & Issues

### Logs

Check application output for detailed logs:
```
2026-03-21 12:34:56,789 - INFO - ✓ Directories ready
2026-03-21 12:34:57,123 - INFO - ✓ Model loaded: EN TTS ready
```

### Performance Tips

1. **First Run**: Model download takes 5-10 minutes
2. **Synthesis**: Longer texts take proportionally longer
3. **Memory**: Close other applications for faster processing
4. **CPU**: Multi-core CPUs process faster

## Future Enhancements

Potential improvements:
- [ ] Batch text processing from multiple files
- [ ] Audio effects (speed, pitch, volume adjustment)
- [ ] Additional languages (Hindi, Spanish, French)
- [ ] Real-time streaming TTS
- [ ] Text preprocessing (number/emotion handling)
- [ ] Audio format conversion
- [ ] Voice cloning capabilities

## Technical Stack

```
Application Layer
    ↓
CLI Interface (Python)
    ↓
VITS TTS Engine
    ↓
sherpa-onnx Framework
    ↓
ONNX Runtime (CPU)
    ↓
Local ONNX Models
    ↓
Audio Output (sounddevice)
```

## Getting Started Quickly

```bash
# 1. Enter voice directory
cd voice

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run application (models auto-download on first run)
python main.py

# 4. Select language [1] English or [2] Telugu

# 5. Choose input method and enter text

# 6. Generated audio saved to voice/outputs/
```

---

**Offline TTS Application** - Built with sherpa-onnx and VITS  
Completely local, CPU-based, no APIs required
