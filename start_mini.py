import html
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.parse import quote
from zoneinfo import ZoneInfo

import requests


def fetch_mini_data(endpoint, puzzle_date):
    """Fetch only a configured Mini endpoint and validate a genuine 5x5 payload."""
    url = endpoint.replace("{date}", quote(puzzle_date))
    response = requests.get(
        url,
        timeout=30,
        headers={"User-Agent": "XWordHint/1.0 (Mini puzzle data fetch)"},
    )
    response.raise_for_status()
    data = response.json()

    if not isinstance(data, dict):
        raise ValueError("Mini response is not a JSON object")
    if data.get("date") != puzzle_date:
        raise ValueError(
            f"Mini date mismatch: requested {puzzle_date}, received {data.get('date')!r}"
        )

    size = data.get("size")
    if isinstance(size, dict):
        rows, columns = size.get("rows"), size.get("cols")
    else:
        rows, columns = data.get("height"), data.get("width")

    if (rows, columns) != (5, 5):
        raise ValueError(
            f"Expected verified 5x5 Mini grid metadata; received {rows}x{columns}"
        )

    clues = data.get("clues")
    answers = data.get("answers")
    if not isinstance(clues, dict) or not isinstance(answers, dict):
        raise ValueError("Mini response is missing clues or answers")

    for direction in ("across", "down"):
        clue_list = clues.get(direction)
        answer_list = answers.get(direction)
        if not isinstance(clue_list, list) or not isinstance(answer_list, list):
            raise ValueError(f"Missing Mini {direction} clue/answer lists")
        if not clue_list or len(clue_list) != len(answer_list):
            raise ValueError(f"Mini {direction} clue and answer counts do not match")
        if any(not isinstance(item, str) or not item.strip()
               for item in clue_list + answer_list):
            raise ValueError(f"Empty or invalid Mini {direction} clue/answer")

    return data


def build_mini_post_html(puzzle, puzzle_day):
    """Render source-provided Mini clues and answers without invented grid data."""
    parts = [
        f"<h1>NYT Mini Crossword Answers — {puzzle_day.strftime('%B %d, %Y')}</h1>",
        "<p>Try each clue first, then open its answer below. Clues and answers "
        "are displayed in the order supplied by the configured Mini data source.</p>",
        "<p><em>XWordHint is an independent puzzle-help website and is not "
        "affiliated with The New York Times.</em></p>",
    ]

    for direction in ("across", "down"):
        clues = puzzle["clues"][direction]
        answers = puzzle["answers"][direction]
        parts.append(
            f"<section><h2>{direction.title()} clues and answers ({len(clues)})</h2><ol>"
        )
        for clue, answer in zip(clues, answers):
            clue_text = html.escape(clue)
            answer_text = html.escape(answer.upper())
            letter_count = sum(character.isalpha() for character in answer)
            parts.append(
                "<li>"
                f"<p><strong>{clue_text}</strong></p>"
                f"<p>Answer length: {letter_count} letters.</p>"
                f"<details><summary>Reveal answer</summary>"
                f"<strong>{answer_text}</strong></details>"
                "</li>"
            )
        parts.append("</ol></section>")

    parts.append(
        "<p><strong>Editorial note:</strong> No solve-time estimate, difficulty "
        "rating, or grid image is included unless the source supplies verified data.</p>"
    )
    return "\n".join(parts)


def send_to_blogger(subject, html_body):
    sender = os.environ.get("BLOGGER_FROM_EMAIL", "").strip()
    app_password = os.environ.get("BLOGGER_APP_PASSWORD", "").strip()
    recipient = os.environ.get("BLOGGER_TO_EMAIL", "").strip()

    if not sender or not app_password or not recipient:
        raise RuntimeError(
            "Set BLOGGER_FROM_EMAIL, BLOGGER_APP_PASSWORD and BLOGGER_TO_EMAIL secrets"
        )

    message = MIMEMultipart("alternative")
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = subject
    message.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
        server.starttls()
        server.login(sender, app_password)
        server.send_message(message)


def main():
    endpoint = os.environ.get("MINI_XWORDINFO_URL", "").strip()
    if not endpoint:
        raise SystemExit(
            "MINI_XWORDINFO_URL is not configured. Mini publishing stopped; no post sent."
        )

    puzzle_day = datetime.now(ZoneInfo("America/New_York")).date()
    puzzle_date = puzzle_day.strftime("%m/%d/%Y")

    try:
        puzzle = fetch_mini_data(endpoint, puzzle_date)
    except Exception as error:
        raise SystemExit(f"Mini puzzle validation failed; no post sent: {error}")

    title = f"NYT Mini Crossword Answers — {puzzle_day.strftime('%B %d, %Y')}"
    body = build_mini_post_html(puzzle, puzzle_day)
    send_to_blogger(title, body)
    print(f"Published verified 5x5 Mini crossword for {puzzle_date}.")


if __name__ == "__main__":
    main()
