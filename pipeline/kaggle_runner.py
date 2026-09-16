#!/usr/bin/env python3
"""
ZeroSec AI - Kaggle GPU Dispatcher & Pipeline Bridge
Orchestrates end-to-end Kaggle GPU processing:
1. Configures ~/.kaggle/kaggle.json from KAGGLE_USERNAME & KAGGLE_KEY secrets.
2. Packages input media into a dedicated Kaggle Dataset (kaggle datasets create/version).
3. Links the dataset to kaggle/kernel-metadata.json under dataset_sources.
4. Pushes the GPU kernel (kaggle kernels push).
5. Polls kernel status until 'complete'.
6. Downloads rendered master.mp4 and shorts/ into build/<slug>/.
If credentials are absent or fail, gracefully executes runner assembly (pipeline/edit.py).
"""

import os
import sys
import json
import time
import shutil
import subprocess
import argparse

def setup_kaggle_credentials():
    username = os.environ.get("KAGGLE_USERNAME")
    key = os.environ.get("KAGGLE_KEY")
    if not username or not key:
        return None

    kaggle_dir = os.path.expanduser("~/.kaggle")
    os.makedirs(kaggle_dir, exist_ok=True)
    kaggle_json = os.path.join(kaggle_dir, "kaggle.json")
    with open(kaggle_json, "w", encoding="utf-8") as f:
        json.dump({"username": username, "key": key}, f)
    os.chmod(kaggle_json, 0o600)
    print(f"[INFO] Kaggle API credentials authenticated for: {username}")
    return username

def stage_and_upload_dataset(username, slug, build_dir, root_dir):
    """
    Packages input media and pushes to a Kaggle Dataset so /kaggle/input receives them.
    """
    staging_dir = os.path.join(build_dir, "_kaggle_dataset_staging")
    os.makedirs(staging_dir, exist_ok=True)

    # Clean existing staging
    for item in os.listdir(staging_dir):
        p = os.path.join(staging_dir, item)
        if os.path.isfile(p):
            os.remove(p)

    # Copy input video, voiceover, and ambient track
    input_video = os.path.join(build_dir, "input.mp4")
    input_audio = os.path.join(build_dir, "vo_master.wav")
    bg_music = os.path.join(root_dir, "assets", "background_ambient.wav")

    if not os.path.exists(input_video) or not os.path.exists(input_audio):
        raise FileNotFoundError(f"Missing required input media in {build_dir}")

    shutil.copy(input_video, os.path.join(staging_dir, "input.mp4"))
    shutil.copy(input_audio, os.path.join(staging_dir, "vo_master.wav"))
    if os.path.exists(bg_music):
        shutil.copy(bg_music, os.path.join(staging_dir, "background_ambient.wav"))

    # Generate dataset-metadata.json
    dataset_slug = f"zerosec-inputs-{slug[:12].strip('-')}"
    dataset_id = f"{username}/{dataset_slug}"
    meta = {
        "title": dataset_slug,
        "id": dataset_id,
        "licenses": [{"name": "CC0-1.0"}]
    }
    with open(os.path.join(staging_dir, "dataset-metadata.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"[INFO] Syncing input media to Kaggle Dataset: {dataset_id}...")

    # Check if dataset already exists
    status_cmd = ["kaggle", "datasets", "status", dataset_id]
    res = subprocess.run(status_cmd, capture_output=True, text=True)

    if res.returncode == 0:
        print("[INFO] Dataset exists, creating new version...")
        cmd = ["kaggle", "datasets", "version", "-p", staging_dir, "-m", "update media", "--dir-mode", "zip"]
    else:
        print("[INFO] Creating new Kaggle dataset...")
        cmd = ["kaggle", "datasets", "create", "-p", staging_dir, "-u", "--dir-mode", "zip"]

    subprocess.run(cmd, check=True)
    print(f"[SUCCESS] Kaggle Dataset synced: {dataset_id}")
    return dataset_id

def dispatch_kaggle_gpu_job(username, slug):
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    kaggle_dir = os.path.join(root, "kaggle")
    meta_path = os.path.join(kaggle_dir, "kernel-metadata.json")
    build_dir = os.path.join(root, "build", slug)

    # 1. Upload input media to Kaggle Dataset
    dataset_id = stage_and_upload_dataset(username, slug, build_dir, root)

    # 2. Update kernel metadata with dataset dependency
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    kernel_slug = f"zerosec-assembly-{slug[:15].strip('-')}"
    meta["id"] = f"{username}/{kernel_slug}"
    meta["code_file"] = "video_assembly_kernel.py"
    meta["enable_gpu"] = "true"
    meta["enable_internet"] = "true"
    meta["dataset_sources"] = [dataset_id]

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    # 3. Push kernel
    print(f"[INFO] Pushing GPU assembly kernel to Kaggle: {meta['id']}...")
    subprocess.run(["kaggle", "kernels", "push", "-p", kaggle_dir], check=True)

    # 4. Poll kernel status until complete
    print("[INFO] Monitoring Kaggle GPU worker execution (max 10 minutes)...")
    kernel_id = meta["id"]
    completed = False
    for attempt in range(60):
        res = subprocess.run(["kaggle", "kernels", "status", kernel_id], capture_output=True, text=True)
        status_text = res.stdout.lower()
        if "complete" in status_text:
            print("[SUCCESS] Kaggle GPU rendering finished successfully!")
            completed = True
            break
        elif "error" in status_text or "failed" in status_text:
            raise RuntimeError(f"Kaggle GPU kernel failed with output: {res.stdout}")
        time.sleep(10)

    if not completed:
        raise TimeoutError("Kaggle GPU kernel timed out after 10 minutes.")

    # 5. Download rendered outputs into build/<slug>/
    print(f"[INFO] Downloading rendered artifacts into {build_dir}...")
    subprocess.run(["kaggle", "kernels", "output", kernel_id, "-p", build_dir], check=True)
    print(f"[SUCCESS] GPU artifacts retrieved into {build_dir}")

def run_assembly_bridge(slug="prevent-prompt-injection-langchain-nemo"):
    username = setup_kaggle_credentials()
    if username:
        try:
            dispatch_kaggle_gpu_job(username, slug)
            return
        except Exception as e:
            print(f"[WARN] Kaggle GPU job failed or was skipped ({e}). Falling back to runner assembly...", file=sys.stderr)

    print("[INFO] Running runner assembly engine (pipeline/edit.py)...")
    sys.path.insert(0, os.path.dirname(__file__))
    from edit import run_assembly
    run_assembly(slug)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug", default="prevent-prompt-injection-langchain-nemo")
    args = parser.parse_args()
    run_assembly_bridge(args.slug)
