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
                print(f"📖 Reading progress file: '{content}'")
                if content:
                    try:
                        parsed_date = datetime.strptime(content, '%Y-%m-%d')
                        print(f"✅ Found last processed date: {parsed_date.strftime('%Y-%m-%d')}")
                        return parsed_date
                    except ValueError as ve:
                        print(f"❌ Invalid date format in progress file: {ve}")
                        return START_DATE
                else:
                    print("⚠️ Progress file is empty")
                    return START_DATE
        else:
            print(f"📝 Progress file '{PROGRESS_FILE}' doesn't exist, starting from beginning")
            return START_DATE
    except Exception as e:
        print(f"❌ Error reading progress file: {e}")
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
                    print(f"✅ Progress saved successfully: {date.strftime('%Y-%m-%d')}")
                    return True
                else:
                    print(f"❌ Progress verification failed. Expected: {date.strftime('%Y-%m-%d')}, Got: {saved_content}")
                    return False
        else:
            print(f"❌ Progress file was not created")
            return False
            
    except Exception as e:
        print(f"❌ Error saving progress: {e}")
        return False

def get_next_date():
    """Get the next date to process (going backwards in time)"""
    last_processed = get_current_progress()
    next_date = last_processed
    
    # Skip Sundays (NYT doesn't publish crosswords on Sundays)
    while next_date.weekday() == 6:  # 6 = Sunday
        next_date -= timedelta(days=1)  # Going backwards
    
    return next_date

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
        
    clues_across = crossword_data.get('clues', {}).get('across', [])
    clues_down = crossword_data.get('clues', {}).get('down', [])
    answers_across = crossword_data.get('answers', {}).get('across', [])
    answers_down = crossword_data.get('answers', {}).get('down', [])
    
    if not clues_across or not answers_across:
        print("No valid crossword data found")
        return None

    # List of available images for random selection
    image_names = [
        'crossword-solution-keyword-optimized.png',
        'crossword-solution-search-engine-friendly.png',
        'crossword-solution-content-marketing.png',
        'crossword-solution-digital-strategy.png',
        'crossword-solution-on-page-seo.png',
        'crossword-solution-link-building.png',
        'crossword-solution-organic-traffic.png',
        'crossword-solution-backlink-analysis.png',
        'crossword-solution-seo-audit.png',
        'crossword-solution-page-speed-optimization.png',
        'crossword-solution-meta-description.png',
        'crossword-solution-keyword-density.png',
        'crossword-solution-mobile-friendliness.png',
        'crossword-solution-rich-snippets.png',
        'crossword-solution-technical-seo.png',
        'crossword-solution-site-architecture.png',
        'crossword-solution-search-console.png',
        'crossword-solution-local-seo.png',
        'crossword-solution-seo-tools.png',
        'crossword-solution-content-update.png',
        'crossword-solution-rank-tracking.png',
        'crossword-solution-schema-markup.png',
        'crossword-solution-user-experience.png',
        'crossword-solution-search-ranking.png',
        'crossword-solution-seo-report.png',
        'crossword-solution-google-analytics.png'
    ]
    
    # Select a random image
    selected_image = random.choice(image_names)
    image_url = f"https://raw.githubusercontent.com/xwordhint/answer/main/{selected_image}"
    
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
                <th>Difficulty</th>
                <th>Category</th>
            </tr>"""

    # Process Across clues for table
    for idx, (clue, answer) in enumerate(zip(clues_across, answers_across), 1):
        if not clue or not answer:
            continue
        letter_count = len(str(answer).replace(" ", ""))
        difficulty = get_difficulty_level(str(answer), str(clue))
        category = get_word_category(str(answer), str(clue))
        html += f"""
            <tr>
                <td>{idx}A</td>
                <td>{clue}</td>
                <td>{letter_count}</td>
                <td>{difficulty}</td>
                <td>{category}</td>
            </tr>"""

    html += """
        </table>

        <h3>Across Clues - Detailed Hints and Explanations</h3>"""

    # Process Across clues for explanations
    for idx, (clue, answer) in enumerate(zip(clues_across, answers_across), 1):
        if not clue or not answer:
            continue
            
        hints = generate_hint_text(str(answer), str(clue))
        letter_count = len(str(answer).replace(" ", ""))
        
        html += f"""
        <h4>{idx}A: "{clue}" ({letter_count} letters)</h4>
        <ul>"""
        
        for hint in hints[:3]:
            html += f"<li>{hint}</li>"
        
        html += f"""
            <li>
                <details>
                    <summary><strong>Click to reveal answer</strong></summary>
                    <strong>Answer:</strong> {answer}
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
                <th>Difficulty</th>
                <th>Category</th>
            </tr>"""

        # Process Down clues for table
        for idx, (clue, answer) in enumerate(zip(clues_down, answers_down), 1):
            if not clue or not answer:
                continue
            letter_count = len(str(answer).replace(" ", ""))
            difficulty = get_difficulty_level(str(answer), str(clue))
            category = get_word_category(str(answer), str(clue))
            html += f"""
            <tr>
                <td>{idx}D</td>
                <td>{clue}</td>
                <td>{letter_count}</td>
                <td>{difficulty}</td>
                <td>{category}</td>
            </tr>"""

        html += """
        </table>

        <h3>Down Clues - Comprehensive Solutions and Tips</h3>"""

        # Process Down clues for explanations
        for idx, (clue, answer) in enumerate(zip(clues_down, answers_down), 1):
            if not clue or not answer:
                continue
                
            hints = generate_hint_text(str(answer), str(clue))
            letter_count = len(str(answer).replace(" ", ""))
            
            html += f"""
        <h4>{idx}D: "{clue}" ({letter_count} letters)</h4>
        <ul>"""
            
            for hint in hints[:3]:
                html += f"<li>{hint}</li>"
            
            html += f"""
            <li>
                <details>
                    <summary><strong>Click to reveal answer</strong></summary>
                    <strong>Answer:</strong> {answer}
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
        
        <h2 id="solving-tips">Pro Solving Tips for {day_name} Puzzles</h2>
        <ul>
            <li>Start with the shortest clues - they often have fewer possible answers</li>
            <li>Look for fill-in-the-blank clues, which are typically easier</li>
            <li>Check crossing letters to confirm your answers</li>
            <li>{day_name} puzzles typically have a difficulty level of {overall_difficulty.split()[0]}</li>
            <li>Pay attention to clue categories - {max(categories_count, key=categories_count.get)} appears most frequently today</li>
            <li>Use the word length as a guide - today's average is {avg_answer_length:.1f} letters</li>
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
        print("❌ No HTML content to send")
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
        
        print(f"✅ Email sent successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Email sending failed: {e}")
        return False

