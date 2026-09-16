#!/usr/bin/env python3
"""
ZeroSec AI - Kaggle GPU Dispatcher & Pipeline Bridge
Orchestrates GPU offload via Kaggle API:
1. Writes ~/.kaggle/kaggle.json from environment variables (KAGGLE_USERNAME & KAGGLE_KEY).
2. Updates kaggle/kernel-metadata.json with target username and slug.
3. Dispatches job to Kaggle GPU runner.
4. Polls status every 10s until complete.
5. Downloads rendered master.mp4 and shorts/ into build/<slug>/.
If credentials are absent or fail, gracefully executes pipeline/edit.py on the runner CPU.
"""

import os
import sys
import json
import time
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
    print(f"[INFO] Kaggle credentials configured for user: {username}")
    return username

def dispatch_kaggle_gpu_job(username, slug):
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    kaggle_dir = os.path.join(root, "kaggle")
    meta_path = os.path.join(kaggle_dir, "kernel-metadata.json")
    build_dir = os.path.join(root, "build", slug)

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    kernel_slug = f"zerosec-assembly-{slug[:20]}"
    meta["id"] = f"{username}/{kernel_slug}"
    meta["code_file"] = "video_assembly_kernel.py"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"[INFO] Dispatching GPU assembly kernel to Kaggle: {meta['id']}...")
    subprocess.run(["kaggle", "kernels", "push", "-p", kaggle_dir], check=True)

    print("[INFO] Polling Kaggle GPU worker status (timeout: 10 mins)...")
    kernel_id = meta["id"]
    completed = False
    for _ in range(60):
        res = subprocess.run(["kaggle", "kernels", "status", kernel_id], capture_output=True, text=True)
        status_text = res.stdout.lower()
        if "complete" in status_text:
            print("[SUCCESS] Kaggle GPU rendering finished successfully!")
            completed = True
            break
        elif "error" in status_text or "failed" in status_text:
            raise RuntimeError(f"Kaggle GPU kernel failed with status: {res.stdout}")
        print("  ... Kaggle GPU rendering in progress (waiting 10s) ...")
        time.sleep(10)

    if not completed:
        raise TimeoutError("Kaggle GPU kernel timed out after 10 minutes.")

    # Pull output files
    print(f"[INFO] Pulling rendered output artifacts into {build_dir}...")
    subprocess.run(["kaggle", "kernels", "output", kernel_id, "-p", build_dir], check=True)
    print(f"[SUCCESS] GPU artifacts retrieved into {build_dir}")

def run_assembly_bridge(slug="prevent-prompt-injection-langchain-nemo"):
    username = setup_kaggle_credentials()
    if username:
        try:
            dispatch_kaggle_gpu_job(username, slug)
            return
        except Exception as e:
            print(f"[WARN] Kaggle GPU job encountered an issue ({e}). Falling back to runner CPU assembly...", file=sys.stderr)

    print("[INFO] Executing high-efficiency runner assembly engine (pipeline/edit.py)...")
    sys.path.insert(0, os.path.dirname(__file__))
    from edit import run_assembly
    run_assembly(slug)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug", default="prevent-prompt-injection-langchain-nemo")
    args = parser.parse_args()
    run_assembly_bridge(args.slug)
