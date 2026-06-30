"""Write the generated newsletter to a text file."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from sources import Article


MASTHEAD = """\
========================================================================
                          BETWEEN THE LINES
        Kelly Anderson Group / Impact Solutions | {month_year}
========================================================================

"""

FOOTER = """

------------------------------------------------------------------------
Kelly Anderson Group / Impact Solutions
Workforce development for the transportation industry since 1996.

  Final Mile Safety Trainer Program ......... P&D fleets
  Truckload Driver Finisher Program ......... line-haul carriers
  ELDT, e-Learning, recruiting and retention consulting

  www.kellyandersongroup.com  |  (417) 451-0853
  Bill Rohr  |  billrohr@kellyandersongroup.com
------------------------------------------------------------------------
"""


def write_newsletter(
    summary: str,
    articles: list[Article],
    output_dir: Path,
    lookback_days: int,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    filename = now.strftime("%Y-%m") + ".txt"
    path = output_dir / filename

    masthead = MASTHEAD.format(month_year=now.strftime("%B %Y"))

    appendix_lines = [
        "\n\n========================================================================",
        "SOURCES",
        f"Compiled {now.strftime('%Y-%m-%d')} from {len({a.source for a in articles})} "
        f"publications over the past {lookback_days} days.",
        "========================================================================\n",
    ]

    by_source: dict[str, list[Article]] = {}
    for art in articles:
        by_source.setdefault(art.source, []).append(art)

    for source, items in sorted(by_source.items()):
        appendix_lines.append(f"\n[{source}]")
        for art in items:
            date = art.published.strftime("%Y-%m-%d") if art.published else "n/a"
            appendix_lines.append(f"  {date}  {art.title}")
            appendix_lines.append(f"             {art.url}")

    full = masthead + summary + FOOTER + "\n".join(appendix_lines) + "\n"

    path.write_text(full, encoding="utf-8")
    print(f"Wrote {path} ({len(full):,} bytes)")
    return path
