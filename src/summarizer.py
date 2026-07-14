"""Generate a structured newsletter from articles using the Claude API."""
from __future__ import annotations

import anthropic
from pydantic import BaseModel, Field

from sources import Article


class KeyNumber(BaseModel):
    """A single number for the 'By the Numbers' callout."""

    number: str = Field(
        description=(
            "The number itself as it should be displayed, short and self-contained. "
            "Examples: '13.5%', '$62M', '20.4', '3.9M', '$8,500'. Include the unit or "
            "symbol. Do NOT include any label or caption text here."
        )
    )
    label: str = Field(
        description=(
            "Short caption for what the number means. 4 to 8 words, sentence case, "
            "no ending period. Example: 'Driver pay surge, April to June'."
        )
    )


class PullQuote(BaseModel):
    """A single pulled quote anchoring the Big Story."""

    text: str = Field(
        description=(
            "One direct quote drawn verbatim from the source articles. Should capture "
            "the essence of the Big Story in a single vivid sentence. Between 10 and 30 "
            "words. Do NOT include [Source] citations, brackets, or surrounding quotation "
            "marks (they will be added by the template)."
        )
    )
    attribution: str = Field(
        description=(
            "The speaker's name and title/affiliation, e.g. 'Dean Croke, DAT Freight & "
            "Analytics'. Do NOT include the [Source] citation."
        )
    )


class NewsletterItem(BaseModel):
    """A short newsletter item (Quick Take or What to Watch entry)."""

    topic: str = Field(
        description=(
            "Single-word or two-word category tag for this item, sentence case. Common "
            "options: 'Regulation', 'Ocean', 'LTL', 'Labor', 'Infrastructure', 'Tech', "
            "'Drivers', 'Rates', 'Fuel', 'Supply Chain', 'M&A', 'Trade'. Pick the one "
            "that best fits the topic. Two words maximum."
        )
    )
    headline: str = Field(
        description=(
            "Short punchy headline for this item. A single sentence, no formatting. "
            "Written like a newsletter subhead, sentence case, no title case."
        )
    )
    body: str = Field(
        description=(
            "2 to 3 sentences of substance, written in the Between the Lines newsletter "
            "voice. Include inline source citations in brackets like [FreightWaves]. "
            "A single paragraph with no line breaks."
        )
    )


class Newsletter(BaseModel):
    """A complete monthly issue of Between the Lines."""

    opening: str = Field(
        description=(
            "One paragraph of about 80 words. Open with energy. Ideally lead with a real "
            "quote or sharp stat pulled from the source articles. Name the single most "
            "important thing this month and preview what's inside the issue. Include "
            "inline [Source] citations. No line breaks."
        )
    )
    big_story_deck: str = Field(
        description=(
            "A single italic-style editorial deck line that sits under 'THE BIG STORY' "
            "label as a subhead. Should complement the h2 headline without repeating it. "
            "One medium sentence or two short ones. Example: 'The rate rebound is real. "
            "The reason isn't what most people think.'"
        )
    )
    big_story_headline: str = Field(
        description=(
            "A single-sentence headline for the big story section. Declarative, complete "
            "sentence, sentence case. Example: 'The freight market has turned. Capacity, "
            "not demand, is doing the heavy lifting.'"
        )
    )
    big_story_paragraphs: list[str] = Field(
        description=(
            "3 to 5 paragraphs, about 300 words total combined, on the deepest story of "
            "the month. Each element is one paragraph of 2 to 4 sentences. Include "
            "[Source] citations inline. No line breaks within any paragraph."
        )
    )
    pull_quote: PullQuote = Field(
        description=(
            "The single strongest quote from the source articles that anchors the Big "
            "Story. Displayed as a visual pull quote between paragraphs. Must be a real "
            "verbatim quote drawn from the source material."
        )
    )
    key_numbers: list[KeyNumber] = Field(
        description=(
            "Exactly 4 standout numbers from this month's stories, chosen to summarize "
            "the state of the market at a glance. Mix percentages, dollar amounts, and "
            "index or count values. All 4 must come directly from the source articles. "
            "Prefer numbers that appear in the Big Story or Quick Takes."
        )
    )
    quick_takes: list[NewsletterItem] = Field(
        description=(
            "4 to 6 shorter items covering other notable developments worth knowing. "
            "Each item body is 2 to 3 sentences with inline [Source] citations. Each "
            "item must have a distinct topic tag."
        )
    )
    what_to_watch: list[NewsletterItem] = Field(
        description=(
            "2 to 3 forward-looking items about emerging stories that will shape next "
            "month. Brief and specific. Each item must have a topic tag."
        )
    )
    bottom_line: str = Field(
        description=(
            "A single closing paragraph of about 60 words. What does this month tell "
            "carriers and final-mile operators about where the industry is heading? "
            "Confident, partner-tone observation. Not a sales pitch. No line breaks."
        )
    )


