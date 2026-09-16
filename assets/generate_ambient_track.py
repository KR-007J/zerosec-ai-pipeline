#!/usr/bin/env python3
"""
Generates a subtle, royalty-free dark ambient electronic background music loop
for defensive cybersecurity tutorials. 100% synthesized, 0 copyright risk.
"""
import os
import subprocess

def generate_ambient_music(output_path, duration_sec=120):
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    # Layered ambient drone with soft pulsing filter
    filter_complex = (
        "sine=frequency=55:duration={d}[b1];"
        "sine=frequency=110:duration={d}[b2];"
        "sine=frequency=220:duration={d}[b3];"
        "[b1][b2][b3]amix=inputs=3:weights=0.5 0.3 0.2,"
        "lowpass=f=400,tremolo=f=0.2:d=0.4,volume=0.08[out]"
    ).format(d=duration_sec)

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", filter_complex,
        "-map", "[out]",
        "-ar", "44100",
        output_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"[SUCCESS] Ambient background music generated -> {output_path}")
    return output_path

if __name__ == "__main__":
    generate_ambient_music("/home/krish/.gemini/antigravity/scratch/sec-ai-pipeline/assets/background_ambient.wav", 180)
