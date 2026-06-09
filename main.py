#!/usr/bin/env python3
"""
🎬 REEL GENERATOR - Main CLI Entry Point
=========================================
Generates professional short-form video reels with:
- AI-powered script generation (DeepSeek R1)
- Text-to-speech voiceover (sherpa-onnx VITS)
- Smart image scraping with NLP keywords
- Animated video composition with subtitles

Usage:
    python main.py
"""

import os
import sys
import yaml
import logging
import shutil
import random
from pathlib import Path
from datetime import datetime
from typing import Optional, List

# Force UTF-8 encoding
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

os.environ['PYTHONIOENCODING'] = 'utf-8'

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(str(PROJECT_ROOT / "reel_generator.log"), encoding='utf-8'),
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)

# Try rich for pretty console output
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich import print as rprint
    HAS_RICH = True
    console = Console()
except ImportError:
    HAS_RICH = False
    console = None


# ============================================================================
# CONFIGURATION
# ============================================================================

def load_config() -> dict:
    """Load configuration from config.yaml."""
    config_path = PROJECT_ROOT / "config.yaml"
    
    if not config_path.exists():
        logger.error(f"Config not found: {config_path}")
        sys.exit(1)
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    return config


# ============================================================================
# PRETTY DISPLAY
# ============================================================================

