"""Fetch articles from logistics industry RSS feeds."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

import feedparser
import trafilatura


@dataclass
class Article:
    source: str
    title: str
    url: str
    published: datetime | None
    summary: str
    content: str

    def to_prompt_block(self) -> str:
        date_str = self.published.strftime("%Y-%m-%d") if self.published else "n/a"
        body = self.content or self.summary or "(no content available)"
        return (
            f"SOURCE: {self.source}\n"
            f"TITLE: {self.title}\n"
            f"DATE: {date_str}\n"
            f"URL: {self.url}\n"
            f"CONTENT:\n{body}\n"
        )


def _parse_date(entry) -> datetime | None:
    for key in ("published", "updated", "created"):
        raw = entry.get(key)
        if not raw:
            continue
        try:
            dt = parsedate_to_datetime(raw)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except (TypeError, ValueError):
            continue
    return None


def _extract_full_text(url: str) -> str:
    try:
        downloaded = trafilatura.fetch_url(url, no_ssl=True)
        if not downloaded:
            return ""
        text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
        return text or ""
    except Exception:
        return ""


def fetch_source(
    name: str,
    url: str,
    max_articles: int,
    lookback_days: int,
    fetch_full_text: bool = True,
) -> list[Article]:
    """Fetch and parse an RSS feed; return up to max_articles within lookback window."""
    feed = feedparser.parse(url)
    if feed.bozo and not feed.entries:
        print(f"  [!] {name}: feed parse error ({feed.bozo_exception})")
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    articles: list[Article] = []

    for entry in feed.entries[: max_articles * 2]:
        published = _parse_date(entry)
        if published and published < cutoff:
            continue

        link = entry.get("link", "")
        title = entry.get("title", "(untitled)").strip()
        summary = entry.get("summary", "") or entry.get("description", "")

        content = ""
        if fetch_full_text and link:
            content = _extract_full_text(link)

        articles.append(
            Article(
                source=name,
                title=title,
                url=link,
                published=published,
                summary=summary,
                content=content,
            )
        )

        if len(articles) >= max_articles:
            break

    return articles


def fetch_all(sources: list[dict], max_articles: int, lookback_days: int) -> list[Article]:
    all_articles: list[Article] = []
    for src in sources:
        name = src["name"]
        print(f"Fetching {name}...")
        articles = fetch_source(name, src["url"], max_articles, lookback_days)
        print(f"  -> {len(articles)} articles")
        all_articles.extend(articles)
    return all_articles
