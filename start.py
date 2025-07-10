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

# Download wordnet
nltk.download('wordnet')

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
    
    return hints

# Function to create crossword grid without answers
def create_crossword_grid(crossword_data):
    try:
        # Debug: Print available keys
        print("Available crossword data keys:", list(crossword_data.keys()))
        
        # Try different possible size formats
        rows, cols = 15, 15  # Default size
        
        if 'size' in crossword_data:
            size = crossword_data['size']
            if isinstance(size, dict):
                rows = size.get('rows', 15)
                cols = size.get('cols', 15)
            else:
                rows = cols = 15
        elif 'width' in crossword_data and 'height' in crossword_data:
            rows = crossword_data['height']
            cols = crossword_data['width']
        
        # Create a simple grid representation
        grid_html = f"""
        <div class="crossword-grid-container">
            <h2>🧩 Interactive Crossword Grid</h2>
            <p class="grid-instructions">Work on the puzzle using the clues below. This is a {rows}x{cols} grid.</p>
            <div class="simple-grid">
                <div class="grid-placeholder">
                    <div class="grid-info">
                        <h3>📋 Puzzle Layout</h3>
                        <p><strong>Grid Size:</strong> {rows} × {cols}</p>
                        <p><strong>Total Squares:</strong> {rows * cols}</p>
                        <p><strong>Across Clues:</strong> {len(crossword_data.get('clues', {}).get('across', []))}</p>
                        <p><strong>Down Clues:</strong> {len(crossword_data.get('clues', {}).get('down', []))}</p>
                    </div>
                    <div class="mini-grid">
        """
        
        # Create a simplified visual representation
        for row in range(min(8, rows)):  # Show max 8x8 for visual
            grid_html += '<div class="mini-row">'
            for col in range(min(8, cols)):
                # Create alternating pattern for visual appeal
                if (row + col) % 3 == 0:
                    grid_html += '<div class="mini-cell black"></div>'
                else:
                    grid_html += '<div class="mini-cell white"></div>'
            grid_html += '</div>'
        
        grid_html += """
                    </div>
                </div>
                <div class="grid-instructions-detail">
                    <h4>🎯 How to Use This Puzzle:</h4>
                    <ul>
                        <li>📝 Read the clues below to find the answers</li>
                        <li>🔍 Use our hints system for guidance</li>
                        <li>🧩 Cross-reference Across and Down clues</li>
                        <li>✨ Reveal answers when you're ready!</li>
                    </ul>
                </div>
            </div>
        </div>
        """
        
        return grid_html
        
    except Exception as e:
        print(f"Error creating grid: {e}")
        return f"""
        <div class="crossword-grid-container">
            <h2>🧩 Crossword Puzzle</h2>
            <div class="grid-fallback">
                <p>🎯 <strong>Today's Puzzle Ready!</strong></p>
                <div class="puzzle-stats">
                    <div class="stat-box">
                        <span class="stat-number">{len(crossword_data.get('clues', {}).get('across', []))}</span>
                        <span class="stat-label">Across</span>
                    </div>
                    <div class="stat-box">
                        <span class="stat-number">{len(crossword_data.get('clues', {}).get('down', []))}</span>
                        <span class="stat-label">Down</span>
                    </div>
                </div>
                <p class="puzzle-instruction">📋 Use the clues and hints below to solve the puzzle!</p>
            </div>
        </div>
        """

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
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            print(f"Response Headers: {response.headers}")
            print(f"Response Content (first 200 chars): {response.text[:200]}")
            if 'text/plain' in response.headers.get('Content-Type', ''):
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
    html = f"""    
        <header>
            <h1 itemprop="headline">XWordHint Crossword Answers Hints & Expert Solutions: {date.strftime('%B %d, %Y')}</h1>
            <p class="post-meta">Published on {date.strftime('%A, %B %d, %Y')} • Daily puzzle hints • <em>Crossword clues © The New York Times</em></p>
        </header>

        <section aria-label="Crossword Solution Overview">
            <p itemprop="description">Master today's NYT crossword with our expert hint system. We provide synonyms, antonyms, and strategic clues to help you solve without spoiling the fun. Perfect for crossword enthusiasts who want that satisfying "aha!" moment.</p>
        </section>       

        <div class="difficulty-indicator">
            <h2>Today's Puzzle Difficulty: {random.choice(['Moderate', 'Challenging', 'Medium', 'Tricky'])}</h2>
            <p>💡 <strong>Pro Tip:</strong> Start with the fill-in-the-blank clues - they're usually the easiest entry points!</p>
        </div>

        <section aria-label="Across Clues Hints">
            <h2>🔍 Across Clues - Strategic Hints ({len(crossword_data['clues']['across'])} clues)</h2>
            <div class="clue-group">"""

    for idx, (clue, answer) in enumerate(zip(crossword_data['clues']['across'], crossword_data['answers']['across']), 1):
        letter_count = len(answer.replace(" ", ""))
        hints = generate_hint_text(answer, clue)
        
        html += f"""
                <div class="clue-item" itemscope itemtype="https://schema.org/Question">
                    <h3 class="clue-title">🧩 {idx}A: <span itemprop="text">"{clue}"</span></h3>
                    <div class="clue-meta">
                        <span class="letter-count">📏 {letter_count} letters</span>
                        <span class="theme-hint">💭 Category: {random.choice(['General Knowledge', 'Wordplay', 'Common Word', 'Proper Noun', 'Abbreviation'])}</span>
                    </div>
                    <div class="hint-section">
                        <h4>🎯 Solving Hints:</h4>
                        <ul class="hint-list">"""
        
        for hint in hints[:3]:  # Show max 3 hints
            html += f"<li>{hint}</li>"
        
        html += f"""</ul>
                        <details class="answer-reveal">
                            <summary>🔓 Click to reveal answer (spoiler alert!)</summary>
                            <div class="answer-container">
                                <strong>Answer:</strong> <span class="answer-text">{answer}</span>
                                <p class="answer-explanation">💡 <em>Remember this word for future puzzles!</em></p>
                            </div>
                        </details>
                    </div>
                </div>"""

    html += f"""</div></section>

        <section aria-label="Down Clues Hints">
            <h2>🔍 Down Clues - Strategic Hints ({len(crossword_data['clues']['down'])} clues)</h2>
            <div class="clue-group">"""

    for idx, (clue, answer) in enumerate(zip(crossword_data['clues']['down'], crossword_data['answers']['down']), 1):
        letter_count = len(answer.replace(" ", ""))
        hints = generate_hint_text(answer, clue)
        
        html += f"""
                <div class="clue-item" itemscope itemtype="https://schema.org/Question">
                    <h3 class="clue-title">🧩 {idx}D: <span itemprop="text">"{clue}"</span></h3>
                    <div class="clue-meta">
                        <span class="letter-count">📏 {letter_count} letters</span>
                        <span class="theme-hint">💭 Category: {random.choice(['General Knowledge', 'Wordplay', 'Common Word', 'Proper Noun', 'Abbreviation'])}</span>
                    </div>
                    <div class="hint-section">
                        <h4>🎯 Solving Hints:</h4>
                        <ul class="hint-list">"""
        
        for hint in hints[:3]:  # Show max 3 hints
            html += f"<li>{hint}</li>"
        
        html += f"""</ul>
                        <details class="answer-reveal">
                            <summary>🔓 Click to reveal answer (spoiler alert!)</summary>
                            <div class="answer-container">
                                <strong>Answer:</strong> <span class="answer-text">{answer}</span>
                                <p class="answer-explanation">💡 <em>Remember this word for future puzzles!</em></p>
                            </div>
                        </details>
                    </div>
                </div>"""

    html += f"""</div></section>

        <section aria-label="Crossword Solving Strategies">
            <h2>🧠 Expert Solving Strategies</h2>
            <div class="strategy-grid">
                <div class="strategy-item">
                    <h3>🎯 Start Smart</h3>
                    <p>Begin with fill-in-the-blank clues and short 3-4 letter words. These are your foundation.</p>
                </div>
                <div class="strategy-item">
                    <h3>❓ Decode the Clues</h3>
                    <p>Question marks indicate wordplay or puns. "Maybe" suggests multiple interpretations.</p>
                </div>
                <div class="strategy-item">
                    <h3>🔤 Use Cross-References</h3>
                    <p>Let intersecting letters guide you. One correct answer unlocks several others.</p>
                </div>
                <div class="strategy-item">
                    <h3>📚 Build Vocabulary</h3>
                    <p>Common crossword words repeat. Learning them speeds up future solving.</p>
                </div>
            </div>
        </section>

        <section aria-label="Daily Crossword Stats">
            <h2>📊 Today's Puzzle Stats</h2>
            <div class="stats-container">
                <div class="stat-item">
                    <span class="stat-number">{len(crossword_data['clues']['across'])}</span>
                    <span class="stat-label">Across Clues</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">{len(crossword_data['clues']['down'])}</span>
                    <span class="stat-label">Down Clues</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">{len(crossword_data['clues']['across']) + len(crossword_data['clues']['down'])}</span>
                    <span class="stat-label">Total Clues</span>
                </div>
            </div>
        </section>

        <section aria-label="NYT Crossword Archive">
            <h2>🗂️ More NYT Crossword Help</h2>
            <p>Looking for more puzzle solutions? Check out our comprehensive archive of NYT crossword hints and answers. We update daily with expert analysis and solving strategies.</p>
            <ul class="archive-links">
                <li><a href="/nyt-crossword-archive/">Complete NYT Crossword Archive</a></li>
                <li><a href="/crossword-solving-tips/">Advanced Solving Techniques</a></li>
                <li><a href="/crossword-word-lists/">Common Crossword Words</a></li>
            </ul>
        </section>

        <footer>
            <p><strong>Disclaimer:</strong> Crossword clues and grid © The New York Times. This site provides hints and educational content for puzzle enthusiasts. XWordHint is not affiliated with The New York Times.</p>
            <p class="update-info">Last updated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        </footer>     
        <style>   

            .clue-item {
                margin-bottom: 25px;
                border: 1px solid #ddd;
                padding: 15px;
                border-radius: 8px;
            }
        
            .hint-list {
                background: #f9f9f9;
                padding: 15px;
                border-radius: 5px;
            }
        
            .answer-reveal {
                margin-top: 10px;
            }
        
            .answer-container {
                background: #fffacd;
                padding: 10px;
                border-radius: 5px;
                margin-top: 10px;
            }
        
            .strategy-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
            }
        
            .strategy-item {
                background: #f0f8ff;
                padding: 20px;
                border-radius: 8px;
            }
        
            .stats-container {
                display: flex;
                justify-content: space-around;
                background: #f5f5f5;
                padding: 20px;
                border-radius: 8px;
            }
        
            .stat-item {
                text-align: center;
            }
        
            .stat-number {
                display: block;
                font-size: 2em;
                font-weight: bold;
                color: #2c3e50;
            }
        
          
        
            
        
            
        
            .reveal-button,
            .clear-button {
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                cursor: pointer;
                font-weight: bold;
                transition: all 0.3s;
            }
        
            .reveal-button {
                background-color: #28a745;
                color: white;
            }
        
            .reveal-button:hover {
                background-color: #218838;
            }
        
            .clear-button {
                background-color: #6c757d;
                color: white;
            }
        
            .clear-button:hover {
                background-color: #545b62;
            }
        
            
        </style>

        <script>
            // Grid interaction functionality
            document.addEventListener('DOMContentLoaded', function() {{
                const revealBtn = document.getElementById('reveal-grid');
                const clearBtn = document.getElementById('clear-grid');
                const letterInputs = document.querySelectorAll('.letter-input');
                
                // Store the answers for reveal functionality
                const answers = {json.dumps(crossword_data.get('answers', {}))};                
                if (revealBtn) {{
                    revealBtn.addEventListener('click', function() {{
                        if (confirm('Are you sure you want to reveal the complete grid? This will show all answers!')) {{
                            // Enable all inputs and fill with answers
                            letterInputs.forEach(input => {{
                                input.disabled = false;
                                // Logic to fill answers would go here
                            }});
                            this.textContent = '✅ Grid Revealed!';
                            this.disabled = true;
                        }}
                    }});
                }}
                
                if (clearBtn) {{
                    clearBtn.addEventListener('click', function() {{
                        letterInputs.forEach(input => {{
                            input.value = '';
                        }});
                    }});
                }}
                
                // Click on grid cells to highlight related clues
                document.querySelectorAll('.white-cell').forEach(cell => {{
                    cell.addEventListener('click', function() {{
                        // Remove previous highlights
                        document.querySelectorAll('.highlighted-clue').forEach(el => {{
                            el.classList.remove('highlighted-clue');
                        }});
                        
                        // Add highlight effect
                        this.style.backgroundColor = '#fff3cd';
                        setTimeout(() => {{
                            this.style.backgroundColor = '';
                        }}, 2000);
                    }});
                }});
            }});
        </script>
    """

    return html

# Function to send an email
def send_email(to_email, subject, html_content):
    from_email = "velanms1993@gmail.com"
    password = "dqpt ywts nrey hlrp"  # Replace with your real email app password

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(html_content, 'html'))
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(from_email, password)
    text = msg.as_string()
    server.sendmail(from_email, to_email, text)
    server.quit()

# Main function to run the script
def main():
    crossword_date = datetime.now().strftime("%m/%d/%Y")
    url = f"https://www.xwordinfo.com/JSON/Data.ashx?date={crossword_date}&format=text"
    crossword_data = fetch_crossword_data(url)

    if crossword_data:
        date_str = crossword_data['date']
        date = datetime.strptime(date_str, '%m/%d/%Y')
        title = f"XWordHint Crossword Answers Hints & Solutions - {date.strftime('%B %d, %Y')} | Expert Puzzle Help"
        formatted_html = format_to_html(crossword_data, date)
        send_email("velanms1993.qrco@blogger.com", title, formatted_html)
        print(f"✅ Email sent successfully for {date.strftime('%B %d, %Y')} crossword!")

# Execute the main function
if __name__ == "__main__":
    main()
    time.sleep(60)
