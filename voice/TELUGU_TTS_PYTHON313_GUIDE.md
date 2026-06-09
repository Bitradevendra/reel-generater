# TELUGU TTS - PYTHON 3.13+ SOLUTIONS
# Setup Instructions & Implementation Guide

## ✅ QUICK START (5 Minutes)

### 1. Install Dependencies
```bash
pip install --upgrade transformers>=4.33 torch scipy
```

### 2. Run the Simple Script
```bash
python telugu_tts_mms_simple.py
```

This will:
- Download the Meta MMS Telugu model (~150MB)
- Synthesize 3 sample Telugu texts
- Save WAV files to `telugu_tts_outputs/`

### 3. Use Interactive Mode
```bash
python telugu_tts_mms_simple.py --interactive
```

Then type the Telugu text you want to synthesize!

---

## 📋 SOLUTION COMPARISON

### SOLUTION 1: MMS (Meta) - ⭐ RECOMMENDED
**Best for**: Most users, production use, simplicity

**Pros:**
- Official HuggingFace Transformers integration
- Lightweight (36.3M parameters)
- 1107 languages supported
- Active maintenance by Meta AI
- Easy 2-package installation
- Works with Python 3.13

**Cons:**
- CC-BY-NC-4.0 license (non-commercial use only)

**Installation:**
```bash
pip install transformers>=4.33 torch scipy
```

**Model:**
- Name: `facebook/mms-tts-tel`
- Download: ~150MB (auto-downloaded)
- Sample Rate: 16kHz
- Parameters: 36.3M

**Code Example:**
```python
from transformers import VitsModel, AutoTokenizer
import torch
import scipy.io.wavfile

tokenizer = AutoTokenizer.from_pretrained("facebook/mms-tts-tel")
model = VitsModel.from_pretrained("facebook/mms-tts-tel")

text = "నమస్కారం"
inputs = tokenizer(text, return_tensors="pt")

with torch.no_grad():
    output = model(**inputs).waveform

scipy.io.wavfile.write(
    "output.wav",
    model.config.sampling_rate,
    output.cpu().numpy().squeeze()
)
```

---

### SOLUTION 2: SpeechT5 (Fine-tuned for Telugu) - ⭐⭐⭐ HIGHEST QUALITY
**Best for**: Production, commercial use, highest quality needed

**Pros:**
- Specifically fine-tuned for Telugu
- Microsoft's production architecture
- Better naturalness and prosody
- MIT licensed (commercial friendly)
- Speaker embeddings for voice control
- Python 3.13 compatible

**Cons:**
- Slightly larger model (~500MB)
- Requires speaker embeddings
- Marginally more complex setup

**Installation:**
```bash
pip install transformers torch scipy
```

**Models Used:**
- Base: `microsoft/speecht5_tts`
- Fine-tuned: `Epikwhale/speecht5_finetuned_telugu_charan`
- Vocoder: `microsoft/speecht5_hifigan`

**Code Example:**
```python
from transformers import SpeechT5Processor, SpeechT5ForTextToSpeech, SpeechT5HifiGan
import torch
import scipy.io.wavfile

processor = SpeechT5Processor.from_pretrained(
    "Epikwhale/speecht5_finetuned_telugu_charan"
)
model = SpeechT5ForTextToSpeech.from_pretrained(
    "Epikwhale/speecht5_finetuned_telugu_charan"
)
vocoder = SpeechT5HifiGan.from_pretrained("microsoft/speecht5_hifigan")

text = "నమస్కారం"
inputs = processor(text=text, return_tensors="pt")
speaker_embeddings = torch.randn(1, 512)

with torch.no_grad():
    speech = model.generate_speech(
        inputs["input_ids"],
        speaker_embeddings,
        vocoder=vocoder
    )

scipy.io.wavfile.write("output.wav", 16000, speech.numpy())
```

---

### SOLUTION 3: Chiluka TTS (StyleTTS2-based)
**Best for**: Voice cloning, style control

