"""Search tools for the chat agent: arXiv, and Tavily web search when TAVILY_API_KEY is set."""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

log = logging.getLogger(__name__)

_ARXIV_API = "http://export.arxiv.org/api/query"
_TAVILY_API = "https://api.tavily.com/search"


def search_arxiv(query: str, max_results: int = 5) -> str:
    """Search arXiv for papers matching a query.

    Returns titles, authors, abstracts, and links for the top results.
    Use this when you need to reference real papers, find seminal works,
    or ground your content in published research.

    Args:
        query: Search query (e.g. "importance sampling variance reduction").
        max_results: Maximum number of results (default 5, max 10).
    """
    max_results = min(max_results, 10)
    params = urllib.parse.urlencode({
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    })
    url = f"{_ARXIV_API}?{params}"

    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = resp.read().decode("utf-8")
    except (urllib.error.URLError, TimeoutError) as e:
        log.warning("arXiv search failed: %s", e)
        return f"Error: arXiv search failed: {e}"

    # Parse Atom XML
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(data)
    entries = root.findall("atom:entry", ns)

    if not entries:
        return f"No arXiv results for: {query}"

    results = []
    for entry in entries:
        title = entry.findtext("atom:title", "", ns).strip().replace("\n", " ")
        summary = entry.findtext("atom:summary", "", ns).strip().replace("\n", " ")
        # Truncate long abstracts
        if len(summary) > 400:
            summary = summary[:400] + "..."
        authors = [a.findtext("atom:name", "", ns) for a in entry.findall("atom:author", ns)]
        authors_str = ", ".join(authors[:5])
        if len(authors) > 5:
            authors_str += f" (+{len(authors) - 5} more)"
        link = ""
        for lnk in entry.findall("atom:link", ns):
            if lnk.get("type") == "text/html":
                link = lnk.get("href", "")
                break
        if not link:
            link = entry.findtext("atom:id", "", ns)

        results.append(
            f"**{title}**\n"
            f"Authors: {authors_str}\n"
            f"Link: {link}\n"
            f"Abstract: {summary}"
        )

    return "\n\n---\n\n".join(results)

def web_search(query: str, max_results: int = 5) -> str:
    """Search the web using Tavily for general information.

    Use this for finding tutorials, blog posts, documentation, or any
    non-academic content. Complements arXiv search for broader coverage.

    Args:
        query: Search query (e.g. "Bellman equation intuitive explanation").
        max_results: Maximum number of results (default 5, max 10).
    """
    api_key = os.environ.get("TAVILY_API_KEY", "")
    if not api_key:
        return "Error: TAVILY_API_KEY environment variable not set."

    max_results = min(max_results, 10)
    payload = json.dumps({
        "query": query,
        "max_results": max_results,
        "include_answer": True,
    }).encode("utf-8")

    req = urllib.request.Request(
        _TAVILY_API,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError) as e:
        log.warning("Tavily search failed: %s", e)
        return f"Error: Web search failed: {e}"

    parts = []

    # Tavily sometimes returns a direct answer
    answer = data.get("answer")
    if answer:
        parts.append(f"**Summary:** {answer}")

    for result in data.get("results", []):
        title = result.get("title", "Untitled")
        url = result.get("url", "")
        content = result.get("content", "")
        if len(content) > 400:
            content = content[:400] + "..."
        parts.append(f"**{title}**\nURL: {url}\n{content}")

    return "\n\n---\n\n".join(parts) if parts else f"No web results for: {query}"


def web_search_enabled() -> bool:
    return bool(os.environ.get("TAVILY_API_KEY"))
