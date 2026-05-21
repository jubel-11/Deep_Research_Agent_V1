"""
Research Agent Memory
Stores the agent's findings, visited URLs, and reasoning steps
across the full ReAct research loop.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class Finding:
    """A single research finding from a page."""
    url:     str
    title:   str
    content: str
    summary: str  # LLM-generated summary of this page


@dataclass
class ResearchMemory:
    """
    Memory system for the research agent.
    Combines:
      - Buffer memory   : recent ReAct steps
      - Working memory  : all findings accumulated so far
      - Episodic memory : which URLs have been visited
    """
    topic:          str
    findings:       List[Finding]      = field(default_factory=list)
    visited_urls:   List[str]          = field(default_factory=list)
    search_queries: List[str]          = field(default_factory=list)
    react_steps:    List[Dict]         = field(default_factory=list)
    citations:      List[Dict]         = field(default_factory=list)

    def add_finding(self, url: str, title: str, content: str, summary: str):
        """Add a new research finding."""
        if url not in self.visited_urls:
            self.visited_urls.append(url)
            self.findings.append(Finding(
                url=url, title=title,
                content=content, summary=summary
            ))
            # Add as citation
            self.citations.append({
                "index": len(self.citations) + 1,
                "title": title,
                "url":   url,
                "excerpt": content[:200],
            })

    def add_step(self, step_type: str, content: str):
        """Record a ReAct step (Thought/Action/Observation)."""
        self.react_steps.append({
            "type":    step_type,
            "content": content,
            "step_n":  len(self.react_steps) + 1,
        })

    def get_findings_summary(self) -> str:
        """Return all findings as a formatted string for prompts."""
        if not self.findings:
            return "No findings yet."
        parts = []
        for i, f in enumerate(self.findings, 1):
            parts.append(f"[Source {i}] {f.title}\nURL: {f.url}\n{f.summary}")
        return "\n\n---\n\n".join(parts)

    def has_visited(self, url: str) -> bool:
        return url in self.visited_urls

    def source_count(self) -> int:
        return len(self.findings)

    def __repr__(self):
        return (f"ResearchMemory(topic={self.topic!r}, "
                f"sources={self.source_count()}, "
                f"steps={len(self.react_steps)})")
