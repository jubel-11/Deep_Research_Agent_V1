"""
Deep Research Agent v1 — Main Entry Point
Week 2 Project: ReAct + Tools + Memory + RAG + Structured Output + Reflection

Note: Built with Python + Gemini API (substituted for OpenAI as specified
in project — identical architecture, only API client differs)
"""

import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


def check_setup():
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY not found in .env file")
        sys.exit(1)
    os.makedirs("reports", exist_ok=True)
    print("  ✅ Setup OK")


def save_report(report, topic: str):
    """Save report as HTML, Markdown, and JSON."""
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug       = topic.lower().replace(" ", "_")[:30]
    base       = f"reports/{slug}_{timestamp}"

    # Markdown
    md_file = f"{base}.md"
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(report.to_markdown())
    print(f"  💾 Markdown : {md_file}")

    # HTML
    html_file = f"{base}.html"
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(report.to_html())
    print(f"  💾 HTML     : {html_file}")

    # JSON (structured data)
    json_file = f"{base}.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(report.model_dump(), f, indent=2, default=str)
    print(f"  💾 JSON     : {json_file}")

    return html_file


def print_report_summary(report):
    """Print a summary of the report to the terminal."""
    print(f"\n{'='*60}")
    print(f"  📋 RESEARCH REPORT SUMMARY")
    print(f"{'='*60}")
    print(f"  Topic    : {report.topic}")
    print(f"  Sources  : {report.total_sources}")
    print(f"  Sections : {len(report.sections)}")
    print(f"  Citations: {len(report.citations)}")

    print(f"\n  📌 Executive Summary:")
    print(f"  {report.summary}")

    print(f"\n  🔑 Key Findings:")
    for i, finding in enumerate(report.key_findings, 1):
        print(f"  {i}. {finding[:80]}...")

    print(f"\n  📚 Sources Used:")
    for c in report.citations:
        print(f"  [{c.index}] {c.title[:50]} — {c.url[:50]}")

    if report.reflection:
        r   = report.reflection
        avg = (r.coverage + r.depth + r.citations + r.clarity + r.overall) / 5
        print(f"\n  🔍 Self-Reflection: {avg:.1f}/10")
        print(f"     Coverage: {r.coverage} | Depth: {r.depth} | "
              f"Citations: {r.citations} | Clarity: {r.clarity}")
        if r.strengths:
            print(f"     ✅ {r.strengths[0]}")
        if r.weaknesses:
            print(f"     ⚠️  {r.weaknesses[0]}")

    print(f"\n{'='*60}")


DEFAULT_TOPIC = "The impact of large language models on software engineering"


if __name__ == "__main__":
    print("\n🔬 Deep Research Agent v1")
    print("=" * 60)
    print()

    check_setup()

    print("\n1 → Demo topic (LLMs impact on software engineering)")
    print("2 → Enter your own topic")

    choice = input("\nYour choice (1 or 2): ").strip()

    if choice == "2":
        topic = input("Enter research topic: ").strip()
        if not topic:
            topic = DEFAULT_TOPIC
    else:
        topic = DEFAULT_TOPIC

    from agent.research_agent import DeepResearchAgent

    agent  = DeepResearchAgent(
        model_name="gemini-2.5-flash-lite",  # Best available free tier: 15 RPM, 1000 RPD
        max_steps=8,                          # Reduced to minimize API calls
        min_sources=3,
        verbose=True,
    )

    report = agent.research(topic)

    print_report_summary(report)
    html_file = save_report(report, topic)

    print(f"\n✅ Research complete!")
    print(f"   Open '{html_file}' in your browser to view the full report.")
