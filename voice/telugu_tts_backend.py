"""
Telugu TTS Module - Python 3.13+ Support
=========================================

Drop-in replacement for the existing Coqui TTS Telugu support.
Works with Python 3.13 (Coqui TTS requires Python 3.11).

This module provides multiple backends for Telugu synthesis.
Import and use like the old system but with Python 3.13 compatibility.

Usage:
    from telugu_tts_backend import TeluguTTS
    
    tts = TeluguTTS(backend='mms')  # or 'speecht5'
    wav_path = tts.synthesize("నమస్కారం", "output.wav")
"""

import os
import sys
from pathlib import Path
from typing import Optional, Tuple, Union
import numpy as np
from dataclasses import dataclass
from enum import Enum
import warnings

__version__ = "1.0.0"
__python_3_13_compatible__ = True


class TTS_Backend(Enum):
    """Available TTS backends for Telugu."""
    MMS = "mms"                          # Meta MMS - Recommended
    SPEECHT5 = "speecht5"                # Microsoft SpeechT5 - Highest quality
    CHILUKA = "chiluka"                  # StyleTTS2 - Voice cloning
    VITS_CUSTOM = "vits_custom"          # Fine-tuned VITS models
    FAIRSEQ = "fairseq"                  # Advanced Fairseq MMS


@dataclass
class TTSConfig:
    """Configuration for Telugu TTS."""
    backend: str = "mms"
    output_sample_rate: int = 22050
    use_gpu: bool = True
    cache_dir: Optional[str] = None
    normalize_audio: bool = True
    verbose: bool = True


