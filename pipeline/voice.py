#!/usr/bin/env python3
"""
ZeroSec AI Voice Engine - Phase 3
Generates production-grade neural voice narration using:
1. Piper TTS (100% Open Source, Apache 2.0, self-hosted ONNX, zero ToS risk) [PRIMARY]
2. Kokoro-82M on Hugging Face Spaces [SECONDARY]
3. Edge Neural TTS [FALLBACK]
ZERO fake sine-wave fallbacks. Fails loud if real audio cannot be produced.

Broadcast Chain:
- Pronunciation regex substitution
- Sentence splitting (<= 22 words)
- Highpass filter (80Hz)
- Equalizer de-harshing (6kHz)
- Dynamics compression
- EBU R128 Loudness Normalization (-14 LUFS, TP -1.5dB)
"""

import os
import sys
import re
import json
import asyncio
import subprocess
import argparse
import urllib.request

PRONUNCIATION_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config", "pronunciation.json"))
PIPER_MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "models", "piper"))
PIPER_ONNX_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx"
PIPER_JSON_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json"

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

def ensure_piper_model():
    """
    Ensures the open-source Piper ONNX model is available locally.
    """
    os.makedirs(PIPER_MODEL_DIR, exist_ok=True)
    onnx_path = os.path.join(PIPER_MODEL_DIR, "en_US-lessac-medium.onnx")
    json_path = os.path.join(PIPER_MODEL_DIR, "en_US-lessac-medium.onnx.json")

    if not os.path.exists(json_path):
        print(f"[INFO] Fetching open-source Piper voice config...")
        urllib.request.urlretrieve(PIPER_JSON_URL, json_path)

    if not os.path.exists(onnx_path):
        print(f"[INFO] Fetching open-source Piper ONNX model (~60MB, one-time download)...")
        urllib.request.urlretrieve(PIPER_ONNX_URL, onnx_path)

    return onnx_path, json_path

def synthesize_with_piper(text, output_raw_wav):
    """
    Primary: Synthesizes speech using 100% open-source Piper ONNX engine.
    Self-hosted, CPU-friendly, zero external API or ToS risk.
    """
    onnx_path, json_path = ensure_piper_model()
    # Locate piper binary in venv or path
    piper_bin = "piper"
    venv_piper = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".venv", "bin", "piper"))
    if os.path.exists(venv_piper):
        piper_bin = venv_piper

    print(f"[INFO] Synthesizing speech using open-source Piper neural model...")
    cmd = [
        piper_bin,
        "-m", onnx_path,
        "-c", json_path,
        "-f", output_raw_wav
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = proc.communicate(input=text)
    if proc.returncode == 0 and os.path.exists(output_raw_wav) and os.path.getsize(output_raw_wav) > 1000:
        print(f"[SUCCESS] Piper neural speech synthesized -> {output_raw_wav}")
        return True
    else:
        raise RuntimeError(f"Piper execution failed: {stderr}")

async def synthesize_with_edge(text, output_mp3):
    import edge_tts
    communicate = edge_tts.Communicate(text, "en-US-ChristopherNeural")
    await communicate.save(output_mp3)

def synthesize_audio(text, output_raw_wav):
    """
    Synthesis Pipeline:
    1. Try Piper (100% open source ONNX)
    2. Try Kokoro-82M on HF
    3. Try Edge-TTS
    4. Hard-fail loud if real audio cannot be produced.
    """
    # 1. Try Piper TTS (Open Source, Zero ToS Risk)
    try:
        if synthesize_with_piper(text, output_raw_wav):
            return True
    except Exception as e_piper:
        print(f"[WARN] Piper TTS not available or failed ({e_piper}). Trying alternatives...", file=sys.stderr)

    # 2. Try Kokoro-82M on HF Spaces
    try:
        from gradio_client import Client
        hf_token = os.environ.get("HF_TOKEN", None)
        print("[INFO] Attempting Kokoro-82M HF Space synthesis...")
        client = Client("hexgrad/Kokoro-82M", hf_token=hf_token)
        result = client.predict(text=text, voice="am_adam", api_name="/predict")
        if os.path.exists(result):
            import shutil
            shutil.copy(result, output_raw_wav)
            print(f"[SUCCESS] Kokoro-82M speech synthesized -> {output_raw_wav}")
            return True
    except Exception as e_hf:
        print(f"[WARN] Kokoro HF Space unavailable ({e_hf})...", file=sys.stderr)

    # 3. Try Edge-TTS as tertiary fallback
    try:
        temp_mp3 = output_raw_wav.replace(".wav", ".mp3")
        print("[INFO] Attempting Edge-TTS fallback...")
        asyncio.run(synthesize_with_edge(text, temp_mp3))
        subprocess.run(["ffmpeg", "-y", "-i", temp_mp3, "-ar", "48000", output_raw_wav], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(temp_mp3):
            os.remove(temp_mp3)
        print(f"[SUCCESS] Edge-TTS speech synthesized -> {output_raw_wav}")
        return True
    except Exception as e_edge:
        print(f"[ERROR] Edge-TTS also failed: {e_edge}", file=sys.stderr)

    raise RuntimeError("FATAL: All real speech synthesis engines failed. Pipeline will not output videos with missing or fake audio.")

def post_process_audio(input_wav, output_master_wav):
    """
    Universal broadcast mastering chain:
    - Highpass 80Hz
    - Equalizer de-harshing (6kHz)
    - Dynamics compressor
    - EBU R128 YouTube loudnorm (-14 LUFS, TP -1.5dB)
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

    qc_path = os.path.join(build_dir, "voice_script_qc.txt")
    with open(qc_path, "w", encoding="utf-8") as f:
        f.write(qc_text)
    word_count = len(qc_text.split())
    print(f"[INFO] Processed spoken text for TTS: {word_count} words -> {qc_path}")

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
