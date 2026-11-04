import html
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from zoneinfo import ZoneInfo

import requests


XWORDINFO_URL = "https://www.xwordinfo.com/JSON/Data.ashx"


def fetch_crossword_data(puzzle_date):
    """Fetch the requested puzzle and reject incomplete or mismatched data."""
    response = requests.get(
        XWORDINFO_URL,
        params={"date": puzzle_date, "format": "text"},
        timeout=30,
        headers={"User-Agent": "XWordHint/1.0 (daily puzzle data fetch)"},
    )
    response.raise_for_status()
    data = response.json()

    if not isinstance(data, dict):
        raise ValueError("Puzzle response is not a JSON object")
    if data.get("date") != puzzle_date:
        raise ValueError(
            f"Puzzle date mismatch: requested {puzzle_date}, received {data.get('date')!r}"
        )

    clues = data.get("clues")
    answers = data.get("answers")
    if not isinstance(clues, dict) or not isinstance(answers, dict):
        raise ValueError("Puzzle response is missing clues or answers")

    for direction in ("across", "down"):
        clue_list = clues.get(direction)
        answer_list = answers.get(direction)
        if not isinstance(clue_list, list) or not isinstance(answer_list, list):
            raise ValueError(f"Missing {direction} clue/answer lists")
        if not clue_list or len(clue_list) != len(answer_list):
            raise ValueError(f"{direction} clue and answer counts do not match")
        if any(not isinstance(item, str) or not item.strip()
               for item in clue_list + answer_list):
            raise ValueError(f"Empty or invalid {direction} clue/answer")

    return data


def build_post_html(puzzle, puzzle_day):
    """Render source clues and answers; do not fabricate hints, stats, or grids."""
    parts = [
        f"<h1>NYT Crossword Answers — {puzzle_day.strftime('%B %d, %Y')}</h1>",
        "<p>This page lists the source-provided Across and Down clues with "
        "answer reveals. Try each clue before opening its answer.</p>",
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
        "<p><strong>Editorial note:</strong> Difficulty ratings, solve times, "
        "and a filled grid are not shown because verified values for those "
        "items are not present in this data feed.</p>"
    )
    return "\n".join(parts)


def send_to_blogger(subject, html_body):
    """Send through Blogger's email-to-post address using GitHub Secrets."""
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
    # NYT puzzle publication date follows the New York calendar date.
    puzzle_day = datetime.now(ZoneInfo("America/New_York")).date()
    puzzle_date = puzzle_day.strftime("%m/%d/%Y")

    try:
        puzzle = fetch_crossword_data(puzzle_date)
    except Exception as error:
        raise SystemExit(f"Daily puzzle validation failed; no post sent: {error}")

    title = f"NYT Crossword Answers — {puzzle_day.strftime('%B %d, %Y')}"
    body = build_post_html(puzzle, puzzle_day)
    send_to_blogger(title, body)
    print(f"Published verified daily crossword for {puzzle_date}.")


if __name__ == "__main__":
    main()
