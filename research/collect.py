#!/usr/bin/env python3
"""
ZeroSec AI Research Agent - Phase 1
Collects trending security & AI developer problems from official APIs.
Scores topics based on search demand, freshness, demo feasibility, and affiliate tie-ins.
Emits a ranked top-20 /research/queue.md file.
"""

import os
import sys
import json
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone

HN_TOP_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"
GITHUB_SEARCH_URL = "https://api.github.com/search/repositories?q=topic:security+topic:ai&sort=updated&order=desc&per_page=15"
NVD_RECENT_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0?resultsPerPage=10"

HEADERS = {
    "User-Agent": "ZeroSecAI-ResearchAgent/1.0 (Defensive-AI-Security-Research)"
}

def fetch_json(url, headers=None, timeout=10):
    req = urllib.request.Request(url, headers=headers or HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print(f"[WARN] Error fetching {url}: {e}", file=sys.stderr)
        return None

def fetch_hacker_news_signals():
    print("[INFO] Fetching Hacker News security & AI signals...")
    top_ids = fetch_json(HN_TOP_URL)
    signals = []
    if not top_ids:
        return signals

    # Sample top 30 stories
    for item_id in top_ids[:30]:
        item = fetch_json(HN_ITEM_URL.format(item_id))
        if not item or "title" not in item:
            continue
        title = item.get("title", "")
        lower = title.lower()
        keywords = ["ai", "llm", "security", "vulnerability", "cve", "auth", "api", "prompt", "agent", "cloud", "docker", "guardrail"]
        if any(k in lower for k in keywords):
            signals.append({
                "source": "HackerNews",
                "title": title,
                "url": item.get("url", f"https://news.ycombinator.com/item?id={item_id}"),
                "score": item.get("score", 10),
                "comments": item.get("descendants", 0),
                "timestamp": item.get("time", int(time.time()))
            })
    return signals

def fetch_github_trending_signals():
    print("[INFO] Fetching GitHub security & AI repositories...")
    data = fetch_json(GITHUB_SEARCH_URL)
    signals = []
    if not data or "items" not in data:
        return signals

    for repo in data["items"][:15]:
        signals.append({
            "source": "GitHub",
            "title": f"{repo.get('name')}: {repo.get('description', '')}",
            "url": repo.get("html_url"),
            "stars": repo.get("stargazers_count", 0),
            "language": repo.get("language", "Python"),
            "timestamp": int(datetime.fromisoformat(repo.get("updated_at").replace("Z", "+00:00")).timestamp())
        })
    return signals

def fetch_nvd_signals():
    print("[INFO] Fetching NVD CVE alerts...")
    data = fetch_json(NVD_RECENT_URL)
    signals = []
    if not data or "vulnerabilities" not in data:
        return signals

    for item in data.get("vulnerabilities", [])[:10]:
        cve = item.get("cve", {})
        cve_id = cve.get("id", "CVE-UNKNOWN")
        descriptions = cve.get("descriptions", [{}])
        desc = descriptions[0].get("value", "") if descriptions else ""
        signals.append({
            "source": "NVD",
            "title": f"{cve_id}: {desc[:120]}...",
            "url": f"https://nvd.nist.gov/vuln/detail/{cve_id}",
            "cve_id": cve_id,
            "timestamp": int(time.time())
        })
    return signals

# Seed curated high-intent problem archetypes for US/EU professionals
CURATED_PROBLEM_TEMPLATES = [
    {
        "problem": "Prevent Prompt Injection in LangChain Agents with NeMo Guardrails",
        "slug": "prevent-prompt-injection-langchain-nemo",
        "target_keyword": "langchain prompt injection nemo guardrails tutorial",
        "search_demand": 9.2,
        "freshness": 9.5,
        "demo_ability": 10.0,
        "affiliate_availability": 8.5,
        "affiliate_category": "Cloud Infrastructure / VPS",
        "demo_stack": "Python 3.11, LangChain, NeMo Guardrails CLI",
        "defensive_focus": "Blue-team input sanitization and Colang rails enforcement"
    },
    {
        "problem": "Audit Model Context Protocol (MCP) Server Permissions and Leaks",
        "slug": "audit-mcp-server-security-permissions",
        "target_keyword": "mcp server security audit tools",
        "search_demand": 9.5,
        "freshness": 9.8,
        "demo_ability": 9.5,
        "affiliate_availability": 8.0,
        "affiliate_category": "Identity & Secrets Management",
        "demo_stack": "Node.js/TypeScript, Inspector, FastMCP",
        "defensive_focus": "Local filesystem containment and token boundary inspection"
    },
    {
        "problem": "Detecting Malicious PyPI Packages in CI/CD using GuardDog and Pip-Audit",
        "slug": "detect-malicious-pypi-packages-cicd-guarddog",
        "target_keyword": "guarddog pypi supply chain attack detection",
        "search_demand": 8.8,
        "freshness": 9.0,
        "demo_ability": 9.8,
        "affiliate_availability": 9.0,
        "affiliate_category": "Cloud Infrastructure",
        "demo_stack": "GitHub Actions, pip-audit, GuardDog CLI",
        "defensive_focus": "Software supply chain security and AST-based malicious package scanning"
    },
    {
        "problem": "Secure Dockerized LLM Inference with Rootless Containers and Seccomp",
        "slug": "secure-docker-llm-rootless-seccomp",
        "target_keyword": "docker rootless llm security container hardening",
        "search_demand": 8.5,
        "freshness": 8.7,
        "demo_ability": 9.5,
        "affiliate_availability": 9.5,
        "affiliate_category": "Cloud Infrastructure",
        "demo_stack": "Docker, vLLM/Ollama, Linux seccomp profile",
        "defensive_focus": "Hardening container privilege escalation boundaries"
    },
    {
        "problem": "Hardening Cloud IAM Secrets Against CI/CD Pipeline Exfiltration",
        "slug": "hardening-cloud-iam-secrets-cicd-exfiltration",
        "target_keyword": "prevent github actions secrets exfiltration aws iam",
        "search_demand": 9.0,
        "freshness": 8.9,
        "demo_ability": 9.2,
        "affiliate_availability": 9.8,
        "affiliate_category": "Identity & Secrets Management",
        "demo_stack": "OIDC, AWS IAM / Google Cloud IAM, GitHub Actions",
        "defensive_focus": "Zero-static-secret authentication using OpenID Connect"
    },
    {
        "problem": "Analyzing LLM SSRF Vulnerabilities in Retrieval-Augmented Generation (RAG)",
        "slug": "mitigate-rag-ssrf-vulnerabilities-vector-db",
        "target_keyword": "rag ssrf vector database security fix",
        "search_demand": 8.7,
        "freshness": 9.3,
        "demo_ability": 9.0,
        "affiliate_availability": 8.8,
        "affiliate_category": "Network & Intelligence / Proxies",
        "demo_stack": "Qdrant/Chroma, Python RAG crawler, network egress filtering",
        "defensive_focus": "Private IP blocklists and safe internal DNS resolution"
    },
    {
        "problem": "Enforcing HTTPS/TLS Client Certificate Auth (mTLS) for Internal Microservices",
        "slug": "enforce-mtls-internal-microservices-caddy",
        "target_keyword": "setup mtls internal microservices caddy python",
        "search_demand": 8.3,
        "freshness": 8.2,
        "demo_ability": 9.5,
        "affiliate_availability": 9.0,
        "affiliate_category": "Network Privacy",
        "demo_stack": "Caddy / Nginx, OpenSSL, Python FastAPI",
        "defensive_focus": "Zero Trust cryptographical identity between service meshes"
    }
]

def score_topic(search_demand, freshness, demo_ability, affiliate_availability):
    """
    Score = search_demand * freshness * demo_ability * affiliate_availability
    Scaled to a 100-point normalized index.
    """
    raw = (search_demand * freshness * demo_ability * affiliate_availability)
    # Max possible = 10 * 10 * 10 * 10 = 10,000 -> Scale to 100
    return round(raw / 100.0, 2)

def generate_queue():
    print("[INFO] Synthesizing research signals and problem templates...")
    hn_signals = fetch_hacker_news_signals()
    gh_signals = fetch_github_trending_signals()
    nvd_signals = fetch_nvd_signals()

    queue = []
    # Integrate curated high-yield problem topics
    for item in CURATED_PROBLEM_TEMPLATES:
        score = score_topic(
            item["search_demand"],
            item["freshness"],
            item["demo_ability"],
            item["affiliate_availability"]
        )
        queue.append({
            "problem": item["problem"],
            "slug": item["slug"],
            "target_keyword": item["target_keyword"],
            "score": score,
            "metrics": {
                "demand": item["search_demand"],
                "freshness": item["freshness"],
                "demo": item["demo_ability"],
                "affiliate": item["affiliate_availability"]
            },
            "affiliate_category": item["affiliate_category"],
            "demo_stack": item["demo_stack"],
            "defensive_focus": item["defensive_focus"],
            "source": "Engineered Long-Tail Search Intent"
        })

    # Convert high-signal HN / GH trends into long-tail problems
    for s in hn_signals[:5]:
        title = s["title"]
        slug = "".join(c if c.isalnum() else "-" for c in title.lower()[:40]).strip("-")
        queue.append({
            "problem": f"Blue-Team Analysis & Remediation: {title}",
            "slug": f"remediation-{slug}",
            "target_keyword": f"how to remediate {title.lower()[:30]}",
            "score": score_topic(8.0, 9.8, 8.5, 7.5),
            "metrics": {"demand": 8.0, "freshness": 9.8, "demo": 8.5, "affiliate": 7.5},
            "affiliate_category": "Cloud Infrastructure",
            "demo_stack": "Linux CLI, Python Audit Scripts",
            "defensive_focus": "Threat hunting and defensive architecture patch",
            "source": f"HN: {s['url']}"
        })

    for g in gh_signals[:5]:
        title = g["title"]
        slug = "".join(c if c.isalnum() else "-" for c in title.lower()[:40]).strip("-")
        queue.append({
            "problem": f"Hands-on Defensive Evaluation: {title.split(':')[0]} Security Architecture",
            "slug": f"eval-{slug}",
            "target_keyword": f"{title.split(':')[0].lower()} security review benchmark",
            "score": score_topic(8.4, 9.2, 9.0, 8.0),
            "metrics": {"demand": 8.4, "freshness": 9.2, "demo": 9.0, "affiliate": 8.0},
            "affiliate_category": "Cloud Infrastructure / VPS",
            "demo_stack": f"{g['language']}, Git, Docker",
            "defensive_focus": "Local testbed evaluation and static analysis",
            "source": f"GitHub: {g['url']}"
        })

    # Sort descending by score
    queue.sort(key=lambda x: x["score"], reverse=True)
    top_20 = queue[:20]

    # Write /research/queue.md
    out_dir = os.path.join(os.path.dirname(__file__))
    queue_path = os.path.join(out_dir, "queue.md")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        "# 🛡️ ZeroSec AI Topic Research Queue (Ranked Top 20)",
        f"*Generated automatically on: {now}*",
        "",
        "> **Formula:** `Score = (Demand × Freshness × DemoFeasibility × AffiliateMatch) / 100`",
        "> **Policy:** 100% Defensive / Blue-Team / Review content. Zero exploit code.",
        "",
        "| Rank | Score | Long-Tail Problem Title | Target Keyword | Stack / Demo | Affiliate Tie-In |",
        "| :---: | :---: | :--- | :--- | :--- | :--- |"
    ]

    for idx, item in enumerate(top_20, 1):
        lines.append(
            f"| **{idx}** | **{item['score']}** | `{item['problem']}` | *{item['target_keyword']}* | {item['demo_stack']} | {item['affiliate_category']} |"
        )

    lines.append("\n## Detailed Topic Dossiers\n")
    for idx, item in enumerate(top_20, 1):
        lines.append(f"### {idx}. {item['problem']}")
        lines.append(f"- **Slug:** `{item['slug']}`")
        lines.append(f"- **Search Query:** `{item['target_keyword']}`")
        lines.append(f"- **Defensive Focus:** {item['defensive_focus']}")
        lines.append(f"- **Demo Stack:** `{item['demo_stack']}`")
        lines.append(f"- **Affiliate Target:** {item['affiliate_category']}")
        lines.append(f"- **Scores:** Demand: {item['metrics']['demand']} | Freshness: {item['metrics']['freshness']} | Demo: {item['metrics']['demo']} | Affiliate: {item['metrics']['affiliate']}")
        lines.append(f"- **Source Reference:** {item['source']}")
        lines.append("")

    with open(queue_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"[SUCCESS] Research queue written with {len(top_20)} ranked topics -> {queue_path}")
    return queue_path

if __name__ == "__main__":
    generate_queue()
