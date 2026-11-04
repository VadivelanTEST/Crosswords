import os
import requests
import smtplib
import json
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from nltk.corpus import wordnet
import nltk
from datetime import datetime
import random
import xml.etree.ElementTree as ET
import re

# Download wordnet if not already present
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

# Helper function to get week of month (1-4)
def get_week_of_month(date_obj):
    """Calculate the week of the month (1-4)"""
    day = date_obj.day
    week = (day - 1) // 7 + 1
    # Cap at 4 as requested "4 weeks in per month"
    return min(week, 4)

# SEO-optimized title templates for NYT Mini
SEO_TITLE_TEMPLATES = [
    "NYT Mini Trivia Week {week_num} {date} - Hints & Answers",
    "Trivia Week {week_num} NYT Mini {date} Solutions & Guide",
    "NYT Mini Crossword Trivia Week {week_num} {date} - Daily Answers",
    "Quick NYT Mini Crossword {date} (Trivia Week {week_num}) - Solutions",
    "NYT Mini Puzzle Trivia Week {week_num} {date} - Solved",
    "Today's Trivia Week {week_num} NYT Mini Crossword {date} Answers",
    "Trivia Week {week_num} {date} NYT Mini Crossword Hints",
    "NYT Mini Answers {date} - Trivia Week {week_num} Special",
    "Complete Solutions for NYT Mini Trivia Week {week_num} {date}",
    "Trivia Week {week_num} Manual for NYT Mini {date}"
]

# Function to fetch internal links from sitemap
def fetch_sitemap_urls(max_links=20):
    """Fetch URLs from xwordhint sitemap for internal linking"""
    internal_links = []

    try:
        # Try to fetch from both pages of sitemap
        for page in [1, 2]:
            url = f"https://xwordhint.blogspot.com/sitemap.xml?page={page}"

            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    # Parse XML
                    root = ET.fromstring(response.content)

                    # Extract URLs from the sitemap
                    # Blogger sitemaps use the namespace
                    namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

                    for url_element in root.findall('.//ns:url', namespace):
                        loc = url_element.find('ns:loc', namespace)
                        if loc is not None and loc.text:
                            url_text = loc.text
                            # Only include actual post URLs, not the homepage
                            if url_text and ('/2024/' in url_text or '/2025/' in url_text or '/2021/' in url_text or '/2022/' in url_text or '/2023/' in url_text):
                                # Extract title from URL for anchor text
                                title_match = re.search(r'/(\d{4}/\d{2})/(.+?)\.html', url_text)
                                if title_match:
                                    post_slug = title_match.group(2)
                                    # Convert slug to readable title
                                    title = post_slug.replace('-', ' ').title()
                                    # Clean up common patterns
                                    title = title.replace('Nyt', 'NYT').replace('Crossword', 'Crossword')
                                    internal_links.append({
                                        'url': url_text,
                                        'title': title
                                    })
            except Exception as e:
                print(f"Error fetching sitemap page {page}: {e}")

    except Exception as e:
        print(f"Error in sitemap fetching: {e}")

    # If no links fetched, use fallback links
    if not internal_links:
        internal_links = [
            {'url': 'https://xwordhint.blogspot.com/2024/12/nyt-crossword-december-hints.html', 'title': 'NYT Crossword December Hints'},
            {'url': 'https://xwordhint.blogspot.com/2024/11/nyt-crossword-november-solutions.html', 'title': 'NYT Crossword November Solutions'},
            {'url': 'https://xwordhint.blogspot.com/2024/10/crossword-puzzle-tips.html', 'title': 'Crossword Puzzle Tips'},
            {'url': 'https://xwordhint.blogspot.com/2024/09/mini-crossword-guide.html', 'title': 'Mini Crossword Guide'},
            {'url': 'https://xwordhint.blogspot.com/2024/08/daily-puzzle-help.html', 'title': 'Daily Puzzle Help'}
        ]

    # Return random selection of links
    if len(internal_links) > max_links:
        return random.sample(internal_links, max_links)
    return internal_links

