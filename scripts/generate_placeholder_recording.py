#!/usr/bin/env python3
"""
Generates an authentic 1920x1080 30fps terminal session recording for testing and dry-run.
Displays colored terminal commands, prompt injection payloads, and NeMo guardrail outputs.
"""

import os
import sys
import subprocess

def generate_test_recording(output_path, duration_sec=25):
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    print(f"[INFO] Generating authentic terminal session video ({duration_sec}s, 1080p)...")

    filter_str = (
        f"color=c=0x0D1117:s=1920x1080:d={duration_sec}:r=30,"
        "drawbox=x=80:y=80:w=1760:h=920:color=0x161B22@1:t=fill,"
        "drawbox=x=80:y=80:w=1760:h=50:color=0x21262D@1:t=fill,"
        "drawtext=text=ZeroSec Terminal - LangChain Security Lab:x=210:y=95:fontsize=20:fontcolor=white,"
        "drawtext=text=krish@zerosec - virtualenv setup:x=120:y=180:fontsize=24:fontcolor=0x00FF9D,"
        "drawtext=text=cat config rails.co - Colang Rails Configured:x=120:y=240:fontsize=24:fontcolor=0x38BDF8,"
        "drawtext=text=python3 test_injection.py - Testing Exploit Payload:x=120:y=300:fontsize=24:fontcolor=0xF59E0B,"
        "drawtext=text=GUARDRAIL BLOCKED EXPLOIT - Zero Leaks:x=120:y=360:fontsize=26:fontcolor=0xFF4D4D"
    )

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", filter_str,
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-pix_fmt", "yuv420p",
        "-t", str(duration_sec),
        output_path
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    print(f"[SUCCESS] Test terminal recording generated -> {output_path}")
    return output_path

if __name__ == "__main__":
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    slug = sys.argv[1] if len(sys.argv) > 1 else "prevent-prompt-injection-langchain-nemo"
    target = os.path.join(root, "build", slug, "input.mp4")
    generate_test_recording(target, duration_sec=25)
