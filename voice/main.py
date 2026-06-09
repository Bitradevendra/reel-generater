#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Offline Text-to-Speech CLI Application
- Complete local processing with sherpa-onnx (English) and Transformers (Telugu)
- Support for English and Telugu  
- CPU-only inference
- Python 3.13+ compatible
"""

import os
import sys
import json
import requests
import threading
import sounddevice as sd
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urljoin
import logging
from tqdm import tqdm
import io

# Force UTF-8 encoding for all I/O
if sys.stdin and hasattr(sys.stdin, 'reconfigure'):
    sys.stdin.reconfigure(encoding='utf-8', errors='replace')
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

os.environ['PYTHONIOENCODING'] = 'utf-8'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try importing sherpa_onnx for English
try:
    import sherpa_onnx
except ImportError:
    logger.warning("sherpa_onnx not installed. Run: pip install -r requirements.txt")
    sherpa_onnx = None

# Try importing Telugu TTS (Meta MMS via Transformers - Python 3.13 compatible)
try:
    from telugu_tts import TeluguTTSMMS
    HAS_TELUGU = True
except ImportError:
    logger.warning("Telugu TTS module not found. Run: pip install -r requirements.txt")
    HAS_TELUGU = False
    TeluguTTSMMS = None


# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_DIR = Path(__file__).parent.resolve()
MODELS_DIR = BASE_DIR / "models"
OUTPUTS_DIR = BASE_DIR / "outputs"
EN_MODEL_DIR = MODELS_DIR / "en"
TE_MODEL_DIR = MODELS_DIR / "te"
PROJECT_A_DIR = BASE_DIR.parent / "Project_A"

# Speaker ID mapping for English VITS (YouTube Optimization)
SPEAKER_PROFILES = {
    1: {"name": "The Professor", "id": 3, "description": "Deep, mature, and authoritative. Best for technical deep-dives."},
    2: {"name": "The Narrator", "id": 46, "description": "Clear, resonant, and engaging. Best for storytelling/intro videos."},
    3: {"name": "The Tech Lead", "id": 8, "description": "Bassy, bold, and energetic. Best for fast-paced tutorials."},
}

# Model URLs from GitHub releases and HuggingFace
MODEL_URLS = {
    "en": {
        "name": "vits-vctk",
        "url": "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-vctk.tar.bz2",
        "model_file": "vits-vctk.onnx",
        "tokens_file": "tokens.txt",
        "lexicon_file": "lexicon.txt",
        "extract_dir": "vits-vctk",
        "type": "tar.bz2"
    },
    "te": {
        "name": "facebook/mms-tts-tel",
        "model_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/te/te_IN/padmavathi/medium/te_IN-padmavathi-medium.onnx",
        "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/te/te_IN/padmavathi/medium/te_IN-padmavathi-medium.onnx.json",
        "model_file": "model.onnx",
        "type": "piper"
    }
}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def ensure_directories():
    """Create required directories if they don't exist."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    EN_MODEL_DIR.mkdir(parents=True, exist_ok=True)
    TE_MODEL_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"[OK] Directories ready: {BASE_DIR}")


def sanitize_telugu_text(text: str) -> str:
    """
    Remove English characters and metadata from Telugu text.
    
    Args:
        text: Mixed text (Telugu + potential English)
        
    Returns:
        Sanitized Telugu text
    """
    import re
    
    # Remove English letters (A-Z, a-z) and numbers
    sanitized = re.sub(r'[a-zA-Z0-9]', '', text)
    
    # Remove common metadata patterns
    sanitized = re.sub(r'\[.*?\]', '', sanitized)  # Remove [brackets]
    sanitized = re.sub(r'\(.*?\)', '', sanitized)  # Remove (parentheses)
    sanitized = re.sub(r'#.*$', '', sanitized, flags=re.MULTILINE)  # Remove #comments
    
    # Clean extra whitespace
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    
    return sanitized


def read_translated_text() -> Optional[str]:
    """
    Read translated Telugu text from Project_A/translated_text.txt.
    
    Returns:
        Text content or None if not found
    """
    file_path = PROJECT_A_DIR / "translated_text.txt"
    
    if not PROJECT_A_DIR.exists():
        logger.warning(f"[WARN] Project_A directory not found: {PROJECT_A_DIR}")
        return None
    
    if not file_path.exists():
        logger.warning(f"[WARN] File not found: {file_path}")
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read().strip()
        
        if not text:
            logger.warning("File is empty")
            return None
        
        logger.info(f"[OK] Loaded: {file_path}")
        return text
    
    except Exception as e:
        logger.error(f"Error reading translated text: {e}")
        return None


