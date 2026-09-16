#!/usr/bin/env python3
"""
Generates a subtle, royalty-free dark ambient electronic background music loop.
"""
import os
import subprocess

def generate_ambient_music(output_path, duration_sec=180):
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"sine=frequency=55:duration={duration_sec}",
        "-f", "lavfi", "-i", f"sine=frequency=110:duration={duration_sec}",
        "-filter_complex", "[0:a][1:a]amix=inputs=2:weights=0.6 0.4,lowpass=f=350,volume=0.05[out]",
        "-map", "[out]",
        "-ar", "44100",
        output_path
    ]
    subprocess.run(cmd, check=True)
    print(f"[SUCCESS] Ambient background music generated -> {output_path}")
    return output_path

if __name__ == "__main__":
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    target = os.path.join(root, "assets", "background_ambient.wav")
    generate_ambient_music(target, 180)
