"""
Deep Research Agent — Core ReAct Loop (OPTIMIZED for free tier)
Combines: ReAct + Web Search + Page Reading + Memory + Structured Output

Optimized to minimize API calls for Gemini free tier (15 RPM limit).
"""

import os
import re
import json
import time
import google.generativeai as genai
from dotenv import load_dotenv
from typing import Optional

from agent.memory     import ResearchMemory
from tools.web_search  import web_search
from tools.page_reader import read_page
from output.structured_report import (
    ResearchReport, ReportSection, Citation, ReflectionScore
)

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


REACT_SYSTEM_PROMPT = """You are a Deep Research Agent. Research the topic by searching and reading pages.

Tools:
  web_search(query)  — search for pages
  read_page(url)     — read a URL
  synthesize()       — write the report (use when you have 2+ sources)

Format:
Thought: <reasoning>
Action: <tool>("<arg>")

Rules:
- Do 1 search, read 2 pages, then synthesize
- Never read the same URL twice"""


class DeepResearchAgent:
    """
    Deep Research Agent v1 — Optimized for free tier API limits.
    
    Reduces API calls by:
    - Skipping per-page summarization
    - Generating entire report in ONE call
    - Skipping RAG embeddings
    - Using built-in reflection scores
    """

    def __init__(
        self,
        model_name:   str = "gemini-2.5-flash-lite",
        max_steps:    int = 8,
        min_sources:  int = 3,
        verbose:      bool = True,
    ):
        # Available models in order of preference (best free tier limits first)
        self.available_models = [
            "gemini-2.5-flash-lite",  # 15 RPM, 1000 RPD (best free tier)
            "gemini-2.5-flash",       # 10 RPM, 250 RPD  
            "gemini-2.5-pro",         # 5 RPM, 100 RPD
        ]
        
        # Set attributes first before calling _initialize_model
        self.model_name = model_name
        self.max_steps   = max_steps
        self.min_sources = min_sources
        self.verbose     = verbose
        
        # Now initialize model (which uses self.verbose)
        self.model = self._initialize_model()

    def _initialize_model(self):
        """Try to initialize with the best available model."""
        models_to_try = [self.model_name] + [m for m in self.available_models if m != self.model_name]
        
        for model_name in models_to_try:
            try:
                model = genai.GenerativeModel(model_name)
                self.model_name = model_name
                print(f"  ✅ Using model: {model_name}")
                return model
            except Exception as e:
                print(f"  ⚠️  {model_name} failed: {str(e)[:100]}...")
                continue
        
        # If all fail, raise an error with helpful message
        raise Exception(f"All models failed. Available models: {self.available_models}. Check your API key and quota.")

    def _call_llm(self, prompt: str, label: str = "") -> str:
        """Call Gemini with rate limit handling and longer delays."""
        for attempt in range(3):
            try:
                if self.verbose and label:
                    print(f"    📡 [{label}]...")
                response = self.model.generate_content(prompt)
                # Wait 8 seconds between calls to stay well under 15 RPM
                time.sleep(8)
                return response.text.strip()
            except Exception as e:
                err_str = str(e).lower()
                if "429" in str(e) or "quota" in err_str or "resource" in err_str:
                    wait = 60 * (attempt + 1)
                    print(f"    ⚠️  Rate limit — waiting {wait}s...")
                    time.sleep(wait)
                else:
                    print(f"    ❌ Error: {e}")
                    return f"Error: {str(e)}"
        return "Error: max retries exceeded"

    def _parse_action(self, llm_output: str) -> tuple:
        """Parse Thought and Action from LLM output."""
        thought_match = re.search(
            r"Thought:\s*(.+?)(?=\nAction:|$)", llm_output, re.DOTALL
        )
        action_match = re.search(
            r'Action:\s*(\w+)\s*\(\s*["\']?(.*?)["\']?\s*\)',
            llm_output, re.DOTALL
        )

        thought = thought_match.group(1).strip() if thought_match else ""
        action  = action_match.group(1).strip()  if action_match  else ""
        arg     = action_match.group(2).strip()  if action_match  else ""

        return thought, action, arg

    def _generate_report(self, memory: ResearchMemory) -> ResearchReport:
        """
        Generate the ENTIRE report in ONE LLM call to minimize API usage.
        """
        topic    = memory.topic
        findings = memory.get_findings_summary()

        # Single comprehensive prompt for entire report
        prompt = f"""You are writing a research report on: "{topic}"

Research findings:
{findings[:3000]}

Generate a complete research report as JSON with this EXACT structure:
{{
  "summary": "2-3 sentence executive summary",
  "sections": [
    {{"heading": "Introduction", "content": "150-200 words with [1] citations", "key_points": ["point1", "point2"]}},
    {{"heading": "Key Findings", "content": "150-200 words with citations", "key_points": ["point1", "point2"]}},
    {{"heading": "Implications", "content": "150-200 words with citations", "key_points": ["point1", "point2"]}},
    {{"heading": "Conclusion", "content": "100-150 words summary", "key_points": ["point1", "point2"]}}
  ],
  "key_findings": ["finding 1", "finding 2", "finding 3", "finding 4", "finding 5"],
  "limitations": ["limitation 1", "limitation 2"],
  "reflection": {{
    "coverage": 7,
    "depth": 6,
    "citations": 7,
    "clarity": 7,
    "overall": 7,
    "strengths": ["strength 1", "strength 2"],
    "weaknesses": ["weakness 1", "weakness 2"]
  }}
}}

Use [1], [2] etc. to cite sources. Reply with ONLY valid JSON, no markdown."""

        raw = self._call_llm(prompt, "Generating full report")
        
        try:
            clean = re.sub(r"```(?:json)?|```", "", raw).strip()
            data  = json.loads(clean)
        except Exception as e:
            print(f"    ⚠️  JSON parse failed, using fallback: {e}")
            # Fallback report
            data = {
                "summary": f"Research report on {topic} based on {memory.source_count()} sources.",
                "sections": [
                    {"heading": "Overview", "content": findings[:500], "key_points": []},
                ],
                "key_findings": [f.summary[:100] for f in memory.findings[:5]],
                "limitations": ["Limited sources available"],
                "reflection": {
                    "coverage": 6, "depth": 6, "citations": 6, 
                    "clarity": 7, "overall": 6,
                    "strengths": ["Research completed"],
                    "weaknesses": ["Could use more sources"]
                }
            }

        # Build sections
        sections = []
        for s in data.get("sections", []):
            sections.append(ReportSection(
                heading=s.get("heading", "Section"),
                content=s.get("content", ""),
                key_points=s.get("key_points", []),
                citations=[],
            ))

        # Build citations from memory
        citations = [
            Citation(
                index=c["index"],
                title=c["title"],
                url=c["url"],
                excerpt=c["excerpt"],
                relevance=f"Source {c['index']}",
            )
            for c in memory.citations
        ]

        # Build reflection
        ref_data = data.get("reflection", {})
        reflection = ReflectionScore(
            coverage=ref_data.get("coverage", 7),
            depth=ref_data.get("depth", 6),
            citations=ref_data.get("citations", 7),
            clarity=ref_data.get("clarity", 7),
            overall=ref_data.get("overall", 7),
            strengths=ref_data.get("strengths", []),
            weaknesses=ref_data.get("weaknesses", []),
        )

        return ResearchReport(
            topic=topic,
            summary=data.get("summary", ""),
            sections=sections,
            citations=citations,
            key_findings=data.get("key_findings", []),
            limitations=data.get("limitations", []),
            total_sources=memory.source_count(),
            reflection=reflection,
        )

    def research(self, topic: str) -> ResearchReport:
        """
        Main entry point — research a topic and return a structured report.
        
        OPTIMIZED: Only ~5-6 LLM calls total instead of 15-20.
        """
        print(f"\n{'='*60}")
        print(f"  🔬 DEEP RESEARCH AGENT v1 (Optimized)")
        print(f"  Topic: {topic}")
        print(f"  Model: {self.model_name}")
        print(f"{'='*60}")

        memory     = ResearchMemory(topic=topic)
        scratchpad = ""
        step       = 0

        # ── ReAct Loop ─────────────────────────────
        while step < self.max_steps:
            step += 1
            print(f"\n[Step {step}/{self.max_steps}]")

            # Build prompt with context
            context = f"Topic: {topic}\n"
            if memory.visited_urls:
                context += f"URLs visited: {len(memory.visited_urls)}\n"
            if memory.search_queries:
                context += f"Searches done: {memory.search_queries}\n"
            if memory.source_count() >= self.min_sources:
                context += f"\n⚡ You have {memory.source_count()} sources — synthesize NOW.\n"

            prompt = (
                f"{REACT_SYSTEM_PROMPT}\n\n"
                f"Context:\n{context}\n\n"
                f"Previous:\n{scratchpad[-1500:]}\n\n"
                f"Next action?"
            )

            llm_output = self._call_llm(prompt, "ReAct")
            thought, action, arg = self._parse_action(llm_output)

            if not action:
                print(f"  ⚠️  No action parsed, nudging...")
                scratchpad += "(Use web_search, read_page, or synthesize)\n"
                continue

            print(f"  💭 Thought: {thought[:80]}...")
            print(f"  🔧 Action : {action}({repr(arg)[:50]})")

            memory.add_step("thought", thought)
            memory.add_step("action",  f"{action}({arg})")

            # ── Tool: web_search ──
            if action == "web_search" and arg:
                memory.search_queries.append(arg)
                results = web_search(arg, max_results=3)
                obs = f"Found {len(results)} results:\n"
                for i, r in enumerate(results, 1):
                    obs += f"  {i}. {r['title'][:50]} — {r['url']}\n"
                print(f"  👁️  {obs[:150]}...")
                memory.add_step("observation", obs)
                scratchpad += f"Action: web_search(\"{arg}\")\nResult: {obs}\n"

            # ── Tool: read_page ──
            elif action == "read_page" and arg:
                if memory.has_visited(arg):
                    print(f"  ⏭️  Already visited, skipping")
                else:
                    print(f"  📄 Reading: {arg[:50]}...")
                    page = read_page(arg)
                    # NO summarization call — just store raw content
                    summary = page["content"][:300] + "..."
                    memory.add_finding(arg, page["title"], page["content"], summary)
                    obs = f"Read: {page['title'][:50]}"
                    print(f"  👁️  {obs}")
                    memory.add_step("observation", obs)
                    scratchpad += f"Action: read_page — got {page['title'][:40]}\n"

            # ── Tool: synthesize ──
            elif action == "synthesize":
                if memory.source_count() < self.min_sources:
                    obs = f"Need {self.min_sources} sources, have {memory.source_count()}"
                    print(f"  ⚠️  {obs}")
                    scratchpad += f"(Need more sources)\n"
                    continue
                print(f"\n  ✅ Synthesizing from {memory.source_count()} sources...")
                break
            else:
                scratchpad += "(Use web_search, read_page, or synthesize)\n"

        # ── Generate Report (ONE call) ─────────────
        print(f"\n{'─'*60}")
        print(f"  📝 Generating report (single API call)...")
        print(f"{'─'*60}")
        
        report = self._generate_report(memory)

        avg_score = (
            report.reflection.coverage +
            report.reflection.depth +
            report.reflection.citations +
            report.reflection.clarity +
            report.reflection.overall
        ) / 5
        print(f"  📊 Quality score: {avg_score:.1f}/10")

        return report
