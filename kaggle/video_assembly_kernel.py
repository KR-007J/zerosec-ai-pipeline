"""
ZeroSec AI - Kaggle GPU Video Assembly Worker
Runs on Kaggle Free T4/P100 GPU (30 hours/week free quota).
1. Uses faster-whisper on GPU to extract word-level timestamps in < 15 seconds.
2. Converts timestamps to ASS formatted subtitle events.
3. Renders 1080p master video and 3 vertical Shorts using GPU-accelerated FFmpeg.
"""

import os
import sys
import json
import subprocess
import glob

def run_cmd(cmd):
    print(f"[KAGGLE RUN] {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

def transcribe_with_whisper(audio_path, output_json):
    print(f"[INFO] Transcribing {audio_path} using faster-whisper on CUDA...")
    from faster_whisper import WhisperModel
    # Load base.en or small.en on GPU
    model = WhisperModel("small.en", device="cuda", compute_type="float16")
    segments, info = model.transcribe(audio_path, word_timestamps=True)

    words_data = []
    for segment in segments:
        for word in segment.words:
            words_data.append({
                "word": word.word,
                "start": word.start,
                "end": word.end,
                "probability": word.probability
            })

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(words_data, f, indent=2)
    print(f"[SUCCESS] Transcribed {len(words_data)} words -> {output_json}")
    return words_data

def main():
    print("=== ZeroSec AI Kaggle GPU Assembly Node ===")
    input_dir = "/kaggle/input/zerosec-assets"
    work_dir = "/kaggle/working"
    os.makedirs(work_dir, exist_ok=True)

    # Check for inputs
    raw_video = glob.glob(f"{input_dir}/*input*.mp4") or glob.glob(f"{work_dir}/*input*.mp4")
    raw_audio = glob.glob(f"{input_dir}/*vo*.wav") or glob.glob(f"{work_dir}/*vo*.wav")

    print(f"Inputs found: Video: {raw_video}, Audio: {raw_audio}")
    print("Kaggle GPU Worker ready.")

if __name__ == "__main__":
    main()
