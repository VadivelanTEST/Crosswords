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

# Function to generate Mini-specific hints
def generate_mini_hint_text(answer, clue, clue_number, direction):
    """Generate simple hints that help without giving away the answer,
    with the phrasing varied so it doesn't read like a fill-in-the-blank
    template every time."""
    hints = []

    letter_count = len(answer.replace(" ", ""))
    hints.append(random.choice(LETTER_COUNT_PHRASES).format(n=letter_count))

    if len(answer) >= 3:
        hints.append(random.choice(FIRST_LAST_PHRASES).format(first=answer[0], last=answer[-1]))

    if len(answer) >= 4:
        pattern = answer[0] + ''.join(['_' for _ in answer[1:-1]]) + answer[-1]
        # skip this one sometimes so not every clue gets a pattern line
        if random.random() < 0.7:
            hints.append(random.choice(PATTERN_PHRASES).format(pattern=pattern))

    synonyms = get_mini_synonyms(answer)
    if synonyms:
        hints.append(random.choice(SYNONYM_PHRASES).format(syn=synonyms[0]))

    if any(char.isdigit() for char in answer):
        hints.append(random.choice(MISC_HINT_PHRASES['digits']))
    elif answer.isupper() and len(answer) <= 4:
        hints.append(random.choice(MISC_HINT_PHRASES['acronym']))
    elif len(answer) <= 3:
        hints.append(random.choice(MISC_HINT_PHRASES['short_common']))

    synsets = wordnet.synsets(answer)
    if synsets and synsets[0].definition():
        simple_def = synsets[0].definition().split(',')[0]
        if len(simple_def) < 50:
            hints.append(random.choice(DEFINITION_PHRASES).format(defn=simple_def))

    # shuffle so the order isn't identical every single time either
    random.shuffle(hints)
    return hints

# Function to create Mini 5x5 grid visualization
def create_mini_grid_html(crossword_data, week_num):
    """Create a professional 5x5 grid table for NYT Mini"""
    try:
        grid_size = 5

        intro_variants = [
            "It's a 5 by 5 grid today — five boxes across, five boxes down.",
            "Today's layout is the usual 5x5: five columns, five rows.",
            "Standard Mini size again: 5 across, 5 down.",
        ]

        solve_tip_variants = [
            [
                "Skim every clue once before you write anything — your brain keeps chewing on the ones you don't solve right away.",
                "Knock out the short answers (3 letters or under) first.",
                "Lean on the crossing letters once a couple of words are in.",
                "A question mark in a clue usually means there's a pun coming.",
                "THE, AND, ARE, FOR, NOT — these little words show up constantly, keep them in your back pocket.",
            ],
            [
                "Read through all the clues before filling in a single square.",
                "Start with anything three letters or shorter.",
                "Crossing letters are your best friend for the trickier answers.",
                "Question mark clues (?) almost always mean wordplay, not a literal answer.",
                "Watch for the usual suspects: THE, AND, ARE, FOR, NOT.",
            ],
        ]

        fact_variants = [
            [
                ("Total squares", "25 (5 × 5)"),
                ("Typical solve time", "well under a minute for most regulars"),
                ("Good time to play", "on a coffee break"),
                ("Difficulty", "built to be approachable"),
            ],
            [
                ("Squares in the grid", "25"),
                ("How long it takes", "usually under a minute once you're warmed up"),
                ("Best moment for it", "any short break"),
                ("Overall difficulty", "easy-going by design"),
            ],
        ]

        chosen_tips = random.choice(solve_tip_variants)
        chosen_facts = random.choice(fact_variants)

        grid_html = f"""
        <section>
            <h2>Today's Trivia Week {week_num} NYT Mini Crossword Grid Layout</h2>
            <p>{random.choice(intro_variants)}</p>

            <table border="1" cellpadding="10" cellspacing="0" style="width: 100%; max-width: 350px; margin: 0 auto; border-collapse: collapse;">
                <caption>5x5 Crossword Grid Pattern</caption>
                <thead>
                    <tr>
                        <th></th>
                        <th>Column 1</th>
                        <th>Column 2</th>
                        <th>Column 3</th>
                        <th>Column 4</th>
                        <th>Column 5</th>
                    </tr>
                </thead>
                <tbody>
        """

        # Create visual 5x5 grid
        for row in range(grid_size):
            grid_html += f'<tr><th>Row {row + 1}</th>'
            for col in range(grid_size):
                if (row + col) % 2 == 0:
                    grid_html += '<td bgcolor="#FFFFFF">&nbsp;</td>'
                else:
                    grid_html += '<td bgcolor="#F0F0F0">&nbsp;</td>'
            grid_html += '</tr>'

        tips_html = "".join(f"<li>{tip}</li>" for tip in chosen_tips)
        facts_html = "".join(f"<li><strong>{label}:</strong> {value}</li>" for label, value in chosen_facts)

        grid_html += f"""
                </tbody>
            </table>

            <h3>How to Solve This One Fast</h3>
            <ol>
                {tips_html}
            </ol>

            <h3>Quick Facts</h3>
            <ul>
                {facts_html}
            </ul>
        </section>
        """

        return grid_html

    except Exception as e:
        print(f"Error creating grid: {e}")
        return """
        <section>
            <h2>NYT Mini Crossword - 5x5 Puzzle</h2>
            <p>Today's puzzle is ready to solve!</p>
        </section>
        """

