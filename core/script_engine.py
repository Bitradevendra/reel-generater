"""
Script Engine - Wraps the script/ module for importable use.
Generates voiceover scripts using DeepSeek R1 GGUF model.

Priority chain:
  1. llama-cpp-python (native Python bindings, supports Qwen2)
  2. ctransformers (fallback, older models only)
  3. Ollama (external fallback)
"""

import os
import sys
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
SCRIPT_DIR = PROJECT_ROOT / "script"


def _calculate_tokens(duration: int, words_per_second: float = 2.2) -> int:
    """Calculate approximate tokens from duration."""
    return int(duration * words_per_second * 1.3)


def _build_prompt(topic: str, content_type: str, duration: int, audience: str, language: str = "en") -> str:
    """Build the generation prompt with audience-specific adjustments."""
    audience_guidance = {
        "engineers": "Professional, exam-focused, practical insights. Explain with real-world applications and technical depth.",
        "common": "Simple, clear, easy to understand. Avoid jargon. Explain like talking to a friend.",
        "kids": "Very simple, friendly tone. Use easy words. Make it fun and engaging.",
    }
    guidance = audience_guidance.get(audience, audience_guidance["common"])

    return f"""You are a high-performance short-form content generator.

Your task is to generate ONLY a clean voiceover text for reels.

INPUT:
Topic: {topic}
Content Type: {content_type}
Duration: {duration} seconds
Target Audience: {audience}

STRICT RULES:
Output ONLY the final spoken script.
No sections or headings
No scene breakdown
No markdown symbols like --- or ###

CRITICAL PUNCTUATION RULES (the Voice Engine needs these to sound human):
- Every sentence MUST end with a period, question mark, or exclamation mark.
- Use commas frequently. Add a comma every 5-7 words to create natural breathing pauses.
- Use "..." (three dots) for dramatic pauses. Example: "And the answer... is surprising."
- Use short sentences. Maximum 12 words per sentence. Break long ideas into 2-3 short sentences.
- Use question marks to create curiosity. Example: "But why? Because it changes everything."
- Use exclamation marks sparingly for emphasis. Example: "That's insane!"
- NEVER write a wall of text without punctuation. Every phrase needs a comma or period.

GOOD EXAMPLE (notice the pauses):
"Have you ever wondered... why bananas are yellow? It's not what you think. See, bananas contain a pigment, called carotenoid. And when they ripen, the green chlorophyll breaks down. What's left... is that bright yellow color. Pretty cool, right?"

BAD EXAMPLE (no pauses, robotic):
"Bananas are yellow because they contain carotenoid pigments and when they ripen the chlorophyll breaks down leaving the yellow color visible"

OUTPUT REQUIREMENTS:
Text must be ready for Text-to-Speech and subtitles
Use natural, conversational speaking style
Keep sentences SHORT (5-12 words each)
Make it engaging and viral

LENGTH CONTROL:
Use ~2.2 words per second
For {duration} seconds, generate approximately {int(duration * 2.2)} words.

CONTENT STRUCTURE (HIDDEN):
Start with strong hook (a question or surprising fact)
Introduce topic quickly
Explain clearly with pauses
End with punch or CTA

TONE & STYLE:
{guidance}

ENGAGEMENT RULES:
First line must create curiosity
Use "you" to connect with the viewer
Ask rhetorical questions to keep attention
Avoid boring openings

FINAL RULE:
Return ONLY the final text. Nothing else."""