class TeluguTTS:
    """
    Unified Telugu TTS interface for Python 3.13+
    
    Supports multiple backends:
    1. MMS (Recommended) - Lightweight, production-ready
    2. SpeechT5 - Highest quality, fine-tuned for Telugu
    3. Chiluka - Voice cloning, style control
    4. Custom VITS - Community-trained models
    5. Fairseq - Advanced, research-oriented
    """
    
    def __init__(self, backend: str = "mms", config: Optional[TTSConfig] = None):
        """
        Initialize Telugu TTS system.
        
        Args:
            backend: TTS backend to use ('mms', 'speecht5', etc.)
            config: TTSConfig object with parameters
        """
        self.config = config or TTSConfig(backend=backend)
        self.backend_name = backend
        self.model = None
        self.tokenizer = None
        self.torch = None
        self.scipy = None
        
        if self.config.verbose:
            print(f"Initializing TeluguTTS with backend: {backend}")
            print(f"Python Version: {sys.version}")
        
        self._setup_backend()
    
    def _setup_backend(self):
        """Setup the selected TTS backend."""
        if self.backend_name == "mms":
            self._setup_mms()
        elif self.backend_name == "speecht5":
            self._setup_speecht5()
        elif self.backend_name == "chiluka":
            self._setup_chiluka()
        else:
            raise ValueError(f"Unknown backend: {self.backend_name}")
    
    def _setup_mms(self):
        """Setup Meta MMS TTS backend."""
        try:
            from transformers import VitsModel, AutoTokenizer
            import torch
            import scipy.io.wavfile
            
            if self.config.verbose:
                print("[MMS] Loading models...")
            
            self.tokenizer = AutoTokenizer.from_pretrained("facebook/mms-tts-tel")
            self.model = VitsModel.from_pretrained("facebook/mms-tts-tel")
            self.model.eval()
            
            self.torch = torch
            self.scipy = scipy
            
            self.sample_rate = 16000  # MMS uses 16kHz
            
            if self.config.verbose:
                print("[MMS] ✓ Models loaded successfully")
                print(f"      Sample rate: {self.sample_rate}Hz")
        
        except ImportError as e:
            print(f"ERROR: {e}")
            print("Install: pip install transformers>=4.33 torch scipy")
            raise
    
    def _setup_speecht5(self):
        """Setup SpeechT5 fine-tuned backend."""
        try:
            from transformers import (
                SpeechT5Processor, 
                SpeechT5ForTextToSpeech, 
                SpeechT5HifiGan
            )
            import torch
            import scipy.io.wavfile
            
            if self.config.verbose:
                print("[SpeechT5] Loading models...")
            
            self.processor = SpeechT5Processor.from_pretrained(
                "Epikwhale/speecht5_finetuned_telugu_charan"
            )
            self.model = SpeechT5ForTextToSpeech.from_pretrained(
                "Epikwhale/speecht5_finetuned_telugu_charan"
            )
            self.vocoder = SpeechT5HifiGan.from_pretrained("microsoft/speecht5_hifigan")
            
            self.torch = torch
            self.scipy = scipy
            self.sample_rate = 16000
            self.speaker_embeddings = None  # Will be generated
            
            if self.config.verbose:
                print("[SpeechT5] ✓ Models loaded successfully")
                print(f"           Sample rate: {self.sample_rate}Hz")
        
        except ImportError as e:
            print(f"ERROR: {e}")
            print("Install: pip install transformers torch scipy")
            raise
    
    def _setup_chiluka(self):
        """Setup Chiluka TTS backend."""
        try:
            if self.config.verbose:
                print("[Chiluka] This requires: pip install git+https://github.com/Seemanth/chiluka-tts.git")
            
            from chiluka import Chiluka
            
            if self.config.verbose:
                print("[Chiluka] Loading model...")
            
            self.model = Chiluka.from_pretrained("Seemanth/chiluka-tts")
            self.sample_rate = 22050
            
            if self.config.verbose:
                print("[Chiluka] ✓ Model loaded successfully")
        
        except ImportError as e:
            print(f"ERROR: {e}")
            print("Install: pip install git+https://github.com/Seemanth/chiluka-tts.git")
            raise
    
    def synthesize(
        self, 
        text: str, 
        output_path: Union[str, Path] = "output.wav",
        play: bool = False
    ) -> str:
        """
        Synthesize Telugu text to speech.
        
        Args:
            text: Telugu text to synthesize
            output_path: Path to save WAV file
            play: Whether to play audio after synthesis (requires sounddevice)
            
        Returns:
            Path to generated WAV file
            
        Example:
            tts = TeluguTTS(backend='mms')
            tts.synthesize("నమస్కారం", "hello.wav")
        """
        
        if not text:
            raise ValueError("Text cannot be empty")
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if self.backend_name == "mms":
            return self._synthesize_mms(text, output_path, play)
        elif self.backend_name == "speecht5":
            return self._synthesize_speecht5(text, output_path, play)
        elif self.backend_name == "chiluka":
            return self._synthesize_chiluka(text, output_path, play)
        else:
            raise ValueError(f"Unknown backend: {self.backend_name}")
    
    def _synthesize_mms(
        self,
        text: str,
        output_path: Path,
        play: bool = False
    ) -> str:
        """Synthesize using MMS backend."""
        try:
            if self.config.verbose:
                print(f"[MMS] Synthesizing: {text}")
            
            # Tokenize
            inputs = self.tokenizer(text, return_tensors="pt")
            
            # Generate
            with self.torch.no_grad():
                output = self.model(**inputs).waveform
            
            # Convert to numpy
            waveform = output.cpu().numpy().squeeze()
            
            # Normalize if requested
            if self.config.normalize_audio and waveform.dtype == np.float32:
                waveform = (waveform * 32767).astype(np.int16)
            
            # Resample if needed
            if self.config.output_sample_rate != self.sample_rate:
                import librosa
                waveform = librosa.resample(
                    waveform,
                    orig_sr=self.sample_rate,
                    target_sr=self.config.output_sample_rate
                )
            
            # Save
            self.scipy.io.wavfile.write(str(output_path), self.sample_rate, waveform)
            
            if self.config.verbose:
                duration = len(waveform) / self.sample_rate
                size_mb = output_path.stat().st_size / (1024 * 1024)
                print(f"[MMS] ✓ Saved: {output_path}")
                print(f"      Duration: {duration:.2f}s, Size: {size_mb:.2f}MB")
            
            if play:
                self._play_audio(output_path)
            
            return str(output_path)
        
        except Exception as e:
            print(f"ERROR in MMS synthesis: {e}")
            raise
    
    def _synthesize_speecht5(
        self,
        text: str,
        output_path: Path,
        play: bool = False
    ) -> str:
        """Synthesize using SpeechT5 backend."""
        try:
            if self.config.verbose:
                print(f"[SpeechT5] Synthesizing: {text}")
            
            # Prepare inputs
            inputs = self.processor(text=text, return_tensors="pt")
            
            # Generate speaker embeddings
            speaker_embeddings = self.torch.randn(1, 512)
            
            # Generate speech
            with self.torch.no_grad():
                speech = self.model.generate_speech(
                    inputs["input_ids"],
                    speaker_embeddings,
                    vocoder=self.vocoder
                )
            
            # Convert to numpy
            waveform = speech.cpu().numpy().squeeze()
            
            # Save
            self.scipy.io.wavfile.write(str(output_path), self.sample_rate, waveform)
            
            if self.config.verbose:
                duration = len(waveform) / self.sample_rate
                print(f"[SpeechT5] ✓ Saved: {output_path}")
                print(f"           Duration: {duration:.2f}s")
            
            if play:
                self._play_audio(output_path)
            
            return str(output_path)
        
        except Exception as e:
            print(f"ERROR in SpeechT5 synthesis: {e}")
            raise
    
    def _synthesize_chiluka(
        self,
        text: str,
        output_path: Path,
        play: bool = False
    ) -> str:
        """Synthesize using Chiluka backend."""
        try:
            if self.config.verbose:
                print(f"[Chiluka] Synthesizing: {text}")
            
            wav = self.model.synthesize(text=text, lang="telugu")
            self.model.save_wav(wav, str(output_path))
            
            if self.config.verbose:
                print(f"[Chiluka] ✓ Saved: {output_path}")
            
            if play:
                self._play_audio(output_path)
            
            return str(output_path)
        
        except Exception as e:
            print(f"ERROR in Chiluka synthesis: {e}")
            raise
    
    @staticmethod
    def _play_audio(path: Union[str, Path]):
        """Play audio file if sounddevice is available."""
        try:
            import sounddevice as sd
            import scipy.io.wavfile
            
            sr, data = scipy.io.wavfile.read(str(path))
            sd.play(data, sr)
            sd.wait()
        
        except ImportError:
            print("Install sounddevice to play audio: pip install sounddevice")
        except Exception as e:
            print(f"Error playing audio: {e}")
    
    def batch_synthesize(
        self,
        texts: list[str],
        output_dir: Union[str, Path] = "batch_output",
        prefix: str = "telugu"
    ) -> list[str]:
        """
        Synthesize multiple texts in batch.
        
        Args:
            texts: List of Telugu texts
            output_dir: Directory for output files
            prefix: Prefix for output filenames
            
        Returns:
            List of paths to generated files
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        paths = []
        for idx, text in enumerate(texts, 1):
            output_path = output_dir / f"{prefix}_{idx:03d}.wav"
            path = self.synthesize(text, output_path, play=False)
            paths.append(path)
            
            if self.config.verbose:
                print(f"  [{idx}/{len(texts)}] Completed")
        
        return paths
    
    @staticmethod
    def list_backends() -> dict:
        """List available backends with their features."""
        return {
            "mms": {
                "name": "Meta Massively Multilingual Speech",
                "quality": "Good",
                "speed": "Fast",
                "memory": "Low (36M)",
                "voices": "Single",
                "languages": "1107",
                "license": "CC-BY-NC-4.0",
                "recommended": True
            },
            "speecht5": {
                "name": "Microsoft SpeechT5 (Fine-tuned)",
                "quality": "Excellent",
                "speed": "Medium",
                "memory": "Medium (500M)",
                "voices": "Single with embeddings",
                "languages": "Telugu",
                "license": "MIT",
                "recommended": True
            },
            "chiluka": {
                "name": "Chiluka (StyleTTS2)",
                "quality": "Very Good",
                "speed": "Medium",
                "memory": "Medium",
                "voices": "Single",
                "languages": "Telugu + English",
                "license": "MIT",
                "recommended": False
            }
        }


# ============================================================================
# Compatibility wrapper for old Coqui TTS code
# ============================================================================

class TTS:
    """
    Drop-in replacement for Coqui TTS Telugu module.
    
    This class provides API compatibility with the old system while using
    the new Python 3.13-compatible backends.
    """
    
    def __init__(self, model_name: str = "tts_models/te/cv/vits", **kwargs):
        """
        Initialize TTS (compatible with old Coqui API).
        
        Args:
            model_name: Model identifier (ignored, always uses best available)
        """
        # Map old model names to new backends
        if "te/" in model_name or "telugu" in model_name.lower():
            backend = "mms"  # Use MMS by default
        else:
            backend = "mms"
        
        self.tts_engine = TeluguTTS(backend=backend)
    
    def tts_to_file(self, text: str, file_path: str = "output.wav"):
        """
        Synthesize text to file (compatible with old API).
        
        Args:
            text: Telugu text to synthesize
            file_path: Output file path
        """
        return self.tts_engine.synthesize(text, file_path)
    
    def tts_to_array(self, text: str) -> Tuple[np.ndarray, int]:
        """
        Synthesize text to numpy array.
        
        Args:
            text: Telugu text to synthesize
            
        Returns:
            (audio_array, sample_rate)
        """
        import tempfile
        import scipy.io.wavfile
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = f.name
        
        try:
            self.tts_engine.synthesize(text, temp_path)
            sr, data = scipy.io.wavfile.read(temp_path)
            return data, sr
        finally:
            Path(temp_path).unlink(missing_ok=True)


# ============================================================================
# Quick utility functions
# ============================================================================

def synthesize_quickly(text: str, output: str = "output.wav") -> str:
    """
    Quick one-liner to synthesize Telugu text.
    
    Args:
        text: Telugu text
        output: Output file path
        
    Returns:
        Path to generated audio file
        
    Example:
        from telugu_tts_backend import synthesize_quickly
        synthesize_quickly("నమస్కారం", "hello.wav")
    """
    tts = TeluguTTS(backend="mms")
    return tts.synthesize(text, output)


if __name__ == "__main__":
    # Demo
    print("Telugu TTS Backend Module - Python 3.13+ Compatible")
    print("=" * 70)
    
    # Show available backends
    backends = TeluguTTS.list_backends()
    print("\nAvailable Backends:")
    for name, info in backends.items():
        print(f"\n  {name.upper()}")
        for key, value in info.items():
            print(f"    {key}: {value}")
    
    # Try MMS
    print("\n" + "=" * 70)
    print("Testing MMS Backend...")
    print("=" * 70)
    
    try:
        tts = TeluguTTS(backend="mms", config=TTSConfig(verbose=True))
        output = tts.synthesize("నమస్కారం", "test_output.wav")
        print(f"\n✓ Test successful! Audio saved to: {output}")
    
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        print("This is expected if dependencies are not installed yet.")
        print("Install with: pip install transformers torch scipy")
