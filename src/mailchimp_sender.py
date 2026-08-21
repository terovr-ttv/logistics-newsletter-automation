"""Create and send a Mailchimp campaign from the most recent newsletter HTML."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from base64 import b64encode
from datetime import datetime
from pathlib import Path

import yaml
from dotenv import load_dotenv


def _dc(api_key: str) -> str:
    return api_key.rsplit("-", 1)[-1]


def _auth(api_key: str) -> str:
    return "Basic " + b64encode(f"anystring:{api_key}".encode()).decode()


def _call(method: str, url: str, api_key: str, body: dict | None = None) -> dict:
    payload = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Authorization": _auth(api_key), "Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        raise RuntimeError(
            f"Mailchimp {method} {url} -> {exc.code}: {detail}"
        ) from exc


def _inject_intro(html: str, message: str) -> str:
    """Insert a styled intro banner immediately after the opening <body> tag."""
    idx = html.find("<body")
    if idx == -1:
        return html
    close = html.find(">", idx) + 1
    banner = (
        '<div style="background:#f0f4f8;border-left:4px solid #1a3a5c;'
        'padding:16px 20px;margin:0 0 0;font-family:sans-serif;'
        'font-size:14px;color:#333;line-height:1.6;">'
        f"{message}"
        "</div>"
    )
    return html[:close] + banner + html[close:]


def send_campaign(
    *,
    api_key: str,
    list_id: str,
    from_name: str,
    reply_to: str,
    subject_line: str,
    html: str,
) -> str:
    """Create, populate, and send a Mailchimp regular campaign. Returns campaign ID."""
    base = f"https://{_dc(api_key)}.api.mailchimp.com/3.0"

    campaign = _call("POST", f"{base}/campaigns", api_key, {
        "type": "regular",
        "recipients": {"list_id": list_id},
        "settings": {
            "subject_line": subject_line,
            "from_name": from_name,
            "reply_to": reply_to,
        },
    })
    campaign_id = campaign["id"]
    print(f"  Created campaign {campaign_id}")

    _call("PUT", f"{base}/campaigns/{campaign_id}/content", api_key, {"html": html})
    print(f"  Set HTML content ({len(html):,} chars)")

    _call("POST", f"{base}/campaigns/{campaign_id}/actions/send", api_key)
    print(f"  Sent.")

    return campaign_id


def main() -> int:
    load_dotenv()

    api_key = os.getenv("MAILCHIMP_API_KEY", "")
    list_id = os.getenv("MAILCHIMP_LIST_ID", "")

    if not api_key or not list_id:
        print("MAILCHIMP_API_KEY and MAILCHIMP_LIST_ID must be set. Skipping send.")
        return 0

    repo_root = Path(__file__).resolve().parent.parent
    config_path = repo_root / "config.yaml"
    with config_path.open(encoding="utf-8") as f:
        config = yaml.safe_load(f)

    mc = config.get("mailchimp", {})
    from_name = mc.get("from_name", "Kelly Anderson Group")
    reply_to = mc.get("reply_to", "")
    subject_prefix = mc.get("subject_prefix", "Between the Lines")

    summaries_dir = repo_root / "summaries"
    html_files = sorted(summaries_dir.glob("*.html"))
    if not html_files:
        print("No HTML files found in summaries/. Nothing to send.")
        return 1
    html_path = html_files[-1]  # YYYY-MM.html sorts correctly

    stem = html_path.stem  # "2026-08"
    try:
        month_year = datetime.strptime(stem, "%Y-%m").strftime("%B %Y")
    except ValueError:
        month_year = stem
    subject_line = f"{subject_prefix} | {month_year}"

    html = html_path.read_text(encoding="utf-8")
    intro_message = mc.get("intro_message", "")
    if intro_message:
        html = _inject_intro(html, intro_message)
        print(f"  Intro message injected ({len(intro_message)} chars)")

    print(f"Sending {html_path.name} ({len(html):,} chars) as Mailchimp campaign...")
    print(f"  Subject:  {subject_line}")
    print(f"  From:     {from_name} <{reply_to}>")
    print(f"  List ID:  {list_id}")

    campaign_id = send_campaign(
        api_key=api_key,
        list_id=list_id,
        from_name=from_name,
        reply_to=reply_to,
        subject_line=subject_line,
        html=html,
    )
    print(f"Campaign {campaign_id} sent successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