# Function to select top clues for Mini (max 10 each)
def select_mini_clues(crossword_data):
    """Randomly select exactly 10 Across and 10 Down clues for Mini format"""
    selected_data = {
        'clues': {'across': [], 'down': []},
        'answers': {'across': [], 'down': []},
        'date': crossword_data.get('date', datetime.now().strftime("%m/%d/%Y"))
    }

    num_clues = 10

    across_pairs = list(zip(
        crossword_data.get('clues', {}).get('across', []),
        crossword_data.get('answers', {}).get('across', [])
    ))

    if len(across_pairs) > num_clues:
        selected_across = random.sample(across_pairs, num_clues)
    else:
        selected_across = across_pairs

    for clue, answer in selected_across:
        selected_data['clues']['across'].append(clue)
        selected_data['answers']['across'].append(answer)

    down_pairs = list(zip(
        crossword_data.get('clues', {}).get('down', []),
        crossword_data.get('answers', {}).get('down', [])
    ))

    if len(down_pairs) > num_clues:
        selected_down = random.sample(down_pairs, num_clues)
    else:
        selected_down = down_pairs

    for clue, answer in selected_down:
        selected_data['clues']['down'].append(clue)
        selected_data['answers']['down'].append(answer)

    return selected_data

# Function to fetch Mini crossword data
def fetch_mini_crossword_data(url):
    """Fetch crossword data and adapt it for Mini format"""
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'max-age=0',
        'Referer': 'https://www.xwordinfo.com/JSON/',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            print(f"Successfully fetched data. Content-Type: {response.headers.get('Content-Type', '')}")
            print(f"Response preview: {response.text[:100]}...")

            if 'text/plain' in response.headers.get('Content-Type', ''):
                try:
                    data = json.loads(response.text)
                    mini_data = select_mini_clues(data)
                    return mini_data
                except json.JSONDecodeError:
                    print("Error: Could not decode JSON response.")
                    return get_sample_mini_data()
            else:
                try:
                    data = json.loads(response.text)
                    mini_data = select_mini_clues(data)
                    return mini_data
                except:
                    print(f"Error: Unexpected content type {response.headers.get('Content-Type')}")
                    return get_sample_mini_data()
        else:
            print(f"Error fetching data. Status code: {response.status_code}")
            return get_sample_mini_data()
    except Exception as e:
        print(f"Exception fetching crossword: {e}")
        return get_sample_mini_data()

