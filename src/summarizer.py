"""Generate a structured newsletter from articles using the Claude API."""
from __future__ import annotations

import anthropic
from pydantic import BaseModel, Field

from sources import Article


class NewsletterItem(BaseModel):
    """A short newsletter item (Quick Take or What to Watch entry)."""

    headline: str = Field(
        description=(
            "Short punchy headline for this item -- a single sentence, no formatting. "
            "Written like a newsletter subhead, sentence case, no title case."
        )
    )
    body: str = Field(
        description=(
            "2-3 sentences of substance, written in the Between the Lines newsletter voice. "
            "Include inline source citations in brackets like [FreightWaves]. "
            "May be a single paragraph -- no line breaks."
        )
    )


class Newsletter(BaseModel):
    """A complete monthly issue of Between the Lines."""

    opening: str = Field(
        description=(
            "One paragraph of ~80 words. Open with energy -- ideally a real quote or sharp "
            "stat pulled from the source articles. Name the single most important thing this "
            "month and preview what's inside the issue. Include inline [Source] citations. "
            "No line breaks."
        )
    )
    big_story_headline: str = Field(
        description=(
            "A single-sentence headline for the big story section. Declarative, complete "
            "sentence, sentence case. Example: 'The freight market has turned, and this "
            "time it looks structural, not seasonal.'"
        )
    )
    big_story_paragraphs: list[str] = Field(
        description=(
            "3-5 paragraphs, ~300 words total combined, on the deepest story of the month. "
            "Each element is one paragraph (2-4 sentences). Include [Source] citations inline. "
            "No line breaks within any paragraph."
        )
    )
    quick_takes: list[NewsletterItem] = Field(
        description=(
            "4-6 shorter items covering other notable developments worth knowing. "
            "Each item's body is 2-3 sentences with inline [Source] citations."
        )
    )
    what_to_watch: list[NewsletterItem] = Field(
        description=(
            "2-3 forward-looking items about emerging stories that will shape next month. "
            "Brief and specific."
        )
    )
    bottom_line: str = Field(
        description=(
            "A single closing paragraph of ~60 words. What does this month tell carriers and "
            "final-mile operators about where the industry is heading? Confident, partner-tone "
            "observation -- not a sales pitch. No line breaks."
        )
    )


SYSTEM_PROMPT = """You are writing "Between the Lines" -- the monthly industry newsletter \
published by Kelly Anderson Group / Impact Solutions, a 28-year workforce development partner \
to the transportation industry. Our flagship programs are the Final Mile Safety Trainer Program \
(for P&D fleets) and the Truckload Driver Finisher Program (for line-haul carriers). Our readers \
-- customers and prospects -- are fleet executives, safety directors, and operations managers at \
trucking and final-mile companies. They read this newsletter to stay current on the freight and \
logistics market without wading through a dozen trade publications.

VOICE & STYLE
- Conversational but professional. Contractions are welcome. Talk WITH the reader, not at them.
- Open with energy. Lead with a vivid framing line, a sharp number, or a real quote pulled from \
the source articles -- never with "This month..." or "In recent news..."
- Short paragraphs. Let strong sentences carry the weight.
- Cite sources inline in brackets like [FreightWaves] so readers can trace claims to the appendix.
- Optimistic and partnership-oriented in framing. We're industry insiders sharing useful \
intelligence -- not doomscrolling.
- Do NOT sell our programs inside the body of the newsletter. Brand mentions live in the footer, \
which is added automatically.

WHAT MATTERS TO OUR READERS
Freight rates and capacity, driver recruiting and retention, safety and DOT compliance, fuel \
and regulation, autonomy and technology, M&A among major carriers, and anything that affects \
the economics of running a truck or a delivery fleet."""


USER_PROMPT_TEMPLATE = """Below are {article_count} articles from {source_count} leading \
transportation publications, gathered over the past {lookback_days} days. Write the next \
issue of Between the Lines as a structured JSON object matching the provided schema.

TARGET LENGTH
Total ~1,000-1,300 words across all fields combined. Fits on two 8.5x11 printed pages.

If a section lacks a real story this month, keep it brief rather than pad -- but do include \
at least the minimum item counts specified in the schema.

Every paragraph and item body must be a single continuous string with no line breaks.

ARTICLES:

{articles}
"""


def build_newsletter(
    articles: list[Article],
    model: str,
    lookback_days: int,
) -> Newsletter | None:
    """Return a parsed Newsletter, or None if no articles were gathered."""
    if not articles:
        return None

    source_count = len({a.source for a in articles})
    article_blocks = "\n\n---\n\n".join(a.to_prompt_block() for a in articles)

    user_prompt = USER_PROMPT_TEMPLATE.format(
        article_count=len(articles),
        source_count=source_count,
        lookback_days=lookback_days,
        articles=article_blocks,
    )

    client = anthropic.Anthropic()

    print(f"Calling Claude ({model}) with {len(articles)} articles...")
    response = client.messages.parse(
        model=model,
        max_tokens=16000,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
        output_format=Newsletter,
    )

    usage = response.usage
    print(f"  -> {usage.input_tokens} input + {usage.output_tokens} output tokens")

    return response.parsed_output
