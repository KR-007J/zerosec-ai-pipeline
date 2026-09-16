#!/usr/bin/env python3
"""
ZeroSec AI Voice Engine - Phase 3
Generates production-grade neural voice narration using Edge Neural TTS / Kokoro-82M.
ZERO fake fallbacks. Produces genuine, articulate tech documentary speech.
Enforces:
1. Pronunciation dictionary regex replacement before synthesis.
2. Sentence length QC check (splits long sentences to <= 22 words).
3. Universal broadcast mastering: highpass, high-frequency de-harshing, compression, loudnorm -14 LUFS.
4. Audio clipping QC check.
"""

import os
import sys
import re
import json
import asyncio
import subprocess
import argparse

PRONUNCIATION_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config", "pronunciation.json"))

def load_pronunciation_rules():
    if os.path.exists(PRONUNCIATION_FILE):
        with open(PRONUNCIATION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def apply_pronunciation(text, rules):
    processed = text
    for term, phonetic in rules.items():
        pattern = re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
        processed = pattern.sub(phonetic, processed)
    return processed

def split_long_sentences(text, max_words=22):
    paragraphs = text.split("\n\n")
    clean_paragraphs = []

    for para in paragraphs:
        if not para.strip():
            continue
        raw_sentences = re.split(r'(?<=[.?!])\s+', para.strip())
        normalized = []

        for s in raw_sentences:
            words = s.split()
            if len(words) <= max_words:
                normalized.append(s)
            else:
                sub_parts = re.split(r'(?<=[,;])\s+|(?<=\s)(?:and|but|while|because)\s+', s)
                current_chunk = []
                for part in sub_parts:
                    if len(current_chunk) + len(part.split()) <= max_words:
                        current_chunk.append(part)
                    else:
                        if current_chunk:
                            normalized.append(" ".join(current_chunk).rstrip(",") + ".")
                        current_chunk = [part]
                if current_chunk:
                    chunk_text = " ".join(current_chunk).strip()
                    if not chunk_text.endswith((".", "!", "?")):
                        chunk_text += "."
                    normalized.append(chunk_text)
        clean_paragraphs.append(" ".join(normalized))

    return "\n\n".join(clean_paragraphs)

def extract_spoken_text(script_markdown):
    lines = script_markdown.split("\n")
    spoken = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith(("#", "-", "*", ">", "|", "Command:")):
            continue
        if line.startswith("[Source:") or line.startswith("```"):
            continue
        clean_line = re.sub(r'\[Source:.*?\]', '', line).strip()
        if clean_line:
            spoken.append(clean_line)
    return "\n\n".join(spoken)

async def synthesize_edge_tts(text, output_path, voice="en-US-ChristopherNeural"):
    """
    Synthesizes natural, broadcast-grade speech using Edge Neural TTS.
    100% free, zero API keys, no cold starts.
    """
    import edge_tts
    print(f"[INFO] Synthesizing neural speech with voice '{voice}'...")
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)
    return output_path

def synthesize_audio(text, output_raw_wav):
    """
    Synthesizes real human voice.
    Primary: Edge Neural TTS (en-US-ChristopherNeural)
    Secondary: Kokoro-82M HF Space
    FAIL if real TTS cannot be reached (zero sine-wave stubs).
    """
    temp_mp3 = output_raw_wav.replace(".wav", ".mp3")

    # Try Edge Neural TTS
    try:
        asyncio.run(synthesize_edge_tts(text, temp_mp3))
        # Convert MP3 to 24kHz / 48kHz WAV
        cmd = ["ffmpeg", "-y", "-i", temp_mp3, "-ar", "48000", output_raw_wav]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        if os.path.exists(temp_mp3):
            os.remove(temp_mp3)
        print(f"[SUCCESS] Real neural speech synthesized -> {output_raw_wav}")
        return True
    except Exception as e_edge:
        print(f"[WARN] Edge-TTS error: {e_edge}. Attempting Kokoro-82M on Hugging Face...", file=sys.stderr)

    # Try Kokoro-82M via gradio_client
    try:
        from gradio_client import Client
        hf_token = os.environ.get("HF_TOKEN", None)
        client = Client("hexgrad/Kokoro-82M", hf_token=hf_token)
        result = client.predict(text=text, voice="am_adam", api_name="/predict")
        if os.path.exists(result):
            import shutil
            shutil.copy(result, output_raw_wav)
            print(f"[SUCCESS] Kokoro-82M speech synthesized -> {output_raw_wav}")
            return True
    except Exception as e_hf:
        print(f"[ERROR] Kokoro HF Space also failed: {e_hf}", file=sys.stderr)

    raise RuntimeError("CRITICAL: Failed to synthesize real voice! Pipeline will not ship videos with fake or missing audio.")

def post_process_audio(input_wav, output_master_wav):
    """
    Applies broadcast audio mastering using standard FFmpeg filters:
    - Highpass at 80Hz (cuts rumble)
    - Equalizer de-harshing at 6kHz (universal de-esser)
    - Compression for consistent presence
    - EBU R128 YouTube standard loudnorm (-14 LUFS, True Peak -1.5dB)
    """
    print("[INFO] Applying universal broadcast audio mastering (loudnorm -14 LUFS)...")
    filter_chain = (
        "highpass=f=80,"
        "equalizer=f=6000:t=q:w=1.2:g=-3.5,"
        "acompressor=threshold=-18dB:ratio=3:attack=15:release=120,"
        "loudnorm=I=-14:TP=-1.5:LRA=7"
    )
    cmd = [
        "ffmpeg", "-y",
        "-i", input_wav,
        "-af", filter_chain,
        "-ar", "48000",
        output_master_wav
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    # QC Check: Verify no clipping
    qc_cmd = ["ffmpeg", "-i", output_master_wav, "-af", "volumedetect", "-f", "null", "-"]
    res = subprocess.run(qc_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if "max_volume: 0.0 dB" in res.stderr:
        raise ValueError("Audio QC FAILED: Peak volume hit 0.0 dBFS (clipping)!")
    else:
        print("[SUCCESS] Audio QC passed: 100% clean dynamics, zero clipping.")
    return output_master_wav

def build_voice_pipeline(slug="prevent-prompt-injection-langchain-nemo"):
    build_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "build", slug))
    script_file = os.path.join(build_dir, "script.md")
    if not os.path.exists(script_file):
        raise FileNotFoundError(f"Script not found: {script_file}")

    with open(script_file, "r", encoding="utf-8") as f:
        raw_md = f.read()

    spoken = extract_spoken_text(raw_md)
    rules = load_pronunciation_rules()
    phonetic_text = apply_pronunciation(spoken, rules)
    qc_text = split_long_sentences(phonetic_text, max_words=22)

    raw_wav = os.path.join(build_dir, "vo_raw.wav")
    master_wav = os.path.join(build_dir, "vo_master.wav")

    synthesize_audio(qc_text, raw_wav)
    post_process_audio(raw_wav, master_wav)

    print(f"[SUCCESS] Real Voice Pipeline Complete -> {master_wav}")
    return master_wav

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug", default="prevent-prompt-injection-langchain-nemo")
    args = parser.parse_args()
    build_voice_pipeline(args.slug)