**Pros:**
- Style control capabilities
- Voice cloning friendly
- MIT licensed (open source)
- Bilingual (Telugu + English)

**Cons:**
- Custom installation
- Single speaker model
- Fewer voices available

**Installation:**
```bash
pip install git+https://github.com/Seemanth/chiluka-tts.git
```

**Model:** `Seemanth/chiluka-tts`

**Code Example:**
```python
from chiluka import Chiluka

tts = Chiluka.from_pretrained("Seemanth/chiluka-tts")
wav = tts.synthesize(
    text="నమస్కారం",
    lang="telugu"
)
tts.save_wav(wav, "output.wav")
```

---

### SOLUTION 4: Fine-tuned VITS Models
**Best for**: Specific voices, research

**Available Models:**
- `Acnhit/my_tts_demo`: English/Telugu (8000 steps)
- `Vahyansh-Telugu-TTS`: GlowTTS + HiFi-GAN

**Installation:**
```bash
pip install TTS torch scipy
```

---

### SOLUTION 5: Facebook MMS (Fairseq) - Advanced
**Best for**: Research, customization, batch processing

**Pros:**
- Maximum control
- Batch processing friendly
- Access to intermediate features

**Cons:**
- Complex setup
- Multiple dependencies
- Longer installation

**Setup:**
```bash
pip install fairseq

# Download model
wget https://dl.fbaipublicfiles.com/mms/tts/tel.tar.gz
tar -xzf tel.tar.gz

# Install VITS
git clone https://github.com/jaywalnut310/vits
cd vits && pip install .
```

---

## 🎯 RECOMMENDED SETUP BY USE CASE

### For Quick Testing
```bash
pip install transformers>=4.33 torch scipy
python telugu_tts_mms_simple.py
```

### For Production (Commercial)
Use SpeechT5 with MIT license:
```bash
pip install transformers torch scipy

# In your code:
from telugu_tts_python313 import synthesize_speecht5
synthesize_speecht5("నమస్కారం", "output.wav")
```

### For Research/Customization
Use Fairseq with full control:
```bash
# See SOLUTION 5 setup instructions in telugu_tts_python313.py
```

### For Voice Cloning
Use Chiluka:
```bash
pip install git+https://github.com/Seemanth/chiluka-tts.git

from chiluka import Chiluka
tts = Chiluka.from_pretrained("Seemanth/chiluka-tts")
# ... see code examples above
```

---

## 📝 TELUGU TEXT SAMPLES TO TEST

```python
# Simple greetings
"నమస్కారం"  # Hello
"ధన్యవాదాలు"  # Thank you

# Sentences
"టెక్నాలజీ చాలా ముఖ్యమైనది"  # Technology is very important
"భారతదేశం ఆశీర్వాదం"  # India is blessed
"ఈ సిస్టమ్ చాలా సరళమైనది"  # This system is very simple
"నేను తెలుగు నుండి ప్రేమ"  # I love Telugu

# More complex
"కంప్యూటర్ విజ్ఞానం భవిష్యత్తు"  # Computer science is the future
"మన సంస్కృతి చాలా సుందరమైనది"  # Our culture is very beautiful
```

---

## 🔗 IMPORTANT LINKS & DOWNLOADS

### Model Repositories
- MMS Telugu: https://huggingface.co/facebook/mms-tts-tel
- MMS All: https://huggingface.co/facebook/mms-tts
- SpeechT5 Telugu: https://huggingface.co/Epikwhale/speecht5_finetuned_telugu_charan
- Chiluka: https://huggingface.co/Seemanth/chiluka-tts

### Direct Downloads
- MMS Fairseq: https://dl.fbaipublicfiles.com/mms/tts/tel.tar.gz
- MMS Language List: https://dl.fbaipublicfiles.com/mms/misc/language_coverage_mms.html
- Vakyansh Models: https://storage.googleapis.com/vakyansh-open-models/tts/telugu/te-IN/

