# 🛡️ ZeroSec AI - Semi-Automated Defensive Video Production System

> **Cloud-Only, Zero Paid Services, High-RPM Faceless Channel Production Engine**
> Targeting US/EU professional software and security engineers via long-tail search queries.

---

## 🏗️ Architecture & Philosophy

1. **100% Free & Cloud-Native:** Runs entirely on GitHub Actions (public repository = unlimited minutes) + Kaggle GPU notebooks (30h/week free T4/P100 GPU quota via Kaggle API).
2. **Strict Blue-Team Policy:** 100% defensive engineering, security auditing, and tool evaluation. Zero exploit or malware creation.
3. **Fact-Checking Gate:** Every factual claim requires a verified source URL. Any unverified claim emits `NEEDS_VERIFY: <claim>` and triggers a fatal build failure.
4. **Human-in-the-Loop 80/20 Rule:** The pipeline automates research, scripting, pronunciation normalization, voice synthesis, audio mastering (-14 LUFS), ASS subtitle burning, video assembly, Shorts extraction, thumbnail variants, and SEO metadata. The creator owns only the **15-20 min terminal screen demo** and **60-sec YouTube Studio drag-and-drop**.

---

## 📂 Repository Layout

```
sec-ai-pipeline/
├── .github/workflows/
│   ├── research.yml       # Weekly scheduled topic research agent
│   └── publish.yml        # Quality gate verification & release packaging
├── assets/
│   ├── brand.json         # Visual brand identity, styling, subtitle typography
│   └── background_ambient.wav # Royalty-free synthesized electronic tech drone
├── config/
│   ├── pronunciation.json # Regex phonetic replacement dictionary for tech acronyms
│   └── affiliates.json    # Verified affiliate links & mandatory FTC disclosures
├── research/
│   ├── collect.py         # Multi-API research agent (HN, GitHub, NVD CVE, YT)
│   └── queue.md           # Ranked top-20 long-tail topic queue
├── pipeline/
│   ├── script.py          # Structured script engine + manual recording shotlist
│   ├── voice.py           # Kokoro-82M TTS + EBU R128 loudness mastering (-14 LUFS)
│   ├── edit.py            # 1080p video assembly, subtitle burn, ducking, 3x Shorts
│   ├── thumbnail.py       # PIL engine: 3 high-contrast 1280x720 variants for A/B testing
│   ├── metadata.py        # YouTube packaging: title (<60c), timestamps, tags, disclosures
│   └── analytics.py       # Feedback loop: weekly retention, RPM, and CTR analysis
├── kaggle/
│   ├── kernel-metadata.json   # Kaggle GPU dispatcher config
│   └── video_assembly_kernel.py # Kaggle GPU worker (faster-whisper + ffmpeg)
└── scripts/
    ├── dry_run.py         # End-to-end dry-run testing orchestrator
    ├── generate_placeholder_recording.py # Mock 1080p terminal session generator
    └── verify_gate.py     # Hard gatekeeper script enforcing zero-unverified claims
```

---

## 🚀 Quickstart & Dry-Run

Run the end-to-end verification pipeline locally:

```bash
python3 scripts/dry_run.py
```

Inspect packaged outputs under:
`build/prevent-prompt-injection-langchain-nemo/`
