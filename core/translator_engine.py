"""
Translator Engine - Wraps the language_converter/ module.
Translates English text to target language using NLLB-200.
"""

import logging
import time
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

# Language options (from language_converter/main.py)
LANGUAGE_OPTIONS = {
    "telugu": "tel_Telu",
    "hindi": "hin_Deva",
    "tamil": "tam_Taml",
    "kannada": "kan_Knda",
    "malayalam": "mal_Mlym",
    "bengali": "ben_Beng",
    "marathi": "mar_Deva",
    "gujarati": "guj_Gujr",
    "punjabi": "pan_Guru",
    "urdu": "urd_Arab",
    "spanish": "spa_Latn",
    "french": "fra_Latn",
    "german": "deu_Latn",
    "arabic": "arb_Arab",
    "japanese": "jpn_Jpan",
}

# Cache for loaded model
_cached_model = None
_cached_tokenizer = None


def _load_model(config: Optional[Dict] = None):
    """Load or retrieve cached NLLB model."""
    global _cached_model, _cached_tokenizer
    
    if _cached_model is not None and _cached_tokenizer is not None:
        return _cached_tokenizer, _cached_model
    
    cfg = (config or {}).get("translation", {})
    model_name = cfg.get("model_name", "facebook/nllb-200-distilled-600M")
    use_quantization = cfg.get("quantization", "8bit") == "8bit"
    
    import torch
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    
    # Monkey-patch for PyTorch 2.4+ compatibility
    if not hasattr(torch.nn.Module, "set_submodule"):
        def set_submodule(self, target, module):
            atoms = target.split(".")
            name = atoms.pop(-1)
            mod = self
            for item in atoms:
                mod = getattr(mod, item)
            setattr(mod, name, module)
        torch.nn.Module.set_submodule = set_submodule
    
    logger.info(f"[Translator] Loading {model_name}...")
    
    tokenizer = AutoTokenizer.from_pretrained(model_name, src_lang="eng_Latn")
    
    load_kwargs = {
        "device_map": "auto",
        "use_safetensors": True,
    }
    
    if use_quantization and torch.cuda.is_available():
        from transformers import BitsAndBytesConfig
        load_kwargs["quantization_config"] = BitsAndBytesConfig(load_in_8bit=True)
    
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name, **load_kwargs)
    model.eval()
    
    _cached_model = model
    _cached_tokenizer = tokenizer
    
    logger.info("[Translator] Model loaded successfully")
    return tokenizer, model


def translate_text(
    text: str,
    target_language: str = "telugu",
    config: Optional[Dict] = None,
    max_retries: int = 3,
) -> Optional[str]:
    """
    Translate English text to target language.
    
    Args:
        text: English text to translate
        target_language: Language name or NLLB code
        config: Optional config dict
        max_retries: Number of retry attempts
        
    Returns:
        Translated text, or None on failure
    """
    if not text or not text.strip():
        return None
    
    # Resolve language code
    lang_code = LANGUAGE_OPTIONS.get(target_language.lower(), target_language)
    
    cfg = (config or {}).get("translation", {})
    max_tokens = cfg.get("max_tokens", 256)
    num_beams = cfg.get("num_beams", 4)
    
    for attempt in range(1, max_retries + 1):
        try:
            import torch
            
            tokenizer, model = _load_model(config)
            
            tokenizer.src_lang = "eng_Latn"
            inputs = tokenizer(text, return_tensors="pt")
            inputs = {k: v.to(model.device) for k, v in inputs.items()}
            
            forced_bos_token_id = tokenizer.convert_tokens_to_ids(lang_code)
            if forced_bos_token_id == tokenizer.unk_token_id:
                logger.error(f"[Translator] Unsupported language code: {lang_code}")
                return None
            
            with torch.inference_mode():
                generated = model.generate(
                    **inputs,
                    forced_bos_token_id=forced_bos_token_id,
                    max_new_tokens=max_tokens,
                    num_beams=num_beams,
                    early_stopping=True,
                )
            
            translated = tokenizer.batch_decode(generated, skip_special_tokens=True)[0]
            logger.info(f"[Translator] Translated to {target_language}: {translated[:80]}...")
            return translated
            
        except Exception as e:
            logger.warning(f"[Translator] Attempt {attempt} failed: {e}")
            if attempt < max_retries:
                time.sleep(2 ** attempt)
    
    return None


def get_available_languages() -> Dict[str, str]:
    """Return dict of available language names to NLLB codes."""
    return LANGUAGE_OPTIONS.copy()
