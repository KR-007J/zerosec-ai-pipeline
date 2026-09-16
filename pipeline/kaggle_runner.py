#!/usr/bin/env python3
"""
ZeroSec AI - Kaggle GPU Dispatcher & Pipeline Bridge
Orchestrates GPU offload via Kaggle API:
1. Writes ~/.kaggle/kaggle.json from environment variables.
2. Injects slug and metadata into kaggle/kernel-metadata.json.
3. Pushes kernel to Kaggle free GPU cluster (30h/week free quota).
4. Polls kernel status until 'complete'.
5. Downloads rendered master video and Shorts.
If credentials are not provided, gracefully runs pipeline/edit.py locally.
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
    return username

def dispatch_kaggle_gpu_job(username, slug):
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    kaggle_dir = os.path.join(root, "kaggle")
    meta_path = os.path.join(kaggle_dir, "kernel-metadata.json")

    # Update metadata with current username
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    meta["id"] = f"{username}/zerosec-assembly-{slug}"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"[INFO] Dispatching GPU assembly job to Kaggle: {meta['id']}...")
    push_cmd = ["kaggle", "kernels", "push", "-p", kaggle_dir]
    subprocess.run(push_cmd, check=True)

    print("[INFO] Polling Kaggle GPU worker status...")
    kernel_id = meta["id"]
    for _ in range(60): # Max 10 minutes
        status_cmd = ["kaggle", "kernels", "status", kernel_id]
        res = subprocess.run(status_cmd, capture_output=True, text=True)
        out = res.stdout.lower()
        if "complete" in out:
            print("[SUCCESS] Kaggle GPU rendering complete!")
            break
        elif "error" in out or "failed" in out:
            raise RuntimeError(f"Kaggle GPU kernel failed: {res.stdout}")
        print("  ... Kaggle GPU rendering in progress ...")
        time.sleep(10)

    # Pull output
    build_dir = os.path.join(root, "build", slug)
    pull_cmd = ["kaggle", "kernels", "output", kernel_id, "-p", build_dir]
    subprocess.run(pull_cmd, check=True)
    print(f"[SUCCESS] GPU rendered artifacts retrieved into {build_dir}")

def run_assembly_bridge(slug="prevent-prompt-injection-langchain-nemo"):
    username = setup_kaggle_credentials()
    if username:
        try:
            dispatch_kaggle_gpu_job(username, slug)
            return
        except Exception as e:
            print(f"[WARN] Kaggle GPU job error: {e}. Falling back to runner CPU assembly...", file=sys.stderr)

    print("[INFO] Running runner assembly engine (pipeline/edit.py)...")
    from edit import run_assembly
    run_assembly(slug)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug", default="prevent-prompt-injection-langchain-nemo")
    args = parser.parse_args()
    run_assembly_bridge(args.slug)
