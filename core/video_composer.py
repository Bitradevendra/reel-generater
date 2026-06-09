"""
Video Composer - Assembles the final reel video from:
- Background image
- Scraped images (with animations)
- Audio voiceover
- Subtitles (word-by-word karaoke)

Uses Pillow for frame rendering and MoviePy for video assembly.
"""

import os
import math
import random
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.resolve()


# ============================================================================
# IMAGE PROCESSING UTILITIES
# ============================================================================

def _load_and_resize_background(bg_path: str, width: int, height: int, config: Dict) -> Image.Image:
    """Load background image, resize to fill, apply effects."""
    bg_cfg = config.get("background", {})
    
    img = Image.open(bg_path).convert("RGB")
    
    # Resize to fill (cover mode)
    img_ratio = img.width / img.height
    target_ratio = width / height
    
    if img_ratio > target_ratio:
        # Image is wider proportionally
        new_height = height
        new_width = int(height * img_ratio)
    else:
        new_width = width
        new_height = int(width / img_ratio)
    
    img = img.resize((new_width, new_height), Image.LANCZOS)
    
    # Center crop
    left = (new_width - width) // 2
    top = (new_height - height) // 2
    img = img.crop((left, top, left + width, top + height))
    
    # Apply blur
    blur_radius = bg_cfg.get("blur_radius", 3)
    if blur_radius > 0:
        img = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    
    # Apply brightness
    brightness = bg_cfg.get("brightness", 0.85)
    if brightness < 1.0:
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(brightness)
    
    # Apply dark overlay
    overlay_color = tuple(bg_cfg.get("overlay_color", [0, 0, 0]))
    overlay_opacity = bg_cfg.get("overlay_opacity", 0.25)
    if overlay_opacity > 0:
        overlay = Image.new("RGBA", (width, height), overlay_color + (int(255 * overlay_opacity),))
        img = img.convert("RGBA")
        img = Image.alpha_composite(img, overlay)
        img = img.convert("RGB")
    
    return img


def _prepare_content_image(
    img_path: str,
    max_w: int,
    max_h: int,
    min_w: int,
    corner_radius: int = 20,
    border_width: int = 4,
    border_color: Tuple = (255, 255, 255),
) -> Optional[Image.Image]:
    """Load, resize, and style a content image."""
    try:
        img = Image.open(img_path).convert("RGBA")
    except Exception as e:
        logger.warning(f"[Composer] Cannot open image {img_path}: {e}")
        return None
    
    # Calculate target size preserving aspect ratio
    img_ratio = img.width / img.height
    target_w = min(max_w, int(max_h * img_ratio))
    target_h = min(max_h, int(max_w / img_ratio))
    
    # Enforce minimum
    target_w = max(target_w, min_w)
    target_h = max(target_h, int(min_w / img_ratio)) if img_ratio > 0 else target_h
    
    img = img.resize((target_w, target_h), Image.LANCZOS)
    
    # Apply rounded corners
    if corner_radius > 0:
        mask = Image.new("L", (target_w, target_h), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle(
            [0, 0, target_w - 1, target_h - 1],
            radius=corner_radius,
            fill=255,
        )
        img.putalpha(mask)
    
    # Add border
    if border_width > 0:
        bordered_w = target_w + 2 * border_width
        bordered_h = target_h + 2 * border_width
        bordered = Image.new("RGBA", (bordered_w, bordered_h), (0, 0, 0, 0))
        
        # Draw border with rounded corners
        border_draw = ImageDraw.Draw(bordered)
        border_draw.rounded_rectangle(
            [0, 0, bordered_w - 1, bordered_h - 1],
            radius=corner_radius + border_width,
            fill=border_color + (255,),
        )
        
        # Paste image on top of border
        bordered.paste(img, (border_width, border_width), img)
        img = bordered
    
    return img


def _add_shadow(
    base: Image.Image,
    content_img: Image.Image,
    x: int,
    y: int,
    shadow_offset: Tuple[int, int] = (6, 6),
    shadow_color: Tuple[int, int, int] = (0, 0, 0),
    shadow_opacity: float = 0.5,
    shadow_blur: int = 15,
) -> Image.Image:
    """Add drop shadow behind content image."""
    shadow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    
    # Create shadow shape
    shadow_img = Image.new("RGBA", content_img.size,
                           shadow_color + (int(255 * shadow_opacity),))
    
    if content_img.mode == 'RGBA':
        shadow_img.putalpha(content_img.split()[-1])
    
    shadow.paste(shadow_img, (x + shadow_offset[0], y + shadow_offset[1]), shadow_img)
    
    # Blur shadow
    if shadow_blur > 0:
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=shadow_blur))
    
    # Composite: background -> shadow -> image
    if base.mode != 'RGBA':
        base = base.convert('RGBA')
    
    base = Image.alpha_composite(base, shadow)
    
    return base


