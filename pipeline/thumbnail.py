#!/usr/bin/env python3
"""
ZeroSec AI Thumbnail Engine - Phase 5
Generates 3 high-contrast, clickable 1280x720 thumbnail variants using Pillow (PIL).
Enforces:
- 1280x720 exact dimensions
- 4-word punchy headline in bold typography
- High contrast: Dark terminal background with neon accent (#00FF9D / #38BDF8 / #FF4D4D)
- Focal UI element: Terminal box, security badge, shield glyph
"""

import os
import sys
import argparse
from PIL import Image, ImageDraw, ImageFont

def get_font(size):
    # Try DejaVu Sans Bold or Fallback
    font_paths = [
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf"
    ]
    for p in font_paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()

def create_thumbnail_variant(output_path, headline_words, badge_text, badge_color, border_color):
    width, height = 1280, 720
    im = Image.new("RGB", (width, height), color="#0D1117")
    draw = ImageDraw.Draw(im)

    # Outer border accent
    draw.rectangle([0, 0, width - 1, height - 1], outline=border_color, width=12)

    # Background card / terminal window mock
    draw.rectangle([60, 60, width - 60, height - 60], fill="#161B22", outline="#30363D", width=2)
    # Terminal top bar
    draw.rectangle([60, 60, width - 60, 120], fill="#21262D")
    # Window controls
    draw.ellipse([85, 82, 105, 102], fill="#FF5F56")
    draw.ellipse([115, 82, 135, 102], fill="#FFBD2E")
    draw.ellipse([145, 82, 165, 102], fill="#27C93F")

    font_label = get_font(24)
    draw.text((185, 80), "ZeroSec AI // Defensive Security Lab", fill="#8B949E", font=font_label)

    # Category Badge
    font_badge = get_font(32)
    draw.rectangle([100, 160, 480, 225], fill=badge_color)
    draw.text((120, 172), badge_text.upper(), fill="#0D1117", font=font_badge)

    # 4-Word Large Impact Headline (Split into 2 lines)
    font_head = get_font(84)
    line1 = " ".join(headline_words[:2])
    line2 = " ".join(headline_words[2:])

    # Text shadows for maximum readability on mobile
    draw.text((104, 274), line1, fill="#000000", font=font_head)
    draw.text((100, 270), line1, fill="#FFFFFF", font=font_head)

    draw.text((104, 384), line2, fill="#000000", font=font_head)
    draw.text((100, 380), line2, fill=border_color, font=font_head)

    # Code / Exploit visualization card on right side
    draw.rectangle([780, 200, 1180, 620], fill="#0A0D12", outline="#30363D", width=2)
    font_code = get_font(22)
    draw.text((810, 230), "$ cat config/rails.co", fill="#8B949E", font=font_code)
    draw.text((810, 280), "define flow check input", fill="#38BDF8", font=font_code)
    draw.text((810, 330), "  $is_safe = run detector", fill="#F0F6FC", font=font_code)
    draw.text((810, 380), "  if not $is_safe", fill="#F59E0B", font=font_code)
    draw.text((810, 430), "    bot refuse execution", fill="#FF4D4D", font=font_code)
    draw.rectangle([810, 500, 1150, 580], fill="#1F242C")
    draw.text((830, 525), "[BLOCK] ZERO LEAKS", fill="#00FF9D", font=get_font(28))

    # Save PNG
    im.save(output_path, "PNG")
    print(f"[SUCCESS] Thumbnail generated -> {output_path}")
    return output_path

def generate_thumbnails(slug="prevent-prompt-injection-langchain-nemo"):
    build_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "build", slug))
    os.makedirs(build_dir, exist_ok=True)

    variants = [
        {
            "name": "thumb_variant_a_threat.png",
            "words": ["HIJACKED", "IN", "10", "SECONDS"],
            "badge": "LangChain Vulnerability",
            "badge_color": "#FF4D4D",
            "border_color": "#FF5F56"
        },
        {
            "name": "thumb_variant_b_defense.png",
            "words": ["STOP", "PROMPT", "INJECTION", "NOW"],
            "badge": "NeMo Guardrails 2026",
            "badge_color": "#00FF9D",
            "border_color": "#00FF9D"
        },
        {
            "name": "thumb_variant_c_architecture.png",
            "words": ["NEVER", "TRUST", "RAW", "LLMS"],
            "badge": "Blue-Team Defense",
            "badge_color": "#38BDF8",
            "border_color": "#38BDF8"
        }
    ]

    generated = []
    for v in variants:
        p = os.path.join(build_dir, v["name"])
        create_thumbnail_variant(p, v["words"], v["badge"], v["badge_color"], v["border_color"])
        generated.append(p)

    return generated

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug", default="prevent-prompt-injection-langchain-nemo")
    args = parser.parse_args()
    generate_thumbnails(args.slug)
