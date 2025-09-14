import os
import requests
import smtplib
import json
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from nltk.corpus import wordnet
import nltk
from datetime import datetime, timedelta
import random
import xml.etree.ElementTree as ET
import re

# Download wordnet
nltk.download('wordnet')

# Configuration for GitHub Actions - Reverse chronological order
START_DATE = datetime(2024, 7, 20)  # Starting from recent date
END_DATE = datetime(1990, 2, 1)  # Going back to Feb 1, 1990
PROGRESS_FILE = "crossword_progress.txt"

def get_current_progress():
    """Get the last processed date from progress file"""
    try:
        # Check if file exists and has content
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                print(f"[READ] Reading progress file: '{content}'")
                if content:
                    try:
                        parsed_date = datetime.strptime(content, '%Y-%m-%d')
                        print(f"[OK] Found last processed date: {parsed_date.strftime('%Y-%m-%d')}")
                        return parsed_date
                    except ValueError as ve:
                        print(f"[ERROR] Invalid date format in progress file: {ve}")
                        return START_DATE
                else:
                    print("[WARNING] Progress file is empty")
                    return START_DATE
        else:
            print(f"[INFO] Progress file '{PROGRESS_FILE}' doesn't exist, starting from beginning")
            return START_DATE
    except Exception as e:
        print(f"[ERROR] Error reading progress file: {e}")
        return START_DATE

def save_progress(date):
    """Save the current processed date to progress file"""
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(PROGRESS_FILE) if os.path.dirname(PROGRESS_FILE) else '.', exist_ok=True)
        
        # Write the date
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            f.write(date.strftime('%Y-%m-%d'))
        
        # Verify the write was successful
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                saved_content = f.read().strip()
                if saved_content == date.strftime('%Y-%m-%d'):
                    print(f"[OK] Progress saved successfully: {date.strftime('%Y-%m-%d')}")
                    return True
                else:
                    print(f"[ERROR] Progress verification failed. Expected: {date.strftime('%Y-%m-%d')}, Got: {saved_content}")
                    return False
        else:
            print(f"[ERROR] Progress file was not created")
            return False
            
    except Exception as e:
        print(f"[ERROR] Error saving progress: {e}")
        return False

def get_next_date():
    """Get the next date to process (going backwards in time)"""
    last_processed = get_current_progress()
    next_date = last_processed

    # Skip Sundays (NYT doesn't publish crosswords on Sundays)
    while next_date.weekday() == 6:  # 6 = Sunday
        next_date -= timedelta(days=1)  # Going backwards

    return next_date

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

# Function to get synonyms
def get_synonyms(word):
    synonyms = set()
    try:
        for syn in wordnet.synsets(word):
            for lemma in syn.lemmas():
                synonym = lemma.name().replace('_', ' ')
                if synonym.lower() != word.lower():
                    synonyms.add(synonym)
    except:
        pass
    return list(synonyms)

# Function to get antonyms
def get_antonyms(word):
    antonyms = set()
    try:
        for syn in wordnet.synsets(word):
            for lemma in syn.lemmas():
                if lemma.antonyms():
                    antonym = lemma.antonyms()[0].name().replace('_', ' ')
                    if antonym.lower() != word.lower():
                        antonyms.add(antonym)
    except:
        pass
    return list(antonyms)

# Function to get word definitions
def get_word_definition(word):
    definitions = []
    try:
        for syn in wordnet.synsets(word):
            definition = syn.definition()
            if definition and len(definition) > 10:
                definitions.append(definition)
    except:
        pass
    return definitions[:2] if definitions else []

# Function to generate hint text without revealing answer
def generate_hint_text(answer, clue):
    if not answer:
        return ["No hints available"]
        
    synonyms = get_synonyms(answer)
    antonyms = get_antonyms(answer)
    definitions = get_word_definition(answer)
    
    hints = []
    
    # Add definition-based hints
    if definitions:
        hints.append(f"Think of something that {definitions[0].lower()}")
    
    # Add synonym hints
    if synonyms:
        selected_synonyms = synonyms[:3]
        hints.append(f"Similar words include: {', '.join(selected_synonyms)}")
    
    # Add antonym hints
    if antonyms:
        selected_antonyms = antonyms[:2]
        hints.append(f"Opposite of: {', '.join(selected_antonyms)}")
    
    # Add letter pattern hint
    letter_pattern = ''.join(['_' if c.isalpha() else c for c in answer])
    hints.append(f"Pattern: {letter_pattern}")
    
    return hints if hints else ["Use the clue to find the answer"]

