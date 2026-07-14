"""Render the newsletter to HTML, then convert to PDF via headless Chromium."""
from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path
from string import Template

from playwright.sync_api import sync_playwright

from sources import Article
from summarizer import KeyNumber, Newsletter, PullQuote

# Issue No. 01 was June 2026 (the first automated issue).
ISSUE_ONE_YEAR = 2026
ISSUE_ONE_MONTH = 6


def _issue_number(now: datetime) -> int:
    return (now.year - ISSUE_ONE_YEAR) * 12 + (now.month - ISSUE_ONE_MONTH) + 1


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


# ---------- PDF rendering ----------


def html_to_pdf(html_path: Path, pdf_path: Path) -> None:
    """Render the given HTML file to a PDF using headless Chromium.

    Uses screen media (not print) so the PDF matches what a browser shows.
    Programmatically expands the collapsible Sources block since its toggle
    button won't fire in a static document.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page()
            page.goto(html_path.absolute().as_uri())
            page.emulate_media(media="screen")
            page.evaluate(
                """
                document.querySelectorAll('.btl-src-toggle').forEach(btn => btn.classList.add('btl-open'));
                document.querySelectorAll('.btl-src-body').forEach(body => body.classList.add('btl-open'));
                """
            )
            page.pdf(
                path=str(pdf_path),
                format="Letter",
                margin={"top": "0.5in", "bottom": "0.5in", "left": "0.5in", "right": "0.5in"},
                print_background=True,
            )
        finally:
            browser.close()


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

    # ---- PDF ----
    pdf_path = output_dir / f"{stem}.pdf"
    html_to_pdf(html_path, pdf_path)
    print(f"Wrote {pdf_path} ({pdf_path.stat().st_size:,} bytes)")

    return html_path, pdf_path
