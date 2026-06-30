"""Generate a newsletter summary from articles using the Claude API."""
from __future__ import annotations

import anthropic

from sources import Article


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
- Short paragraphs (2-4 sentences). Bold the takeaway, not the noun. Use a longer paragraph only \
when one story genuinely deserves more room.
- Cite sources inline in brackets like [FreightWaves] so readers can trace claims to the appendix.
- Optimistic and partnership-oriented in framing. We're industry insiders sharing useful \
intelligence -- not doomscrolling.
- Do NOT sell our programs inside the body of the newsletter. The newsletter earns trust by \
being genuinely useful; brand mentions live in the footer, which is added automatically.

WHAT MATTERS TO OUR READERS
Freight rates and capacity, driver recruiting and retention, safety and DOT compliance, fuel \
and regulation, autonomy and technology, M&A among major carriers, and anything that affects \
the economics of running a truck or a delivery fleet."""


USER_PROMPT_TEMPLATE = """Below are {article_count} articles from {source_count} leading \
transportation publications, gathered over the past {lookback_days} days. Write the next \
issue of Between the Lines.

HARD CONSTRAINTS
- Target length: 1,000-1,300 words total. This must fit on two 8.5x11 printed pages.
- Use the structure below. If a section lacks a real story this month, skip it rather than pad.
- Plain text output only. No Markdown headers, no asterisks for emphasis. Use ALL-CAPS section \
labels followed by a blank line.
- For emphasis within paragraphs, you may use ALL-CAPS sparingly for a key term -- but prefer \
to let strong sentences carry the weight on their own.

STRUCTURE

OPENING (about 80 words)
A confident, one-paragraph lead that names the single most important thing happening in the \
industry this month and previews what's inside the issue.

THE BIG STORY (about 300 words)
The deeper-dive feature -- the story that most affects our readers' operations. Give it room. \
Draw from multiple sources where it strengthens the analysis.

QUICK TAKES (about 400 words across 4-6 items)
Other notable developments worth knowing. Each item: a short headline of your own writing (one \
line, no formatting), then 2-3 sentences of substance. Group thematically if it improves flow \
(e.g., RATES & CAPACITY, REGULATION DESK, TECH WATCH) or run them straight.

WHAT TO WATCH (about 150 words across 2-3 items)
Forward-looking -- emerging stories that haven't fully landed yet but will shape next month. \
Brief and specific.

THE BOTTOM LINE (about 60 words)
A single closing paragraph: what does this month tell carriers and final-mile operators about \
where the industry is heading? End with a confident, partner-tone observation -- not a sales pitch.

ARTICLES:

{articles}
"""


def build_summary(
    articles: list[Article],
    model: str,
    lookback_days: int,
) -> str:
    if not articles:
        return "No articles were gathered this period. Check feed URLs and network access."

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
    with client.messages.stream(
        model=model,
        max_tokens=16000,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    ) as stream:
        message = stream.get_final_message()

    text_parts = [block.text for block in message.content if block.type == "text"]
    summary = "\n".join(text_parts).strip()

    usage = message.usage
    print(
        f"  -> {usage.input_tokens} input + {usage.output_tokens} output tokens"
    )

    return summary
