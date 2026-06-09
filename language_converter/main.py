from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import torch

# PyTorch 2.4+ compatibility patch for Hugging Face Accelerate layer injections
if not hasattr(torch.nn.Module, "set_submodule"):
    def set_submodule(self, target: str, module: torch.nn.Module) -> None:
        atoms = target.split(".")
        name = atoms.pop(-1)
        mod = self
        for item in atoms:
            mod = getattr(mod, item)
        setattr(mod, name, module)
    torch.nn.Module.set_submodule = set_submodule
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, BitsAndBytesConfig


MODEL_NAME = "facebook/nllb-200-distilled-600M"
SOURCE_LANGUAGE = "eng_Latn"


@dataclass(frozen=True)
class LanguageOption:
    key: str
    label: str
    code: str


LANGUAGE_OPTIONS: List[LanguageOption] = [
    LanguageOption("1", "Telugu", "tel_Telu"),
    LanguageOption("2", "Hindi", "hin_Deva"),
    LanguageOption("3", "Tamil", "tam_Taml"),
    LanguageOption("4", "Kannada", "kan_Knda"),
    LanguageOption("5", "Malayalam", "mal_Mlym"),
    LanguageOption("6", "Bengali", "ben_Beng"),
    LanguageOption("7", "Marathi", "mar_Deva"),
    LanguageOption("8", "Gujarati", "guj_Gujr"),
    LanguageOption("9", "Punjabi", "pan_Guru"),
    LanguageOption("10", "Urdu", "urd_Arab"),
    LanguageOption("11", "Spanish", "spa_Latn"),
    LanguageOption("12", "French", "fra_Latn"),
    LanguageOption("13", "German", "deu_Latn"),
    LanguageOption("14", "Arabic", "arb_Arab"),
    LanguageOption("15", "Japanese", "jpn_Jpan"),
]

LANGUAGE_LOOKUP: Dict[str, LanguageOption] = {}
for option in LANGUAGE_OPTIONS:
    LANGUAGE_LOOKUP[option.key.lower()] = option
    LANGUAGE_LOOKUP[option.label.lower()] = option
    LANGUAGE_LOOKUP[option.code.lower()] = option

DEFAULT_LANGUAGE = LANGUAGE_OPTIONS[0]


def load_translation_pipeline() -> tuple[AutoTokenizer, AutoModelForSeq2SeqLM]:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, src_lang=SOURCE_LANGUAGE)

    # ── Try GPU + 8-bit quantization first (fastest, lowest VRAM) ──
    if torch.cuda.is_available():
        try:
            quantization_config = BitsAndBytesConfig(load_in_8bit=True)
            model = AutoModelForSeq2SeqLM.from_pretrained(
                MODEL_NAME,
                device_map="auto",
                quantization_config=quantization_config,
                use_safetensors=True,
            )
            model.eval()
            print("[Translation] Loaded NLLB-200 on GPU (8-bit)")
            return tokenizer, model
        except Exception as e:
            print(f"[Translation] GPU 8-bit failed ({e}), falling back to CPU...")

    # ── Fallback: CPU + FP32 (the 600M model is ~1.2 GB, fits in RAM) ──
    print("[Translation] Loading NLLB-200 on CPU (FP32)...")
    model = AutoModelForSeq2SeqLM.from_pretrained(
        MODEL_NAME,
        use_safetensors=True,
    )
    model.eval()
    print("[Translation] Loaded NLLB-200 on CPU (FP32)")
    return tokenizer, model


def prompt_for_english_text() -> str:
    while True:
        text = input("Enter English text: ").strip()
        if text:
            return text
        print("Please enter some English text to translate.\n")


def print_language_menu() -> None:
    print("\nSelect target language:")
    for option in LANGUAGE_OPTIONS:
        default_text = " (default)" if option == DEFAULT_LANGUAGE else ""
        print(f"{option.key}. {option.label}{default_text}")


def prompt_for_target_language() -> LanguageOption:
    print_language_menu()

    while True:
        choice = input(
            f"\nPress Enter for {DEFAULT_LANGUAGE.label}, or type number/name/code: "
        ).strip()

        if not choice:
            return DEFAULT_LANGUAGE

        selected = LANGUAGE_LOOKUP.get(choice.lower())
        if selected:
            return selected

        print("Invalid selection. Please choose from the list above.\n")


def translate_text(
    text: str,
    target_language: LanguageOption,
    tokenizer: AutoTokenizer,
    model: AutoModelForSeq2SeqLM,
) -> str:
    tokenizer.src_lang = SOURCE_LANGUAGE
    inputs = tokenizer(text, return_tensors="pt")
    inputs = {key: value.to(model.device) for key, value in inputs.items()}

    forced_bos_token_id = tokenizer.convert_tokens_to_ids(target_language.code)
    if forced_bos_token_id == tokenizer.unk_token_id:
        raise ValueError(f"Unsupported NLLB language code: {target_language.code}")

    with torch.inference_mode():
        generated_tokens = model.generate(
            **inputs,
            forced_bos_token_id=forced_bos_token_id,
            max_new_tokens=256,
            num_beams=4,
            early_stopping=True,
        )

    return tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)[0]


def main() -> None:
    print("Loading facebook/nllb-200-distilled-600M in 8-bit mode on GPU...")
    tokenizer, model = load_translation_pipeline()
    print("Model loaded successfully.\n")

    text = prompt_for_english_text()
    target_language = prompt_for_target_language()
    translated_text = translate_text(text, target_language, tokenizer, model)

    print(f"\nTarget language: {target_language.label}")
    print("Translated text:")
    print(translated_text)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as exc:
        print(f"\nError: {exc}")
