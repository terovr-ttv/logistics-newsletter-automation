"""Entry point: fetch articles, summarize via Claude, write newsletter to disk."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

from sources import fetch_all
from summarizer import build_summary
from output import write_newsletter


def main() -> int:
    load_dotenv()

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY is not set. Add it to .env or your environment.")
        return 1

    repo_root = Path(__file__).resolve().parent.parent
    config_path = repo_root / "config.yaml"
    output_dir = repo_root / "summaries"

    with config_path.open(encoding="utf-8") as f:
        config = yaml.safe_load(f)

    articles = fetch_all(
        sources=config["sources"],
        max_articles=config["max_articles_per_source"],
        lookback_days=config["lookback_days"],
    )

    print(f"\nTotal articles gathered: {len(articles)}\n")

    summary = build_summary(
        articles=articles,
        model=config["model"],
        lookback_days=config["lookback_days"],
    )

    write_newsletter(
        summary=summary,
        articles=articles,
        output_dir=output_dir,
        lookback_days=config["lookback_days"],
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