# ============================================================================
# ANIMATION FUNCTIONS
# ============================================================================

def _apply_ken_burns(
    img: Image.Image,
    progress: float,
    config: Dict,
) -> Image.Image:
    """Apply Ken Burns (slow zoom + pan) effect."""
    style_cfg = config.get("animations", {}).get("styles", {}).get("ken_burns", {})
    zoom_start = style_cfg.get("zoom_start", 1.0)
    zoom_end = style_cfg.get("zoom_end", 1.15)
    pan_range = style_cfg.get("pan_range", 0.05)
    
    # Interpolate zoom
    zoom = zoom_start + (zoom_end - zoom_start) * progress
    
    # Pan direction (use hash of image size as seed for consistency)
    pan_x = math.sin(progress * math.pi) * pan_range
    pan_y = math.cos(progress * math.pi * 0.5) * pan_range * 0.5
    
    w, h = img.size
    new_w = int(w * zoom)
    new_h = int(h * zoom)
    
    img_zoomed = img.resize((new_w, new_h), Image.LANCZOS)
    
    # Calculate crop for pan
    cx = int((new_w - w) / 2 + pan_x * w)
    cy = int((new_h - h) / 2 + pan_y * h)
    
    cx = max(0, min(cx, new_w - w))
    cy = max(0, min(cy, new_h - h))
    
    return img_zoomed.crop((cx, cy, cx + w, cy + h))


def _apply_fade_scale(
    img: Image.Image,
    progress: float,
    total_progress: float,
    config: Dict,
) -> Tuple[Image.Image, float]:
    """Apply fade-in with subtle scale effect. Returns (image, alpha)."""
    style_cfg = config.get("animations", {}).get("styles", {}).get("fade_scale", {})
    fade_dur = style_cfg.get("fade_duration", 0.5)
    scale_start = style_cfg.get("scale_start", 1.05)
    scale_end = style_cfg.get("scale_end", 1.0)
    
    # Fade in/out
    alpha = 1.0
    if progress < fade_dur:
        alpha = progress / fade_dur
    elif progress > (1.0 - fade_dur):
        alpha = (1.0 - progress) / fade_dur
    alpha = max(0.0, min(1.0, alpha))
    
    # Scale
    scale = scale_start + (scale_end - scale_start) * min(1.0, progress / 0.5)
    
    if abs(scale - 1.0) > 0.01:
        w, h = img.size
        new_w = int(w * scale)
        new_h = int(h * scale)
        img = img.resize((new_w, new_h), Image.LANCZOS)
        
        # Center crop back
        left = (new_w - w) // 2
        top = (new_h - h) // 2
        img = img.crop((left, top, left + w, top + h))
    
    return img, alpha


def _apply_slide_pop(
    x: int,
    y: int,
    img_w: int,
    screen_w: int,
    progress: float,
    direction: str,
    config: Dict,
) -> Tuple[int, int, float]:
    """Apply slide-in animation. Returns (x, y, alpha)."""
    style_cfg = config.get("animations", {}).get("styles", {}).get("slide_pop", {})
    slide_dur = style_cfg.get("slide_duration", 0.4)
    
    alpha = 1.0
    
    if progress < slide_dur:
        t = progress / slide_dur
        # Ease-out cubic
        t = 1 - (1 - t) ** 3
        
        if direction == "left":
            x = int(-img_w + (x + img_w) * t)
        elif direction == "right":
            x = int(screen_w - (screen_w - x) * t)
        
        alpha = t
    elif progress > (1.0 - slide_dur):
        t = (1.0 - progress) / slide_dur
        alpha = t
    
    return x, y, alpha


