#!/usr/bin/env python3
"""
ZeroSec AI - Kaggle GPU Video Assembly Worker
Runs on Kaggle Free T4/P100 GPU (30 hours/week free quota).
1. Uses faster-whisper on GPU to transcribe audio with word timestamps in <15s.
2. Formats ASS subtitles according to ZeroSec brand styling.
3. Assembles 1080p master video with audio ducking and burned subtitles.
4. Exports 3 vertical 1080x1920 Shorts from key retention beats.
All outputs are saved to /kaggle/working/ for automatic retrieval via Kaggle API.
"""

import os
import sys
import json
import glob
import subprocess

def format_ass_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds - int(seconds)) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

def transcribe_audio_whisper(audio_path, output_json, output_ass):
    """
    Runs faster-whisper on CUDA GPU. Generates word-level timestamps & ASS subtitles.
    """
    print(f"[KAGGLE GPU] Loading faster-whisper on CUDA for: {audio_path}...")
    try:
        from faster_whisper import WhisperModel
        # Use GPU with float16 on Kaggle T4
        model = WhisperModel("small.en", device="cuda", compute_type="float16")
    except Exception as e:
        print(f"[WARN] CUDA Whisper unavailable ({e}), attempting CPU fallback...", file=sys.stderr)
        from faster_whisper import WhisperModel
        model = WhisperModel("base.en", device="cpu", compute_type="int8")

    segments, info = model.transcribe(audio_path, word_timestamps=True)

    words_data = []
    dialogue_events = []
    
    for segment in segments:
        text = segment.text.strip()
        start = segment.start
        end = segment.end
        dialogue_events.append({
            "start": start,
            "end": end,
            "text": text
        })
        if segment.words:
            for w in segment.words:
                words_data.append({
                    "word": w.word,
                    "start": w.start,
                    "end": w.end,
                    "prob": w.probability
                })

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump({"info": {"language": info.language, "duration": info.duration}, "words": words_data, "segments": dialogue_events}, f, indent=2)

    # Build ASS subtitles
    ass_header = """[Script Info]
Title: ZeroSec AI Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,DejaVu Sans,24,&H00FFFFFF,&H0000FF9D,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,3,2,1,2,60,60,45,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    for d in dialogue_events:
        start_str = format_ass_time(d["start"])
        end_str = format_ass_time(d["end"])
        t = d["text"].replace("\n", "\\N")
        lines.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{t}")

    with open(output_ass, "w", encoding="utf-8") as f:
        f.write(ass_header + "\n".join(lines) + "\n")

    print(f"[SUCCESS] Transcribed {len(dialogue_events)} segments -> {output_ass}")
    return output_ass

def render_master_and_shorts(input_video, input_audio, bg_music, ass_path, working_dir):
    """
    Assembles master video and exports 3 vertical Shorts into /kaggle/working/
    """
    master_path = os.path.join(working_dir, "master.mp4")
    shorts_dir = os.path.join(working_dir, "shorts")
    os.makedirs(shorts_dir, exist_ok=True)

    print(f"[KAGGLE GPU] Rendering 1080p master video -> {master_path}")
    
    vf = (
        f"ass='{ass_path}',"
        f"drawtext=text=ZeroSec AI:x=w-160:y=40:fontsize=18:fontcolor=white,"
        f"drawbox=x=80:y=h-80:w=580:h=40:color=0x161B22@0.85:t=fill,"
        f"drawtext=text=Defensive Lab Sandbox - Blue Team Verified:x=100:y=h-68:fontsize=16:fontcolor=0x00FF9D"
    )

    af = (
        "[1:a]volume=1.0[vo];"
        "[2:a]volume=0.03,afade=t=in:ss=0:d=2[bg];"
        "[vo][bg]amix=inputs=2:duration=first:dropout_transition=2[aout]"
    )

    cmd_master = [
        "ffmpeg", "-y",
        "-i", input_video,
        "-i", input_audio,
        "-i", bg_music,
        "-filter_complex", f"[0:v]{vf}[vout];{af}",
        "-map", "[vout]",
        "-map", "[aout]",
        "-c:v", "libx264",
        "-preset", "fast",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        master_path
    ]
    subprocess.run(cmd_master, check=True)
    print(f"[SUCCESS] Master video rendered -> {master_path}")

    # Export 3 Vertical Shorts (1080x1920)
    shorts_specs = [
        ("short_1_exploit_threat.mp4", 0, 8, "Can you hijack LangChain in 10 lines?"),
        ("short_2_colang_rails.mp4", 8, 8, "How NeMo Guardrails Works"),
        ("short_3_blocked_defense.mp4", 16, 8, "Prompt Injection BLOCKED at runtime")
    ]

    for fname, start_sec, dur_sec, hook in shorts_specs:
        out_short = os.path.join(shorts_dir, fname)
        filter_short = (
            f"scale=1080:-1[fg];"
            f"color=c=0x0D1117:s=1080x1920[bg];"
            f"[bg][fg]overlay=x=0:y=(H-h)/2[base];"
            f"[base]drawbox=x=40:y=240:w=1000:h=120:color=0x161B22@0.9:t=fill,"
            f"drawtext=text='{hook}':x=60:y=285:fontsize=34:fontcolor=0x00FF9D,"
            f"drawtext=text='ZeroSec AI #Shorts':x=60:y=1750:fontsize=28:fontcolor=0x8B949E"
        )
        cmd_short = [
            "ffmpeg", "-y",
            "-ss", str(start_sec),
            "-i", master_path,
            "-t", str(dur_sec),
            "-filter_complex", filter_short,
            "-c:v", "libx264",
            "-preset", "fast",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            out_short
        ]
        subprocess.run(cmd_short, check=True)
        print(f"[SUCCESS] Short rendered -> {out_short}")

def main():
    print("=== ZeroSec AI Kaggle GPU Assembly Worker Starting ===")
    
    # Locate inputs
    search_dirs = ["/kaggle/input", "/kaggle/working", "."]
    videos = []
    audios = []
    musics = []

    for d in search_dirs:
        videos.extend(glob.glob(os.path.join(d, "**", "*input*.mp4"), recursive=True))
        audios.extend(glob.glob(os.path.join(d, "**", "*vo_master*.wav"), recursive=True))
        musics.extend(glob.glob(os.path.join(d, "**", "*background*.wav"), recursive=True))

    if not videos or not audios:
        print(f"[ERROR] Required inputs not found! Videos: {videos}, Audios: {audios}", file=sys.stderr)
        sys.exit(1)

    input_video = videos[0]
    input_audio = audios[0]
    bg_music = musics[0] if musics else input_audio

    working_dir = "/kaggle/working" if os.path.exists("/kaggle") else "./build_output"
    os.makedirs(working_dir, exist_ok=True)

    output_json = os.path.join(working_dir, "transcription.json")
    output_ass = os.path.join(working_dir, "subtitles.ass")

    # Step 1: Transcribe with Faster-Whisper
    transcribe_audio_whisper(input_audio, output_json, output_ass)

    # Step 2: Assemble Master & Shorts via FFmpeg
    render_master_and_shorts(input_video, input_audio, bg_music, output_ass, working_dir)

    print("=== ZeroSec AI Kaggle GPU Worker Finished Successfully ===")

if __name__ == "__main__":
    main()
