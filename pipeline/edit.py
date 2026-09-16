#!/usr/bin/env python3
"""
ZeroSec AI Video Assembly Engine - Phase 4
Assembles screen recording, voiceover, background music, burned subtitles,
and animated lower-thirds into a 1080p master video + 3 vertical Shorts.
"""

import os
import sys
import json
import subprocess
import argparse

BRAND_CONFIG = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "brand.json"))
BG_MUSIC_DEFAULT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "background_ambient.wav"))

def load_brand():
    if os.path.exists(BRAND_CONFIG):
        with open(BRAND_CONFIG, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "channel_name": "ZeroSec AI",
        "colors": {"accent_green": "#00FF9D", "background_hex": "#0D1117"},
        "subtitles": {"fontsize": 22, "margin_v": 45}
    }

def generate_ass_subtitles(dialogue_chunks, output_ass_path):
    brand = load_brand()
    sub_cfg = brand.get("subtitles", {})
    fontsize = sub_cfg.get("fontsize", 22)
    margin_v = sub_cfg.get("margin_v", 45)

    header = f"""[Script Info]
Title: ZeroSec AI Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,DejaVu Sans,{fontsize},&H00FFFFFF,&H0000FF9D,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,3,2,1,2,60,60,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    for chunk in dialogue_chunks:
        start_str = format_ass_time(chunk["start"])
        end_str = format_ass_time(chunk["end"])
        text = chunk["text"].replace("\n", "\\N")
        events.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{text}")

    with open(output_ass_path, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(events) + "\n")
    print(f"[SUCCESS] Subtitles generated -> {output_ass_path}")
    return output_ass_path

def format_ass_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds - int(seconds)) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

def assemble_master(input_video, input_vo, bg_music, ass_subs, output_master, duration_sec=24):
    print(f"[INFO] Assembling 1080p master video ({duration_sec}s)...")
    escaped_ass = ass_subs.replace(":", "\\:").replace("'", "\\'")

    # Dynamically verify if ass or subtitles filter is present in the environment
    res = subprocess.run(["ffmpeg", "-filters"], capture_output=True, text=True)
    if " ass " in res.stdout:
        sub_filter = f"ass='{escaped_ass}',"
    elif " subtitles " in res.stdout:
        sub_filter = f"subtitles='{escaped_ass}',"
    else:
        sub_filter = ""

    vf = (
        f"{sub_filter}"
        f"drawtext=text=ZeroSec AI:x=w-160:y=40:fontsize=18:fontcolor=white,"
        f"drawbox=x=80:y=h-80:w=580:h=40:color=0x161B22@0.85:t=fill,"
        f"drawtext=text=Defensive Lab Sandbox - Blue Team Verified:x=100:y=h-68:fontsize=16:fontcolor=0x00FF9D"
    )

    af = (
        "[1:a]volume=1.0[vo];"
        "[2:a]volume=0.03,afade=t=in:ss=0:d=2[bg];"
        "[vo][bg]amix=inputs=2:duration=first:dropout_transition=2[aout]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", input_video,
        "-i", input_vo,
        "-i", bg_music,
        "-filter_complex", f"[0:v]{vf}[vout];{af}",
        "-map", "[vout]",
        "-map", "[aout]",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-t", str(duration_sec),
        output_master
    ]

    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    print(f"[SUCCESS] Master video created -> {output_master}")
    return output_master

def export_shorts(input_master, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    print("[INFO] Exporting 3 high-retention vertical Shorts (1080x1920)...")

    segments = [
        {"name": "short_1_exploit_threat.mp4", "start": 0, "duration": 8, "hook": "Can you hijack LangChain in 10 lines?"},
        {"name": "short_2_colang_rails.mp4", "start": 8, "duration": 8, "hook": "How NeMo Guardrails Works"},
        {"name": "short_3_blocked_defense.mp4", "start": 16, "duration": 8, "hook": "Prompt Injection BLOCKED at runtime"}
    ]

    exported = []
    for s in segments:
        out_path = os.path.join(output_dir, s["name"])
        filter_complex = (
            f"scale=1080:-1[fg];"
            f"color=c=0x0D1117:s=1080x1920[bg];"
            f"[bg][fg]overlay=x=0:y=(H-h)/2[base];"
            f"[base]drawbox=x=40:y=240:w=1000:h=120:color=0x161B22@0.9:t=fill,"
            f"drawtext=text='{s['hook']}':x=60:y=285:fontsize=34:fontcolor=0x00FF9D,"
            f"drawtext=text='ZeroSec AI #Shorts':x=60:y=1750:fontsize=28:fontcolor=0x8B949E"
        )
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(s["start"]),
            "-i", input_master,
            "-t", str(s["duration"]),
            "-filter_complex", filter_complex,
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            out_path
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print(f"[SUCCESS] Short generated -> {out_path}")
        exported.append(out_path)

    return exported

def run_assembly(slug="prevent-prompt-injection-langchain-nemo"):
    build_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "build", slug))
    os.makedirs(build_dir, exist_ok=True)
    input_video = os.path.join(build_dir, "input.mp4")
    input_vo = os.path.join(build_dir, "vo_master.wav")
    output_master = os.path.join(build_dir, "master.mp4")
    shorts_dir = os.path.join(build_dir, "shorts")
    ass_subs = os.path.join(build_dir, "subtitles.ass")

    # If input.mp4 does not exist in build dir (e.g. clean CI runner), generate placeholder recording
    if not os.path.exists(input_video):
        print(f"[INFO] input.mp4 not found in {build_dir}. Generating clean testbed terminal recording...")
        scripts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts"))
        gen_script = os.path.join(scripts_dir, "generate_placeholder_recording.py")
        subprocess.run([sys.executable, gen_script], check=True)

    dialogue_chunks = [
        {"start": 0.5, "end": 5.0, "text": "An LLM agent with direct tool access is a security vulnerability waiting to happen."},
        {"start": 5.5, "end": 11.0, "text": "If you connect LangChain to a shell without deterministic guardrails, attackers can bypass your prompts."},
        {"start": 11.5, "end": 17.0, "text": "Today, we configure NVIDIA NeMo Guardrails to stop jailbreaks at the runtime layer."},
        {"start": 17.5, "end": 23.5, "text": "When we inject the malicious payload, the Colang input rail intercepts and blocks the execution."}
    ]

    generate_ass_subtitles(dialogue_chunks, ass_subs)
    assemble_master(input_video, input_vo, BG_MUSIC_DEFAULT, ass_subs, output_master, duration_sec=24)
    shorts = export_shorts(output_master, shorts_dir)

    print(f"[SUCCESS] Assembly complete! Master: {output_master}")
    return output_master, shorts

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug", default="prevent-prompt-injection-langchain-nemo")
    args = parser.parse_args()
    run_assembly(args.slug)
