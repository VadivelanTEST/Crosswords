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

# Configuration for GitHub Actions
START_DATE = datetime(1990, 1, 1)
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
    """Get the next date to process"""
    last_processed = get_current_progress()
    next_date = last_processed
    
    # Skip Sundays (NYT doesn't publish crosswords on Sundays)
    while next_date.weekday() == 6:  # 6 = Sunday
        next_date += timedelta(days=1)
    
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

    html = f"""    
        <header>
            <p class="post-meta">Published on {date.strftime('%A, %B %d, %Y')} • Daily puzzle hints • <em>Crossword clues © The New York Times</em></p>
        </header>

        <section aria-label="Crossword Solution Overview">
            <p itemprop="description">Master the NYT crossword from {date.strftime('%B %d, %Y')} with our expert hint system. We provide synonyms, antonyms, and strategic clues to help you solve without spoiling the fun.</p>
        </section>  

        <div class="difficulty-indicator">
            <h2>Puzzle Difficulty: {random.choice(['Moderate', 'Challenging', 'Medium', 'Tricky'])}</h2>
            <p><strong>Pro Tip:</strong> Start with the fill-in-the-blank clues - they're usually the easiest entry points!</p>
        </div>

        <section aria-label="Across Clues Hints">
            <h2>Across Clues - Strategic Hints ({len(clues_across)} clues)</h2>
            <div class="clue-group">"""

    # Process Across clues
    for idx, (clue, answer) in enumerate(zip(clues_across, answers_across), 1):
        if not clue or not answer:
            continue
            
        letter_count = len(str(answer).replace(" ", ""))
        hints = generate_hint_text(str(answer), str(clue))
        
        html += f"""
                <div class="clue-item" itemscope itemtype="https://schema.org/Question">
                    <h3 class="clue-title">{idx}A: <span itemprop="text">"{clue}"</span></h3>
                    <div class="clue-meta">
                        <span class="letter-count">{letter_count} letters</span>
                        <span class="theme-hint">Category: {random.choice(['General Knowledge', 'Wordplay', 'Common Word', 'Proper Noun', 'Abbreviation'])}</span>
                    </div>
                    <div class="hint-section">
                        <h4>Solving Hints:</h4>
                        <ul class="hint-list">"""
        
        for hint in hints[:3]:
            html += f"<li>{hint}</li>"
        
        html += f"""</ul>
                        <details class="answer-reveal">
                            <summary>Click to reveal answer</summary>
                            <div class="answer-container">
                                <strong>Answer:</strong> <span class="answer-text">{answer}</span>
                            </div>
                        </details>
                    </div>
                </div>"""

    html += f"""</div></section>"""

    # Process Down clues
    if clues_down and answers_down:
        html += f"""
        <section aria-label="Down Clues Hints">
            <h2>Down Clues - Strategic Hints ({len(clues_down)} clues)</h2>
            <div class="clue-group">"""

        for idx, (clue, answer) in enumerate(zip(clues_down, answers_down), 1):
            if not clue or not answer:
                continue
                
            letter_count = len(str(answer).replace(" ", ""))
            hints = generate_hint_text(str(answer), str(clue))
            
            html += f"""
                    <div class="clue-item" itemscope itemtype="https://schema.org/Question">
                        <h3 class="clue-title">{idx}D: <span itemprop="text">"{clue}"</span></h3>
                        <div class="clue-meta">
                            <span class="letter-count">{letter_count} letters</span>
                            <span class="theme-hint">Category: {random.choice(['General Knowledge', 'Wordplay', 'Common Word', 'Proper Noun', 'Abbreviation'])}</span>
                        </div>
                        <div class="hint-section">
                            <h4>Solving Hints:</h4>
                            <ul class="hint-list">"""
            
            for hint in hints[:3]:
                html += f"<li>{hint}</li>"
            
            html += f"""</ul>
                            <details class="answer-reveal">
                                <summary>Click to reveal answer</summary>
                                <div class="answer-container">
                                    <strong>Answer:</strong> <span class="answer-text">{answer}</span>
                                </div>
                            </details>
                        </div>
                    </div>"""

        html += f"""</div></section>"""

    # Add footer and styles
    html += f"""
        <section aria-label="Daily Crossword Stats">
            <h2>Puzzle Stats</h2>
            <div class="stats-container">
                <div class="stat-item">
                    <span class="stat-number">{len(clues_across)}</span>
                    <span class="stat-label">Across</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">{len(clues_down)}</span>
                    <span class="stat-label">Down</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">{len(clues_across) + len(clues_down)}</span>
                    <span class="stat-label">Total</span>
                </div>
            </div>
        </section>

        <footer>
            <p><strong>Disclaimer:</strong> Crossword clues © The New York Times. Educational content for puzzle enthusiasts.</p>
            <p class="update-info">Processed: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        </footer>

        <style>            
            .clue-item {{ margin-bottom: 20px; border: 1px solid #ddd; padding: 15px; border-radius: 8px; }}
            .hint-list {{ background: #f9f9f9; padding: 15px; border-radius: 5px; }}
            .answer-reveal {{ margin-top: 10px; }}
            .answer-container {{ background: #fffacd; padding: 10px; border-radius: 5px; margin-top: 10px; }}
            .stats-container {{ display: flex; justify-content: space-around; background: #f5f5f5; padding: 20px; border-radius: 8px; }}
            .stat-item {{ text-align: center; }}
            .stat-number {{ display: block; font-size: 2em; font-weight: bold; color: #2c3e50; }}
            .clue-meta {{ margin: 10px 0; }}
            .letter-count {{ background: #e3f2fd; padding: 4px 8px; border-radius: 4px; margin-right: 10px; }}
        </style>
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
    
    # Check if we've reached a reasonable end date (optional)
    end_date = datetime(2024, 12, 31)  # Adjust as needed
    if target_date > end_date:
        print(f"🏁 Reached end date. Processing complete!")
        return
    
    # Format date for API
    crossword_date = target_date.strftime("%m/%d/%Y")
    url = f"https://www.xwordinfo.com/JSON/Data.ashx?date={crossword_date}&format=text"
    
    print(f"🌐 Fetching: {url}")
    
    # Fetch crossword data
    crossword_data = fetch_crossword_data(url)
    
    # Always try to advance to next date, regardless of success/failure
    next_date = target_date + timedelta(days=1)
    
    if crossword_data:
        try:
            # Validate data structure
            if 'clues' in crossword_data and 'answers' in crossword_data:
                print("✅ Valid crossword data found")
                
                # Format HTML
                html_content = format_to_html(crossword_data, target_date)
                
                if html_content:
                    # Prepare email
                    title = f"NYT Crossword - {target_date.strftime('%B %d, %Y')} | XWordHint"
                    
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