def get_telugu_input_method() -> Optional[str]:
    """
    Get Telugu text input method and text from user.
    
    Returns:
        Telugu text to synthesize or None if cancelled
    """
    while True:
        print("\n[TELUGU INPUT METHOD]")
        print("  [1] Load from Project_A/translated_text.txt")
        print("  [2] Load from custom file")
        print("  [3] Enter text manually")
        print("  [0] Back to language selection")
        
        try:
            choice = input("\nEnter choice [0-3]: ").strip()
            
            if choice == "0":
                return None
            
            elif choice == "1":
                # Try to load from Project_A
                print("\n[FILE SEARCH]")
                text = read_translated_text()
                
                if text is None:
                    print("[WARN] File not found in Project_A")
                    print("[TIP] Try option [2] to specify custom file path")
                    continue
                
                logger.info(f"[OK] Loaded from Project_A: {len(text)} characters")
                return text
            
            elif choice == "2":
                # Load from custom file path
                print("\n[LOAD FROM CUSTOM FILE]")
                while True:
                    file_path = input("Enter file path (.txt): ").strip()
                    
                    # Remove surrounding quotes if present
                    if file_path.startswith('"') and file_path.endswith('"'):
                        file_path = file_path[1:-1]
                    elif file_path.startswith("'") and file_path.endswith("'"):
                        file_path = file_path[1:-1]
                    
                    if not file_path:
                        print("[WARN] File path cannot be empty. Try again.")
                        continue
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            text = f.read().strip()
                        
                        if not text:
                            print("[WARN] File is empty. Try again.")
                            continue
                        
                        logger.info(f"[OK] Loaded: {file_path}")
                        print(f"[OK] Loaded: {len(text)} characters")
                        return text
                    
                    except FileNotFoundError:
                        print(f"[FAIL] File not found: {file_path}")
                        continue
                    except Exception as e:
                        print(f"[FAIL] Error reading file: {e}")
                        print("[TIP] Try entering path without quotes or use forward slashes")
                        continue
            
            elif choice == "3":
                # Enter text manually
                print("\n[TELUGU TEXT INPUT]")
                print("Enter Telugu text to synthesize:")
                while True:
                    text = input("> ").strip()
                    
                    # Ensure text is properly decoded as UTF-8
                    if isinstance(text, bytes):
                        text = text.decode('utf-8', errors='replace')
                    
                    if not text:
                        print("[WARN] Text cannot be empty. Try again.")
                        continue
                    
                    logger.info(f"User input: {len(text)} characters")
                    return text
            
            else:
                print("[WARN] Invalid choice. Please enter 0, 1, 2, or 3.")
                continue
        
        except EOFError:
            return None
        except Exception as e:
            print(f"[FAIL] Input error: {e}")
            return None


def save_metadata_log(language: str, voice_id: int, filename: str) -> bool:
    """
    Save metadata log of current session.
    
    Args:
        language: "en" or "te"
        voice_id: Speaker ID or model name
        filename: Output audio filename
        
    Returns:
        bool: True if successful
    """
    try:
        log_path = OUTPUTS_DIR / "last_session.txt"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        language_name = "English" if language == "en" else "Telugu"
        voice_name = SPEAKER_PROFILES.get(voice_id, {}).get("name", f"Custom ID {voice_id}") if language == "en" else "Meta MMS"
        
        log_content = f"""--- LAST SESSION LOG ---
Timestamp: {timestamp}
Language: {language_name}
Voice/Model: {voice_name}
Output File: {filename}
"""
        
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(log_content)
        
        logger.info(f"[OK] Metadata saved: {log_path}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to save metadata: {e}")
        return False


def download_file(url: str, target_path: Path, chunk_size: int = 8192) -> bool:
    """Download file with progress bar."""
    try:
        logger.info(f"Downloading: {url}")
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(target_path, 'wb') as f:
            with tqdm(total=total_size, unit='B', unit_scale=True, desc=target_path.name) as pbar:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
        
        logger.info(f"[OK] Downloaded: {target_path.name}")
        return True
    except Exception as e:
        logger.error(f"[FAIL] Download failed: {e}")
        if target_path.exists():
            target_path.unlink()
        return False


def extract_tar_bz2(tar_path: Path, extract_to: Path) -> bool:
    """Extract tar.bz2 file."""
    try:
        import tarfile
        logger.info(f"Extracting: {tar_path.name}")
        
        with tarfile.open(tar_path, 'r:bz2') as tar:
            tar.extractall(path=extract_to)
        
        tar_path.unlink()  # Remove after extraction
        logger.info(f"[OK] Extracted: {tar_path.name}")
        return True
    except Exception as e:
        logger.error(f"[FAIL] Extraction failed: {e}")
        return False


def download_from_huggingface(repo_id: str, filename: str, target_path: Path) -> bool:
    """
    Download a file from HuggingFace model hub.
    
    Args:
        repo_id: HuggingFace repo ID (e.g., "csukuangfj/vits-mimic3-te_IN-cmu-indic_low")
        filename: File to download (e.g., "model.onnx")
        target_path: Where to save the file
        
    Returns:
        bool: True if download successful
    """
    try:
        # HuggingFace CDN URL
        url = f"https://huggingface.co/{repo_id}/resolve/main/{filename}"
        logger.info(f"Downloading from HuggingFace: {filename}")
        
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(target_path, 'wb') as f:
            with tqdm(total=total_size, unit='B', unit_scale=True, desc=filename) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
        
        logger.info(f"[OK] Downloaded: {filename}")
        return True
    except Exception as e:
        logger.error(f"[FAIL] HuggingFace download failed: {e}")
        if target_path.exists():
            target_path.unlink()
        return False