# Function to fetch crossword data from URL
def fetch_crossword_data(url):
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
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            if 'application/json' in response.headers.get('Content-Type', '') or 'text/plain' in response.headers.get('Content-Type', ''):
                try:
                    data = json.loads(response.text)
                    return data
                except json.JSONDecodeError:
                    print("Error: Could not decode JSON response.")
            else:
                print(f"Error: Unexpected content type {response.headers.get('Content-Type')}")
        else:
            print(f"Error: Failed to fetch data. Status code: {response.status_code}")
    except Exception as e:
        print(f"Exception occurred: {e}")
    return None

def get_word_category(answer, clue):
    """Determine the category of a crossword answer"""
    answer_lower = answer.lower()
    clue_lower = clue.lower()
    
    # Category detection based on clue and answer patterns
    if any(word in clue_lower for word in ['actor', 'actress', 'singer', 'author', 'director', 'star', 'celebrity']):
        return "Celebrity/Entertainment"
    elif any(word in clue_lower for word in ['city', 'country', 'state', 'capital', 'river', 'mountain', 'ocean']):
        return "Geography"
    elif any(word in clue_lower for word in ['history', 'war', 'century', 'ancient', 'historical', 'era']):
        return "History"
    elif any(word in clue_lower for word in ['science', 'element', 'chemical', 'physics', 'biology', 'math']):
        return "Science/Technology"
    elif any(word in clue_lower for word in ['sport', 'game', 'player', 'team', 'championship', 'olympic']):
        return "Sports"
    elif any(word in clue_lower for word in ['food', 'drink', 'cuisine', 'dish', 'meal', 'recipe']):
        return "Food & Drink"
    elif any(word in clue_lower for word in ['book', 'novel', 'poem', 'literature', 'writer', 'literary']):
        return "Literature"
    elif any(word in clue_lower for word in ['music', 'song', 'composer', 'opera', 'symphony', 'album']):
        return "Music"
    elif any(word in clue_lower for word in ['movie', 'film', 'cinema', 'oscar', 'hollywood']):
        return "Movies/Film"
    elif any(word in clue_lower for word in ['abbr.', 'briefly', 'for short', 'initially']):
        return "Abbreviation"
    elif len(answer) <= 3:
        return "Short Answer"
    elif '"' in clue or "'" in clue:
        return "Quote/Saying"
    else:
        return "General Knowledge"

def get_difficulty_level(answer, clue):
    """Determine difficulty level based on answer length and clue complexity"""
    answer_length = len(answer)
    clue_words = len(clue.split())
    
    # Calculate difficulty score
    score = 0
    
    # Length factor
    if answer_length <= 3:
        score += 1
    elif answer_length <= 5:
        score += 2
    elif answer_length <= 7:
        score += 3
    elif answer_length <= 10:
        score += 4
    else:
        score += 5
    
    # Clue complexity
    if clue_words <= 2:
        score += 1
    elif clue_words <= 4:
        score += 2
    elif clue_words <= 6:
        score += 3
    else:
        score += 4
    
    # Check for wordplay indicators
    if any(word in clue.lower() for word in ['?', 'perhaps', 'maybe', 'sometimes', 'often']):
        score += 2
    
    # Determine level
    if score <= 3:
        return "Easy"
    elif score <= 5:
        return "Medium"
    elif score <= 7:
        return "Hard"
    else:
        return "Expert"