# Mini-specific high-traffic keywords for SEO
MINI_KEYWORDS = {
    'primary': [
        'NYT Mini Trivia Week',
        'Trivia Week {week_num}',
        'Mini crossword Trivia Week',
        'Trivia Week answers',
        'NYT Trivia Week',
        'NYT Mini',
        'Mini crossword',
        'today'
    ],
    'long_tail': [
        'NYT Mini Trivia Week answers',
        'Trivia Week {week_num} crossword hints',
        'NYT Mini Trivia Week solutions',
        'how to solve Trivia Week {week_num} Mini',
        'Trivia Week crossword help',
        'NYT 5x5 Trivia Week puzzle'
    ],
    'voice_search': [
        'What are today\'s Trivia Week answers',
        'How do I solve the Trivia Week Mini',
        'Give me hints for Trivia Week {week_num}',
        'Show me NYT Mini Trivia Week solutions'
    ]
}

# Function to get synonyms (optimized for Mini's shorter words)
def get_mini_synonyms(word):
    """Get relevant synonyms for Mini crossword's typically shorter words"""
    synonyms = set()
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            synonym = lemma.name().replace('_', ' ')
            # Mini tends to use shorter words, filter by length
            if synonym.lower() != word.lower() and len(synonym) <= 7:
                synonyms.add(synonym)
    return list(synonyms)[:2]  # Return fewer synonyms for Mini

# Function to get antonyms (simplified for Mini)
def get_mini_antonyms(word):
    """Get antonyms suitable for Mini crossword hints"""
    antonyms = set()
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            if lemma.antonyms():
                antonym = lemma.antonyms()[0].name().replace('_', ' ')
                if antonym.lower() != word.lower() and len(antonym) <= 7:
                    antonyms.add(antonym)
    return list(antonyms)[:1]  # Just one antonym for Mini

# ---------------------------------------------------------------------------
# Hint phrasing pools. Each hint "type" below has several ways of saying the
# same thing so two clues in the same post (or the same clue on two
# different days) don't read like they came out of a template. Pick one at
# random each time instead of always using sentence #1.
# ---------------------------------------------------------------------------
LETTER_COUNT_PHRASES = [
    "It's a {n}-letter word.",
    "Count on {n} letters here.",
    "This one runs {n} letters long.",
    "You're looking for {n} letters.",
]

FIRST_LAST_PHRASES = [
    "Starts with '{first}', ends with '{last}'.",
    "First letter's a '{first}', last letter's a '{last}'.",
    "Kicks off with '{first}' and wraps up with '{last}'.",
]

PATTERN_PHRASES = [
    "Pattern-wise it looks like: {pattern}",
    "If that helps, the shape is: {pattern}",
    "Blank it out and you get: {pattern}",
]

SYNONYM_PHRASES = [
    "Close enough in meaning: {syn}.",
    "You could also think of it as \"{syn}.\"",
    "'{syn}' points in the same direction.",
]

DEFINITION_PHRASES = [
    "In plain terms: {defn}.",
    "Basically, {defn}.",
    "Think of it this way — {defn}.",
]

MISC_HINT_PHRASES = {
    'digits': [
        "There are numbers baked into this answer.",
        "Yep, digits show up in this one.",
    ],
    'acronym': [
        "This is more of an abbreviation than a regular word.",
        "Short form / acronym territory here.",
    ],
    'short_common': [
        "One of those tiny, everyday words — you've used it a hundred times.",
        "Super common short word, don't overthink it.",
    ],
}

def generate_mini_hint_text(answer, clue, clue_number, direction):
    """Provide only verifiable letter-count information; avoid fabricated clues."""
    count = sum(ch.isalpha() for ch in str(answer))
    return [f"Answer length: {count} letters."]

def create_mini_grid_html(crossword_data, week_num):
    # Do not invent a checkerboard that does not match the source puzzle.
    return "<p><em>Grid preview omitted because verified cell-layout data is unavailable.</em></p>"