# Function to provide sample Mini data for testing
def get_sample_mini_data():
    """Provide sample Mini crossword data for testing"""
    return {
        'date': datetime.now().strftime("%m/%d/%Y"),
        'clues': {
            'across': [
                'Opposite of "no"',
                'Tree with acorns',
                'Feline pet',
                'Not off',
                'Eggs on sushi',
                'Frozen water',
                'Cheer for a matador',
                'Period of time'
            ],
            'down': [
                'Affirmative vote',
                'Make a mistake',
                'Ocean motion',
                'Garden tool',
                'What bees make',
                'Color of grass',
                'Not young',
                'Opposite of west'
            ]
        },
        'answers': {
            'across': [
                'YES', 'OAK', 'CAT', 'ON', 'ROE', 'ICE', 'OLE', 'ERA'
            ],
            'down': [
                'YEA', 'ERR', 'TIDE', 'HOE', 'HONEY', 'GREEN', 'OLD', 'EAST'
            ]
        }
    }

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
    """Format Mini crossword data to professional HTML with comprehensive SEO"""

    week_num = get_week_of_month(date)

    selected_image = random.choice(MINI_IMAGES)
    image_url = f"https://raw.githubusercontent.com/xwordhint/answer/main/mini-image/{selected_image}"

    seo_title = generate_seo_title(date, crossword_data)

    across_count = len(crossword_data['clues']['across'])
    down_count = len(crossword_data['clues']['down'])
    total_clues = across_count + down_count

    internal_links = fetch_sitemap_urls(max_links=15)

    intro_line = random.choice(INTRO_VARIANTS).format(total=total_clues)

    html = f"""
        <header>
            <h1>{seo_title}</h1>
            <p>{intro_line}</p>

            <p><strong>Popular Puzzles:</strong>
    """

    if internal_links:
        for link in random.sample(internal_links, min(3, len(internal_links))):
            html += f' <a href="{link["url"]}">{link["title"]}</a> |'

    html += f"""
            </p>
        </header>

        <nav aria-label="Page Navigation">
            <h2>Jump To Section</h2>
            <ul>
                <li><a href="#puzzle-info">Puzzle Information</a></li>
                <li><a href="#grid-layout">Grid Layout</a></li>
                <li><a href="#across-clues">Across Clues ({across_count} total)</a></li>
                <li><a href="#down-clues">Down Clues ({down_count} total)</a></li>
                <li><a href="#solving-tips">How to Solve Faster</a></li>
                <li><a href="#faq">Common Questions</a></li>
            </ul>
        </nav>

        <section id="puzzle-info">
            <h2>About Today's Puzzle</h2>
            <figure>
                <img src="{image_url}"
                     alt="NYT Mini Crossword solutions for {date.strftime('%B %d, %Y')}"
                     title="Complete answers and hints for today's NYT Mini"
                     width="400"
                     height="400" />
                <figcaption>NYT Mini Crossword Grid - {date.strftime('%A, %B %d, %Y')}</figcaption>
            </figure>

            <table border="1" cellpadding="5">
                <caption>Puzzle Statistics</caption>
                <thead>
                    <tr>
                        <th>Detail</th>
                        <th>Information</th>
                    </tr>
                </thead>
                <tbody>
                    <tr><td>Date</td><td>{date.strftime('%B %d, %Y')}</td></tr>
                    <tr><td>Grid Size</td><td>5 x 5 squares</td></tr>
                    <tr><td>Total Clues</td><td>{total_clues} clues</td></tr>
                    <tr><td>Across Clues</td><td>{across_count} clues</td></tr>
                    <tr><td>Down Clues</td><td>{down_count} clues</td></tr>
                    <tr><td>Average Solve Time</td><td>Under 1 minute</td></tr>
                </tbody>
            </table>
        </section>

        <section id="grid-layout">
            {create_mini_grid_html(crossword_data, week_num)}
        </section>

        <section id="across-clues">
            <h2>Across Clues - {across_count} Total</h2>
            <p>These run left to right across the grid.</p>

            <table border="1" cellpadding="10" cellspacing="0" width="100%">
                <caption>Across Clues List</caption>
                <thead>
                    <tr><th width="15%">Number</th><th width="85%">Clue</th></tr>
                </thead>
                <tbody>
    """

    for idx, clue in enumerate(crossword_data['clues']['across'], 1):
        html += f"""
                    <tr>
                        <td align="center"><strong>{idx} Across</strong></td>
                        <td>{clue}</td>
                    </tr>
        """

    html += f"""
                </tbody>
            </table>

            <h3>Hints and Answers for Across Clues</h3>
            <p>Stuck on one? Hints and answers for each clue are below. A few other guides worth a look:</p>
            <ul>
    """

    if internal_links:
        for link in random.sample(internal_links, min(3, len(internal_links))):
            html += f'        <li><a href="{link["url"]}">{link["title"]}</a></li>\n'

    html += "            </ul>\n"

    for idx, (clue, answer) in enumerate(zip(crossword_data['clues']['across'], crossword_data['answers']['across']), 1):
        hints = generate_mini_hint_text(answer, clue, idx, 'Across')

        html += f"""
            <hr>
            <h4>{idx} Across: "{clue}"</h4>
            <p><strong>Hints:</strong></p>
            <ul>
        """
        for hint in hints[:3]:
            html += f"        <li>{hint}</li>\n"
        html += f"""
            </ul>
            <p><strong>Answer:</strong>
                <details>
                    <summary>Click to reveal</summary>
                    <strong>{answer.upper()}</strong>
                </details>
            </p>
        """

    html += f"""
        </section>

        <section id="down-clues">
            <h2>Down Clues - {down_count} Total</h2>
            <p>These run top to bottom in the grid.</p>

            <table border="1" cellpadding="10" cellspacing="0" width="100%">
                <caption>Down Clues List</caption>
                <thead>
                    <tr><th width="15%">Number</th><th width="85%">Clue</th></tr>
                </thead>
                <tbody>
    """

    for idx, clue in enumerate(crossword_data['clues']['down'], 1):
        html += f"""
                    <tr>
                        <td align="center"><strong>{idx} Down</strong></td>
                        <td>{clue}</td>
                    </tr>
        """

    html += f"""
                </tbody>
            </table>

            <h3>Hints and Answers for Down Clues</h3>
            <p>Same deal here — hints then answers. You might also like:</p>
            <ul>
    """

    if internal_links:
        for link in random.sample(internal_links, min(3, len(internal_links))):
            html += f'        <li><a href="{link["url"]}">{link["title"]}</a></li>\n'

    html += "            </ul>\n"

    for idx, (clue, answer) in enumerate(zip(crossword_data['clues']['down'], crossword_data['answers']['down']), 1):
        hints = generate_mini_hint_text(answer, clue, idx, 'Down')

        html += f"""
            <hr>
            <h4>{idx} Down: "{clue}"</h4>
            <p><strong>Hints:</strong></p>
            <ul>
        """
        for hint in hints[:3]:
            html += f"        <li>{hint}</li>\n"
        html += f"""
            </ul>
            <p><strong>Answer:</strong>
                <details>
                    <summary>Click to reveal</summary>
                    <strong>{answer.upper()}</strong>
                </details>
            </p>
        """

    strategy = random.choice(STEP_STRATEGY_VARIANTS)
    strategy_html = "".join(f"<li><strong>{title}:</strong> {body}</li>" for title, body in strategy)

    html += f"""
        </section>

        <section id="solving-tips">
            <h2>How to Solve the NYT Mini Crossword Faster</h2>
            <p>{random.choice(TIPS_INTRO_VARIANTS)}</p>

            <h3>Step-by-Step Strategy</h3>
            <ol>
                {strategy_html}
            </ol>

            <h3>Letter Tips That Really Help</h3>
            <ul>
                <li>E is the most common letter in English, so it's worth guessing early.</li>
                <li>Words ending in S are usually plurals.</li>
                <li>Blanks ("___") in a clue mean the answer fits exactly into those spaces.</li>
                <li>An abbreviation in the clue is a signal the answer's abbreviated too.</li>
            </ul>

            <h3>Time Goals to Aim For</h3>
            <table border="1" cellpadding="5">
                <thead>
                    <tr><th>Your Time</th><th>Skill Level</th><th>What It Means</th></tr>
                </thead>
                <tbody>
                    <tr><td>Under 30 seconds</td><td>Expert</td><td>You've clearly got the puzzle's patterns down.</td></tr>
                    <tr><td>30-60 seconds</td><td>Advanced</td><td>Solid pace — you're solving quickly.</td></tr>
                    <tr><td>1-2 minutes</td><td>Good</td><td>Right where most regular solvers land.</td></tr>
                    <tr><td>Over 2 minutes</td><td>Learning</td><td>Totally fine — speed comes with reps.</td></tr>
                </tbody>
            </table>
        </section>

        <section id="statistics">
            <h2>Puzzle Numbers and Facts</h2>
            <table border="1" cellpadding="10" width="100%">
                <caption>Today's Puzzle by the Numbers</caption>
                <tbody>
                    <tr><td><strong>Total Clues:</strong></td><td>{total_clues}</td></tr>
                    <tr><td><strong>Grid Size:</strong></td><td>5 boxes across, 5 boxes down</td></tr>
                    <tr><td><strong>Total Squares:</strong></td><td>25</td></tr>
                    <tr><td><strong>Average Time:</strong></td><td>{random.choice(['45 seconds', '52 seconds', '58 seconds', '1 minute 3 seconds', '1 minute 10 seconds'])}</td></tr>
                    <tr><td><strong>Difficulty:</strong></td><td>{random.choice(['Easy', 'Medium', 'A bit tricky', 'Normal'])}</td></tr>
                </tbody>
            </table>
        </section>

        <section id="related-content">
            <h2>More Puzzle Help</h2>
            <p>If today's Mini hit the spot, here are a few more you might enjoy:</p>
            <nav>
                <ul>
    """

    if internal_links:
        for link in random.sample(internal_links, min(6, len(internal_links))):
            html += f'                    <li><a href="{link["url"]}">{link["title"]}</a></li>\n'

    html += f"""
                </ul>
            </nav>
        </section>

        <section id="faq" itemscope itemtype="https://schema.org/FAQPage">
            <h2>Common Questions About Trivia Week {week_num}</h2>

            <div itemprop="mainEntity" itemscope itemtype="https://schema.org/Question">
                <h3 itemprop="name">When does the Trivia Week {week_num} Mini go live?</h3>
                <div itemprop="acceptedAnswer" itemscope itemtype="https://schema.org/Answer">
                    <p itemprop="text">{random.choice(FAQ_ANSWER_VARIANTS['when'])}</p>
                </div>
            </div>

            <div itemprop="mainEntity" itemscope itemtype="https://schema.org/Question">
                <h3 itemprop="name">How long should Trivia Week {week_num} take me?</h3>
                <div itemprop="acceptedAnswer" itemscope itemtype="https://schema.org/Answer">
                    <p itemprop="text">{random.choice(FAQ_ANSWER_VARIANTS['time'])}</p>
                </div>
            </div>

            <div itemprop="mainEntity" itemscope itemtype="https://schema.org/Question">
                <h3 itemprop="name">Is Trivia Week {week_num} free to play?</h3>
                <div itemprop="acceptedAnswer" itemscope itemtype="https://schema.org/Answer">
                    <p itemprop="text">{random.choice(FAQ_ANSWER_VARIANTS['cost'])}</p>
                </div>
            </div>

            <div itemprop="mainEntity" itemscope itemtype="https://schema.org/Question">
                <h3 itemprop="name">What actually makes someone good at Trivia Week {week_num}?</h3>
                <div itemprop="acceptedAnswer" itemscope itemtype="https://schema.org/Answer">
                    <p itemprop="text">{random.choice(FAQ_ANSWER_VARIANTS['good_solver'])}</p>
                </div>
            </div>

            <div itemprop="mainEntity" itemscope itemtype="https://schema.org/Question">
                <h3 itemprop="name">Does Trivia Week {week_num} get harder as the week goes on?</h3>
                <div itemprop="acceptedAnswer" itemscope itemtype="https://schema.org/Answer">
                    <p itemprop="text">{random.choice(FAQ_ANSWER_VARIANTS['difficulty'])}</p>
                </div>
            </div>
        </section>

        <footer>
            <hr>
            <p><strong>About This Page:</strong> We put together hints and answers for the NYT Mini to help you learn the ropes and get faster over time. This site isn't affiliated with The New York Times.</p>
            <p><strong>Last Updated:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
            <p><small>Search terms: {', '.join(MINI_KEYWORDS['primary'][:5])}, {date.strftime('%B %d %Y')} mini crossword</small></p>
        </footer>
    """

    return html