def format_to_html(crossword_data, date):
    # Safety checks
    if not crossword_data or 'clues' not in crossword_data or 'answers' not in crossword_data:
        return None

    # Fetch internal links from sitemap for better SEO
    internal_links = fetch_sitemap_urls(max_links=15)

    clues_across = crossword_data.get('clues', {}).get('across', [])
    clues_down = crossword_data.get('clues', {}).get('down', [])
    answers_across = crossword_data.get('answers', {}).get('across', [])
    answers_down = crossword_data.get('answers', {}).get('down', [])
    
    if not clues_across or not answers_across:
        print("No valid crossword data found")
        return None

    # Generate list of available images dynamically (1-100)
    image_names = [
        "crossword_puzzle_{}.png".format(i) for i in range(1, 201)
    ]
    # Select a random image
    selected_image = random.choice(image_names)
    image_url = f"https://raw.githubusercontent.com/xwordhint/answer/main/image/{selected_image}"
    
    # Calculate puzzle difficulty
    total_clues = len(clues_across) + len(clues_down)
    avg_answer_length = sum(len(str(a).replace(" ", "")) for a in answers_across + answers_down) / total_clues if total_clues > 0 else 0
    
    if avg_answer_length <= 4:
        overall_difficulty = "Easy Monday Puzzle"
    elif avg_answer_length <= 5:
        overall_difficulty = "Medium Tuesday Puzzle"
    elif avg_answer_length <= 6:
        overall_difficulty = "Moderate Wednesday Puzzle"
    elif avg_answer_length <= 7:
        overall_difficulty = "Challenging Thursday Puzzle"
    elif avg_answer_length <= 8:
        overall_difficulty = "Hard Friday Puzzle"
    else:
        overall_difficulty = "Expert Saturday Puzzle"
    
    # Day of week for SEO
    day_name = date.strftime('%A')
    
    # SEO header variations for Across
    across_headers = [
        f"NYT {day_name} Crossword Across Clues - {date.strftime('%B %d, %Y')} Solutions",
        f"{date.strftime('%B %d, %Y')} Across Hints: NYT {day_name} Crossword Answers",
        f"Across Clues Explained - {day_name} NYT Crossword {date.strftime('%B %d, %Y')}",
        f"Master Today's Across: NYT {day_name} Puzzle {date.strftime('%B %d, %Y')}",
        f"{date.strftime('%B %d, %Y')} {day_name} NYT - Complete Across Solutions"
    ]
    
    # SEO header variations for Down
    down_headers = [
        f"NYT {day_name} Crossword Down Clues - {date.strftime('%B %d, %Y')} Answers",
        f"{date.strftime('%B %d, %Y')} Down Hints: NYT {day_name} Crossword Guide",
        f"Down Clues Decoded - {day_name} NYT Crossword {date.strftime('%B %d, %Y')}",
        f"Solve the Down: NYT {day_name} Puzzle {date.strftime('%B %d, %Y')}",
        f"{date.strftime('%B %d, %Y')} {day_name} NYT - All Down Answers"
    ]

    html = f"""

        <h2>Quick Navigation - Table of Contents</h2>
        <ul>
            <li><a href="#puzzle-overview">Puzzle Overview & Difficulty</a></li>
            <li><a href="#across-clues">Across Clues ({len(clues_across)} clues)</a></li>
            <li><a href="#down-clues">Down Clues ({len(clues_down)} clues)</a></li>
            <li><a href="#category-breakdown">Category Breakdown</a></li>
            <li><a href="#puzzle-stats">Complete Puzzle Statistics</a></li>
            <li><a href="#solving-tips">Pro Solving Tips</a></li>
            <li><a href="#related-puzzles">Related Crossword Solutions</a></li>
        </ul>

        <h2>Related Puzzles</h2>
        <p>Check out these other crossword solutions and helpful guides:</p>
        <ul>
    """

    # Add 5 random internal links at the top
    if internal_links:
        for link in random.sample(internal_links, min(5, len(internal_links))):
            html += f'            <li><a href="{link["url"]}">{link["title"]}</a></li>\n'

    html += f"""
        </ul>

        
        <h2 id="puzzle-overview">Puzzle Overview & Difficulty Analysis</h2>
        <p><strong>Date:</strong> {date.strftime('%A, %B %d, %Y')}</p>
        <p><strong>Difficulty Level:</strong> {overall_difficulty}</p>
        <p><strong>Total Clues:</strong> {total_clues} ({len(clues_across)} Across, {len(clues_down)} Down)</p>
        <p><strong>Average Word Length:</strong> {avg_answer_length:.1f} letters</p>
        
        <div class="separator" style="clear: both; text-align: center;">
            <a href="{image_url}" style="margin-left: 1em; margin-right: 1em;">
                <img alt="{date.strftime('%B %d, %Y')} NYT Clues Solutions" border="0" data-original-height="514" data-original-width="509" height="320" src="{image_url}" title="{date.strftime('%B %d, %Y')} NYT Clues Solutions" width="317" />
            </a>
        </div>

        <h2 id="across-clues">{random.choice(across_headers)}</h2>
        
        <table border="1">
            <tr>
                <th>No.</th>
                <th>Clue</th>
                <th>Letters</th>
            </tr>"""

    # Process Across clues for table
    for idx, (clue, answer) in enumerate(zip(clues_across, answers_across), 1):
        if not clue or not answer:
            continue
        letter_count = len(str(answer).replace(" ", ""))
        html += f"""
            <tr>
                <td>{idx}A</td>
                <td>{clue}</td>
                <td>{letter_count}</td>
            </tr>"""

    html += """
        </table>

        <h3>Let's Solve the Across Clues Together!</h3>
        <p>Here are helpful hints to solve each clue. Remember, crossword puzzles are like word games - have fun with them!</p>"""

    # Process Across clues for explanations
    for idx, (clue, answer) in enumerate(zip(clues_across, answers_across), 1):
        if not clue or not answer:
            continue
            
        hints = generate_hint_text(str(answer), str(clue))
        letter_count = len(str(answer).replace(" ", ""))
        difficulty = get_difficulty_level(str(answer), str(clue))
        category = get_word_category(str(answer), str(clue))
        
        html += f"""
        <h4>Clue {idx} Across: "{clue}"</h4>
        <p><strong>Quick Info:</strong> This answer has {letter_count} letters. It's a {difficulty.lower()} clue about {category.lower()}.</p>
        <p><strong>Here's how to solve it:</strong></p>
        <ul>"""
        
        # Make hints more friendly and readable
        for hint in hints[:3]:
            # Simplify the hint language
            friendly_hint = hint.replace("Think of something that", "This could be something that")
            friendly_hint = friendly_hint.replace("Similar words include:", "Words that mean the same thing:")
            friendly_hint = friendly_hint.replace("Opposite of:", "The opposite would be:")
            friendly_hint = friendly_hint.replace("Pattern:", "The word looks like this:")
            html += f"<li>{friendly_hint}</li>"
        
        html += f"""
            <li>Still stuck? Remember to use the crossing words to help you!</li>
            <li>
                <details>
                    <summary><strong>Ready for the answer? Click here!</strong></summary>
                    <p><strong>The answer is:</strong> {answer}</p>
                    <p>Great job if you got it right!</p>
                </details>
            </li>
        </ul>"""

    # Process Down clues
    if clues_down and answers_down:
        html += f"""
        <h2 id="down-clues">{random.choice(down_headers)}</h2>
        
        <table border="1">
            <tr>
                <th>No.</th>
                <th>Clue</th>
                <th>Letters</th>
            </tr>"""

        # Process Down clues for table
        for idx, (clue, answer) in enumerate(zip(clues_down, answers_down), 1):
            if not clue or not answer:
                continue
            letter_count = len(str(answer).replace(" ", ""))
            html += f"""
            <tr>
                <td>{idx}D</td>
                <td>{clue}</td>
                <td>{letter_count}</td>
            </tr>"""

        html += """
        </table>

        <h3>Now Let's Solve the Down Clues!</h3>
        <p>Down clues go from top to bottom. Use the letters from your across answers to help!</p>"""

        # Process Down clues for explanations
        for idx, (clue, answer) in enumerate(zip(clues_down, answers_down), 1):
            if not clue or not answer:
                continue
                
            hints = generate_hint_text(str(answer), str(clue))
            letter_count = len(str(answer).replace(" ", ""))
            difficulty = get_difficulty_level(str(answer), str(clue))
            category = get_word_category(str(answer), str(clue))
            
            html += f"""
        <h4>Clue {idx} Down: "{clue}"</h4>
        <p><strong>Quick Info:</strong> This answer has {letter_count} letters. It's a {difficulty.lower()} clue about {category.lower()}.</p>
        <p><strong>Here's how to solve it:</strong></p>
        <ul>"""
            
            # Make hints more friendly and readable
            for hint in hints[:3]:
                # Simplify the hint language
                friendly_hint = hint.replace("Think of something that", "This could be something that")
                friendly_hint = friendly_hint.replace("Similar words include:", "Words that mean the same thing:")
                friendly_hint = friendly_hint.replace("Opposite of:", "The opposite would be:")
                friendly_hint = friendly_hint.replace("Pattern:", "The word looks like this:")
                html += f"<li>{friendly_hint}</li>"
            
            html += f"""
            <li>Still stuck? Remember to use the crossing words to help you!</li>
            <li>
                <details>
                    <summary><strong>Ready for the answer? Click here!</strong></summary>
                    <p><strong>The answer is:</strong> {answer}</p>
                    <p>Great job if you got it right!</p>
                </details>
            </li>
        </ul>"""

    # Calculate category statistics
    categories_count = {}
    for clue, answer in zip(clues_across + clues_down, answers_across + answers_down):
        if clue and answer:
            cat = get_word_category(str(answer), str(clue))
            categories_count[cat] = categories_count.get(cat, 0) + 1
    
    # Add category breakdown
    html += f"""
        <h2 id="category-breakdown">Category Breakdown</h2>
        <table border="1">
            <tr>
                <th>Category</th>
                <th>Number of Clues</th>
                <th>Percentage</th>
            </tr>"""
    
    for category, count in sorted(categories_count.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_clues * 100) if total_clues > 0 else 0
        html += f"""
            <tr>
                <td>{category}</td>
                <td>{count}</td>
                <td>{percentage:.1f}%</td>
            </tr>"""
    
    html += f"""
        </table>
        
        <h2 id="puzzle-stats">Complete Puzzle Statistics</h2>
        <table border="1">
            <tr>
                <th>Metric</th>
                <th>Value</th>
            </tr>
            <tr>
                <td>Across Clues</td>
                <td>{len(clues_across)}</td>
            </tr>
            <tr>
                <td>Down Clues</td>
                <td>{len(clues_down)}</td>
            </tr>
            <tr>
                <td>Total Clues</td>
                <td>{len(clues_across) + len(clues_down)}</td>
            </tr>
            <tr>
                <td>Average Answer Length</td>
                <td>{avg_answer_length:.1f} letters</td>
            </tr>
            <tr>
                <td>Shortest Answer</td>
                <td>{min(len(str(a).replace(' ', '')) for a in answers_across + answers_down)} letters</td>
            </tr>
            <tr>
                <td>Longest Answer</td>
                <td>{max(len(str(a).replace(' ', '')) for a in answers_across + answers_down)} letters</td>
            </tr>
        </table>
        
        <h2 id="solving-tips">Fun Tips to Solve Crossword Puzzles!</h2>
        <ul>
            <li>Start with short words first - they're usually easier!</li>
            <li>Look for clues with blanks to fill in - these are like fill-in-the-blank questions at school</li>
            <li>When letters cross, they must be the same in both words - this helps you check if you're right!</li>
            <li>Today is {day_name}, and these puzzles are usually {overall_difficulty.split()[0].lower()} level</li>
            <li>Most clues today are about {max(categories_count, key=categories_count.get).lower()}</li>
            <li>The average word today has about {int(avg_answer_length)} letters</li>
            <li>Remember: It's okay to take breaks and come back later with fresh eyes!</li>
            <li>Ask someone for help if you need it - crosswords are more fun with friends!</li>
        </ul>

        <h2 id="related-puzzles">More Crossword Resources</h2>
        <p>Explore more crossword solutions and helpful guides to improve your solving skills:</p>
        <ul>
    """

    # Add more internal links at the bottom
    if internal_links:
        for link in random.sample(internal_links, min(10, len(internal_links))):
            html += f'            <li><a href="{link["url"]}">{link["title"]}</a></li>\n'

    html += f"""
        </ul>

        <p><strong>Disclaimer:</strong> Crossword clues are property of The New York Times. This educational content is designed to help puzzle enthusiasts improve their solving skills.</p>
        <p><strong>Last Updated:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
    """

    return html

