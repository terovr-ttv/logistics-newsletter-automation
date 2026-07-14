"""Render the newsletter to plain text and HTML files."""
from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path
from string import Template

from sources import Article
from summarizer import KeyNumber, Newsletter, PullQuote

# Issue No. 01 was June 2026 (the first automated issue).
ISSUE_ONE_YEAR = 2026
ISSUE_ONE_MONTH = 6


def _issue_number(now: datetime) -> int:
    return (now.year - ISSUE_ONE_YEAR) * 12 + (now.month - ISSUE_ONE_MONTH) + 1


# ---------- Plain-text rendering ----------

TEXT_MASTHEAD = """\
========================================================================
                          BETWEEN THE LINES
     Issue No. {issue_no:02d}  |  {month_year}  |  Kelly Anderson Group
========================================================================

"""

TEXT_FOOTER_TEMPLATE = """

------------------------------------------------------------------------
Kelly Anderson Group / Impact Solutions
Workforce development for the transportation industry since 1996.

  Final Mile Safety Trainer Program ......... P&D fleets
  Truckload Driver Finisher Program ......... line-haul carriers
  ELDT, e-Learning, recruiting and retention consulting

  www.kellyandersongroup.com  |  (417) 451-0853

  (c) {year} Kelly Anderson Group. Compiled from public industry reporting.
------------------------------------------------------------------------
"""


def _text_stats(numbers: list[KeyNumber]) -> str:
    lines = ["", "BY THE NUMBERS", ""]
    width = max(len(n.number) for n in numbers) if numbers else 0
    for n in numbers:
        lines.append(f"  {n.number.ljust(width)}    {n.label}")
    return "\n".join(lines) + "\n"


def _text_pull_quote(quote: PullQuote) -> str:
    return (
        "\n"
        f'    "{quote.text}"\n'
        f"      -- {quote.attribution}\n"
    )


def _text_body(nl: Newsletter) -> str:
    parts = [
        "OPENING",
        "",
        nl.opening,
        "",
        "",
        "THE BIG STORY",
        nl.big_story_deck,
        "",
        nl.big_story_headline,
        "",
    ]

    # Weave stats after paragraph 1 and pull quote after paragraph 2.
    paragraphs = nl.big_story_paragraphs
    if paragraphs:
        parts.append(paragraphs[0])
    if nl.key_numbers:
        parts.append(_text_stats(nl.key_numbers))
    if len(paragraphs) > 1:
        parts.append(paragraphs[1])
    if nl.pull_quote:
        parts.append(_text_pull_quote(nl.pull_quote))
    for p in paragraphs[2:]:
        parts.append(p)
    parts.append("")

    parts.extend(["QUICK TAKES", ""])
    for item in nl.quick_takes:
        parts.append(f"[{item.topic.upper()}]  {item.headline}")
        parts.append(item.body)
        parts.append("")

    parts.extend(["WHAT TO WATCH", ""])
    for item in nl.what_to_watch:
        parts.append(f"[{item.topic.upper()}]  {item.headline}")
        parts.append(item.body)
        parts.append("")

    parts.extend(["THE BOTTOM LINE", "", nl.bottom_line])
    return "\n".join(parts)


def _text_sources(articles: list[Article], compile_date: str, lookback_days: int) -> str:
    lines = [
        "\n\n========================================================================",
        "SOURCES",
        f"Compiled {compile_date} from {len({a.source for a in articles})} "
        f"publications over the past {lookback_days} days.",
        "========================================================================\n",
    ]
    by_source: dict[str, list[Article]] = {}
    for art in articles:
        by_source.setdefault(art.source, []).append(art)

    for source, items in sorted(by_source.items()):
        lines.append(f"\n[{source}]")
        for art in items:
            date = art.published.strftime("%Y-%m-%d") if art.published else "n/a"
            lines.append(f"  {date}  {art.title}")
            lines.append(f"             {art.url}")

    return "\n".join(lines)


# ---------- HTML rendering ----------


def _esc(s: str) -> str:
    """Escape only characters that break HTML text content (& < >). Apostrophes and
    quotes are safe in text nodes and left as-is for readable source."""
    return escape(s, quote=False)


def _html_stats(numbers: list[KeyNumber]) -> str:
    cells = []
    for n in numbers:
        cells.append(
            f'      <div>\n'
            f'        <div class="btl-stat-num">{_esc(n.number)}</div>\n'
            f'        <div class="btl-stat-label">{_esc(n.label)}</div>\n'
            f'      </div>'
        )
    return (
        '    <div class="btl-stats">\n'
        + "\n".join(cells)
        + '\n    </div>'
    )