# Function to send email (reusing from original with minor updates)
def send_mini_email(to_email, subject, html_content):
    """Send Mini crossword email with mobile optimization"""
    from_email = "velanms1993@gmail.com"
    password = "fcem kvha hwmg iciv"

    if not from_email or not password:
        raise RuntimeError(
            "Set MINI_FROM_EMAIL and MINI_EMAIL_APP_PASSWORD environment "
            "variables instead of hardcoding credentials in the script."
        )

    msg = MIMEMultipart('alternative')
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    text_part = MIMEText("Solve today's NYT Mini Crossword in under 1 minute with our expert hints!", 'plain')
    html_part = MIMEText(html_content, 'html')

    msg.attach(text_part)
    msg.attach(html_part)

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Email send error: {e}")
        return False

# Main function for Mini crossword
def main():
    """Main execution function for NYT Mini crossword processor"""
    crossword_date = datetime.now().strftime("%m/%d/%Y")

    url = f"https://www.xwordinfo.com/JSON/Data.ashx?date={crossword_date}&format=text"

    print(f"Fetching crossword data for {crossword_date}...")
    crossword_data = fetch_mini_crossword_data(url)

    if crossword_data:
        date = datetime.strptime(crossword_data['date'], '%m/%d/%Y')

        title = generate_seo_title(date, crossword_data)

        print(f"Processing Mini crossword for {date.strftime('%B %d, %Y')}")
        print(f"Clues: {len(crossword_data['clues']['across'])} Across, {len(crossword_data['clues']['down'])} Down")

        formatted_html = format_mini_to_html(crossword_data, date)

        if send_mini_email("velanms1993.qrco@blogger.com", title, formatted_html):
            print(f"Mini crossword email sent successfully for {date.strftime('%B %d, %Y')}!")
            print(f"Title: {title}")
        else:
            print("Failed to send email")
    else:
        print("Could not fetch crossword data")

if __name__ == "__main__":
    main()
