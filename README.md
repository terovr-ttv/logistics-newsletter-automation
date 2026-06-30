# Logistics Industry Newsletter Automation

An automated monthly briefing pipeline for the freight, trucking, and supply chain industry. Pulls articles from leading industry publications, runs them through Claude (Anthropic's LLM), and produces a sectioned, citation-linked executive summary written for operational decision-makers.

Runs on a schedule via GitHub Actions, commits each issue back to the repo so the archive is browsable directly on GitHub.

## What it does

1. **Aggregates** the latest articles from 6 logistics publications via RSS (FreightWaves, Supply Chain Dive, The Loadstar, Transport Topics, Logistics Management, DC Velocity).
2. **Extracts** full article text from each link (not just the RSS blurb) using [trafilatura](https://trafilatura.readthedocs.io/).
3. **Summarizes** the corpus with Claude Opus 4.7 into a structured briefing: executive summary, freight & trucking, supply chain, regulation, technology, M&A, and a watch list.
4. **Writes** the output to `summaries/YYYY-MM.txt` and commits it back to the repo.

## Sample output structure

```
========================================================================
LOGISTICS INDUSTRY NEWSLETTER -- June 2026
Generated: 2026-06-30 13:00 | Lookback: 30 days
Sources: 6 | Articles analyzed: 54
========================================================================

1. EXECUTIVE SUMMARY
   - [bullet points of the most important developments]

2. FREIGHT & TRUCKING
   - Spot rates moved X% [FreightWaves]
   - ...

[... full sectioned report ...]

========================================================================
ARTICLE INDEX
========================================================================
-- FreightWaves --
  [2026-06-15] Article title
    https://www.freightwaves.com/...
```

## Architecture

```
config.yaml          source list, model, lookback window
src/
  main.py            orchestrator
  sources.py         RSS fetching + full-text extraction
  summarizer.py      Claude API call (adaptive thinking enabled)
  output.py          text file writer
.github/workflows/
  newsletter.yml     scheduled cron + commit-back
summaries/           generated newsletters (one per month)
```

## Run it yourself

### Locally

```bash
pip install -r requirements.txt
cp .env.example .env
# edit .env and add your ANTHROPIC_API_KEY
python src/main.py
```

Output lands in `summaries/YYYY-MM.txt`.

### On a schedule (GitHub Actions)

1. Fork this repo.
2. In **Settings → Secrets and variables → Actions**, add `ANTHROPIC_API_KEY`.
3. The workflow runs automatically on the 1st of each month at 13:00 UTC, or you can trigger it manually from the **Actions** tab.
4. New summaries are committed back to `summaries/`.

## Configuration

`config.yaml` controls behavior:

```yaml
model: claude-opus-4-7        # Anthropic model ID
max_articles_per_source: 10   # cap per feed
lookback_days: 30             # only summarize articles published in last N days

sources:
  - name: FreightWaves
    url: https://www.freightwaves.com/news/feed
    type: rss
  # ... add or remove sources here
```

Sources can be swapped or extended without touching code.

## Cost

Each monthly run is roughly **$0.10–$0.50** on Claude Opus 4.7, depending on article volume. The pipeline uses adaptive thinking, so cost scales with task complexity rather than a fixed token budget.

## Tech stack

- **Python 3.12**
- **[anthropic](https://github.com/anthropics/anthropic-sdk-python)** — Claude API client
- **[feedparser](https://feedparser.readthedocs.io/)** — RSS parsing
- **[trafilatura](https://trafilatura.readthedocs.io/)** — article body extraction
- **GitHub Actions** — scheduling and artifact commits
