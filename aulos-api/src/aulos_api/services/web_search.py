"""Generic open-web gatherers for listening research (no composer branches).

Search enablers (priority): Wikipedia → DuckDuckGo → optional Brave → optional
Agent Reach Jina deepen (policy-fenced; see aulos-skills/enabler-agent-reach).
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any
from urllib.parse import quote, urlparse

import httpx

logger = logging.getLogger("aulos_api.web_search")

_UA = "AulosResearchBot/0.1 (classical listening guides; +https://aulos.purezen.ai)"
_JINA_PREFIX = "https://r.jina.ai/"

_BOILERPLATE = re.compile(
    r"\b(listening\s+guides?|deep\s+listening|help\s+me|please|write\s+a|"
    r"导赏|欣赏|帮我|一份|详细|准备开始|我想听|写一份)\b",
    re.I,
)


def _clean(text: str, limit: int = 600) -> str:
    text = re.sub(r"\s+", " ", (text or "").strip())
    return text[:limit]


def _search_query(work_title: str, composer: str = "") -> str:
    """Strip chat boilerplate so encyclopedia search sees the work, not the ask."""
    title = _BOILERPLATE.sub(" ", work_title or "")
    title = re.sub(r"\s+", " ", title).strip(" .,:;/-")
    parts = [composer.strip(), title] if composer and composer.lower() not in title.lower() else [title or work_title]
    return " ".join(p for p in parts if p).strip()


def _query_variants(query: str) -> list[str]:
    """Progressively broaden: full → drop opus/no. → head tokens."""
    q = re.sub(r"\s+", " ", (query or "").strip())
    out: list[str] = []
    if q:
        out.append(q)
    simplified = re.sub(
        r"\b(op\.?|opus|no\.?|nr\.?|bwv|woo|hob|kv)\s*\d+([–\-./]\d+)*\b",
        " ",
        q,
        flags=re.I,
    )
    simplified = re.sub(r"\s+", " ", simplified).strip(" .,:;/-")
    if simplified and simplified not in out:
        out.append(simplified)
    tokens = [t for t in re.findall(r"[A-Za-z\u4e00-\u9fff]{2,}", q)]
    if len(tokens) >= 2:
        for n in (4, 3, 2):
            short = " ".join(tokens[:n])
            if short and short not in out:
                out.append(short)
    return out


def search_wikipedia(*, query: str, langs: tuple[str, ...] = ("en", "zh"), limit: int = 3) -> list[dict[str, Any]]:
    """MediaWiki OpenSearch + REST summary — reliable, keyless, bilingual."""
    out: list[dict[str, Any]] = []
    q = (query or "").strip()
    if not q:
        return out
    with httpx.Client(timeout=12.0, headers={"User-Agent": _UA}, follow_redirects=True) as client:
        for lang in langs:
            try:
                r = client.get(
                    f"https://{lang}.wikipedia.org/w/api.php",
                    params={
                        "action": "opensearch",
                        "search": q,
                        "limit": limit,
                        "namespace": 0,
                        "format": "json",
                    },
                )
                r.raise_for_status()
                data = r.json()
            except Exception as exc:  # noqa: BLE001
                logger.warning("wikipedia_opensearch_failed lang=%s err=%s", lang, exc)
                continue
            titles = list(data[1] or []) if isinstance(data, list) and len(data) > 1 else []
            for title in titles[:limit]:
                try:
                    s = client.get(
                        f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{quote(title, safe='')}"
                    )
                    if s.status_code >= 400:
                        continue
                    body = s.json()
                except Exception as exc:  # noqa: BLE001
                    logger.warning("wikipedia_summary_failed title=%s err=%s", title, exc)
                    continue
                extract = _clean(str(body.get("extract") or ""), 900)
                if not extract:
                    continue
                url = str((body.get("content_urls") or {}).get("desktop", {}).get("page") or "") or str(
                    body.get("content_urls", {}).get("mobile", {}).get("page") or ""
                )
                if not url:
                    url = f"https://{lang}.wikipedia.org/wiki/{quote(title.replace(' ', '_'), safe='/_')}"
                out.append(
                    {
                        "provider": "wikipedia",
                        "lang": lang,
                        "title": str(body.get("title") or title),
                        "url": url,
                        "snippet": extract,
                    }
                )
    return out


def search_duckduckgo(*, query: str, limit: int = 5) -> list[dict[str, Any]]:
    """DuckDuckGo Instant Answer API — keyless; Abstract + RelatedTopics."""
    q = (query or "").strip()
    if not q:
        return []
    out: list[dict[str, Any]] = []
    try:
        with httpx.Client(timeout=12.0, headers={"User-Agent": _UA}, follow_redirects=True) as client:
            r = client.get(
                "https://api.duckduckgo.com/",
                params={"q": q, "format": "json", "no_html": "1", "skip_disambig": "1"},
            )
            r.raise_for_status()
            data = r.json()
    except Exception as exc:  # noqa: BLE001
        logger.warning("duckduckgo_failed err=%s", exc)
        return []
    abstract = _clean(str(data.get("AbstractText") or ""), 700)
    abs_url = str(data.get("AbstractURL") or "")
    abs_src = str(data.get("AbstractSource") or "DuckDuckGo")
    if abstract:
        out.append(
            {
                "provider": "duckduckgo",
                "title": str(data.get("Heading") or abs_src or q),
                "url": abs_url or "https://duckduckgo.com/",
                "snippet": abstract,
            }
        )
    for topic in list(data.get("RelatedTopics") or [])[: limit * 2]:
        if not isinstance(topic, dict):
            continue
        if "Topics" in topic:
            continue
        text = _clean(str(topic.get("Text") or ""), 500)
        url = str(topic.get("FirstURL") or "")
        if text and url:
            out.append(
                {
                    "provider": "duckduckgo",
                    "title": text.split(" - ")[0][:120],
                    "url": url,
                    "snippet": text,
                }
            )
        if len(out) >= limit:
            break
    return out[:limit]


def search_brave(*, query: str, api_key: str, limit: int = 5) -> list[dict[str, Any]]:
    """Optional Brave Search API when ops configures a key."""
    q = (query or "").strip()
    key = (api_key or "").strip()
    if not q or not key:
        return []
    try:
        with httpx.Client(timeout=12.0, headers={"User-Agent": _UA, "X-Subscription-Token": key}) as client:
            r = client.get(
                "https://api.search.brave.com/res/v1/web/search",
                params={"q": q, "count": limit},
            )
            r.raise_for_status()
            data = r.json()
    except Exception as exc:  # noqa: BLE001
        logger.warning("brave_search_failed err=%s", exc)
        return []
    out: list[dict[str, Any]] = []
    for row in list((data.get("web") or {}).get("results") or [])[:limit]:
        if not isinstance(row, dict):
            continue
        snippet = _clean(str(row.get("description") or ""), 500)
        url = str(row.get("url") or "")
        title = str(row.get("title") or "")
        if snippet and url:
            out.append({"provider": "brave", "title": title, "url": url, "snippet": snippet})
    return out


def _safe_http_url(url: str) -> str | None:
    raw = (url or "").strip()
    if not raw:
        return None
    parsed = urlparse(raw)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return None
    host = (parsed.hostname or "").lower()
    if host in {"localhost", "127.0.0.1", "::1"} or host.endswith(".local"):
        return None
    if host.startswith("10.") or host.startswith("192.168.") or host.startswith("169.254."):
        return None
    return raw


def fetch_jina_reader(*, url: str, limit: int = 1200) -> dict[str, Any] | None:
    """Agent Reach web-channel pattern: deepen a public URL via Jina Reader."""
    safe = _safe_http_url(url)
    if not safe:
        return None
    jina_url = f"{_JINA_PREFIX}{safe}"
    try:
        with httpx.Client(timeout=20.0, headers={"User-Agent": _UA, "Accept": "text/plain"}, follow_redirects=True) as client:
            r = client.get(jina_url)
            if r.status_code >= 400:
                return None
            text = _clean(r.text, limit)
    except Exception as exc:  # noqa: BLE001
        logger.warning("agent_reach_jina_failed url=%s err=%s", safe, exc)
        return None
    if len(text) < 80:
        return None
    title = text.split(".", 1)[0][:120] if text else safe
    return {
        "provider": "agent-reach-jina",
        "title": title,
        "url": safe,
        "snippet": text,
        "enabler": "enabler-agent-reach",
    }


def deepen_with_agent_reach(
    sources: list[dict[str, Any]],
    *,
    max_pages: int = 2,
) -> list[dict[str, Any]]:
    """Deepen top discovery hits via Agent Reach Jina — search enabler, not discovery."""
    done = 0
    for row in sources:
        if done >= max_pages:
            break
        if str(row.get("provider") or "") == "agent-reach-jina":
            continue
        url = str(row.get("url") or "")
        deepened = fetch_jina_reader(url=url)
        if not deepened:
            continue
        row["snippet"] = deepened["snippet"]
        row["deepened_by"] = "agent-reach-jina"
        row["enabler"] = "enabler-agent-reach"
        done += 1
    return sources


def agent_reach_enabled_from_env() -> bool:
    raw = os.environ.get("AULOS_AGENT_REACH_ENABLED", "true").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def gather_web_sources(
    *,
    work_title: str,
    composer: str = "",
    brave_api_key: str = "",
    max_sources: int = 10,
    agent_reach_enabled: bool | None = None,
) -> list[dict[str, Any]]:
    """Gather open sources for a work — generic query from identity fields only."""
    query = _search_query(work_title, composer)
    if not query:
        return []
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    use_reach = agent_reach_enabled_from_env() if agent_reach_enabled is None else bool(agent_reach_enabled)

    def add_all(rows: list[dict[str, Any]]) -> None:
        for row in rows:
            url = str(row.get("url") or "").strip()
            if not url or url in seen:
                continue
            seen.add(url)
            out.append(row)

    for variant in _query_variants(query):
        add_all(search_wikipedia(query=variant))
        if len(out) >= max_sources:
            break
    if len(out) < 2:
        add_all(search_duckduckgo(query=f"{_query_variants(query)[-1]} classical music"))
    if brave_api_key:
        add_all(search_brave(query=query, api_key=brave_api_key))
    if use_reach and out:
        deepen_with_agent_reach(out, max_pages=2)
    if not out:
        logger.warning("web_gather_empty query=%r title=%r composer=%r", query, work_title, composer)
    else:
        logger.info(
            "web_gather_ok query=%r sources=%s agent_reach=%s",
            query,
            len(out),
            use_reach,
        )
    return out[:max_sources]