# Accept only a real 5x5 Mini puzzle. Never sample clues from the full-size puzzle.
def select_mini_clues(crossword_data):
    if not isinstance(crossword_data, dict):
        raise ValueError("Mini source payload must be a JSON object")
    size = crossword_data.get("size") or {}
    rows = size.get("rows") if isinstance(size, dict) else None
    cols = size.get("cols") if isinstance(size, dict) else None
    if rows is None:
        rows = crossword_data.get("height")
    if cols is None:
        cols = crossword_data.get("width")
    if (rows, cols) != (5, 5):
        raise ValueError(f"Expected an actual 5x5 Mini puzzle; received {rows}x{cols}")
    if not crossword_data.get("date"):
        raise ValueError("Mini puzzle date is missing")

    clues = crossword_data.get("clues") or {}
    answers = crossword_data.get("answers") or {}
    for direction in ("across", "down"):
        clue_list = clues.get(direction)
        answer_list = answers.get(direction)
        if not isinstance(clue_list, list) or not isinstance(answer_list, list):
            raise ValueError(f"Missing Mini {direction} clues or answers")
        if not clue_list or len(clue_list) != len(answer_list):
            raise ValueError(f"Mini {direction} clue/answer counts do not match")
        if any(not isinstance(x, str) or not x.strip() for x in clue_list + answer_list):
            raise ValueError(f"Invalid Mini {direction} entry")
    return crossword_data

# Fetch only from a separately configured, verified Mini data endpoint.
def fetch_mini_crossword_data(url):
    try:
        response = requests.get(url, timeout=25)
        response.raise_for_status()
        data = response.json()
        return select_mini_clues(data)
    except Exception as exc:
        print(f"Mini fetch/validation failed; nothing will be published: {exc}")
        return None





# Function to generate SEO-optimized title
def generate_seo_title(date, crossword_data):
    """Generate SEO-optimized title using templates and data"""
    template = random.choice(SEO_TITLE_TEMPLATES)

    across_count = len(crossword_data['clues']['across'])
    down_count = len(crossword_data['clues']['down'])
    total_clues = across_count + down_count
    week_num = get_week_of_month(date)

    title = template.format(
        date=date.strftime('%B %d, %Y'),
        short_date=date.strftime('%b %d'),
        day=date.strftime('%A'),
        total=total_clues,
        across=across_count,
        down=down_count,
        time=random.choice(['1', '2', '3']),
        week_num=week_num
    )

    return title

MINI_IMAGES = [
    "nyt_mini_puzzle_{}.png".format(i) for i in range(1, 51)
]

# Varied intro / summary lines so the opening paragraph isn't identical
# on every post
INTRO_VARIANTS = [
    "Here's today's NYT Mini — {total} clues in total, and we've got hints plus answers for every one of them.",
    "Today's Mini has {total} clues to get through. Hints and answers for all of them are below.",
    "{total} clues today. If you're stuck on any of them, scroll down — hints first, answers hidden underneath.",
]

TIPS_INTRO_VARIANTS = [
    "A few things that actually help once you've been doing these a while:",
    "Some habits that speed things up over time:",
    "Here's what tends to work if you solve these regularly:",
]

STEP_STRATEGY_VARIANTS = [
    [
        ("Read it all first", "Go through every clue once before writing anything down — it primes your brain even on the ones you skip."),
        ("Grab the short ones", "Two and three letter answers (things like \"IT\" or \"ON\") are usually the easiest place to start."),
        ("Use the crossings", "Once a couple of words are in, the crossing letters do a lot of the work for you on the harder ones."),
        ("Watch for question marks", "A \"?\" at the end of a clue almost always signals a pun rather than a literal answer."),
        ("Keep the regulars in mind", "ERA, ORE, ATE, ICE — these turn up often enough that it's worth remembering them."),
    ],
    [
        ("Scan before you solve", "One quick read-through of all the clues before you commit to anything usually pays off."),
        ("Short words first", "The 2-3 letter answers are almost always the low-hanging fruit."),
        ("Let crossings guide you", "Harder answers get much easier once a couple of crossing letters are locked in."),
        ("Puns hide behind question marks", "If a clue ends in \"?\", expect wordplay, not a straight answer."),
        ("A few words repeat a lot", "ERA, ORE, ATE, ICE show up more than you'd expect — keep them in mind."),
    ],
]

