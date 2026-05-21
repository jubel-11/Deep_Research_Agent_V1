"""
Reflection Module
The agent reviews its own report and scores it.
Based on the Reflexion pattern from Week 1.

After the report is written, the agent:
  1. Reads its own output
  2. Scores it on 5 dimensions
  3. Identifies weaknesses
  4. Returns a ReflectionScore attached to the report
"""

import os
import re
import json
import time
import google.generativeai as genai
from dotenv import load_dotenv
from output.structured_report import ReflectionScore, ResearchReport

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


def reflect_on_report(
    report: ResearchReport,
    model_name: str = "gemini-2.5-flash-lite"
) -> ReflectionScore:
    """
    Agent reviews its own report and produces a self-critique.

    Args:
        report:     The generated ResearchReport
        model_name: Gemini model to use

    Returns:
        ReflectionScore with scores and feedback
    """
    model = genai.GenerativeModel(model_name)

    # Format report for review
    report_preview = f"""
Topic: {report.topic}
Summary: {report.summary}
Sections: {[s.heading for s in report.sections]}
Key findings: {report.key_findings[:3]}
Number of citations: {len(report.citations)}
Total sources: {report.total_sources}
Sample section content: {report.sections[0].content[:300] if report.sections else 'None'}
"""

    prompt = f"""You are a research quality evaluator reviewing an AI-generated research report.

Report to evaluate:
{report_preview}

Score this report on each dimension from 1-10:
- coverage:   Does it cover the topic broadly and thoroughly?
- depth:      Does it go beyond surface-level information?
- citations:  Are claims well-supported with sources?
- clarity:    Is the writing clear and well-structured?
- overall:    Overall quality as a research report?

Also identify:
- strengths:  2-3 things done well
- weaknesses: 2-3 specific areas needing improvement

Reply with ONLY this JSON (no markdown, no extra text):
{{
  "coverage": 7,
  "depth": 6,
  "citations": 8,
  "clarity": 7,
  "overall": 7,
  "strengths": ["Good source variety", "Clear structure"],
  "weaknesses": ["Needs more quantitative data", "Some sections too brief"]
}}"""

    try:
        response = model.generate_content(prompt)
        raw      = response.text.strip()
        clean    = re.sub(r"```(?:json)?|```", "", raw).strip()
        data     = json.loads(clean)
        time.sleep(3)

        return ReflectionScore(
            coverage=   int(data.get("coverage",   7)),
            depth=      int(data.get("depth",       6)),
            citations=  int(data.get("citations",   7)),
            clarity=    int(data.get("clarity",     7)),
            overall=    int(data.get("overall",     7)),
            strengths=  data.get("strengths",  []),
            weaknesses= data.get("weaknesses", []),
        )

    except Exception as e:
        print(f"  ⚠️  Reflection failed: {e} — using default scores")
        return ReflectionScore(
            coverage=7, depth=6, citations=7, clarity=7, overall=7,
            strengths=["Research completed successfully"],
            weaknesses=["Could not perform detailed self-evaluation"],
        )