def download_piper_model(model_url: str, config_url: str, target_dir: Path) -> bool:
    """
    Download Piper Telugu model from HuggingFace (direct /resolve/main/ URLs).
    
    Args:
        model_url: Direct URL to .onnx file
        config_url: Direct URL to .onnx.json config file
        target_dir: Target directory
        
    Returns:
        bool: True if successful
    """
    try:
        import json
        
        # Download ONNX model
        model_path = target_dir / "model.onnx"
        logger.info("Downloading Telugu Piper model...")
        response = requests.get(model_url, stream=True, timeout=60)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        with open(model_path, 'wb') as f:
            with tqdm(total=total_size, unit='B', unit_scale=True, desc="model.onnx") as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
        
        logger.info(f"[OK] Downloaded model: {model_path.name}")
        
        # Download config to extract tokens
        config_path = target_dir / "config.json"
        logger.info("Downloading Telugu model config...")
        response = requests.get(config_url, stream=True, timeout=30)
        response.raise_for_status()
        
        with open(config_path, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"[OK] Downloaded config")
        
        # Extract phoneme tokens from config
        tokens_path = target_dir / "tokens.txt"
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Piper config has 'phoneme_id_map' or 'phonemes'
            phonemes = []
            if 'phoneme_id_map' in config:
                # Dictionary format: {phoneme: id}
                phoneme_dict = config['phoneme_id_map']
                # Sort by ID values to maintain order
                sorted_phonemes = sorted(phoneme_dict.items(), key=lambda x: x[1])
                phonemes = [p[0] for p in sorted_phonemes]
            elif 'phonemes' in config:
                phonemes = config['phonemes']
            else:
                # Fallback: use common phoneme set
                phonemes = ['#', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
                           'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', ' ']
                logger.warning("[WARN] Using default phoneme set")
            
            # Write tokens.txt (one per line)
            with open(tokens_path, 'w', encoding='utf-8') as f:
                for phoneme in phonemes:
                    f.write(f"{phoneme}\n")
            
            logger.info(f"[OK] Created tokens.txt with {len(phonemes)} phonemes")
            return True
        
        except Exception as e:
            logger.warning(f"[WARN] Failed to extract tokens from config: {e}")
            # Create a basic tokens file anyway
            tokens_path = target_dir / "tokens.txt"
            with open(tokens_path, 'w', encoding='utf-8') as f:
                f.write("# Basic token set\n")
                for c in "అ ఆ ఇ ఈ ఉ ఊ ఋ ఌ ఎ ఏ ఐ ఒ ఓ ఔ ౄ":
                    f.write(f"{c}\n")
            logger.info("[OK] Created basic tokens.txt")
            return True
    
    except Exception as e:
        logger.error(f"[FAIL] Piper model download failed: {e}")
        return False