def _clean_output(text: str) -> str:
    """Clean and format the LLM output."""
    import re
    text = text.strip()

    # Remove thinking/reasoning text (DeepSeek R1 specific)
    if "</think>" in text:
        text = text.split("</think>")[-1].strip()
    elif "<think>" in text:
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
        
    if "...done thinking." in text:
        text = text.split("...done thinking.")[-1].strip()
        
    # Nuke common conversational leaks just in case
    text = re.sub(r"^(Okay, let's see\.|Here is the|Here's a|The user wants).*?(\n\n|$)", "", text, flags=re.IGNORECASE | re.DOTALL).strip()

    # Remove any remaining thinking prefixes
    if text.startswith("Thinking..."):
        lines = text.split('\n')
        for i, line in enumerate(lines):
            stripped = line.strip()
            if (not stripped.startswith("Thinking") and
                not stripped.startswith("The user") and
                not stripped.startswith("I'm") and
                not stripped.startswith("For") and
                not stripped.startswith("Engineers") and i > 0):
                text = '\n'.join(lines[i:])
                break

    # Remove markdown formatting
    text = re.sub(r'\*\*|__|##|###', '', text)
    text = re.sub(r'^\s*[-*]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)

    # Join into single paragraph
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    text = ' '.join(lines)

    # Fix multiple spaces
    while '  ' in text:
        text = text.replace('  ', ' ')

    return text.strip()


# ============================================================================
# METHOD 1: llama-cpp-python (Primary - supports Qwen2/DeepSeek R1)
# ============================================================================

def _generate_via_llama_cpp(prompt: str, model_path: str, tokens: int, config: Dict) -> Optional[str]:
    """Generate using llama-cpp-python (native bindings for llama.cpp)."""
    try:
        from llama_cpp import Llama

        script_cfg = config.get("script", {})

        logger.info(f"[Script] Loading model via llama-cpp-python: {Path(model_path).name}")

        llm = Llama(
            model_path=model_path,
            n_ctx=2048,
            n_threads=script_cfg.get("threads", 8),
            n_gpu_layers=script_cfg.get("gpu_layers", 50),
            verbose=False,
        )

        output = llm.create_chat_completion(
            messages=[
                {"role": "system", "content": "You are an expert video script writer. You MUST do all your reasoning inside <think> tags first. After the </think> tag, you must output ONLY the final spoken script exactly as it will be spoken IN ENGLISH. Do NOT say 'Here is the script'. Begin the script immediately after the think tag."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=min(tokens, 1500),
            temperature=script_cfg.get("temperature", 0.8),
            top_p=script_cfg.get("top_p", 0.9),
            repeat_penalty=script_cfg.get("repetition_penalty", 1.1),
        )

        # Extract text from response
        if output and "choices" in output:
            text = output["choices"][0]["message"].get("content", "").strip()
            if text:
                return text

        logger.warning("[Script] llama-cpp-python returned empty output")
        return None

    except ImportError:
        logger.info("[Script] llama-cpp-python not installed")
        return None
    except Exception as e:
        logger.warning(f"[Script] llama-cpp-python error: {e}")
        return None


# ============================================================================
# METHOD 2: ctransformers (fallback)
# ============================================================================

def _generate_via_ctransformers(prompt: str, model_path: str, tokens: int, config: Dict) -> Optional[str]:
    """Generate using ctransformers (older, may not support Qwen2)."""
    try:
        from ctransformers import AutoModelForCausalLM

        script_cfg = config.get("script", {})

        logger.info(f"[Script] Loading model via ctransformers: {Path(model_path).name}")
        llm = AutoModelForCausalLM.from_pretrained(
            model_path,
            model_type=script_cfg.get("model_type", "qwen2"),
            gpu_layers=script_cfg.get("gpu_layers", 50),
            threads=script_cfg.get("threads", 8),
        )

        output = llm(
            prompt,
            max_new_tokens=min(tokens, 1500),
            temperature=script_cfg.get("temperature", 0.8),
            top_p=script_cfg.get("top_p", 0.9),
            repetition_penalty=script_cfg.get("repetition_penalty", 1.1),
            stream=False,
        )

        if output and output.strip():
            return output.strip()

        return None

    except ImportError:
        logger.info("[Script] ctransformers not installed")
        return None
    except Exception as e:
        logger.warning(f"[Script] ctransformers error: {e}")
        return None


# ============================================================================
# METHOD 3: llama-cli (Local Executable)
# ============================================================================

def _generate_via_llama_cli(prompt: str, model_path: str, tokens: int, config: Dict) -> Optional[str]:
    """Generate using compiled llama.cpp executable (llama-cli.exe/main.exe)."""
    import subprocess
    
    script_cfg = config.get("script", {})
    threads = script_cfg.get("threads", 8)
    
    # Check for executable
    cli_paths = [
        PROJECT_ROOT / "script" / "llama.cpp" / "build" / "bin" / "Release" / "llama-cli.exe",
        PROJECT_ROOT / "script" / "llama.cpp" / "build" / "bin" / "Release" / "main.exe",
        PROJECT_ROOT / "script" / "llama-cli.exe",
        PROJECT_ROOT / "script" / "main.exe",
    ]
    
    cli_exe = None
    for p in cli_paths:
        if p.exists():
            cli_exe = str(p)
            break
            
    if not cli_exe:
        logger.info("[Script] llama-cli executable not found")
        return None
        
    logger.info(f"[Script] Using llama-cli executable: {Path(cli_exe).name}")
    
    cmd = [
        cli_exe,
        "-m", model_path,
        "-p", prompt,
        "-n", str(min(tokens, 1500)),
        "-c", "2048",
        "-t", str(threads),
        "--temp", str(script_cfg.get("temperature", 0.8)),
        "--top-p", str(script_cfg.get("top_p", 0.9)),
        "--repeat-penalty", str(script_cfg.get("repetition_penalty", 1.1)),
        "--log-disable"
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=1200, # 20 mins max
            encoding='utf-8'
        )
        if result.returncode == 0 and result.stdout:
            # Llama-cli outputs the prompt + response, so we need to grab the response
            out = result.stdout
            if prompt in out:
                out = out.split(prompt)[-1]
            return out.strip()
            
        logger.warning(f"[Script] llama-cli failed (code {result.returncode}): {result.stderr[:200]}")
    except Exception as e:
        logger.warning(f"[Script] llama-cli error: {e}")
        
    return None

# ============================================================================
# METHOD 4: Ollama (external fallback)
# ============================================================================

def _generate_via_ollama(prompt: str, config: Dict) -> Optional[str]:
    """Generate using Ollama CLI (requires Ollama running)."""
    import subprocess

    script_cfg = config.get("script", {})

    try:
        logger.info("[Script] Trying Ollama fallback...")
        result = subprocess.run(
            ["ollama", "run", script_cfg.get("ollama_model", "deepseek-r1"), prompt],
            capture_output=True,
            text=True,
            timeout=script_cfg.get("ollama_timeout", 600),
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except FileNotFoundError:
        logger.warning("[Script] Ollama not installed")
    except Exception as e:
        logger.warning(f"[Script] Ollama error: {e}")

    return None


# ============================================================================
# MAIN GENERATOR
# ============================================================================

def generate_script(
    topic: str,
    content_type: str = "educational",
    duration: int = 60,
    audience: str = "common",
    language: str = "en",
    config: Optional[Dict[str, Any]] = None,
    max_retries: int = 3,
) -> Optional[str]:
    """
    Generate a voiceover script for the given topic.

    Tries these methods in order:
      1. llama-cpp-python (best Qwen2 support)
      2. ctransformers (fallback)
      3. Ollama (external service)

    Args:
        topic: The topic to generate a script about
        content_type: "technology", "funny", "professional", or "educational"
        duration: Target duration in seconds
        audience: "engineers", "common", or "kids"
        config: Optional config dict with model params
        max_retries: Number of retry attempts

    Returns:
        Generated script text, or None on failure
    """
    if config is None:
        config = {}

    script_cfg = config.get("script", {})
    model_path = script_cfg.get("model_path", str(SCRIPT_DIR / "model.gguf"))

    # Resolve relative paths against project root
    if not os.path.isabs(model_path):
        model_path = str(PROJECT_ROOT / model_path)

    prompt = _build_prompt(topic, content_type, duration, audience, language)
    tokens = _calculate_tokens(duration, script_cfg.get("words_per_second", 2.2))

    for attempt in range(1, max_retries + 1):
        logger.info(f"[Script] Attempt {attempt}/{max_retries} - Generating script for: {topic}")

        if os.path.exists(model_path):
            # Method 1: llama-cpp-python (primary)
            output = _generate_via_llama_cpp(prompt, model_path, tokens, config)
            if output:
                cleaned = _clean_output(output)
                if cleaned and len(cleaned) > 20:
                    logger.info(f"[Script] Generated {len(cleaned.split())} words via llama-cpp-python")
                    return cleaned
                logger.warning("[Script] llama-cpp-python output too short")

            # Method 2: ctransformers (fallback 1)
            output = _generate_via_ctransformers(prompt, model_path, tokens, config)
            if output:
                cleaned = _clean_output(output)
                if cleaned and len(cleaned) > 20:
                    logger.info(f"[Script] Generated {len(cleaned.split())} words via ctransformers")
                    return cleaned
                logger.warning("[Script] ctransformers output too short")
                
            # Method 3: llama-cli executable (fallback 2)
            output = _generate_via_llama_cli(prompt, model_path, tokens, config)
            if output:
                cleaned = _clean_output(output)
                if cleaned and len(cleaned) > 20:
                    logger.info(f"[Script] Generated {len(cleaned.split())} words via llama-cli")
                    return cleaned
                logger.warning("[Script] llama-cli output too short")
        else:
            logger.warning(f"[Script] Model not found: {model_path}")

        # Method 4: Ollama (external)
        if script_cfg.get("ollama_fallback", True):
            output = _generate_via_ollama(prompt, config)
            if output:
                cleaned = _clean_output(output)
                if cleaned and len(cleaned) > 20:
                    logger.info(f"[Script] Generated {len(cleaned.split())} words via Ollama")
                    return cleaned

        # Exponential backoff between retries
        if attempt < max_retries:
            delay = 2 ** attempt
            logger.info(f"[Script] Retrying in {delay}s...")
            time.sleep(delay)

    logger.error(f"[Script] Failed to generate script after {max_retries} attempts")
    return None


def generate_series_scripts(
    topic: str,
    num_videos: int,
    duration_per_video: int = 60,
    content_type: str = "educational",
    audience: str = "common",
    config: Optional[Dict[str, Any]] = None,
) -> list:
    """
    Generate scripts for a video series.
    Each episode covers a different aspect of the topic.

    Returns:
        List of (episode_title, script_text) tuples
    """
    scripts = []

    subtopics = []

    # Try to generate sub-topics via LLM
    try:
        raw = generate_script(
            topic=f"Generate {num_videos} sub-topics for: {topic}",
            content_type=content_type,
            duration=30,
            audience=audience,
            config=config,
        )
        if raw:
            import re
            lines = raw.strip().split('\n')
            for line in lines:
                line = line.strip()
                match = re.match(r'^\d+[.\)]\s*(.+)', line)
                if match:
                    subtopics.append(match.group(1).strip())
    except Exception as e:
        logger.warning(f"[Script] Failed to generate sub-topics: {e}")

    # Fallback: generate simple numbered episodes
    if len(subtopics) < num_videos:
        subtopics = [f"{topic} - Part {i+1}" for i in range(num_videos)]

    # Generate script for each sub-topic
    for i, subtopic in enumerate(subtopics[:num_videos]):
        logger.info(f"[Script] Generating episode {i+1}/{num_videos}: {subtopic}")

        script = generate_script(
            topic=subtopic,
            content_type=content_type,
            duration=duration_per_video,
            audience=audience,
            config=config,
        )

        if script:
            scripts.append((subtopic, script))
        else:
            logger.error(f"[Script] Failed to generate episode {i+1}")
            scripts.append((subtopic, f"Let's explore {subtopic}. This is a fascinating topic that will change how you think."))

    return scripts
