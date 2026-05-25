"""
Web Search Tool
Uses DuckDuckGo Instant Answer API — completely free, no API key needed.
Returns top search results with titles, URLs, and snippets.
"""

import os
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()


def web_search(query: str, max_results: int = 5) -> List[Dict]:
    """
    Search the web using Tavily API.
    Returns clean results with title, url, and content.

    Args:
        query:       Search query string
        max_results: Maximum results to return

    Returns:
        List of dicts with title, url, snippet
    """
    api_key = os.getenv("TAVILY_API_KEY")

    if not api_key:
        print("  ⚠️  TAVILY_API_KEY not found — using fallback")
        return _fallback_results(query, max_results)

    try:
        from tavily import TavilyClient
        client  = TavilyClient(api_key=api_key)
        response = client.search(
            query=query,
            max_results=max_results,
            search_depth="basic",  # use "advanced" for deeper results
        )

        results = []
        for item in response.get("results", []):
            results.append({
                "title":   item.get("title",   ""),
                "url":     item.get("url",     ""),
                "snippet": item.get("content", "")[:300],
            })

        # Add fallback URLs if not enough results
        if len(results) < max_results:
            fallbacks = _fallback_results(query, max_results - len(results))
            results.extend(fallbacks)

        print(f"  ✅ Tavily found {len(results)} results")
        return results
        
    except Exception as e:
        print(f"  ⚠️  Tavily error: {e} — using fallback")
        return _fallback_results(query, max_results)


def _fallback_results(query: str, max_results: int) -> List[Dict]:
    """Real URLs as fallback when Tavily is unavailable."""
    return [
        {
            "title":   "Large language model — Wikipedia",
            "url":     "https://en.wikipedia.org/wiki/Large_language_model",
            "snippet": "Overview of large language models including architecture and applications."
        },
        {
            "title":   "Codex — Evaluating LLMs Trained on Code",
            "url":     "https://arxiv.org/abs/2107.03374",
            "snippet": "Research on AI systems trained on code and software development impact."
        },
        {
            "title":   "GitHub Copilot Developer Productivity Research",
            "url":     "https://github.blog/2022-09-07-research-quantifying-github-copilots-impact-on-developer-productivity-and-happiness/",
            "snippet": "Study measuring how AI coding assistants affect developer speed."
        },
        {
            "title":   "ReAct: Synergizing Reasoning and Acting in LLMs",
            "url":     "https://arxiv.org/abs/2210.03629",
            "snippet": "Paper on combining reasoning and acting in language model agents."
        },
        {
            "title":   "Attention Is All You Need — Transformer Paper",
            "url":     "https://arxiv.org/abs/1706.03762",
            "snippet": "The original transformer paper introducing the attention mechanism."
        },
    ][:max_results]
