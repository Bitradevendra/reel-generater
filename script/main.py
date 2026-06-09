#!/usr/bin/env python3

import os
import sys

# Fix encoding for Windows
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def check_and_install_llama_cpp():
    """Check and install ctransformers (simpler, pre-built)"""
    try:
        import ctransformers
        return True
    except ImportError:
        print("[+] Installing ctransformers (no compilation needed)...")
        import subprocess
        try:
            result = subprocess.run([
                sys.executable, "-m", "pip", "install",
                "ctransformers",
                "--only-binary=:all:",
                "-q"
            ], timeout=300)
            if result.returncode == 0:
                print("[+] Installation complete!\n")
                return True
            else:
                print("[-] Failed to install ctransformers")
                print("[*] Trying ollama as alternative...")
                return check_ollama()
        except Exception as e:
            print(f"[-] Error: {e}")
            return False

def check_ollama():
    """Check if ollama is available"""
    import subprocess
    try:
        result = subprocess.run(["ollama", "--version"], capture_output=True, timeout=5)
        return result.returncode == 0
    except:
        return False

def calculate_tokens(duration):
    """Calculate approximate number of tokens based on duration"""
    # ~2.2 words per second, ~1.3 tokens per word
    return int(duration * 2.2 * 1.3)

def build_prompt(topic, content_type, duration, audience):
    """Build the generation prompt with audience-specific adjustments"""
    
    audience_guidance = {
        "engineers": "Professional, exam-focused, practical insights. Explain with real-world applications and technical depth.",
        "common": "Simple, clear, easy to understand. Avoid jargon. Explain like talking to a friend.",
        "kids": "Very simple, friendly tone. Use easy words. Make it fun and engaging."
    }
    
    guidance = audience_guidance.get(audience, audience_guidance["common"])
    
    prompt = f"""You are a high-performance short-form content generator.

Your task is to generate ONLY a clean voiceover text for reels.

INPUT:
Topic: {topic}
Content Type: {content_type}
Duration: {duration} seconds
Target Audience: {audience}

STRICT RULES:
Output ONLY one continuous text
No sections
No labels
No headings
No explanations
No scene breakdown
No extra formatting
No symbols like --- or ###

OUTPUT REQUIREMENTS:
Text must be ready for Text-to-Speech and subtitles
Use natural speaking style
Add commas and small pauses for human-like speaking
Keep sentences short and clear
Make it engaging and viral

LENGTH CONTROL:
Use ~2.2 words per second

CONTENT STRUCTURE (HIDDEN):
Start with strong hook
Introduce topic quickly
Explain clearly
End with punch or CTA

TONE & STYLE:
{guidance}

ENGAGEMENT RULES:
First line must create curiosity
Use "you" to connect
Avoid boring openings

FINAL RULE:
Return ONLY the final text. Nothing else."""
    
    return prompt

