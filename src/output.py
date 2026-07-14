"""Render the newsletter to plain text and HTML files."""
from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path
from string import Template

from sources import Article
from summarizer import Newsletter


TEXT_MASTHEAD = """\
========================================================================
                          BETWEEN THE LINES
        Kelly Anderson Group / Impact Solutions | {month_year}
========================================================================

"""

TEXT_FOOTER = """

------------------------------------------------------------------------
Kelly Anderson Group / Impact Solutions
Workforce development for the transportation industry since 1996.

  Final Mile Safety Trainer Program ......... P&D fleets
  Truckload Driver Finisher Program ......... line-haul carriers
  ELDT, e-Learning, recruiting and retention consulting

  www.kellyandersongroup.com  |  (417) 451-0853
------------------------------------------------------------------------
"""


def _text_body(nl: Newsletter) -> str:
    parts = [
        "OPENING",
        "",
        nl.opening,
        "",
        "",
        "THE BIG STORY",
        "",
        nl.big_story_headline,
        "",
    ]
    parts.extend(p + "\n" for p in nl.big_story_paragraphs)
    parts.append("")

    parts.extend(["QUICK TAKES", ""])
    for item in nl.quick_takes:
        parts.append(item.headline)
        parts.append(item.body)
        parts.append("")

    parts.extend(["WHAT TO WATCH", ""])
    for item in nl.what_to_watch:
        parts.append(item.headline)
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


def _esc(s: str) -> str:
    """Escape only characters that break HTML text content (& < >). Apostrophes and
    quotes are safe in text nodes and left as-is for readable source."""
    return escape(s, quote=False)


def _html_paragraphs(paragraphs: list[str], indent: str = "    ") -> str:
    return "\n".join(f"{indent}<p>{_esc(p)}</p>" for p in paragraphs)


def _html_items(items, indent: str = "    ") -> str:
    blocks = []
    for it in items:
        blocks.append(
            f'{indent}<div class="btl-item">\n'
            f'{indent}  <h3>{_esc(it.headline)}</h3>\n'
            f'{indent}  <p>{_esc(it.body)}</p>\n'
            f'{indent}</div>'
        )
    return "\n".join(blocks)


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

    # ---- TEXT ----
    text_path = output_dir / f"{stem}.txt"
    text_body = _text_body(nl)
    text_full = (
        TEXT_MASTHEAD.format(month_year=month_year)
        + text_body
        + TEXT_FOOTER
        + _text_sources(articles, compile_date, lookback_days)
        + "\n"
    )
    text_path.write_text(text_full, encoding="utf-8")
    print(f"Wrote {text_path} ({len(text_full):,} bytes)")

    # ---- HTML ----
    html_path = output_dir / f"{stem}.html"
    template = Template((templates_dir / "newsletter.html").read_text(encoding="utf-8"))
    html_full = template.substitute(
        month_year=_esc(month_year),
        opening=_esc(nl.opening),
        big_story_headline=_esc(nl.big_story_headline),
        big_story_paragraphs=_html_paragraphs(nl.big_story_paragraphs),
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