# Main function - processes one date per run
def main():
    print("🚀 Starting single date crossword processing...")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"📋 Progress file path: {os.path.abspath(PROGRESS_FILE)}")
    
    # Get next date to process
    target_date = get_next_date()
    
    print(f"📅 Processing date: {target_date.strftime('%A, %B %d, %Y')}")
    
    # Check if we've reached the end date (going backwards)
    if target_date < END_DATE:
        print(f"🏁 Reached end date {END_DATE.strftime('%B %d, %Y')}. Processing complete!")
        return
    
    # Format date for API
    crossword_date = target_date.strftime("%m/%d/%Y")
    url = f"https://www.xwordinfo.com/JSON/Data.ashx?date={crossword_date}&format=text"
    
    print(f"🌐 Fetching: {url}")
    
    # Fetch crossword data
    crossword_data = fetch_crossword_data(url)
    
    # Always try to advance to next date (going backwards), regardless of success/failure
    next_date = target_date - timedelta(days=1)
    
    if crossword_data:
        try:
            # Validate data structure
            if 'clues' in crossword_data and 'answers' in crossword_data:
                print("✅ Valid crossword data found")
                
                # Format HTML
                html_content = format_to_html(crossword_data, target_date)
                
                if html_content:
                    # Prepare email
                    title = f" {target_date.strftime('%B %d, %Y')} NYT Clues Solutions | XWordHint"
                    
                    # Send email
                    success = send_email("velanms1993.qrco@blogger.com", title, html_content)
                    
                    if success:
                        print(f"📈 Success: Completed {target_date.strftime('%Y-%m-%d')}")
                    else:
                        print(f"❌ Email failed for {target_date.strftime('%Y-%m-%d')}")
                else:
                    print(f"❌ Failed to format HTML for {target_date.strftime('%Y-%m-%d')}")
            else:
                print(f"⚠️ Invalid crossword data structure for {target_date.strftime('%Y-%m-%d')}")
        except Exception as e:
            print(f"❌ Error processing crossword data for {target_date.strftime('%Y-%m-%d')}: {e}")
    else:
        print(f"⚠️ No crossword data available for {target_date.strftime('%Y-%m-%d')}")
    
    # ALWAYS save progress to move to next date
    print(f"💾 Saving progress to move to next date: {next_date.strftime('%Y-%m-%d')}")
    save_success = save_progress(next_date)
    
    if save_success:
        print(f"📅 Next run will process: {next_date.strftime('%A, %B %d, %Y')}")
    else:
        print(f"❌ Failed to save progress! Next run may repeat {target_date.strftime('%Y-%m-%d')}")
    
    # Show file status for debugging
    try:
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                current_content = f.read().strip()
                print(f"📄 Current progress file content: '{current_content}'")
        else:
            print(f"📄 Progress file does not exist after save attempt")
    except Exception as e:
        print(f"❌ Error checking progress file: {e}")

if __name__ == "__main__":
    main()