def download_models() -> bool:
    """
    Automatically download VITS models if not present.
    
    Returns:
        bool: True if all models are available
    """
    import shutil
    
    ensure_directories()
    
    all_ready = True
    
    for lang_code, lang_info in MODEL_URLS.items():
        target_dir = EN_MODEL_DIR if lang_code == "en" else TE_MODEL_DIR
        model_filename = lang_info["model_file"]
        model_path = target_dir / model_filename
        tokens_path = target_dir / "tokens.txt"
        
        # Check if model already exists
        if model_path.exists() and tokens_path.exists():
            logger.info(f"[OK] {lang_info['name']} model found - ready to use")
            continue
        
        logger.info(f"Downloading {lang_code.upper()} model: {lang_info['name']}")
        
        try:
            if lang_info.get("type") == "piper":
                # Download Piper model (Telugu)
                if download_piper_model(lang_info["model_url"], lang_info["config_url"], target_dir):
                    logger.info(f"[OK] {lang_info['name']} ready")
                else:
                    logger.error(f"[FAIL] Failed to download {lang_code.upper()} Piper model")
                    all_ready = False
            
            elif lang_info.get("type") == "huggingface":
                # Download from HuggingFace
                repo_id = lang_info["hf_repo"]
                
                # Download model file
                if not download_from_huggingface(repo_id, lang_info["model_file"], model_path):
                    logger.error(f"[FAIL] Failed to download {lang_code.upper()} model file")
                    all_ready = False
                    continue
                
                # Download tokens file
                if not download_from_huggingface(repo_id, lang_info["tokens_file"], tokens_path):
                    logger.error(f"[FAIL] Failed to download {lang_code.upper()} tokens file")
                    if model_path.exists():
                        model_path.unlink()
                    all_ready = False
                    continue
                
                logger.info(f"[OK] {lang_info['name']} ready")
            
            else:
                # Download from GitHub releases (tar.bz2)
                # Create temp directory
                temp_dir = target_dir / "temp_extract"
                temp_dir.mkdir(exist_ok=True)
                
                try:
                    # Download
                    tar_path = temp_dir / f"{lang_info['name']}.tar.bz2"
                    if not download_file(lang_info["url"], tar_path):
                        logger.error(f"[FAIL] Failed to download {lang_code.upper()} model")
                        all_ready = False
                        shutil.rmtree(temp_dir, ignore_errors=True)
                        continue
                    
                    # Extract
                    if not extract_tar_bz2(tar_path, temp_dir):
                        logger.error(f"[FAIL] Failed to extract {lang_code.upper()} model")
                        all_ready = False
                        shutil.rmtree(temp_dir, ignore_errors=True)
                        continue
                    
                    # Move files to target directory
                    extract_src = temp_dir / lang_info["extract_dir"]
                    
                    if not extract_src.exists():
                        logger.error(f"[FAIL] Extracted directory not found: {extract_src}")
                        all_ready = False
                        shutil.rmtree(temp_dir, ignore_errors=True)
                        continue
                    
                    # Copy model file
                    src_model = extract_src / model_filename
                    if src_model.exists():
                        shutil.copy2(src_model, model_path)
                        logger.info(f"[OK] Copied model: {model_path.name}")
                    else:
                        logger.error(f"[FAIL] Model file not found: {src_model}")
                        all_ready = False
                    
                    # Copy tokens file
                    src_tokens = extract_src / "tokens.txt"
                    if src_tokens.exists():
                        shutil.copy2(src_tokens, tokens_path)
                        logger.info(f"[OK] Copied tokens: tokens.txt")
                    else:
                        logger.warning(f"[WARN] Tokens file not found: {src_tokens}")
                    
                    # Copy lexicon file if it exists
                    if "lexicon_file" in lang_info:
                        src_lexicon = extract_src / lang_info["lexicon_file"]
                        lexicon_path = target_dir / lang_info["lexicon_file"]
                        if src_lexicon.exists():
                            shutil.copy2(src_lexicon, lexicon_path)
                            logger.info(f"[OK] Copied lexicon: {lang_info['lexicon_file']}")
                    
                    # Cleanup
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    logger.info(f"[OK] {lang_info['name']} ready")
                    
                except Exception as e:
                    logger.error(f"[FAIL] Error setting up {lang_code.upper()} model: {e}")
                    all_ready = False
                    shutil.rmtree(temp_dir, ignore_errors=True)
        
        except Exception as e:
            logger.error(f"[FAIL] Error downloading {lang_code.upper()} model: {e}")
            all_ready = False
    
    return all_ready


# ============================================================================
# TTS ENGINE
# ============================================================================