SYSTEM_PROMPT = """You are writing "Between the Lines," the monthly industry newsletter \
published by Kelly Anderson Group / Impact Solutions, a 28-year workforce development \
partner to the transportation industry. Our flagship programs are the Final Mile Safety \
Trainer Program (for P&D fleets) and the Truckload Driver Finisher Program (for line-haul \
carriers). Our readers are fleet executives, safety directors, and operations managers at \
trucking and final-mile companies. They read this newsletter to stay current on the \
freight and logistics market without wading through a dozen trade publications.

VOICE
- Write like a human industry insider who's read all this so the reader doesn't have to.
- Conversational and professional. Contractions are welcome. Talk with the reader, not at \
them.
- Open sections with a vivid framing line, a sharp number, or a real quote pulled from \
the source articles. Never open with "This month..." or "In recent news..."
- Short paragraphs. Let strong sentences carry the weight.
- Cite sources inline in brackets like [FreightWaves] so readers can trace claims to the \
appendix.
- Optimistic and partnership-oriented in framing. Industry insiders sharing useful \
intelligence, not doomscrolling.
- Do NOT sell our programs inside the body of the newsletter. Brand mentions live in the \
footer, which is added automatically.

PUNCTUATION AND WORD CHOICE (this is important, our readers can spot AI writing)
- NEVER use em dashes or double hyphens. That includes the characters "--", "—", and \
"–". This is the single strongest AI tell in prose. When you would reach for one, use \
a comma, period, colon, semicolon, or parentheses instead. Rewrite the sentence if you \
have to.
- Avoid AI-tell phrases and hedges: "it's worth noting," "notably," "furthermore," \
"moreover," "in essence," "at the end of the day," "leverage" as a verb, "utilize," \
"delve into," "navigate the landscape," "unpack."
- Avoid the "not X, but Y" construction as a crutch. Use it at most once per issue.
- Vary sentence openings and structure. Don't start consecutive sentences the same way.
- Use straight quotes (" and ') rather than curly quotes.

STRUCTURED FIELDS TO FILL WELL
- big_story_deck: one italic-style tagline that sets up the Big Story. Should hook \
without giving away the whole thesis. Two short sentences work well.
- pull_quote: pick the single most quotable line from the source articles that captures \
the Big Story's core idea. Attribute it accurately with speaker name and title.
- key_numbers: exactly 4 numbers that summarize the month. Mix percentage, dollar, and \
index/count formats. Every number must appear verbatim in the source articles.
- topic on each item: keep to one or two words. Prefer common categories over exotic ones.

WHAT MATTERS TO OUR READERS
Freight rates and capacity, driver recruiting and retention, safety and DOT compliance, \
fuel and regulation, autonomy and technology, M&A among major carriers, and anything that \
affects the economics of running a truck or a delivery fleet."""


USER_PROMPT_TEMPLATE = """Below are {article_count} articles from {source_count} leading \
transportation publications, gathered over the past {lookback_days} days. Write the next \
issue of Between the Lines as a structured JSON object matching the provided schema.

TARGET LENGTH
About 1,000 to 1,300 words across all prose fields combined. Fits on two 8.5x11 printed \
pages.

If a section lacks a real story this month, keep it brief rather than pad. But do include \
at least the minimum item counts specified in the schema.

Every paragraph and item body must be a single continuous string with no line breaks.

REMINDER: no em dashes, no double hyphens. Rewrite any sentence where you'd reach for one.

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
