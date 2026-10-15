"""The agent team under debug: Magentic-One orchestrator + Coder + Executor + WebSearcher (cached web)."""

from __future__ import annotations

import asyncio
import html
import json
import os
import re
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from unittest.mock import patch

from autogen_agentchat.agents import AssistantAgent, CodeExecutorAgent
from autogen_agentchat.teams import MagenticOneGroupChat
from autogen_ext.agents.magentic_one import MagenticOneCoderAgent
from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor

from .llm import AnthropicClient

CORPUS = json.loads((Path(__file__).with_name("corpus.json")).read_text())
_WORD = re.compile(r"[a-z0-9]+")


def _tokens(s: str) -> set[str]:
    return set(_WORD.findall(s.lower()))


async def web_search(query: str) -> str:
    """Search the web. Returns the top 5 results as title, url and a short snippet."""
    q = _tokens(query)
    scored = []
    for page in CORPUS:
        score = 3 * len(q & _tokens(page["title"])) + len(q & _tokens(page["body"]))
        if score:
            scored.append((score, page))
    scored.sort(key=lambda t: -t[0])
    if not scored:
        return "No results."
    return "\n\n".join(
        f"[{i + 1}] {p['title']}\n{p['url']}\n{p['body'][:140].strip()}..." for i, (_, p) in enumerate(scored[:5])
    )


PAGE_CHARS = 900
BOILERPLATE = {
    "lumenvalleyobservatory.org": (
        "Lumen Valley Observatory | Halden Ridge\nSkip to content. Menu: Home | Visit | Tickets and opening hours | Night tours | "
        "School visits | Facilities | Research | News | Reports | About | Governance | Contact. "
        "We use cookies to improve your experience; see our cookie policy. Search this site. "
        "Plan your visit: open Tuesday to Sunday 10:00 to 21:00, closed Mondays and public holidays. "
        "Accessibility: the visitor centre and planetarium are step-free; the Aster dome is reached by 42 steps. "
        "Newsletter: sign up for monthly sky highlights and event news. Follow us on social media.\n\n"
    ),
    "haldenherald.com": "Halden Herald - local news since 1922 | Subscribe | Sign in | Weather | Sport | Obituaries | Classifieds\n\n",
    "lvpo.org": "Lumen Valley Public Observatory - volunteer-run since 1994 | Home | Telescopes | Events | Join us\n\n",
}


async def fetch_page(url: str, offset: int = 0) -> str:
    """Fetch the text of a web page by its url. Long pages are returned in chunks of 900 characters;
    pass `offset` (the value given at the end of a chunk) to read the next part."""
    for page in CORPUS:
        if page["url"] == url:
            host = url.split("/")[2].removeprefix("www.")
            text = f"# {page['title']}\n\n{BOILERPLATE.get(host, '')}{page['body']}"
            chunk = text[offset:offset + PAGE_CHARS]
            if offset + PAGE_CHARS < len(text):
                chunk += f"\n\n[... page continues; call fetch_page(url, offset={offset + PAGE_CHARS}) for the next part]"
            return chunk or "(empty)"
    return f"404: no page at {url}"


# ---- live Wikipedia (GAIA-style tasks): plain-text extracts, read in chunks like a web surfer's viewport ----
WIKI_API = "https://en.wikipedia.org/w/api.php"
WIKI_UA = "AgentTeamDebugger/0.1 (CS702 course project; contact via course staff)"
WIKI_CHARS = 3000
_wiki_cache: dict[str, str] = {}


def _wiki_get(params: dict) -> dict:
    url = WIKI_API + "?" + urllib.parse.urlencode({**params, "format": "json"})
    req = urllib.request.Request(url, headers={"User-Agent": WIKI_UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


async def wiki_search(query: str) -> str:
    """Search Wikipedia. Returns the top 5 matching articles as title, url and a short snippet."""
    data = await asyncio.to_thread(_wiki_get, {"action": "query", "list": "search", "srsearch": query, "srlimit": 5, "srprop": "snippet"})
    hits = data.get("query", {}).get("search", [])
    if not hits:
        return "No results."
    out = []
    for i, h in enumerate(hits):
        snippet = html.unescape(re.sub(r"<[^>]+>", "", h.get("snippet", "")))
        out.append(f"[{i + 1}] {h['title']}\nhttps://en.wikipedia.org/wiki/{urllib.parse.quote(h['title'].replace(' ', '_'))}\n{snippet}...")
    return "\n\n".join(out)


async def wiki_fetch(url: str, offset: int = 0) -> str:
    """Fetch the plain text of a Wikipedia article by url or title. Articles are returned in chunks of 3000
    characters; pass `offset` (given at the end of a chunk) to read the next part. Tables and infoboxes are not included."""
    title = urllib.parse.unquote(url.rsplit("/wiki/", 1)[-1]).replace("_", " ")
    if title not in _wiki_cache:
        data = await asyncio.to_thread(_wiki_get, {"action": "query", "prop": "extracts", "explaintext": 1, "redirects": 1, "titles": title})
        page = next(iter(data.get("query", {}).get("pages", {}).values()), {})
        if "missing" in page or not page.get("extract"):
            return f"404: no Wikipedia article '{title}'"
        _wiki_cache[title] = f"# {page['title']}\n\n{page['extract']}"
    text = _wiki_cache[title]
    chunk = text[offset:offset + WIKI_CHARS]
    if offset + WIKI_CHARS < len(text):
        chunk += f"\n\n[... article continues ({len(text)} characters in total); call wiki_fetch(url, offset={offset + WIKI_CHARS}) for the next part]"
    return chunk or "(empty)"


def make_team(work_dir: Path, team_id: str | None = None, web: str = "corpus") -> MagenticOneGroupChat:
    client = AnthropicClient()
    coder = MagenticOneCoderAgent("Coder", model_client=client)
    executor = CodeExecutorAgent(
        "Executor", code_executor=LocalCommandLineCodeExecutor(work_dir=work_dir, timeout=60)
    )
    searcher = AssistantAgent(
        "WebSearcher",
        model_client=client,
        tools=[wiki_search, wiki_fetch] if web == "wikipedia" else [web_search, fetch_page],
        reflect_on_tool_use=True,
        max_tool_iterations=int(os.environ.get("AGDBG_SEARCH_ITERS", "4")),
        description="A web researcher that can search the web and fetch pages, then reports what it found.",
        system_message=(
            "You are a web research assistant. Use the search tool to find pages and the fetch tool to read them. "
            "Answer the request concisely with the facts you found and the url they came from. "
            "Do not ask follow-up questions; report what you have."
        ),
    )
    # Recordings pin the team id so that saved checkpoints (keyed by agent id) load back into the same agents.
    with patch("uuid.uuid4", return_value=uuid.UUID(team_id)) if team_id else _nullcontext():
        return MagenticOneGroupChat([coder, executor, searcher], model_client=client, max_turns=25, max_stalls=3)


class _nullcontext:
    def __enter__(self):
        return None

    def __exit__(self, *a):
        return False