class VITSTTSEngine:
    """Text-to-Speech engine using VITS model with sherpa-onnx."""
    
    def __init__(self, language: str = "en", speaker_id: int = 0):
        """
        Initialize TTS engine.
        
        Args:
            language: "en" for English or "te" for Telugu
            speaker_id: Speaker ID for multi-speaker VITS (English only)
        """
        self.language = language
        self.speaker_id = speaker_id
        self.model_dir = EN_MODEL_DIR if language == "en" else TE_MODEL_DIR
        self.model = None
        self.is_playing = False
        self.load_model()
    
    def load_model(self):
        """Load VITS model using sherpa-onnx with CPU-only constraint."""
        try:
            if sherpa_onnx is None:
                logger.error("sherpa_onnx not available")
                return False
            
            # Force CPU device
            os.environ['CUDA_VISIBLE_DEVICES'] = ''
            
            # Get model filename based on language
            if self.language == "en":
                model_filename = "vits-vctk.onnx"
                lexicon_filename = "lexicon.txt"
            else:
                # For custom languages, look for model.onnx first, then any *.onnx
                onnx_files = list(self.model_dir.glob("model.onnx"))
                if not onnx_files:
                    onnx_files = list(self.model_dir.glob("*.onnx"))
                if not onnx_files:
                    logger.error(f"No ONNX model found in {self.model_dir}")
                    return False
                model_filename = onnx_files[0].name
                lexicon_filename = None
            
            model_file = self.model_dir / model_filename
            tokens_file = self.model_dir / "tokens.txt"
            lexicon_file = self.model_dir / lexicon_filename if lexicon_filename else None
            
            if not model_file.exists():
                logger.error(f"Model file not found: {model_file}")
                return False
            
            if not tokens_file.exists():
                logger.error(f"Tokens file not found: {tokens_file}")
                return False
            
            logger.info(f"Loading {self.language.upper()} model: {model_file.name} (CPU-only)")
            
            # Suppress stderr warnings about unknown tokens
            import sys
            import io
            old_stderr = sys.stderr
            sys.stderr = io.StringIO()
            
            try:
                # Prepare VITS config with lexicon if available
                vits_config = sherpa_onnx.OfflineTtsVitsModelConfig(
                    model=str(model_file),
                    tokens=str(tokens_file),
                )
                
                # Add lexicon if it exists (typically for English)
                if lexicon_file and lexicon_file.exists():
                    vits_config.lexicon = str(lexicon_file)
                    logger.info(f"[OK] Using lexicon: {lexicon_file.name}")
                
                # Try creating TTS model with proper config (CPU only)
                config = sherpa_onnx.OfflineTtsConfig(
                    model=sherpa_onnx.OfflineTtsModelConfig(
                        vits=vits_config,
                        num_threads=4,
                    ),
                )
                
                self.model = sherpa_onnx.OfflineTts(config)
                logger.info(f"[OK] Model loaded: {self.language.upper()} TTS ready (Speaker ID: {self.speaker_id})")
                return True
            
            except Exception as e:
                logger.warning(f"Standard config failed, trying alternative: {e}")
                try:
                    # Alternative config
                    config = sherpa_onnx.OfflineTtsConfig(
                        model=sherpa_onnx.OfflineTtsModelConfig(
                            vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                                model=str(model_file),
                                tokens=str(tokens_file),
                            ),
                            num_threads=4,
                        ),
                    )
                    
                    self.model = sherpa_onnx.OfflineTts(config)
                    logger.info(f"[OK] Model loaded (alt): {self.language.upper()} TTS ready (Speaker ID: {self.speaker_id})")
                    return True
                except Exception as e2:
                    logger.error(f"Failed to load model: {e2}")
                    import traceback
                    logger.error(traceback.format_exc())
                    return False
            finally:
                sys.stderr = old_stderr
        
        except Exception as e:
            logger.error(f"Failed to initialize model: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def synthesize(self, text: str) -> Optional[Tuple[np.ndarray, int]]:
        """
        Synthesize text to speech.
        
        Args:
            text: Text to synthesize
            
        Returns:
            Tuple of (audio_data, sample_rate) or None if failed
        """
        if not self.model:
            logger.error("Model not loaded")
            return None
        
        if not text or not text.strip():
            logger.warning("Empty text provided")
            return None
        
        try:
            logger.info(f"Synthesizing: '{text[:50]}{'...' if len(text) > 50 else ''}'")
            
            # Use specified speaker ID for multi-speaker VITS
            audio_obj = self.model.generate(text=text.strip(), sid=self.speaker_id, speed=1.0)
            
            if audio_obj is None:
                logger.error("Synthesis returned None")
                return None
            
            # Extract audio samples from the GeneratedAudio object
            # The audio object has a numpy attribute with the samples
            if hasattr(audio_obj, 'samples'):
                audio_array = np.array(audio_obj.samples, dtype=np.float32)
            else:
                # Try to convert directly
                audio_array = np.array(audio_obj, dtype=np.float32)
            
            # Ensure audio is 1D
            if audio_array.ndim > 1:
                audio_array = audio_array.flatten()
            
            sample_rate = 22050  # Standard sample rate for VITS
            
            logger.info(f"[OK] Generated audio: {len(audio_array)} samples at {sample_rate}Hz")
            return audio_array, sample_rate
            
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None


# ============================================================================
# TELUGU TTS ENGINE (Meta MMS - Python 3.13 compatible)
# ============================================================================

class TeluguTTSEngine:
    """Text-to-Speech engine using Meta MMS for Telugu."""
    
    def __init__(self, language: str = "te"):
        """
        Initialize Telugu TTS engine with CPU-only constraint.
        
        Args:
            language: Language code (always "te" for Telugu)
        """
        # Force CPU device
        os.environ['CUDA_VISIBLE_DEVICES'] = ''
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
        
        self.language = language
        self.model = None
        
        if not HAS_TELUGU or TeluguTTSMMS is None:
            logger.error("Telugu TTS not available")
            return
        
        try:
            logger.info("Initializing Meta MMS Telugu TTS engine (CPU-only)...")
            self.model = TeluguTTSMMS(device="cpu")
            
            if not self.model.model:
                logger.error("Failed to load Telugu model")
                self.model = None
        except Exception as e:
            logger.error(f"Failed to initialize Telugu TTS: {e}")
            self.model = None
    
    def synthesize(self, text: str) -> Optional[Tuple[np.ndarray, int]]:
        """
        Synthesize Telugu text to speech.
        
        Args:
            text: Telugu text to synthesize (should be sanitized)
            
        Returns:
            Tuple of (audio_data, sample_rate) or None if failed
        """
        if not self.model or not self.model.model:
            logger.error("Telugu TTS model not loaded")
            return None
        
        if not text or not text.strip():
            logger.warning("Empty text provided")
            return None
        
        try:
            logger.info(f"Synthesizing Telugu (Meta MMS): '{text[:50]}{'...' if len(text) > 50 else ''}'")
            result = self.model.synthesize(text)
            return result
        
        except Exception as e:
            logger.error(f"Telugu synthesis failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None


# ============================================================================
# AUDIO PLAYBACK
# ============================================================================

def play_audio(audio_data: np.ndarray, sample_rate: int) -> bool:
    """
    Play audio using sounddevice.
    
    Args:
        audio_data: Audio samples (float32, range [-1, 1])
        sample_rate: Sample rate in Hz
        
    Returns:
        bool: True if playback successful
    """
    try:
        logger.info(f"Playing audio at {sample_rate}Hz...")
        
        # Normalize audio if needed
        max_val = np.max(np.abs(audio_data))
        if max_val > 1.0:
            audio_data = audio_data / max_val
        
        sd.play(audio_data, samplerate=sample_rate)
        sd.wait()
        
        logger.info("[OK] Playback complete")
        return True
        
    except Exception as e:
        logger.error(f"[FAIL] Playback failed: {e}")
        return False


def save_audio(audio_data: np.ndarray, sample_rate: int, language: str = "en") -> Optional[Path]:
    """
    Save audio to WAV file with language-specific filename.
    
    Args:
        audio_data: Audio samples
        sample_rate: Sample rate in Hz
        language: "en" or "te"
        
    Returns:
        Path to saved file or None
    """
    try:
        from scipy.io import wavfile
        
        # Use language-specific filename
        filename = f"yt_explanation_{language}.wav"
        filepath = OUTPUTS_DIR / filename
        
        # Normalize audio
        max_val = np.max(np.abs(audio_data))
        if max_val > 0:
            audio_data = audio_data / max_val
        
        # Convert to int16 for WAV
        audio_int16 = np.int16(audio_data * 32767)
        
        wavfile.write(str(filepath), sample_rate, audio_int16)
        logger.info(f"[OK] Saved: {filepath}")
        return filepath
        
    except Exception as e:
        logger.error(f"[FAIL] Failed to save audio: {e}")
        return None


# ============================================================================
# CLI INTERFACE - MAIN INTERACTION MENU
# ============================================================================

def show_main_menu() -> Optional[str]:
    """
    Display main language selection menu.
    
    Returns:
        "en" for English, "te" for Telugu, None to exit
    """
    print("\n" + "="*60)
    print("  OFFLINE TEXT-TO-SPEECH SYSTEM - PROJECT B")
    print("="*60)
    print("\n[SELECT LANGUAGE]")
    print("  [1] English (VITS VCTK - Real-time text entry)")
    
    if HAS_TELUGU:
        print("  [2] Telugu (Meta MMS - File-based from Project_A)")
    else:
        print("  [2] Telugu (Not available - install dependencies)")
    
    print("  [0] Exit")
    
    while True:
        try:
            choice = input("\nEnter choice [0-2]: ").strip()
            
            if choice == "0":
                return None
            elif choice == "1":
                return "en"
            elif choice == "2":
                if not HAS_TELUGU:
                    print("\n[ERROR] Telugu support requires Transformers and PyTorch")
                    print("Install with: pip install -r requirements.txt")
                    continue
                return "te"
            else:
                print("[WARN] Invalid choice. Please enter 0, 1, or 2.")
        except EOFError:
            return None


def show_english_voice_menu() -> Optional[int]:
    """
    Display English voice speaker selection menu (YouTube Optimization).
    
    Returns:
        Choice (1, 2, 3) for predefined speakers, custom ID (4+), or None to go back
    """
    print("\n" + "="*60)
    print("  ENGLISH VOICE SELECTION (YouTube Optimization)")
    print("="*60)
    print("\n[SELECT VOICE]")
    print("  [1] The Professor")
    print("      Speaker ID: 3 | Deep, mature, and authoritative")
    print("      Best for technical deep-dives")
    print()
    print("  [2] The Narrator")
    print("      Speaker ID: 46 | Clear, resonant, and engaging")
    print("      Best for storytelling/intro videos")
    print()
    print("  [3] The Tech Lead")
    print("      Speaker ID: 8 | Bassy, bold, and energetic")
    print("      Best for fast-paced tutorials")
    print()
    print("  [4] Custom Speaker ID")
    print("      Enter any ID between 0–108")
    print()
    print("  [0] Back to language selection")
    
    while True:
        try:
            choice = input("\nEnter choice [0-4]: ").strip()
            
            if choice == "0":
                return None
            elif choice in ["1", "2", "3"]:
                return int(choice)
            elif choice == "4":
                return get_custom_speaker_id()
            else:
                print("[WARN] Invalid choice. Please enter 0, 1, 2, 3, or 4.")
        except EOFError:
            return None


def get_custom_speaker_id() -> int:
    """
    Get custom speaker ID from user.
    
    Returns:
        Speaker ID (0-108)
    """
    while True:
        try:
            speaker_id_str = input("\nEnter Speaker ID (0-108): ").strip()
            
            try:
                speaker_id = int(speaker_id_str)
                if 0 <= speaker_id <= 108:
                    logger.info(f"Selected custom speaker ID: {speaker_id}")
                    return speaker_id
                else:
                    print(f"[WARN] Speaker ID must be between 0 and 108. Got: {speaker_id}")
            except ValueError:
                print(f"[WARN] Invalid input: '{speaker_id_str}'. Must be a number.")
        except EOFError:
            return 0


def get_english_text() -> Optional[str]:
    """
    Get English text from user input.
    
    Returns:
        Text to synthesize or None if cancelled
    """
    print("\n[ENGLISH TEXT INPUT]")
    
    while True:
        try:
            text = input("Enter text to synthesize: ").strip()
            
            # Ensure text is properly decoded as UTF-8
            if isinstance(text, bytes):
                text = text.decode('utf-8', errors='replace')
            
            if not text:
                print("[WARN] Text cannot be empty. Try again.")
                continue
            
            logger.info(f"User input: {len(text)} characters")
            return text
        
        except EOFError:
            return None
        except Exception as e:
            print(f"[FAIL] Input error: {e}")
            return None


def show_telugu_preview(text: str) -> bool:
    """
    Display Telugu translated text preview.
    
    Args:
        text: Telugu text to display
        
    Returns:
        True if user confirms to proceed
    """
    print("\n" + "="*60)
    print("  TELUGU SCRIPT PREVIEW")
    print("="*60)
    print("\n--- SCRIPT PREVIEW ---")
    print(text)
    print("--- END PREVIEW ---\n")
    
    while True:
        try:
            choice = input("Proceed with synthesis? [y/n]: ").strip().lower()
            
            if choice in ['y', 'yes']:
                return True
            elif choice in ['n', 'no']:
                return False
            else:
                print("Invalid choice. Please enter 'y' or 'n'.")
        except EOFError:
            return False


def get_playback_choice() -> bool:
    """Ask user if they want to play audio."""
    while True:
        try:
            choice = input("\n[PLAYBACK]\nPlay audio now? [y/n]: ").strip().lower()
            if choice in ['y', 'yes']:
                return True
            elif choice in ['n', 'no']:
                return False
            else:
                print("Invalid choice. Please enter 'y' or 'n'.")
        except EOFError:
            return False


def get_replay_choice() -> bool:
    """Ask user if they want to replay audio."""
    while True:
        try:
            choice = input("\nReplay? [y/n]: ").strip().lower()
            if choice in ['y', 'yes']:
                return True
            elif choice in ['n', 'no']:
                return False
            else:
                print("Invalid choice. Please enter 'y' or 'n'.")
        except EOFError:
            return False


def get_continue_choice() -> bool:
    """Ask user if they want to continue."""
    while True:
        try:
            choice = input("\nContinue? [y/n]: ").strip().lower()
            if choice in ['y', 'yes']:
                return True
            elif choice in ['n', 'no']:
                return False
            else:
                print("Invalid choice. Please enter 'y' or 'n'.")
        except EOFError:
            return False


# ============================================================================
# OLD CLI FUNCTIONS (KEPT FOR REFERENCE, NOT USED IN NEW FLOW)
# ============================================================================

def get_language_choice() -> str:
    """Get language choice from user."""
    print("\n" + "="*50)
    print("  TEXT-TO-SPEECH (OFFLINE)")
    print("="*50)
    print("\n[SELECT LANGUAGE]")
    print("  [1] English (VITS VCTK)")
    print("  [2] Add Custom Telugu Model")
    print("  [0] Exit")
    
    while True:
        try:
            choice = input("\nEnter choice [0-2]: ").strip()
            if choice == "1":
                return "en"
            elif choice == "2":
                print("\n[CUSTOM MODEL SETUP]")
                print("To add a Telugu VITS model:")
                print("  1. Get Telugu VITS model from:")
                print("     - Hugging Face: https://huggingface.co/models")
                print("  2. Extract/download model.onnx and tokens.txt")
                print("  3. Copy both files to: voice/models/te/")
                print("  4. Run this application again")
                input("\nPress Enter when ready...")
                continue
            elif choice == "0":
                return None
            else:
                print("Invalid choice. Please enter 0, 1, or 2.")
        except EOFError:
            return None


def get_input_method() -> Optional[str]:
    """Get input method and text from user."""
    while True:
        print("\n[INPUT METHOD]")
        print("  [1] Type text")
        print("  [2] Load from file")
        print("  [0] Back to language selection")
        
        try:
            choice = input("\nEnter choice [0-2]: ").strip()
            
            if choice == "0":
                return None
            
            elif choice == "1":
                print("\n[TYPE TEXT]")
                while True:
                    text = input("Enter text to synthesize: ").strip()
                    # Ensure text is properly decoded as UTF-8
                    if isinstance(text, bytes):
                        text = text.decode('utf-8', errors='replace')
                    if not text:
                        print("[WARN] Text cannot be empty. Try again.")
                        continue
                    return text
            
            elif choice == "2":
                print("\n[LOAD FROM FILE]")
                while True:
                    file_path = input("Enter file path (.txt): ").strip()
                    if not file_path:
                        print("[WARN] File path cannot be empty. Try again.")
                        continue
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            text = f.read().strip()
                        
                        if not text:
                            print("[WARN] File is empty. Try again.")
                            continue
                        
                        logger.info(f"[OK] Loaded: {file_path}")
                        return text
                    
                    except FileNotFoundError:
                        print(f"[FAIL] File not found: {file_path}")
                        continue
                    except Exception as e:
                        print(f"[FAIL] Error reading file: {e}")
                        continue
            else:
                print("[WARN] Invalid choice. Please enter 0, 1, or 2.")
                continue
        
        except EOFError:
            return None
        except Exception as e:
            print(f"[FAIL] Input error: {e}")
            return None


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application loop - Project B Voice Engine."""
    print("\n" + "="*60)
    print("  OFFLINE TEXT-TO-SPEECH SYSTEM - PROJECT B")
    print("="*60)
    
    # Setup
    ensure_directories()
    
    # Initialize models
    print("\n[MODEL INITIALIZATION]")
    logger.info("[INFO] Checking English model...")
    en_model_exists = (EN_MODEL_DIR / "vits-vctk.onnx").exists()
    if not en_model_exists:
        print("[INFO] Downloading English model (first run)...")
        download_models()
    else:
        logger.info("[OK] English model found")
        print("[OK] English model ready")
    
    print("\n[SYSTEM STATUS]")
    print("[DEVICE] CPU-only mode (CUDA_VISIBLE_DEVICES='')") 
    print("[ENGLISH] VITS VCTK - Multi-speaker (with lexicon)")
    if HAS_TELUGU:
        print("[TELUGU] Meta MMS (facebook/mms-tts-tel)")
    else:
        print("[TELUGU] Not available")
    
    # Main interactive loop
    while True:
        print("\n" + "="*60)
        
        # 1. Ask Language
        language = show_main_menu()
        
        if language is None:
            print("\n[OK] Thank you! Exiting...")
            break
        
        # 2. IF ENGLISH MODE
        if language == "en":
            print("\n[ENGLISH MODE] Real-time text entry")
            
            # Show voice menu
            voice_choice = show_english_voice_menu()
            if voice_choice is None:
                continue  # Go back to main menu
            
            # Map choice to speaker ID
            if voice_choice in [1, 2, 3]:
                speaker_id = SPEAKER_PROFILES[voice_choice]["id"]
                voice_name = SPEAKER_PROFILES[voice_choice]["name"]
                print(f"\n[VOICE SELECTED] {voice_name} (Speaker ID: {speaker_id})")
            else:
                speaker_id = voice_choice  # Custom ID
                print(f"\n[VOICE SELECTED] Custom Speaker (ID: {speaker_id})")
            
            # Get text from user
            text = get_english_text()
            if text is None:
                continue  # Go back to main menu
            
            # Initialize English engine with selected speaker
            print("\n[LOADING] English TTS engine...")
            engine = VITSTTSEngine(language="en", speaker_id=speaker_id)
            
            if not engine.model:
                print("\n[FAIL] Failed to load English TTS engine")
                if not get_continue_choice():
                    break
                continue
            
            # Synthesize
            print("\n[PROCESSING]")
            result = engine.synthesize(text)
            
            if result is None:
                print("\n[FAIL] Synthesis failed")
                if not get_continue_choice():
                    break
                continue
            
            audio_data, sample_rate = result
            
            # Save
            print("\n[OUTPUT]")
            saved_path = save_audio(audio_data, sample_rate, language="en")
            
            if saved_path:
                # Save metadata
                save_metadata_log("en", voice_choice, saved_path.name)
                print(f"[SUCCESS] Audio saved: {saved_path.name}")
            
            # Playback
            if get_playback_choice():
                while True:
                    play_audio(audio_data, sample_rate)
                    if not get_replay_choice():
                        break
        
        # 3. IF TELUGU MODE
        elif language == "te":
            print("\n[TELUGU MODE] Multiple input options available")
            
            if not HAS_TELUGU:
                print("\n[ERROR] Telugu support not available")
                print("Install dependencies: pip install -r requirements.txt")
                continue
            
            # Get Telugu text
            text = get_telugu_input_method()
            
            if text is None:
                continue  # Go back to main menu
            
            # Display Telugu Preview
            if not show_telugu_preview(text):
                continue  # Go back to main menu
            
            # Sanitization
            print("[SANITIZATION] Removing English characters and metadata...")
            sanitized_text = sanitize_telugu_text(text)
            
            if not sanitized_text:
                print("[WARN] Sanitized text is empty")
                if not get_continue_choice():
                    break
                continue
            
            logger.info(f"Original: {len(text)} chars -> Sanitized: {len(sanitized_text)} chars")
            print(f"[OK] Text sanitized: {len(text)} -> {len(sanitized_text)} characters")
            
            # Initialize Telugu engine
            print("\n[LOADING] Telugu TTS engine (Meta MMS)...")
            engine = TeluguTTSEngine(language="te")
            
            if not engine.model:
                print("\n[FAIL] Failed to load Telugu TTS engine")
                if not get_continue_choice():
                    break
                continue
            
            # Synthesize
            print("\n[PROCESSING]")
            result = engine.synthesize(sanitized_text)
            
            if result is None:
                print("\n[FAIL] Synthesis failed")
                if not get_continue_choice():
                    break
                continue
            
            audio_data, sample_rate = result
            
            # Save
            print("\n[OUTPUT]")
            saved_path = save_audio(audio_data, sample_rate, language="te")
            
            if saved_path:
                # Save metadata
                save_metadata_log("te", 0, saved_path.name)
                print(f"[SUCCESS] Audio saved: {saved_path.name}")
            
            # Playback
            if get_playback_choice():
                while True:
                    play_audio(audio_data, sample_rate)
                    if not get_replay_choice():
                        break
        
        # Ask to continue
        if not get_continue_choice():
            print("\n[OK] Thank you for using Offline TTS!")
            break



if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[OK] Interrupted by user. Goodbye!")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
