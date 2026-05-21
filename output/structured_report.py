"""
Structured Report Models
Pydantic models for the final research report output.
Every claim must have a citation — no uncited facts allowed.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class Citation(BaseModel):
    """A single source citation."""
    index:   int    = Field(description="Citation number e.g. [1]")
    title:   str    = Field(description="Page or article title")
    url:     str    = Field(description="Source URL")
    excerpt: str    = Field(description="Relevant excerpt from the source")
    relevance: str  = Field(description="Why this source is relevant")


class ReportSection(BaseModel):
    """A single section of the research report."""
    heading:     str       = Field(description="Section heading")
    content:     str       = Field(description="Section content with inline [N] citations")
    citations:   List[int] = Field(description="Citation indices used in this section")
    key_points:  List[str] = Field(description="Bullet point key takeaways")


class ReflectionScore(BaseModel):
    """Self-critique scores for the report."""
    coverage:    int = Field(ge=1, le=10, description="How well the topic is covered")
    depth:       int = Field(ge=1, le=10, description="Depth of analysis")
    citations:   int = Field(ge=1, le=10, description="Quality of citations")
    clarity:     int = Field(ge=1, le=10, description="Writing clarity")
    overall:     int = Field(ge=1, le=10, description="Overall quality")
    weaknesses:  List[str] = Field(description="Areas that need improvement")
    strengths:   List[str] = Field(description="What was done well")


class ResearchReport(BaseModel):
    """
    The complete structured research report.
    This is the final output of the Deep Research Agent.
    """
    topic:          str = Field(description="Research topic")
    summary:        str = Field(description="Executive summary (2-3 sentences)")
    sections:       List[ReportSection]
    citations:      List[Citation]
    key_findings:   List[str] = Field(description="Top 5 most important findings")
    limitations:    List[str] = Field(description="Limitations of this research")
    generated_at:   str = Field(default_factory=lambda: datetime.now().isoformat())
    total_sources:  int = Field(description="Number of sources consulted")
    reflection:     Optional[ReflectionScore] = None

    def to_markdown(self) -> str:
        """Convert report to formatted markdown string."""
        lines = [
            f"# Research Report: {self.topic}",
            f"\n**Generated:** {self.generated_at}",
            f"**Sources consulted:** {self.total_sources}",
            f"\n---\n",
            f"## Executive Summary\n{self.summary}\n",
            f"## Key Findings",
        ]
        for i, finding in enumerate(self.key_findings, 1):
            lines.append(f"{i}. {finding}")

        lines.append("\n---\n")
        for section in self.sections:
            lines.append(f"## {section.heading}\n")
            lines.append(section.content)
            if section.key_points:
                lines.append("\n**Key Points:**")
                for point in section.key_points:
                    lines.append(f"- {point}")
            lines.append("")

        lines.append("\n---\n## References\n")
        for cite in self.citations:
            lines.append(
                f"[{cite.index}] **{cite.title}**  \n"
                f"URL: {cite.url}  \n"
                f"*{cite.excerpt[:150]}...*\n"
            )

        if self.reflection:
            r = self.reflection
            avg = (r.coverage + r.depth + r.citations + r.clarity + r.overall) / 5
            lines.append(f"\n---\n## Self-Reflection Score: {avg:.1f}/10\n")
            lines.append(f"- Coverage: {r.coverage}/10")
            lines.append(f"- Depth: {r.depth}/10")
            lines.append(f"- Citations: {r.citations}/10")
            lines.append(f"- Clarity: {r.clarity}/10")
            if r.strengths:
                lines.append(f"\n**Strengths:** {', '.join(r.strengths)}")
            if r.weaknesses:
                lines.append(f"**Areas for improvement:** {', '.join(r.weaknesses)}")

        if self.limitations:
            lines.append(f"\n---\n## Limitations")
            for lim in self.limitations:
                lines.append(f"- {lim}")

        return "\n".join(lines)

    def to_html(self) -> str:
        """Convert report to a clean HTML file."""
        md = self.to_markdown()
        sections_html = ""
        for section in self.sections:
            points_html = "".join(
                f"<li>{p}</li>" for p in section.key_points
            )
            sections_html += f"""
            <div class="section">
                <h2>{section.heading}</h2>
                <p>{section.content.replace(chr(10), '<br>')}</p>
                <ul>{points_html}</ul>
            </div>"""

        citations_html = "".join(
            f'<li><strong>[{c.index}] {c.title}</strong><br>'
            f'<a href="{c.url}">{c.url}</a><br>'
            f'<em>{c.excerpt[:200]}...</em></li>'
            for c in self.citations
        )

        findings_html = "".join(
            f"<li>{f}</li>" for f in self.key_findings
        )

        reflection_html = ""
        if self.reflection:
            r = self.reflection
            avg = (r.coverage + r.depth + r.citations + r.clarity + r.overall) / 5
            reflection_html = f"""
            <div class="reflection">
                <h2>🔍 Self-Reflection Score: {avg:.1f}/10</h2>
                <div class="scores">
                    <span>Coverage: {r.coverage}/10</span>
                    <span>Depth: {r.depth}/10</span>
                    <span>Citations: {r.citations}/10</span>
                    <span>Clarity: {r.clarity}/10</span>
                </div>
            </div>"""

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Research Report: {self.topic}</title>
<style>
  body {{ font-family: Georgia, serif; max-width: 900px; margin: 40px auto;
         padding: 0 20px; color: #333; line-height: 1.7; }}
  h1   {{ color: #1a1a2e; border-bottom: 3px solid #4a90d9; padding-bottom: 10px; }}
  h2   {{ color: #16213e; margin-top: 40px; }}
  .meta  {{ color: #666; font-size: 0.9em; margin-bottom: 30px; }}
  .summary {{ background: #f0f4ff; padding: 20px; border-radius: 8px;
              border-left: 4px solid #4a90d9; margin: 20px 0; }}
  .section {{ margin: 30px 0; padding: 20px; background: #fafafa;
              border-radius: 8px; }}
  .section ul {{ color: #444; }}
  .reflection {{ background: #fff9e6; padding: 20px; border-radius: 8px;
                 border-left: 4px solid #f5a623; margin: 30px 0; }}
  .scores {{ display: flex; gap: 20px; flex-wrap: wrap; margin-top: 10px; }}
  .scores span {{ background: #4a90d9; color: white; padding: 5px 12px;
                  border-radius: 20px; font-size: 0.9em; }}
  .findings li {{ margin: 8px 0; }}
  .citations li {{ margin: 15px 0; font-size: 0.9em; }}
  a {{ color: #4a90d9; }}
  hr {{ border: none; border-top: 1px solid #ddd; margin: 40px 0; }}
</style>
</head>
<body>
<h1>📋 {self.topic}</h1>
<div class="meta">
  Generated: {self.generated_at} | Sources: {self.total_sources}
</div>
<div class="summary"><h2>Executive Summary</h2><p>{self.summary}</p></div>
<h2>🔑 Key Findings</h2>
<ol class="findings">{findings_html}</ol>
<hr>
{sections_html}
<hr>
{reflection_html}
<hr>
<h2>📚 References</h2>
<ol class="citations">{citations_html}</ol>
</body>
</html>"""