def print_banner():
    """Print the application banner."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🎬  R E E L   G E N E R A T O R                          ║
║                                                              ║
║   AI-Powered Short-Form Video Creator                        ║
║   ─────────────────────────────────────                      ║
║   ✦ DeepSeek R1 Script Generation                           ║
║   ✦ VITS Neural Voice Synthesis                             ║
║   ✦ Smart Image Scraping + NLP                              ║
║   ✦ Cinematic Video Composition                             ║
║   ✦ Word-by-Word Karaoke Subtitles                          ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    if HAS_RICH:
        console.print(banner, style="bold cyan")
    else:
        print(banner)


def print_section(title: str):
    """Print a section header."""
    line = "─" * 60
    print(f"\n{line}")
    print(f"  {title}")
    print(f"{line}")


def print_success(msg: str):
    """Print a success message."""
    if HAS_RICH:
        console.print(f"  [bold green]✓[/bold green] {msg}")
    else:
        print(f"  ✓ {msg}")


def print_info(msg: str):
    """Print an info message."""
    if HAS_RICH:
        console.print(f"  [bold blue]ℹ[/bold blue] {msg}")
    else:
        print(f"  ℹ {msg}")


def print_error(msg: str):
    """Print an error message."""
    if HAS_RICH:
        console.print(f"  [bold red]✗[/bold red] {msg}")
    else:
        print(f"  ✗ {msg}")


def print_warning(msg: str):
    """Print a warning message."""
    if HAS_RICH:
        console.print(f"  [bold yellow]⚠[/bold yellow] {msg}")
    else:
        print(f"  ⚠ {msg}")


# ============================================================================
# USER INPUT
# ============================================================================

CONTENT_TYPES = ["educational", "technology", "funny", "professional"]
AUDIENCES = ["common", "engineers", "kids"]
ANIMATION_STYLES = [
    ("ken_burns", "Ken Burns - Slow zoom & pan (documentary)"),
    ("fade_scale", "Fade & Scale - Smooth fade with subtle scale"),
    ("slide_pop", "Slide & Pop - Images slide from sides"),
    ("cinematic", "Cinematic - Letterbox + dramatic zoom + vignette"),
    ("minimal_clean", "Minimal Clean - Simple crossfade (professional)"),
    ("none", "None - Static image (no animation)"),
    ("random_mix", "Random Mix - Random combination each image"),
]
SUBTITLE_STYLES = [
    ("fade_up", "Fade Up - Subtitle fades in from below"),
    ("pop_in", "Pop In - Subtitle pops in with scale"),
    ("slide_left", "Slide Left - Subtitle slides from left"),
    ("typewriter", "Typewriter - Letters appear one by one"),
]
SPEAKER_VOICES = [
    (46, "The Narrator - Clear, engaging (recommended)"),
    (3, "The Professor - Deep, authoritative"),
    (8, "The Tech Lead - Bassy, energetic"),
]
VOICE_LANGUAGES = [
    ("en", "English (Sherpa VITS)"),
    ("te", "Telugu (Meta MMS)"),
]


def get_choice(prompt: str, options: list, allow_default: int = None) -> int:
    """Get a numbered choice from user."""
    for i, opt in enumerate(options, 1):
        if isinstance(opt, tuple):
            print(f"    [{i}] {opt[1]}")
        else:
            print(f"    [{i}] {opt}")
    
    while True:
        try:
            default_hint = f" (default: {allow_default})" if allow_default else ""
            raw = input(f"\n  {prompt}{default_hint}: ").strip()
            
            if not raw and allow_default:
                return allow_default
            
            choice = int(raw)
            if 1 <= choice <= len(options):
                return choice
            print(f"  Please enter 1-{len(options)}")
        except ValueError:
            print("  Please enter a number")
        except EOFError:
            sys.exit(0)


def get_text(prompt: str, default: str = "") -> str:
    """Get text input from user."""
    while True:
        try:
            default_hint = f" (default: {default})" if default else ""
            raw = input(f"  {prompt}{default_hint}: ").strip()
            if not raw and default:
                return default
            if raw:
                return raw
            print("  This field is required")
        except EOFError:
            sys.exit(0)


def get_number(prompt: str, default: int = None, min_val: int = 1, max_val: int = 9999) -> int:
    """Get a number from user."""
    while True:
        try:
            default_hint = f" (default: {default})" if default else ""
            raw = input(f"  {prompt}{default_hint}: ").strip()
            
            if not raw and default:
                return default
            
            val = int(raw)
            if min_val <= val <= max_val:
                return val
            print(f"  Enter a number between {min_val}-{max_val}")
        except ValueError:
            print("  Please enter a number")
        except EOFError:
            sys.exit(0)


# ============================================================================
# SINGLE VIDEO PIPELINE
# ============================================================================

def generate_single_video(config: dict) -> Optional[str]:
    """Full pipeline for generating a single reel video."""
    from core.script_engine import generate_script
    from core.voice_engine import synthesize_speech, get_audio_duration, split_text_to_sentences, estimate_sentence_timings
    from core.image_engine import extract_search_queries, scrape_images_for_video
    from core.video_composer import compose_video
    
    print_section("📝 SINGLE VIDEO SETUP")
    
    # 1. Get topic
    topic = get_text("Enter topic")
    
    # 2. Content type
    print("\n  Content Type:")
    ct_idx = get_choice("Select content type", CONTENT_TYPES, allow_default=1)
    content_type = CONTENT_TYPES[ct_idx - 1]
    
    # 3. Duration
    duration = get_number("Approximate video length (seconds)", default=60, min_val=15, max_val=300)
    
    # 4. Target audience
    print("\n  Target Audience:")
    aud_idx = get_choice("Select audience", AUDIENCES, allow_default=1)
    audience = AUDIENCES[aud_idx - 1]
    
    # 5. Animation style
    print("\n  Animation Style:")
    anim_idx = get_choice("Select animation", ANIMATION_STYLES, allow_default=6)
    animation_style = ANIMATION_STYLES[anim_idx - 1][0]
    
    # 6. Subtitle style
    print("\n  Subtitle Style:")
    sub_idx = get_choice("Select subtitle style", SUBTITLE_STYLES, allow_default=1)
    subtitle_style = SUBTITLE_STYLES[sub_idx - 1][0]
    config["subtitles"]["entrance_animation"] = subtitle_style
    
    # 7. Language
    print("\n  Language:")
    lang_idx = get_choice("Select language", VOICE_LANGUAGES, allow_default=1)
    config["voice"]["language"] = VOICE_LANGUAGES[lang_idx - 1][0]
    
    # 8. Voice (only for English — Telugu has a single voice)
    if config["voice"]["language"] == "en":
        print("\n  Voice:")
        voice_idx = get_choice("Select voice", SPEAKER_VOICES, allow_default=1)
        speaker_id = SPEAKER_VOICES[voice_idx - 1][0]
    else:
        speaker_id = 0
        print("\n  Voice: Telugu MMS (auto-selected)")
    
    print_section("🚀 GENERATING REEL")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_topic = topic.replace(' ', '_')[:30]
    output_dir = Path(config.get("output", {}).get("single_video_dir", "output/single"))
    temp_dir = Path(config.get("output", {}).get("temp_dir", "output/.temp")) / timestamp
    temp_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # ── STEP 1: Generate Script ──
    print_info("Step 1/5: Generating script...")
    script_text = generate_script(
        topic=topic,
        content_type=content_type,
        duration=duration,
        audience=audience,
        language=config["voice"]["language"],
        config=config,
    )
    
    if not script_text:
        print_error("Script generation failed!")
        print_info("Make sure model.gguf exists in script/ or Ollama is running")
        return None
    
    print_success(f"Script generated: {len(script_text.split())} words")
    print(f"\n  Preview: {script_text[:150]}...\n")
    
    # Save script
    script_path = temp_dir / "script.txt"
    script_path.write_text(script_text, encoding='utf-8')
    
    # Save persistent original script
    scripts_dir = Path("output/scripts")
    scripts_dir.mkdir(parents=True, exist_ok=True)
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_topic_file = topic.replace(' ', '_')[:30]
    scripts_dir.joinpath(f"{safe_topic_file}_{timestamp_str}_original.txt").write_text(script_text, encoding='utf-8')
    
    # TRANSLATE SCRIPT IF NOT ENGLISH
    target_language = config.get("voice", {}).get("language", "en")
    voice_text = script_text
    if target_language != "en":
        print_info(f"Translating script to {target_language} via NLLB-200...")
        nllb_lang = "1" if target_language == "te" else "1"
        try:
            voice_text = translate_script_nllb(script_text, nllb_lang)
            print_success("Translation completed!")
            translated_path = temp_dir / "script_translated.txt"
            translated_path.write_text(voice_text, encoding='utf-8')
            
            # Save persistent translated script
            scripts_dir.joinpath(f"{safe_topic_file}_{timestamp_str}_translated.txt").write_text(voice_text, encoding='utf-8')
        except Exception as e:
            print_error(f"Translation failed: {e}")
            print_error("Cannot generate Telugu voice without translated text. Aborting.")
            return None
    
    # ── STEP 2: Generate Voice ──
    print_info("Step 2/5: Synthesizing voiceover...")
    audio_path = str(temp_dir / "voiceover.wav")
    
    result = synthesize_speech(
        text=voice_text,
        output_path=audio_path,
        speaker_id=speaker_id,
        config=config,
    )
    
    if not result:
        print_error("Voice synthesis failed!")
        return None
    
    audio_duration = get_audio_duration(audio_path)
    print_success(f"Audio generated: {audio_duration:.1f} seconds")
    
    # ── STEP 3: Parse sentences & extract keywords ──
    print_info("Step 3/5: Analyzing script & extracting keywords...")
    sentences = split_text_to_sentences(script_text)
    timings = estimate_sentence_timings(sentences, audio_duration)
    search_queries = extract_search_queries(timings, topic=topic, config=config)
    
    total_queries = sum(len(sq["queries"]) for sq in search_queries)
    print_success(f"Found {len(sentences)} sentences, {total_queries} search queries")
    
    # ── STEP 4: Scrape Images ──
    print_info("Step 4/5: Scraping images (this may take a while)...")
    images_dir = str(temp_dir / "images")
    image_map = scrape_images_for_video(
        search_queries=search_queries,
        output_dir=images_dir,
        config=config,
    )
    
    total_images = sum(len(imgs) for imgs in image_map.values())
    print_success(f"Downloaded {total_images} images for {len(image_map)} sentences")
    
    # ── STEP 5: Compose Video ──
    print_info("Step 5/5: Composing video (rendering frames)...")
    
    output_filename = f"{safe_topic}_{timestamp}.mp4"
    output_path = str(output_dir / output_filename)
    
    video_path = compose_video(
        script_text=script_text,
        audio_path=audio_path,
        sentence_timings=timings,
        image_map=image_map,
        output_path=output_path,
        config=config,
        animation_style=animation_style,
    )
    
    if not video_path:
        print_error("Video composition failed!")
        return None
    
    # Cleanup temp files
    if not config.get("output", {}).get("keep_temp_files", False):
        try:
            shutil.rmtree(str(temp_dir))
        except Exception:
            pass
    
    print_success(f"Video saved: {video_path}")
    return video_path


# ============================================================================
# SERIES PIPELINE
# ============================================================================

_nllb_pipeline = None

def translate_script_nllb(script_text: str, target_lang_code: str) -> str:
    global _nllb_pipeline
    import re
    from language_converter.main import load_translation_pipeline, translate_text, LANGUAGE_LOOKUP
    
    target_lang_option = LANGUAGE_LOOKUP.get(target_lang_code)
    
    if _nllb_pipeline is None:
        tokenizer, nllb_model = load_translation_pipeline()
        _nllb_pipeline = (tokenizer, nllb_model)
    else:
        tokenizer, nllb_model = _nllb_pipeline
    
    sentences = re.split(r'(?<=[.!?])\s+', script_text.strip())
    translated_sentences = []
    
    # Simple console info tracking without breaking rich if it doesn't exist
    for sent in sentences:
        if sent.strip():
            trans = translate_text(sent, target_lang_option, tokenizer, nllb_model)
            translated_sentences.append(trans)
            
    return " ".join(translated_sentences)

def generate_series(config: dict) -> List[str]:
    """Full pipeline for generating a video series."""
    from core.script_engine import generate_script, generate_series_scripts
    from core.voice_engine import synthesize_speech, get_audio_duration, split_text_to_sentences, estimate_sentence_timings
    from core.image_engine import extract_search_queries, scrape_images_for_video
    from core.video_composer import compose_video
    
    print_section("📺 VIDEO SERIES SETUP")
    
    # 1. Topic
    topic = get_text("Enter series topic")
    
    # 2. Number of videos
    num_videos = get_number("Number of videos in series", default=3, min_val=2, max_val=20)
    
    # 3. Duration per video
    duration_each = get_number("Duration per video (seconds)", default=60, min_val=15, max_val=300)
    
    # 4. Content type
    print("\n  Content Type:")
    ct_idx = get_choice("Select content type", CONTENT_TYPES, allow_default=1)
    content_type = CONTENT_TYPES[ct_idx - 1]
    
    # 5. Audience
    print("\n  Target Audience:")
    aud_idx = get_choice("Select audience", AUDIENCES, allow_default=1)
    audience = AUDIENCES[aud_idx - 1]
    
    # 6. Animation style
    print("\n  Animation Style:")
    anim_idx = get_choice("Select animation", ANIMATION_STYLES, allow_default=6)
    animation_style = ANIMATION_STYLES[anim_idx - 1][0]
    
    # 7. Subtitle style
    print("\n  Subtitle Style:")
    sub_idx = get_choice("Select subtitle style", SUBTITLE_STYLES, allow_default=1)
    subtitle_style = SUBTITLE_STYLES[sub_idx - 1][0]
    config["subtitles"]["entrance_animation"] = subtitle_style
    
    # 8. Language
    print("\n  Language:")
    lang_idx = get_choice("Select language", VOICE_LANGUAGES, allow_default=1)
    config["voice"]["language"] = VOICE_LANGUAGES[lang_idx - 1][0]
    
    # 9. Voice (only for English — Telugu has a single voice)
    if config["voice"]["language"] == "en":
        print("\n  Voice:")
        voice_idx = get_choice("Select voice", SPEAKER_VOICES, allow_default=1)
        speaker_id = SPEAKER_VOICES[voice_idx - 1][0]
    else:
        speaker_id = 0
        print("\n  Voice: Telugu MMS (auto-selected)")
    
    total_est = num_videos * duration_each
    print(f"\n  📊 Series Summary:")
    print(f"     Topic: {topic}")
    print(f"     Videos: {num_videos}")
    print(f"     Duration each: ~{duration_each}s")
    print(f"     Total est: ~{total_est}s ({total_est // 60}m {total_est % 60}s)")
    
    confirm = input("\n  Start generating? [Y/n]: ").strip().lower()
    if confirm == 'n':
        return []
    
    print_section("🚀 GENERATING VIDEO SERIES")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_topic = topic.replace(' ', '_')[:30]
    series_dir = Path(config.get("output", {}).get("series_dir", "output/series")) / f"{safe_topic}_{timestamp}"
    series_dir.mkdir(parents=True, exist_ok=True)
    
    # ── STEP 1: Generate all scripts ──
    print_info(f"Step 1: Generating {num_videos} scripts...")
    scripts = generate_series_scripts(
        topic=topic,
        num_videos=num_videos,
        duration_per_video=duration_each,
        content_type=content_type,
        audience=audience,
        language=config["voice"]["language"],
        config=config,
    )
    
    print_success(f"Generated {len(scripts)} episode scripts")
    
    # ── STEP 2-5: Generate each video ──
    completed_videos = []
    
    for ep_idx, (ep_title, ep_script) in enumerate(scripts):
        ep_num = ep_idx + 1
        print_section(f"🎬 Episode {ep_num}/{num_videos}: {ep_title}")
        
        temp_dir = series_dir / f".temp_ep{ep_num:02d}"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Save script
        script_path = temp_dir / "script.txt"
        script_path.write_text(ep_script, encoding='utf-8')
        print_info(f"Script: {len(ep_script.split())} words")
        
        # Save persistent original script
        scripts_dir = Path("output/scripts")
        scripts_dir.mkdir(parents=True, exist_ok=True)
        safe_title = ep_title.replace(' ', '_')[:30]
        scripts_dir.joinpath(f"Ep{ep_num:02d}_{safe_title}_{timestamp}_original.txt").write_text(ep_script, encoding='utf-8')
        
        # TRANSLATE SCRIPT IF NOT ENGLISH
        target_language = config.get("voice", {}).get("language", "en")
        voice_text = ep_script
        if target_language != "en":
            print_info(f"Translating script to {target_language} via NLLB-200...")
            nllb_lang = "1" if target_language == "te" else "1"
            try:
                voice_text = translate_script_nllb(ep_script, nllb_lang)
                print_success("Translation completed!")
                translated_path = temp_dir / "script_translated.txt"
                translated_path.write_text(voice_text, encoding='utf-8')
                
                # Save persistent translated script
                scripts_dir.joinpath(f"Ep{ep_num:02d}_{safe_title}_{timestamp}_translated.txt").write_text(voice_text, encoding='utf-8')
            except Exception as e:
                print_error(f"Translation failed: {e}")
                print_error("Skipping this episode (Telugu TTS needs translated text).")
                continue
        
        # Voice
        print_info("Generating voiceover...")
        audio_path = str(temp_dir / "voiceover.wav")
        result = synthesize_speech(
            text=voice_text,
            output_path=audio_path,
            speaker_id=speaker_id,
            config=config,
        )
        
        if not result:
            print_error(f"Voice synthesis failed for episode {ep_num}!")
            continue
        
        audio_duration = get_audio_duration(audio_path)
        print_success(f"Audio: {audio_duration:.1f}s")
        
        # Parse & keyword extract
        print_info("Extracting keywords...")
        sentences = split_text_to_sentences(ep_script)
        timings = estimate_sentence_timings(sentences, audio_duration)
        search_queries = extract_search_queries(timings, topic=ep_title, config=config)
        
        # Scrape images
        print_info("Scraping images...")
        images_dir = str(temp_dir / "images")
        image_map = scrape_images_for_video(
            search_queries=search_queries,
            output_dir=images_dir,
            config=config,
        )
        
        total_images = sum(len(imgs) for imgs in image_map.values())
        print_success(f"Downloaded {total_images} images")
        
        # Compose video
        print_info("Composing video...")
        output_filename = f"{safe_topic}_EP{ep_num:02d}_{timestamp}.mp4"
        output_path = str(series_dir / output_filename)
        
        # Pick animation style for this episode
        if animation_style == "random_mix":
            ep_style = random.choice([s[0] for s in ANIMATION_STYLES if s[0] != "random_mix"])
        else:
            ep_style = animation_style
        
        video_path = compose_video(
            script_text=ep_script,
            audio_path=audio_path,
            sentence_timings=timings,
            image_map=image_map,
            output_path=output_path,
            config=config,
            animation_style=ep_style,
        )
        
        if video_path:
            completed_videos.append(video_path)
            print_success(f"Episode {ep_num} saved: {video_path}")
        else:
            print_error(f"Episode {ep_num} failed!")
        
        # Cleanup temp
        if not config.get("output", {}).get("keep_temp_files", False):
            try:
                shutil.rmtree(str(temp_dir))
            except Exception:
                pass
    
    print_section("📊 SERIES COMPLETE")
    print_success(f"Generated {len(completed_videos)}/{num_videos} videos")
    print_info(f"Output directory: {series_dir}")
    
    for v in completed_videos:
        print(f"    📹 {Path(v).name}")
    
    return completed_videos


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point."""
    print_banner()
    
    # Load config
    config = load_config()
    print_success("Configuration loaded")
    
    # Main menu
    print_section("🎯 WHAT DO YOU WANT TO CREATE?")
    
    options = [
        "Single Video - Generate one reel",
        "Video Series - Generate multiple episode reels",
        "Exit",
    ]
    
    choice = get_choice("Select mode", options)
    
    if choice == 1:
        result = generate_single_video(config)
        if result:
            print_section("🎉 DONE!")
            print_success(f"Your reel is ready: {result}")
            print_info("Upload it to Instagram/YouTube Shorts/TikTok!")
        else:
            print_error("Video generation failed. Check logs for details.")
    
    elif choice == 2:
        results = generate_series(config)
        if results:
            print_section("🎉 SERIES COMPLETE!")
            print_success(f"{len(results)} reels generated!")
        else:
            print_error("Series generation failed. Check logs for details.")
    
    elif choice == 3:
        print("\n  Goodbye! 👋\n")
        sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Interrupted by user. Goodbye! 👋\n")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n  ✗ Fatal error: {e}")
        print("  Check reel_generator.log for details")
        sys.exit(1)
