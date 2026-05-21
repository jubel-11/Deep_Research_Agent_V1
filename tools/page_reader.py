"""
Page Reader Tool
Fetches a web page and extracts clean readable text.
Strips HTML tags, navigation, ads, and boilerplate.
"""

import requests
import re
from typing import Optional


def read_page(url: str, max_chars: int = 3000) -> dict:
    """
    Fetch a web page and extract clean text content.

    Args:
        url:       URL to fetch
        max_chars: Maximum characters to return (keep chunks manageable)

    Returns:
        Dict with url, title, content, success flag
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml",
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        html    = response.text
        title   = _extract_title(html)
        content = _extract_text(html)

        # Truncate to max_chars
        if len(content) > max_chars:
            content = content[:max_chars] + "..."

        return {
            "url":     url,
            "title":   title,
            "content": content,
            "success": True,
            "chars":   len(content),
        }

    except requests.exceptions.Timeout:
        return {"url": url, "title": "", "content": "Page timed out.", "success": False, "chars": 0}
    except requests.exceptions.HTTPError as e:
        return {"url": url, "title": "", "content": f"HTTP error: {e}", "success": False, "chars": 0}
    except Exception as e:
        return {"url": url, "title": "", "content": f"Error: {str(e)}", "success": False, "chars": 0}


def _extract_title(html: str) -> str:
    """Extract page title from HTML."""
    match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if match:
        return _clean_text(match.group(1))[:100]
    return "Unknown Title"


def _extract_text(html: str) -> str:
    """
    Extract readable text from HTML.
    Removes scripts, styles, nav, footer, and cleans whitespace.
    """
    # Remove script and style blocks
    html = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<style[^>]*>.*?</style>",  " ", html, flags=re.DOTALL | re.IGNORECASE)

    # Remove nav, header, footer, aside (boilerplate)
    for tag in ["nav", "header", "footer", "aside", "menu"]:
        html = re.sub(
            f"<{tag}[^>]*>.*?</{tag}>", " ", html,
            flags=re.DOTALL | re.IGNORECASE
        )

    # Convert paragraph and heading tags to newlines
    html = re.sub(r"<br\s*/?>",    "\n", html, flags=re.IGNORECASE)
    html = re.sub(r"<p[^>]*>",     "\n", html, flags=re.IGNORECASE)
    html = re.sub(r"<h[1-6][^>]*>", "\n", html, flags=re.IGNORECASE)
    html = re.sub(r"<li[^>]*>",    "\n• ", html, flags=re.IGNORECASE)

    # Strip all remaining HTML tags
    text = re.sub(r"<[^>]+>", " ", html)

    return _clean_text(text)


def _clean_text(text: str) -> str:
    """Clean up whitespace and special characters."""
    # Decode common HTML entities
    entities = {
        "&amp;": "&", "&lt;": "<", "&gt;": ">",
        "&nbsp;": " ", "&quot;": '"', "&#39;": "'",
        "&mdash;": "—", "&ndash;": "–", "&hellip;": "...",
    }
    for entity, char in entities.items():
        text = text.replace(entity, char)

    # Collapse whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()
