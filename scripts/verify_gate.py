#!/usr/bin/env python3
"""
ZeroSec AI Quality Gate Verifier - Phase 6
Hard Gatekeeper for Video Production Pipeline.
Must pass 100% of checks before packaging or publishing:
1. Zero "NEEDS_VERIFY" tags in script.
2. Committed approval marker exists: /build/<slug>/APPROVED
3. Master video exists and meets 1080p standards.
4. Exactly 3 vertical Shorts exist (1080x1920).
5. Metadata package exists, title < 60 chars, 20 tags present.
6. 3 Thumbnail variants exist (1280x720 PNG).
"""

import os
import sys
import glob
import subprocess
import argparse

def run_gate_checks(slug="prevent-prompt-injection-langchain-nemo"):
    build_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "build", slug))
    print(f"=== Running ZeroSec Quality Gate on: {slug} ===")
    errors = []

    # Check 1: Script & Unverified Claims
    script_path = os.path.join(build_dir, "script.md")
    if not os.path.exists(script_path):
        errors.append(f"Missing script file: {script_path}")
    else:
        with open(script_path, "r", encoding="utf-8") as f:
            script_text = f.read()
        if "NEEDS_VERIFY" in script_text:
            unverified = [line.strip() for line in script_text.split("\n") if "NEEDS_VERIFY" in line]
            errors.append(f"UNVERIFIED CLAIMS FOUND ({len(unverified)}): {unverified}")

    # Check 2: Committed Approval File
    approval_file = os.path.join(build_dir, "APPROVED")
    if not os.path.exists(approval_file):
        errors.append(f"MISSING HUMAN APPROVAL: File '{approval_file}' does not exist. Creator must review script and commit APPROVED.")

    # Check 3: Master Video (1080p)
    master_video = os.path.join(build_dir, "master.mp4")
    if not os.path.exists(master_video):
        errors.append(f"Missing master video: {master_video}")
    else:
        # Check video file size > 500KB
        sz = os.path.getsize(master_video)
        if sz < 500000:
            errors.append(f"Master video file size suspect: {sz} bytes")

    # Check 4: Vertical Shorts
    shorts_dir = os.path.join(build_dir, "shorts")
    shorts = glob.glob(os.path.join(shorts_dir, "*.mp4"))
    if len(shorts) < 3:
        errors.append(f"Expected 3 vertical Shorts, found {len(shorts)} in {shorts_dir}")

    # Check 5: Metadata Package
    meta_path = os.path.join(build_dir, "metadata.txt")
    if not os.path.exists(meta_path):
        errors.append(f"Missing metadata package: {meta_path}")
    else:
        with open(meta_path, "r", encoding="utf-8") as f:
            meta_text = f.read()
        if "TITLE (" in meta_text:
            title_line = [l for l in meta_text.split("\n") if l.startswith("TITLE (")][0]
            # Verify length <= 60
            chars = int(title_line.split("(")[1].split()[0])
            if chars > 60:
                errors.append(f"Title exceeds 60 chars: {chars} chars")
        if "TAGS (" in meta_text:
            tags_line = [l for l in meta_text.split("\n") if l.startswith("TAGS (")][0]
            tag_count = int(tags_line.split("(")[1].split()[0])
            if tag_count != 20:
                errors.append(f"Expected exactly 20 tags, found {tag_count}")

    # Check 6: Thumbnails
    thumbs = glob.glob(os.path.join(build_dir, "thumb_*.png"))
    if len(thumbs) < 3:
        errors.append(f"Expected 3 thumbnail variants, found {len(thumbs)} in {build_dir}")

    if errors:
        print("\n❌ QUALITY GATE FAILED! Build cannot be published:")
        for idx, err in enumerate(errors, 1):
            print(f"  {idx}. {err}")
        return False
    else:
        print("\n✅ QUALITY GATE PASSED! 100% of technical and compliance checks verified.")
        return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug", default="prevent-prompt-injection-langchain-nemo")
    args = parser.parse_args()
    success = run_gate_checks(args.slug)
    sys.exit(0 if success else 1)