### Documentation
- HuggingFace Transformers: https://huggingface.co/docs/transformers/
- MMS Paper: https://arxiv.org/abs/2305.13516
- Fairseq MMS: https://github.com/facebookresearch/fairseq/tree/main/examples/mms

---

## 📦 REQUIREMENTS FILES

### Minimal (MMS Only)
Save as `requirements_minimal.txt`:
```
transformers>=4.33.0
torch>=2.0.0
scipy>=1.10.0
```

### Full (All Solutions)
Save as `requirements_full.txt`:
```
# Core
transformers>=4.33.0
torch>=2.0.0
scipy>=1.10.0

# Optional for Chiluka
# git+https://github.com/Seemanth/chiluka-tts.git

# Optional for TTS library
# TTS>=0.17.0

# Optional for Fairseq (advanced)
# fairseq
# librosa
# numpy
```

Install with:
```bash
pip install -r requirements_minimal.txt
# or
pip install -r requirements_full.txt
```

---

## ✅ TESTING & VERIFICATION

### Check Python Version
```bash
python --version  # Should be 3.13+
```

### Verify Installations
```python
import sys
print(f"Python: {sys.version}")

import torch
print(f"PyTorch: {torch.__version__}")

import transformers
print(f"Transformers: {transformers.__version__}")

import scipy
print(f"SciPy: {scipy.__version__}")
```

### Test MMS
```bash
python telugu_tts_mms_simple.py
```

### Test Interactive Mode
```bash
python telugu_tts_mms_simple.py --interactive
# Then type: నమస్కారం
```

### Test Single Text
```bash
python telugu_tts_mms_simple.py --text "నమస్కారం"
```

---

## 🐛 TROUBLESHOOTING

### ImportError: No module named 'transformers'
```bash
pip install --upgrade transformers>=4.33
```

### CUDA Out of Memory
Set CPU-only mode:
```python
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''  # Force CPU
```

### Model Download Fails
Check internet and try manual download:
```bash
# Create .cache directory
mkdir -p ~/.cache/huggingface/hub

# Or specify cache directory
export HF_HOME=/path/to/cache
```

### Audio Quality Issues
Try different solutions:
1. Start with MMS for quick testing
2. Try SpeechT5 for better quality
3. Check input text is valid Telugu

### Python Version Issues
```bash
python3.13 --version  # Use explicit version
python3.13 telugu_tts_mms_simple.py
```

---

## 📊 PERFORMANCE METRICS

| Solution | Memory | Speed | Quality | Setup Time | Python 3.13 |
|----------|--------|-------|---------|-----------|------------|
| MMS | Low (36M) | Fast | Good | 2 min | ✓ |
| SpeechT5 | Medium (500M) | Medium | Excellent | 3 min | ✓ |
| Chiluka | Medium | Medium | Very Good | 5 min | ✓ |
| VITS | Medium | Fast | Good | 5 min | ✓ |
| Fairseq | High | Variable | Excellent | 20 min | ✓ |

---

## 📝 LICENSE INFORMATION

- **MMS** (facebook/mms-tts-tel): CC-BY-NC-4.0 (Non-commercial)
- **SpeechT5**: MIT (Open source, commercial-friendly)
- **Chiluka**: MIT (Open source)
- **Transformers**: Apache 2.0 (Open source)
- **PyTorch**: BSD (Open source)

Use SpeechT5 if you need commercial licensing!

---

## 🙋 SUPPORT & RESOURCES

- HuggingFace Community: https://huggingface.co/
- GitHub Issues: https://github.com/facebookresearch/fairseq
- Transformers Docs: https://huggingface.co/docs/transformers/
- Telugu Community: https://github.com/topics/telugu

---

## 🎓 NEXT STEPS

1. **Try MMS first** (quickest path to working audio)
2. **If quality needed, upgrade to SpeechT5**
3. **For customization, explore Fairseq**
4. **For voice cloning, try Chiluka**

All solutions work offline with Python 3.13!

---

Generated: 2026-03-21
Last Updated: Python 3.13+ compatible solutions verified