def _apply_cinematic(
    frame: Image.Image,
    progress: float,
    config: Dict,
) -> Image.Image:
    """Apply cinematic letterbox and vignette effect."""
    style_cfg = config.get("animations", {}).get("styles", {}).get("cinematic", {})
    letterbox = style_cfg.get("letterbox_ratio", 0.08)
    vignette = style_cfg.get("vignette_strength", 0.3)
    
    w, h = frame.size
    
    # Letterbox
    if letterbox > 0:
        bar_h = int(h * letterbox)
        draw = ImageDraw.Draw(frame)
        draw.rectangle([0, 0, w, bar_h], fill=(0, 0, 0))
        draw.rectangle([0, h - bar_h, w, h], fill=(0, 0, 0))
    
    # Vignette
    if vignette > 0:
        vignette_overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        vdraw = ImageDraw.Draw(vignette_overlay)
        
        cx, cy = w // 2, h // 2
        max_r = math.sqrt(cx ** 2 + cy ** 2)
        
        for i in range(20):
            r = max_r * (1 - i / 20)
            alpha = int(255 * vignette * (1 - i / 20) ** 2)
            vdraw.ellipse(
                [int(cx - r), int(cy - r), int(cx + r), int(cy + r)],
                fill=(0, 0, 0, alpha),
            )
        
        frame = frame.convert("RGBA")
        frame = Image.alpha_composite(frame, vignette_overlay)
        frame = frame.convert("RGB")
    
    return frame


# ============================================================================
# MAIN COMPOSER
# ============================================================================