def _html_pull_quote(quote: PullQuote) -> str:
    return (
        '    <blockquote class="btl-quote">\n'
        f'      "{_esc(quote.text)}"\n'
        f'      <cite>{_esc(quote.attribution)}</cite>\n'
        '    </blockquote>'
    )


def _html_big_story_body(nl: Newsletter) -> str:
    """Compose the Big Story inner HTML: dropcap on p1, stats after p1, pull quote
    after p2, then remaining paragraphs."""
    parts: list[str] = []
    paragraphs = nl.big_story_paragraphs

    if paragraphs:
        parts.append(f'    <p class="btl-dropcap">{_esc(paragraphs[0])}</p>')

    if nl.key_numbers:
        parts.append("")
        parts.append(_html_stats(nl.key_numbers))
        parts.append("")

    if len(paragraphs) > 1:
        parts.append(f'    <p>{_esc(paragraphs[1])}</p>')

    if nl.pull_quote:
        parts.append("")
        parts.append(_html_pull_quote(nl.pull_quote))
        parts.append("")

    for p in paragraphs[2:]:
        parts.append(f'    <p>{_esc(p)}</p>')

    return "\n".join(parts)


def _html_items(items) -> str:
    blocks = []
    for it in items:
        blocks.append(
            '    <div class="btl-item">\n'
            '      <div class="btl-item-meta">\n'
            f'        <span class="btl-item-tag">{_esc(it.topic)}</span>\n'
            '      </div>\n'
            f'      <h3>{_esc(it.headline)}</h3>\n'
            f'      <p>{_esc(it.body)}</p>\n'
            '    </div>'
        )
    return "\n".join(blocks)


def _html_sources(articles: list[Article]) -> str:
    by_source: dict[str, list[Article]] = {}
    for art in articles:
        by_source.setdefault(art.source, []).append(art)

    blocks: list[str] = []
    for source, items in sorted(by_source.items()):
        rows = []
        for art in items:
            date = art.published.strftime("%Y-%m-%d") if art.published else "n/a"
            rows.append(
                f'        <div class="btl-src-row">'
                f'<span class="btl-src-date">{_esc(date)}</span>'
                f'<a href="{escape(art.url, quote=True)}" target="_blank" rel="noopener">'
                f'{_esc(art.title)}</a></div>'
            )
        rows_html = "\n".join(rows)
        blocks.append(
            f'      <div class="btl-src-pub">\n'
            f'        <div class="btl-src-pub-name">{_esc(source)}</div>\n'
            f'{rows_html}\n'
            f'      </div>'
        )
    return "\n".join(blocks)


# ---------- Entry point ----------


def write_newsletter(
    nl: Newsletter,
    articles: list[Article],
    output_dir: Path,
    templates_dir: Path,
    lookback_days: int,
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    month_year = now.strftime("%B %Y")
    compile_date = now.strftime("%Y-%m-%d")
    stem = now.strftime("%Y-%m")
    issue_no = _issue_number(now)

    # ---- TEXT ----
    text_path = output_dir / f"{stem}.txt"
    text_full = (
        TEXT_MASTHEAD.format(issue_no=issue_no, month_year=month_year)
        + _text_body(nl)
        + TEXT_FOOTER_TEMPLATE.format(year=now.year)
        + _text_sources(articles, compile_date, lookback_days)
        + "\n"
    )
    text_path.write_text(text_full, encoding="utf-8")
    print(f"Wrote {text_path} ({len(text_full):,} bytes)")

    # ---- HTML ----
    html_path = output_dir / f"{stem}.html"
    template = Template((templates_dir / "newsletter.html").read_text(encoding="utf-8"))
    html_full = template.substitute(
        issue_number=f"{issue_no:02d}",
        month_year=_esc(month_year),
        year=str(now.year),
        opening=_esc(nl.opening),
        big_story_deck=_esc(nl.big_story_deck),
        big_story_headline=_esc(nl.big_story_headline),
        big_story_body=_html_big_story_body(nl),
        quick_takes=_html_items(nl.quick_takes),
        what_to_watch=_html_items(nl.what_to_watch),
        bottom_line=_esc(nl.bottom_line),
        compile_date=_esc(compile_date),
        source_count=str(len({a.source for a in articles})),
        lookback_days=str(lookback_days),
        sources_body=_html_sources(articles),
    )
    html_path.write_text(html_full, encoding="utf-8")
    print(f"Wrote {html_path} ({len(html_full):,} bytes)")

    return text_path, html_path
