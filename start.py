import os
import requests
import smtplib
import json
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Function to get synonyms
def get_synonyms(word):
    synonyms = set()
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            synonym = lemma.name().replace('_', ' ')
            if synonym.lower() != word.lower():
                synonyms.add(synonym)
    return list(synonyms)

# Function to get antonyms
def get_antonyms(word):
    antonyms = set()
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            if lemma.antonyms():
                antonym = lemma.antonyms()[0].name().replace('_', ' ')
                if antonym.lower() != word.lower():
                    antonyms.add(antonym)
    return list(antonyms)

# Function to get word definitions
def get_word_definition(word):
    definitions = []
    for syn in wordnet.synsets(word):
        definition = syn.definition()
        if definition and len(definition) > 10:
            definitions.append(definition)
    return definitions[:2] if definitions else []

# Function to generate hint text without revealing answer
def generate_hint_text(answer, clue):
    """Return only verifiable structural help; do not invent synonyms or definitions."""
    letters = len("".join(ch for ch in str(answer) if ch.isalpha()))
    return [f"Answer length: {letters} letters."]

# Do not draw a fake grid. XWordInfo's clue feed does not provide a verified
# cell-by-cell grid layout for this template.
def create_crossword_grid(crossword_data):
    return "<p><em>Grid preview is not available from the verified clue feed.</em></p>"

# Fetch and validate source data. Never publish sample/fallback puzzle content.
def fetch_crossword_data(url):
    try:
        response = requests.get(url, timeout=25)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError("Puzzle response is not a JSON object")
        clues = data.get("clues") or {}
        answers = data.get("answers") or {}
        for direction in ("across", "down"):
            clue_list = clues.get(direction)
            answer_list = answers.get(direction)
            if not isinstance(clue_list, list) or not isinstance(answer_list, list):
                raise ValueError(f"Missing {direction} clues or answers")
            if not clue_list or len(clue_list) != len(answer_list):
                raise ValueError(f"{direction} clue/answer counts do not match")
            if any(not isinstance(x, str) or not x.strip() for x in clue_list + answer_list):
                raise ValueError(f"Invalid empty/non-text {direction} entry")
        if not data.get("date"):
            raise ValueError("Puzzle date is missing")
        return data
    except Exception as exc:
        print(f"Puzzle fetch/validation failed; nothing will be published: {exc}")
        return None



def format_to_html(crossword_data, date):
    """Create a factual clue-and-answer page without fabricated stats or grid art."""
    import html as html_lib

    parts = [
        f"<h1>NYT Crossword Answers and Clues — {date.strftime('%B %d, %Y')}</h1>",
        "<p>This page organizes the source-provided Across and Down clues. "
        "Answer reveals are hidden so readers can try each clue first.</p>",
        "<p><strong>Source:</strong> XWordInfo puzzle data. XWordHint is an independent "
        "puzzle-help site and is not affiliated with The New York Times.</p>",
    ]
    for direction in ("across", "down"):
        clues = crossword_data["clues"][direction]
        answers = crossword_data["answers"][direction]
        heading = direction.title()
        parts.append(f"<section><h2>{heading} clues ({len(clues)})</h2><ol>")
        for clue, answer in zip(clues, answers):
            safe_clue = html_lib.escape(clue)
            safe_answer = html_lib.escape(answer.upper())
            length = sum(ch.isalpha() for ch in answer)
            parts.append(
                f"<li><p><strong>{safe_clue}</strong></p>"
                f"<p>Hint: the answer contains {length} letters.</p>"
                f"<details><summary>Reveal answer</summary><strong>{safe_answer}</strong></details></li>"
            )
        parts.append("</ol></section>")
    parts.append(
        "<p><strong>Editorial note:</strong> Difficulty ratings and solve-time statistics "
        "are not included because this feed does not provide verified measurements.</p>"
    )
    return "\n".join(parts)



# Blogger email-to-post delivery. Credentials must come from GitHub Actions secrets.
def send_email(to_email, subject, html_content):
    from_email = os.environ.get("BLOGGER_FROM_EMAIL", "").strip()
    password = os.environ.get("BLOGGER_APP_PASSWORD", "").strip()
    if not from_email or not password:
        raise RuntimeError("Missing BLOGGER_FROM_EMAIL or BLOGGER_APP_PASSWORD secret")

    msg = MIMEMultipart("alternative")
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
        server.starttls()
        server.login(from_email, password)
        server.send_message(msg)



# Use the NYT puzzle's Eastern Time calendar date, not the runner's UTC date.
def main():
    from zoneinfo import ZoneInfo

    puzzle_date = datetime.now(ZoneInfo("America/New_York")).strftime("%m/%d/%Y")
    url = f"https://www.xwordinfo.com/JSON/Data.ashx?date={puzzle_date}&format=text"
    crossword_data = fetch_crossword_data(url)
    if not crossword_data:
        raise SystemExit("No verified puzzle data; publication cancelled.")

    date = datetime.strptime(crossword_data["date"], "%m/%d/%Y")
    if date.strftime("%m/%d/%Y") != puzzle_date:
        raise SystemExit("Source puzzle date does not match requested Eastern date; publication cancelled.")

    title = f"NYT Crossword Answers — {date.strftime('%B %d, %Y')} | Across and Down Clues"
    html_content = format_to_html(crossword_data, date)
    recipient = os.environ.get("BLOGGER_TO_EMAIL", "velanms1993.qrco@blogger.com")
    send_email(recipient, title, html_content)
    print(f"Verified puzzle email sent for {date.strftime('%B %d, %Y')}.")



# Execute the main function
if __name__ == "__main__":
    main()
    