FAQ_ANSWER_VARIANTS = {
    'when': [
        "It usually goes live around 10 PM Eastern the night before.",
        "Typically drops the evening before, around 10 PM ET.",
    ],
    'time': [
        "Most people land somewhere between 30 seconds and 2 minutes. Slower than that is completely normal too — it gets faster with practice.",
        "Anywhere from 30 seconds to a couple of minutes is typical. Don't stress if you're on the slower end at first.",
    ],
    'cost': [
        "Nope, it's free — no subscription needed like the full-size crossword.",
        "It's free to play, unlike the main NYT Crossword which sits behind a paywall.",
    ],
    'good_solver': [
        "Knowing the common short words, spotting wordplay quickly, and reading crossing letters well — that combination gets you most of the way there.",
        "It mostly comes down to recognizing common short answers and catching puns fast. The rest is just reps.",
    ],
    'difficulty': [
        "It varies day to day — Saturdays tend to be the toughest, Mondays the easiest.",
        "Difficulty shifts through the week; expect Monday to be gentle and Saturday to bite a bit more.",
    ],
}

def format_mini_to_html(crossword_data, date):
    """Create a source-grounded Mini clue page without invented grid/statistics."""
    import html as html_lib

    parts = [
        f"<h1>NYT Mini Crossword — {date.strftime('%B %d, %Y')} Hints and Answers</h1>",
        "<p>Try each clue before opening its answer. The clue and answer lists below "
        "are taken from the configured Mini puzzle data source.</p>",
        "<p>XWordHint is an independent puzzle-help site and is not affiliated with "
        "The New York Times.</p>",
    ]
    for direction in ("across", "down"):
        clues = crossword_data["clues"][direction]
        answers = crossword_data["answers"][direction]
        parts.append(f"<section><h2>{direction.title()} ({len(clues)})</h2><ol>")
        for clue, answer in zip(clues, answers):
            safe_clue = html_lib.escape(clue)
            safe_answer = html_lib.escape(answer.upper())
            count = sum(ch.isalpha() for ch in answer)
            parts.append(
                f"<li><p><strong>{safe_clue}</strong></p>"
                f"<p>Hint: the answer contains {count} letters.</p>"
                f"<details><summary>Reveal answer</summary><strong>{safe_answer}</strong></details></li>"
            )
        parts.append("</ol></section>")
    parts.append(
        "<p><strong>Note:</strong> No solve-time or difficulty estimate is shown "
        "because no verified solver statistics are supplied by the data source.</p>"
    )
    return "\n".join(parts)



# Blogger email-to-post delivery. Credentials must come from GitHub Actions secrets.
def send_mini_email(to_email, subject, html_content):
    from_email = os.environ.get("BLOGGER_FROM_EMAIL", "").strip()
    password = os.environ.get("BLOGGER_APP_PASSWORD", "").strip()
    if not from_email or not password:
        raise RuntimeError("Missing BLOGGER_FROM_EMAIL or BLOGGER_APP_PASSWORD secret")

    msg = MIMEMultipart("alternative")
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html_content, "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
        server.starttls()
        server.login(from_email, password)
        server.send_message(msg)
    return True



# Mini publishing stays fail-closed until a real 5x5 source URL is configured.
def main():
    from zoneinfo import ZoneInfo

    url = os.environ.get("MINI_XWORDINFO_URL", "").strip()
    if not url:
        raise SystemExit("Set MINI_XWORDINFO_URL to a verified 5x5 Mini data endpoint; no post was published.")

    puzzle_date = datetime.now(ZoneInfo("America/New_York")).strftime("%m/%d/%Y")
    crossword_data = fetch_mini_crossword_data(url)
    if not crossword_data:
        raise SystemExit("No verified Mini puzzle data; publication cancelled.")

    date = datetime.strptime(crossword_data["date"], "%m/%d/%Y")
    if date.strftime("%m/%d/%Y") != puzzle_date:
        raise SystemExit("Mini source date does not match requested Eastern date; publication cancelled.")

    title = f"NYT Mini Crossword — {date.strftime('%B %d, %Y')} Hints and Answers"
    html_content = format_mini_to_html(crossword_data, date)
    recipient = os.environ.get("BLOGGER_TO_EMAIL", "velanms1993.qrco@blogger.com")
    send_mini_email(recipient, title, html_content)
    print(f"Verified 5x5 Mini email sent for {date.strftime('%B %d, %Y')}.")



if __name__ == "__main__":
    main()
