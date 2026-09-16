#!/usr/bin/env python3
"""
ZeroSec AI Metadata Packaging Engine - Phase 5
Generates production YouTube metadata package:
- High-CTR, SEO-optimized title (<60 characters, keyword-first)
- Timestamped description with verified sources & FTC affiliate disclosures
- 20 exact long-tail search tags
- Pinned comment text
- Emits /build/<slug>/metadata.txt
"""

import os
import sys
import json
import argparse

AFFILIATES_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config", "affiliates.json"))

def load_affiliates():
    if os.path.exists(AFFILIATES_FILE):
        with open(AFFILIATES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"mandatory_disclosures": {}, "programs": []}

def generate_metadata_package(slug="prevent-prompt-injection-langchain-nemo"):
    build_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "build", slug))
    os.makedirs(build_dir, exist_ok=True)
    affiliates_data = load_affiliates()
    disclosures = affiliates_data.get("mandatory_disclosures", {})

    # Title: Strictly under 60 chars, keyword-first
    title = "LangChain Prompt Injection: Stop Jailbreaks with NeMo"
    if len(title) > 60:
        print(f"[WARN] Title exceeds 60 chars: {len(title)} chars", file=sys.stderr)

    tags = [
        "langchain prompt injection",
        "nemo guardrails tutorial",
        "llm security",
        "prevent prompt injection",
        "owasp llm top 10",
        "ai agent security",
        "langchain security",
        "colang guardrails",
        "nvidia nemo guardrails",
        "blue team ai",
        "cybersecurity for developers",
        "secure llm deployment",
        "prompt injection defense",
        "llm jailbreak prevention",
        "ai red teaming defense",
        "python ai security",
        "cloud security vps",
        "langchain tutorial 2026",
        "defensive security engineering",
        "zerosec ai"
    ]

    # Description template
    desc_lines = [
        "In this hands-on blue team tutorial, we walk through how to defend LangChain agents from prompt injection and runtime jailbreaks using NVIDIA NeMo Guardrails and programmable Colang flow policies.",
        "",
        "Never connect an LLM directly to tools, databases, or shell execution without a deterministic interception rail. Here is the exact architectural setup and testbed.",
        "",
        "⚡ CODE REPOSITORY & DEMO HARNESS:",
        f"https://github.com/YOUR_GITHUB_ORG/zerosec-demos/tree/main/{slug}",
        "",
        "⏱️ TIMESTAMPS:",
        "00:00 - The Threat: Hijacking LangChain in 10 Seconds",
        "00:30 - Threat Model: Why System Prompts Fail (OWASP LLM01)",
        "01:45 - Setting Up the Isolated Virtualenv Sandbox",
        "03:00 - Defining Colang Input & Output Guardrails",
        "05:00 - Live Attack Simulation: Exploit vs Guardrail Defense",
        "07:00 - Performance Tradeoff: Latency Benchmark Overhead",
        "08:00 - Production Verdict & Best Practices",
        "08:45 - Resources, VPS Sandboxes & Next Steps",
        "",
        "📚 VERIFIED DOCUMENTATION & SOURCES:",
        "• OWASP Top 10 for LLM Applications (LLM01: Prompt Injection): https://owasp.org/www-project-top-10-for-large-language-model-applications/",
        "• NVIDIA NeMo Guardrails Security Guidelines: https://github.com/NVIDIA/NeMo-Guardrails/blob/develop/docs/security/guidelines.md",
        "",
        "🛡️ RECOMMENDED DEVELOPER & SECURITY TOOLS:"
    ]

    for p in affiliates_data.get("programs", []):
        desc_lines.append(f"• {p['name']}: {p['url']}")
        desc_lines.append(f"  ({p['offer_text']})")

    desc_lines.extend([
        "",
        "⚖️ " + disclosures.get("description_notice", "DISCLOSURE: Contains affiliate links."),
        "",
        "#LangChain #PromptInjection #Cybersecurity #NeMoGuardrails #LLMSecurity #DevSecOps"
    ])

    description = "\n".join(desc_lines)

    pinned_comment = (
        "💬 Which guardrail framework are you using in production for your LLM agents (NeMo, Llama Guard, or custom regex)? "
        "Let me know your latency requirements below!\n\n"
        "🔗 Grab the full test scripts and Colang config here: "
        f"https://github.com/YOUR_GITHUB_ORG/zerosec-demos/tree/main/{slug}\n\n"
        f"({disclosures.get('pinned_comment_notice', 'Contains affiliate links.')})"
    )

    metadata_path = os.path.join(build_dir, "metadata.txt")
    with open(metadata_path, "w", encoding="utf-8") as f:
        f.write("=== YOUTUBE VIDEO METADATA PACKAGE ===\n\n")
        f.write(f"TITLE ({len(title)} chars):\n{title}\n\n")
        f.write(f"MADE FOR KIDS: False\n")
        f.write(f"CATEGORY: Science & Technology (28)\n\n")
        f.write(f"TAGS ({len(tags)} tags, comma-separated):\n")
        f.write(", ".join(tags) + "\n\n")
        f.write("DESCRIPTION:\n")
        f.write(description + "\n\n")
        f.write("PINNED COMMENT:\n")
        f.write(pinned_comment + "\n")

    print(f"[SUCCESS] Metadata package written ({len(title)} char title, {len(tags)} tags) -> {metadata_path}")
    return metadata_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug", default="prevent-prompt-injection-langchain-nemo")
    args = parser.parse_args()
    generate_metadata_package(args.slug)