def compose_video(
    script_text: str,
    audio_path: str,
    sentence_timings: List[Dict],
    image_map: Dict[int, List[str]],
    output_path: str,
    config: Dict,
    animation_style: str = "ken_burns",
) -> Optional[str]:
    """
    Compose the final reel video.
    
    Args:
        script_text: Full voiceover script
        audio_path: Path to WAV audio file
        sentence_timings: List of sentence timing dicts
        image_map: Dict mapping sentence index to image paths
        output_path: Path for output MP4 file
        config: Full config dict
        animation_style: Animation style name
        
    Returns:
        Path to output video, or None on failure
    """
    from moviepy import AudioFileClip, VideoClip
    from core.subtitle_engine import render_subtitle_frame
    
    video_cfg = config.get("video", {})
    img_cfg = config.get("images", {})
    
    width = video_cfg.get("width", 1080)
    height = video_cfg.get("height", 1920)
    fps = video_cfg.get("fps", 30)
    
    # Load audio
    try:
        audio_clip = AudioFileClip(audio_path)
        total_duration = audio_clip.duration
    except Exception as e:
        logger.error(f"[Composer] Cannot load audio: {e}")
        return None
    
    logger.info(f"[Composer] Audio duration: {total_duration:.1f}s")
    
    # Load background
    bg_path = config.get("background", {}).get("image_path", "background.jpeg")
    if not os.path.isabs(bg_path):
        bg_path = str(PROJECT_ROOT / bg_path)
    
    try:
        background = _load_and_resize_background(bg_path, width, height, config)
    except Exception as e:
        logger.warning(f"[Composer] Cannot load background: {e}, using solid color")
        background = Image.new("RGB", (width, height), (20, 20, 35))
    
    # Prepare content images
    max_img_w = int(width * img_cfg.get("max_width_ratio", 0.80))
    max_img_h = int(height * img_cfg.get("max_height_ratio", 0.45))
    min_img_w = int(width * img_cfg.get("min_width_ratio", 0.50))
    corner_radius = img_cfg.get("corner_radius", 20)
    border_width = img_cfg.get("border_width", 4)
    border_color = tuple(img_cfg.get("border_color", [255, 255, 255]))
    
    # Build timeline: which image shows when
    image_timeline = []  # List of (start, end, image_path) tuples
    
    for sent_idx, sent_data in enumerate(sentence_timings):
        images = image_map.get(sent_idx, [])
        if not images:
            continue
        
        sent_start = sent_data["start"]
        sent_end = sent_data["end"]
        sent_duration = sent_end - sent_start
        
        if sent_duration <= 0:
            continue
        
        # Distribute images across sentence duration
        time_per_image = sent_duration / len(images)
        
        # Enforce min/max display duration
        min_dur = img_cfg.get("display_duration_min", 2.5)
        max_dur = img_cfg.get("display_duration_max", 5.0)
        time_per_image = max(min_dur, min(max_dur, time_per_image))
        
        current_t = sent_start
        for img_path in images:
            end_t = min(current_t + time_per_image, sent_end)
            image_timeline.append({
                "start": current_t,
                "end": end_t,
                "path": img_path,
                "sentence_idx": sent_idx,
            })
            current_t = end_t
            if current_t >= sent_end:
                break
    
    # Pre-load and prepare content images
    prepared_images = {}
    for item in image_timeline:
        path = item["path"]
        if path not in prepared_images:
            prepared = _prepare_content_image(
                path, max_img_w, max_img_h, min_img_w,
                corner_radius, border_width, border_color,
            )
            prepared_images[path] = prepared
    
    logger.info(f"[Composer] Prepared {len(prepared_images)} unique images")
    logger.info(f"[Composer] Image timeline: {len(image_timeline)} slots")
    
    # Image position
    img_pos_x_ratio = img_cfg.get("position_x", 0.5)
    img_pos_y_ratio = img_cfg.get("position_y", 0.30)
    
    # Shadow config
    shadow_offset = tuple(img_cfg.get("shadow_offset", [6, 6]))
    shadow_color = tuple(img_cfg.get("shadow_color", [0, 0, 0]))
    shadow_opacity = img_cfg.get("shadow_opacity", 0.5)
    shadow_blur = img_cfg.get("shadow_blur", 15)
    
    # Transition
    transition_dur = img_cfg.get("transition_duration", 0.6)
    
    # Track direction for slide animations
    slide_directions = ["left", "right"]
    
    def make_frame(t):
        """Generate a single video frame at time t."""
        # Start with background copy
        frame = background.copy()
        
        # Find which image(s) to show at time t
        current_img_data = None
        prev_img_data = None
        
        for idx, item in enumerate(image_timeline):
            if item["start"] <= t < item["end"]:
                current_img_data = item
                if idx > 0:
                    prev_img_data = image_timeline[idx - 1]
                break
        
        # If no image at this time, check if we're in transition
        if current_img_data is None and image_timeline:
            # Find nearest future image
            for item in image_timeline:
                if item["start"] > t and item["start"] - t < transition_dur:
                    current_img_data = item
                    break
        
        if current_img_data:
            img_path = current_img_data["path"]
            content_img = prepared_images.get(img_path)
            
            if content_img:
                img_start = current_img_data["start"]
                img_end = current_img_data["end"]
                img_duration = img_end - img_start
                
                if img_duration > 0:
                    img_progress = (t - img_start) / img_duration
                    img_progress = max(0.0, min(1.0, img_progress))
                else:
                    img_progress = 0.5
                
                display_img = content_img.copy()
                alpha = 1.0
                
                # Apply animation based on style
                if animation_style == "ken_burns":
                    display_img = _apply_ken_burns(display_img, img_progress, config)
                
                elif animation_style == "fade_scale":
                    display_img, alpha = _apply_fade_scale(display_img, img_progress, img_progress, config)
                
                elif animation_style == "cinematic":
                    pass  # Cinematic applied to entire frame later
                
                # Crossfade transition
                if img_progress < transition_dur / max(img_duration, 0.01):
                    # Fade in
                    fade_progress = img_progress / (transition_dur / max(img_duration, 0.01))
                    alpha *= min(1.0, fade_progress)
                elif img_progress > 1.0 - transition_dur / max(img_duration, 0.01):
                    # Fade out
                    fade_progress = (1.0 - img_progress) / (transition_dur / max(img_duration, 0.01))
                    alpha *= min(1.0, fade_progress)
                
                # Calculate position
                img_w, img_h = display_img.size
                x = int(width * img_pos_x_ratio - img_w / 2)
                y = int(height * img_pos_y_ratio - img_h / 2)
                
                # Slide animation position adjustment
                if animation_style == "slide_pop":
                    sent_idx = current_img_data.get("sentence_idx", 0)
                    direction = slide_directions[sent_idx % 2]
                    x, y, alpha = _apply_slide_pop(x, y, img_w, width, img_progress, direction, config)
                
                # Clamp position
                x = max(-img_w // 2, min(width - img_w // 2, x))
                y = max(-img_h // 2, min(height - img_h // 2, y))
                
                # Add shadow
                frame = _add_shadow(
                    frame, display_img, x, y,
                    shadow_offset, shadow_color, shadow_opacity, shadow_blur,
                )
                
                # Composite image onto frame
                frame = frame.convert("RGBA")
                
                if alpha < 1.0:
                    # Apply alpha to content image
                    if display_img.mode == 'RGBA':
                        r, g, b, a = display_img.split()
                        a = a.point(lambda p: int(p * alpha))
                        display_img = Image.merge('RGBA', (r, g, b, a))
                    else:
                        display_img = display_img.convert("RGBA")
                        r, g, b, a = display_img.split()
                        a = a.point(lambda p: int(p * alpha))
                        display_img = Image.merge('RGBA', (r, g, b, a))
                
                if display_img.mode != 'RGBA':
                    display_img = display_img.convert("RGBA")
                
                frame.paste(display_img, (x, y), display_img)
                frame = frame.convert("RGB")
        
        # Apply cinematic effect to full frame
        if animation_style == "cinematic":
            frame = _apply_cinematic(frame, t / max(total_duration, 0.01), config)
        
        # Render subtitles
        current_sentence = None
        for sent_data in sentence_timings:
            if sent_data["start"] <= t < sent_data["end"]:
                current_sentence = sent_data
                break
        
        if current_sentence:
            frame = render_subtitle_frame(frame, current_sentence, t, config)
        
        # Convert to numpy array for MoviePy
        return np.array(frame)
    
    # Create video clip
    logger.info(f"[Composer] Rendering video at {width}x{height} @ {fps}fps...")
    logger.info(f"[Composer] Animation style: {animation_style}")
    
    try:
        video_clip = VideoClip(make_frame, duration=total_duration)
        video_clip = video_clip.with_fps(fps)
        video_clip = video_clip.with_audio(audio_clip)
        
        # Ensure output directory exists
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Write video
        video_clip.write_videofile(
            output_path,
            fps=fps,
            codec=video_cfg.get("codec", "libx264"),
            audio_codec=video_cfg.get("audio_codec", "aac"),
            bitrate=video_cfg.get("bitrate", "8000k"),
            logger="bar",
            threads=4,
        )
        
        video_clip.close()
        audio_clip.close()
        
        logger.info(f"[Composer] Original video saved: {output_path}")
        
        # Apply 1.25x speed conversion
        import subprocess
        from imageio_ffmpeg import get_ffmpeg_exe
        
        try:
            ffmpeg_exe = get_ffmpeg_exe()
            sped_up_path = output_path.replace(".mp4", "_1.25x.mp4")
            logger.info(f"[Composer] Converting to 1.25x speed...")
            
            cmd = [
                ffmpeg_exe, "-y",
                "-i", output_path,
                "-filter_complex", "[0:v]setpts=0.8*PTS[v];[0:a]atempo=1.25[a]",
                "-map", "[v]", "-map", "[a]",
                sped_up_path
            ]
            
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            logger.info(f"[Composer] Fast-paced video saved: {sped_up_path}")
            
            # Apply Oggy overlay
            overlay_path = str(Path("overlay/oggy.mp4").absolute())
            if Path(overlay_path).exists():
                logger.info(f"[Composer] Applying green screen overlay...")
                final_path = output_path.replace(".mp4", "_final.mp4")
                
                cmd_overlay = [
                    ffmpeg_exe, "-y",
                    "-i", sped_up_path,
                    "-stream_loop", "-1", "-i", overlay_path,
                    "-filter_complex",
                    "[1:v]colorkey=0x00FF00:0.3:0.2,scale=-1:700[oggy];[0:v][oggy]overlay=x=30:y=H-h-30:shortest=1[v]",
                    "-map", "[v]", "-map", "0:a",
                    final_path
                ]
                subprocess.run(cmd_overlay, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                logger.info(f"[Composer] Final video with overlay saved: {final_path}")
                return final_path
            
            return sped_up_path
            
        except Exception as speed_err:
            logger.error(f"[Composer] Speed conversion failed: {speed_err}")
            return output_path
        
    except Exception as e:
        logger.error(f"[Composer] Video rendering failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None
