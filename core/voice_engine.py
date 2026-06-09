"""
Voice Engine - Wraps the voice/ module for importable use.
Generates WAV audio from text using sherpa-onnx (English) with retry logic.
"""

import os
import sys
import logging
import time
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

_mms_pipeline_te = None

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
VOICE_DIR = PROJECT_ROOT / "voice"
MODELS_DIR = VOICE_DIR / "models"
EN_MODEL_DIR = MODELS_DIR / "en"

# Speaker profiles from voice/main.py
SPEAKER_PROFILES = {
    "professor": {"id": 3, "desc": "Deep, mature, authoritative - technical deep-dives"},
    "narrator": {"id": 46, "desc": "Clear, resonant, engaging - storytelling/intros"},
    "tech_lead": {"id": 8, "desc": "Bassy, bold, energetic - fast tutorials"},
}


def _ensure_model_dirs():
    """Ensure model directories exist."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    EN_MODEL_DIR.mkdir(parents=True, exist_ok=True)


def _download_english_model() -> bool:
    """Download English VITS model if not present."""
    import shutil
    import requests
    from tqdm import tqdm

    model_path = EN_MODEL_DIR / "vits-vctk.onnx"
    tokens_path = EN_MODEL_DIR / "tokens.txt"

    if model_path.exists() and tokens_path.exists():
        return True

    logger.info("[Voice] Downloading English VITS model...")
    url = "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-vctk.tar.bz2"

    temp_dir = EN_MODEL_DIR / "temp_extract"
    temp_dir.mkdir(exist_ok=True)

    try:
        tar_path = temp_dir / "vits-vctk.tar.bz2"
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()

        total = int(response.headers.get('content-length', 0))
        with open(tar_path, 'wb') as f:
            with tqdm(total=total, unit='B', unit_scale=True, desc="vits-vctk.tar.bz2") as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))

        import tarfile
        with tarfile.open(tar_path, 'r:bz2') as tar:
            tar.extractall(path=temp_dir)

        tar_path.unlink()

        extract_src = temp_dir / "vits-vctk"
        if extract_src.exists():
            for filename in ["vits-vctk.onnx", "tokens.txt", "lexicon.txt"]:
                src = extract_src / filename
                if src.exists():
                    shutil.copy2(src, EN_MODEL_DIR / filename)

        shutil.rmtree(temp_dir, ignore_errors=True)
        logger.info("[Voice] English model downloaded successfully")
        return True

    except Exception as e:
        logger.error(f"[Voice] Download failed: {e}")
        shutil.rmtree(temp_dir, ignore_errors=True)
        return False


def synthesize_speech(
    text: str,
    output_path: str,
    speaker_id: int = 46,
    speed: float = 1.0,
    language: str = "en",
    config: Optional[Dict[str, Any]] = None,
    max_retries: int = 3,
) -> Optional[str]:
    """
    Synthesize text to speech and save as WAV file.
    
    Args:
        text: Text to synthesize
        output_path: Path to save WAV file
        speaker_id: VITS speaker ID (0-108 for English)
        speed: Speech speed multiplier
        language: "en" for English
        config: Optional config dict
        max_retries: Number of retry attempts
        
    Returns:
        Path to saved WAV file, or None on failure
    """
    if not text or not text.strip():
        logger.error("[Voice] Empty text provided")
        return None

    if config is None:
        config = {}
    
    voice_cfg = config.get("voice", {})
    # Override language if present in config
    language = voice_cfg.get("language", language)
    
    if language == "te":
        lang_cfg = voice_cfg.get("telugu", {})
        speaker_id = lang_cfg.get("speaker_id", 0)
        sample_rate = lang_cfg.get("sample_rate", 16000)
    else:
        lang_cfg = voice_cfg.get("english", {})
        speaker_id = lang_cfg.get("speaker_id", speaker_id)
        sample_rate = lang_cfg.get("sample_rate", 22050)
        
    speed = lang_cfg.get("speed", speed)

    _ensure_model_dirs()

    for attempt in range(1, max_retries + 1):
        logger.info(f"[Voice] Attempt {attempt}/{max_retries} - Synthesizing {len(text)} chars")

        try:
            if language == "en":
                import sherpa_onnx
                
                if not (EN_MODEL_DIR / "vits-vctk.onnx").exists():
                    if not _download_english_model():
                        logger.error("[Voice] Cannot download English model")
                        return None
                model_file = str(EN_MODEL_DIR / "vits-vctk.onnx")
                tokens_file = str(EN_MODEL_DIR / "tokens.txt")
                lexicon_file = EN_MODEL_DIR / "lexicon.txt"
                
                # Force CPU
                os.environ['CUDA_VISIBLE_DEVICES'] = ''
                
                vits_config = sherpa_onnx.OfflineTtsVitsModelConfig(
                    model=model_file,
                    tokens=tokens_file,
                )
            elif language == "te":
                from transformers import VitsModel, AutoTokenizer
                import torch
                from scipy.io import wavfile
                
                global _mms_pipeline_te
                if '_mms_pipeline_te' not in globals() or _mms_pipeline_te is None:
                    logger.info("[Voice] Loading MMS Telugu TTS model...")
                    tokenizer = AutoTokenizer.from_pretrained("facebook/mms-tts-tel")
                    model = VitsModel.from_pretrained("facebook/mms-tts-tel")
                    model.eval()
                    _mms_pipeline_te = (tokenizer, model)
                else:
                    tokenizer, model = _mms_pipeline_te
                    
                import re
                sentences = split_text_to_sentences(text)
                all_waveforms = []
                
                # 0.5s silence for full stops (end of sentences)
                silence_len = int(model.config.sampling_rate * 0.5)
                silence = np.zeros(silence_len, dtype=np.float32)
                
                # 0.25s silence for commas and internal pauses
                short_silence_len = int(model.config.sampling_rate * 0.25)
                short_silence = np.zeros(short_silence_len, dtype=np.float32)
                
                with torch.no_grad():
                    for sent in sentences:
                        if not sent.strip():
                            continue
                            
                        # Split by comma or semicolon, capturing the punctuation
                        phrases = re.split(r'([,;:|-])', sent)
                        
                        for phrase in phrases:
                            if not phrase.strip():
                                continue
                                
                            # If it's punctuation, add a short pause
                            if re.match(r'^[,;:|-]+$', phrase.strip()):
                                all_waveforms.append(short_silence)
                                continue
                                
                            inputs = tokenizer(phrase, return_tensors="pt")
                            # 0.72 is a very human, conversational speed for Telugu MMS
                            output_waveform = model(
                                **inputs,
                                speaking_rate=0.72, 
                                noise_scale=0.8
                            ).waveform
                            all_waveforms.append(output_waveform.cpu().numpy().squeeze())
                            
                        # End of sentence silence
                        all_waveforms.append(silence)
                        
                if all_waveforms:
                    waveform = np.concatenate(all_waveforms)
                else:
                    waveform = np.zeros(100, dtype=np.float32)
                
                output_dir = Path(output_path).parent
                output_dir.mkdir(parents=True, exist_ok=True)
                wavfile.write(output_path, rate=model.config.sampling_rate, data=waveform)
                return output_path
            else:
                logger.error(f"[Voice] Unsupported language: {language}")
                return None

            if lexicon_file.exists():
                vits_config.lexicon = str(lexicon_file)

            tts_config = sherpa_onnx.OfflineTtsConfig(
                model=sherpa_onnx.OfflineTtsModelConfig(
                    vits=vits_config,
                    num_threads=4,
                ),
            )

            tts = sherpa_onnx.OfflineTts(tts_config)

            # Generate audio
            audio_obj = tts.generate(text=text.strip(), sid=speaker_id, speed=speed)

            if audio_obj is None:
                logger.warning("[Voice] Synthesis returned None")
                continue

            # Extract samples
            if hasattr(audio_obj, 'samples'):
                audio_array = np.array(audio_obj.samples, dtype=np.float32)
            else:
                audio_array = np.array(audio_obj, dtype=np.float32)

            if audio_array.ndim > 1:
                audio_array = audio_array.flatten()

            if len(audio_array) == 0:
                logger.warning("[Voice] Empty audio generated")
                continue

            # Normalize
            max_val = np.max(np.abs(audio_array))
            if max_val > 0:
                audio_array = audio_array / max_val

            # Save as WAV
            from scipy.io import wavfile
            
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)

            audio_int16 = np.int16(audio_array * 32767)
            wavfile.write(output_path, sample_rate, audio_int16)

            duration = len(audio_array) / sample_rate
            logger.info(f"[Voice] Saved {duration:.1f}s audio to: {output_path}")
            return output_path

        except ImportError:
            logger.error("[Voice] sherpa-onnx not installed. Run: pip install sherpa-onnx")
            return None
        except Exception as e:
            logger.warning(f"[Voice] Attempt {attempt} failed: {e}")
            if attempt < max_retries:
                delay = 2 ** attempt
                logger.info(f"[Voice] Retrying in {delay}s...")
                time.sleep(delay)

    logger.error(f"[Voice] Failed after {max_retries} attempts")
    return None


def get_audio_duration(wav_path: str) -> float:
    """Get duration of a WAV file in seconds."""
    try:
        from scipy.io import wavfile
        sample_rate, data = wavfile.read(wav_path)
        return len(data) / sample_rate
    except Exception as e:
        logger.error(f"[Voice] Error reading WAV: {e}")
        return 0.0


def split_text_to_sentences(text: str) -> list:
    """
    Split text into sentences for subtitle timing.
    Uses period, exclamation, question mark as delimiters.
    """
    import re
    
    # Split on sentence-ending punctuation
    raw_sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    
    sentences = []
    for s in raw_sentences:
        s = s.strip()
        if s:
            sentences.append(s)
    
    # If text has no punctuation, split on commas or every N words
    if len(sentences) <= 1 and len(text.split()) > 10:
        words = text.split()
        chunk_size = 8
        sentences = []
        for i in range(0, len(words), chunk_size):
            chunk = ' '.join(words[i:i + chunk_size])
            sentences.append(chunk)
    
    return sentences


def estimate_sentence_timings(sentences: list, total_duration: float) -> list:
    """
    Estimate start/end times for each sentence based on word count.
    
    Returns:
        List of (sentence, start_time, end_time) tuples
    """
    total_words = sum(len(s.split()) for s in sentences)
    if total_words == 0:
        return []
    
    timings = []
    current_time = 0.0
    
    for sentence in sentences:
        word_count = len(sentence.split())
        # Duration proportional to word count
        sentence_duration = (word_count / total_words) * total_duration
        
        timings.append({
            "text": sentence,
            "start": round(current_time, 3),
            "end": round(current_time + sentence_duration, 3),
            "words": sentence.split(),
        })
        current_time += sentence_duration
    
    return timings