# Function to send email
def send_email(to_email, subject, html_content):
    from_email = os.getenv("EMAIL_USER", "velanms1993@gmail.com")
    password = os.getenv("EMAIL_PASS", "dqpt ywts nrey hlrp")

    if not html_content:
        print("[ERROR] No HTML content to send")
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(html_content, 'html'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, password)
        server.sendmail(from_email, to_email, msg.as_string())
        server.quit()
        
        print(f"[OK] Email sent successfully!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Email sending failed: {e}")
        return False

# Main function - processes one date per run
def main():
    print("[START] Starting single date crossword processing...")
    print(f"[INFO] Working directory: {os.getcwd()}")
    print(f"[INFO] Progress file path: {os.path.abspath(PROGRESS_FILE)}")
    
    # Get next date to process
    target_date = get_next_date()
    
    print(f"[DATE] Processing date: {target_date.strftime('%A, %B %d, %Y')}")
    
    # Check if we've reached the end date (going backwards)
    if target_date < END_DATE:
        print(f"[END] Reached end date {END_DATE.strftime('%B %d, %Y')}. Processing complete!")
        return
    
    # Format date for API
    crossword_date = target_date.strftime("%m/%d/%Y")
    url = f"https://www.xwordinfo.com/JSON/Data.ashx?date={crossword_date}&format=text"
    
    print(f"[URL] Fetching: {url}")
    
    # Fetch crossword data
    crossword_data = fetch_crossword_data(url)
    
    # Always try to advance to next date (going backwards), regardless of success/failure
    next_date = target_date - timedelta(days=1)
    
    if crossword_data:
        try:
            # Validate data structure
            if 'clues' in crossword_data and 'answers' in crossword_data:
                print("[OK] Valid crossword data found")
                
                # Format HTML
                html_content = format_to_html(crossword_data, target_date)
                
                if html_content:
                    # Prepare email
                    title = f" {target_date.strftime('%B %d, %Y')} NYT Clues Solutions | XWordHint"
                    
                    # Send email
                    success = send_email("velanms1993.qrco@blogger.com", title, html_content)
                    
                    if success:
                        print(f"[SUCCESS] Completed {target_date.strftime('%Y-%m-%d')}")
                    else:
                        print(f"[ERROR] Email failed for {target_date.strftime('%Y-%m-%d')}")
                else:
                    print(f"[ERROR] Failed to format HTML for {target_date.strftime('%Y-%m-%d')}")
            else:
                print(f"[WARNING] Invalid crossword data structure for {target_date.strftime('%Y-%m-%d')}")
        except Exception as e:
            print(f"[ERROR] Error processing crossword data for {target_date.strftime('%Y-%m-%d')}: {e}")
    else:
        print(f"[WARNING] No crossword data available for {target_date.strftime('%Y-%m-%d')}")
    
    # ALWAYS save progress to move to next date
    print(f"[SAVE] Saving progress to move to next date: {next_date.strftime('%Y-%m-%d')}")
    save_success = save_progress(next_date)
    
    if save_success:
        print(f"[NEXT] Next run will process: {next_date.strftime('%A, %B %d, %Y')}")
    else:
        print(f"[ERROR] Failed to save progress! Next run may repeat {target_date.strftime('%Y-%m-%d')}")
    
    # Show file status for debugging
    try:
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                current_content = f.read().strip()
                print(f"[FILE] Current progress file content: '{current_content}'")
        else:
            print(f"[FILE] Progress file does not exist after save attempt")
    except Exception as e:
        print(f"[ERROR] Error checking progress file: {e}")

if __name__ == "__main__":
    main()