def run_generation(topic, content_type, duration, audience):
    """Run the generation using ctransformers"""
    
    prompt = build_prompt(topic, content_type, duration, audience)
    tokens = calculate_tokens(int(duration))
    
    model_name = "model.gguf"
    
    # Check if model exists
    if not os.path.exists(model_name):
        print(f"[-] Error: {model_name} not found in current directory")
        print("[*] Download from: https://huggingface.co/bartowski/deepseek-r1-distill-qwen-7b-gguf")
        return None
    
    print(f"[+] Loading model: {model_name}")
    print(f"[+] Generating for: {topic}")
    print(f"[+] Type: {content_type} | Duration: {duration}s | Audience: {audience}")
    print("[*] Processing...\n")
    
    try:
        from ctransformers import AutoModelForCausalLM
        
        # Load model
        llm = AutoModelForCausalLM.from_pretrained(
            model_name,
            model_type="qwen",
            gpu_layers=50,
            threads=8
        )
        
        # Generate
        output = llm(
            prompt,
            max_new_tokens=min(tokens, 1500),
            temperature=0.8,
            top_p=0.9,
            repetition_penalty=1.1,
            stream=False
        )
        
        return output.strip()
    
    except Exception as e:
        print(f"[-] Error: {e}")
        print("[*] Trying ollama fallback...")
        
        try:
            import subprocess
            result = subprocess.run(
                ["ollama", "run", "deepseek-r1", prompt],
                capture_output=True,
                text=True,
                timeout=600
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        
        return None

def clean_output(text):
    """Clean and format the output"""
    text = text.strip()
    
    # Remove thinking/reasoning text (keep only the final explanation)
    if "...done thinking." in text:
        # Extract only the text after the thinking is done
        text = text.split("...done thinking.")[-1].strip()
    
    # Remove any remaining "Thinking..." prefixes
    if text.startswith("Thinking..."):
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if not line.strip().startswith("Thinking") and not line.strip().startswith("The user") and not line.strip().startswith("I'm") and not line.strip().startswith("For") and not line.strip().startswith("Engineers") and i > 0:
                text = '\n'.join(lines[i:])
                break
    
    # Ensure it's a single paragraph
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    text = ' '.join(lines)
    
    # Fix multiple spaces
    while '  ' in text:
        text = text.replace('  ', ' ')
    
    return text.strip()

def save_output(text):
    """Save output to outputs/final.txt"""
    os.makedirs("outputs", exist_ok=True)
    
    output_path = os.path.join("outputs", "final.txt")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(text)
    
    print(f"[+] Output saved to: {output_path}\n")

def main():
    """Main execution"""
    print("=" * 60)
    print("[*] REEL SCRIPT GENERATOR")
    print("=" * 60)
    print()
    
    # Check dependencies
    if not check_and_install_llama_cpp():
        print("\n[-] Cannot proceed without dependencies")
        print("[*] Try installing: pip install ctransformers --only-binary=:all:")  
        print("[*] Or use Ollama: https://ollama.ai")
        return
    
    print()
    
    # Get topic
    topic = input("Enter topic: ").strip()
    if not topic:
        print("[-] Error: Topic cannot be empty")
        return
    
    # Content type menu
    print("\n[*] SELECT CONTENT TYPE:")
    content_types = ["technology", "funny", "professional", "educational"]
    for i, ct in enumerate(content_types, 1):
        print(f"  {i}. {ct}")
    
    while True:
        try:
            choice = int(input("Enter choice (1-4): ").strip())
            if 1 <= choice <= 4:
                content_type = content_types[choice - 1]
                break
            else:
                print("[-] Invalid choice. Enter 1-4")
        except ValueError:
            print("[-] Invalid input. Enter a number")
    
    # Duration
    print()
    try:
        duration = int(input("Enter duration (seconds): ").strip())
        if duration <= 0:
            print("[-] Error: Duration must be positive")
            return
    except ValueError:
        print("[-] Error: Duration must be a number")
        return
    
    # Audience menu
    print("\n[*] SELECT TARGET AUDIENCE:")
    audiences = ["engineers", "common", "kids"]
    audience_desc = ["Professional, exam-focused, technical", "Simple, clear, everyday language", "Very simple, friendly, easy words"]
    for i, (aud, desc) in enumerate(zip(audiences, audience_desc), 1):
        print(f"  {i}. {aud.capitalize()} - {desc}")
    
    while True:
        try:
            choice = int(input("Enter choice (1-3): ").strip())
            if 1 <= choice <= 3:
                audience = audiences[choice - 1]
                break
            else:
                print("[-] Invalid choice. Enter 1-3")
        except ValueError:
            print("[-] Invalid input. Enter a number")
    
    print()
    
    # Generate content
    output = run_generation(topic, content_type, duration, audience)
    
    if output:
        # Clean output
        cleaned = clean_output(output)
        
        # Save to file
        save_output(cleaned)
        
        # Print to console
        print("[*] GENERATED TEXT:")
        print("-" * 60)
        print(cleaned)
        print("-" * 60)
    else:
        print("[-] Failed to generate content")

if __name__ == "__main__":
    main()
