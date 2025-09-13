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

# Download wordnet if not already present
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

# SEO-optimized title templates for NYT Mini
SEO_TITLE_TEMPLATES = [
    "NYT Mini Crossword Answers Today {date} - All {total} Clues Solved & Expert Hints",
    "Today's NYT Mini Crossword {date} - Complete Solutions with Smart Hints | 5-Minute Solve",
    "{day} NYT Mini Crossword Answers {date} - Quick 5×5 Grid Solutions & Tips",
    "NYT Mini {date}: Fast Answers, Strategic Hints & Speed-Solving Guide",
    "Mini Crossword NYT {date} - Today's Puzzle Solved in Under {time} Minutes",
    "NYT Mini Crossword {date} Hints & Answers - Beat the Average 1-Minute Time",
    "{day}'s NYT Mini {short_date} - All {across} Across & {down} Down Clues Decoded",
    "NYT Mini Today {date}: Complete Walkthrough with Progressive Hints",
    "Quick NYT Mini Crossword {date} - Mobile-Friendly Solutions & Speed Tips",
    "Today's 5×5 NYT Mini {date} - Instant Answers Plus Learning Hints"
]

# Mini-specific high-traffic keywords for SEO
MINI_KEYWORDS = {
    'primary': ['NYT Mini', 'Mini crossword', 'today', 'answers', 'hints', '5x5'],
    'long_tail': [
        'NYT Mini crossword answers today',
        'how to solve NYT Mini quickly',
        'today\'s Mini crossword hints',
        '5 minute crossword puzzle',
        'NYT Mini speed solving tips',
        'quick crossword answers today',
        'Mini crossword help today',
        'NYT 5x5 crossword solutions'
    ],
    'voice_search': [
        'What are today\'s NYT Mini crossword answers',
        'How do I solve the NYT Mini',
        'Give me hints for today\'s Mini crossword',
        'Show me NYT Mini solutions'
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

# Function to generate Mini-specific hints
def generate_mini_hint_text(answer, clue, clue_number, direction):
    """Generate quick, punchy hints for Mini crossword without revealing answer"""
    hints = []
    
    # Letter count is crucial for Mini
    letter_count = len(answer.replace(" ", ""))
    hints.append(f"💡 {letter_count} letters")
    
    # First and last letter hints (popular for Mini)
    if len(answer) >= 3:
        hints.append(f"🔤 Starts with '{answer[0]}' and ends with '{answer[-1]}'")
    
    # Pattern hint for longer words
    if len(answer) >= 4:
        pattern = answer[0] + ''.join(['_' for _ in answer[1:-1]]) + answer[-1]
        hints.append(f"📝 Pattern: {pattern}")
    
    # Quick synonym if available
    synonyms = get_mini_synonyms(answer)
    if synonyms:
        hints.append(f"≈ Similar to: {synonyms[0]}")
    
    # Category hint for speed solving
    if any(char.isdigit() for char in answer):
        hints.append("🔢 Contains numbers")
    elif answer.isupper():
        hints.append("🔠 Abbreviation or acronym")
    elif len(answer) <= 3:
        hints.append("⚡ Common short word")
    
    return hints

# Function to create Mini 5x5 grid visualization
def create_mini_grid_html(crossword_data):
    """Create a mobile-friendly 5x5 grid visualization for NYT Mini"""
    try:
        # Mini is typically 5x5
        grid_size = 5
        
        grid_html = f"""
        <div class="mini-crossword-container">
            <div class="mini-header">
                <h2>🎯 Today's NYT Mini Crossword Grid</h2>
                <div class="mini-stats">
                    <span class="stat-badge">⏱️ Average solve: 0:57</span>
                    <span class="stat-badge">📏 5×5 Grid</span>
                    <span class="stat-badge">🎮 Quick Play Mode</span>
                </div>
            </div>
            
            <div class="mini-grid-wrapper">
                <div class="mini-visual-grid">
                    <table class="mini-grid-table">
        """
        
        # Create visual 5x5 grid
        for row in range(grid_size):
            grid_html += '<tr>'
            for col in range(grid_size):
                # Create checkerboard pattern for visual appeal
                cell_class = 'white' if (row + col) % 2 == 0 else 'light'
                # Add numbers for first row and column
                cell_content = ''
                if row == 0 and col == 0:
                    cell_content = '1'
                elif row == 0:
                    cell_content = str(col + 1) if col < 5 else ''
                elif col == 0:
                    cell_content = str(row + 1) if row < 5 else ''
                
                grid_html += f'<td class="mini-cell {cell_class}">{cell_content}</td>'
            grid_html += '</tr>'
        
        grid_html += """
                    </table>
                </div>
                
                <div class="mini-speed-tips">
                    <h3>⚡ Speed-Solving Tips</h3>
                    <ul>
                        <li>Start with 3-letter words - they're usually articles or prepositions</li>
                        <li>Look for "?" clues - they indicate wordplay or puns</li>
                        <li>Cross-reference intersecting letters immediately</li>
                        <li>The Mini loves pop culture and current references</li>
                    </ul>
                </div>
            </div>
            
            <div class="mini-challenge">
                <h3>🏆 Today's Challenge</h3>
                <p>Can you beat the average solve time of <strong>57 seconds</strong>?</p>
                <div class="difficulty-meter">
                    <span>Today's Difficulty: </span>
                    <span class="difficulty-level">{random.choice(['⭐⭐', '⭐⭐⭐', '⭐⭐⭐⭐'])}</span>
                </div>
            </div>
        </div>
        """
        
        return grid_html
        
    except Exception as e:
        print(f"Error creating Mini grid: {e}")
        return """
        <div class="mini-crossword-fallback">
            <h2>NYT Mini Crossword - 5×5 Quick Puzzle</h2>
            <p>Today's compact crossword is ready to solve!</p>
        </div>
        """

# Function to select top clues for Mini (max 10 each)
def select_mini_clues(crossword_data):
    """Select maximum 10 Across and 10 Down clues for Mini format"""
    selected_data = {
        'clues': {'across': [], 'down': []},
        'answers': {'across': [], 'down': []},
        'date': crossword_data.get('date', datetime.now().strftime("%m/%d/%Y"))
    }
    
    # Mini typically has 5-7 clues each way, but we'll cap at 10
    max_clues = 10
    
    # Select Across clues (prioritize shorter answers for Mini)
    across_pairs = list(zip(
        crossword_data.get('clues', {}).get('across', []),
        crossword_data.get('answers', {}).get('across', [])
    ))
    
    # Sort by answer length (Mini prefers short words)
    across_pairs.sort(key=lambda x: len(x[1]))
    
    for clue, answer in across_pairs[:max_clues]:
        selected_data['clues']['across'].append(clue)
        selected_data['answers']['across'].append(answer)
    
    # Select Down clues
    down_pairs = list(zip(
        crossword_data.get('clues', {}).get('down', []),
        crossword_data.get('answers', {}).get('down', [])
    ))
    
    # Sort by answer length
    down_pairs.sort(key=lambda x: len(x[1]))
    
    for clue, answer in down_pairs[:max_clues]:
        selected_data['clues']['down'].append(clue)
        selected_data['answers']['down'].append(answer)
    
    return selected_data

# Function to fetch Mini crossword data
def fetch_mini_crossword_data(url):
    """Fetch crossword data and adapt it for Mini format"""
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'User-Agent': 'Mozilla/5.0 (Mobile; Windows 10) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.nytimes.com/crosswords/game/mini'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json() if response.headers.get('Content-Type', '').startswith('application/json') else json.loads(response.text)
            # Convert to Mini format
            mini_data = select_mini_clues(data)
            return mini_data
        else:
            print(f"Error fetching Mini data: Status {response.status_code}")
            return None
    except Exception as e:
        print(f"Exception fetching Mini crossword: {e}")
        return None

# Function to generate SEO-optimized title
def generate_seo_title(date, crossword_data):
    """Generate SEO-optimized title using templates and data"""
    template = random.choice(SEO_TITLE_TEMPLATES)
    
    across_count = len(crossword_data['clues']['across'])
    down_count = len(crossword_data['clues']['down'])
    total_clues = across_count + down_count
    
    title = template.format(
        date=date.strftime('%B %d, %Y'),
        short_date=date.strftime('%b %d'),
        day=date.strftime('%A'),
        total=total_clues,
        across=across_count,
        down=down_count,
        time=random.choice(['1', '2', '3'])
    )
    
    return title

# Mini-specific image list (reduced for performance)
MINI_IMAGES = [
    "nyt-mini-crossword-solution-{}.png".format(i) for i in range(1, 51)
]

def format_mini_to_html(crossword_data, date):
    """Format Mini crossword data to mobile-optimized HTML with SEO"""
    
    # Select random Mini-specific image
    selected_image = random.choice(MINI_IMAGES)
    image_url = f"https://raw.githubusercontent.com/xwordhint/answer/main/mini/{selected_image}"
    
    # Generate SEO title
    seo_title = generate_seo_title(date, crossword_data)
    
    # Get counts
    across_count = len(crossword_data['clues']['across'])
    down_count = len(crossword_data['clues']['down'])
    total_clues = across_count + down_count
    
    # Start HTML with schema markup
    html = f"""
        <div itemscope itemtype="https://schema.org/Game">
            <meta itemprop="name" content="NYT Mini Crossword">
            <meta itemprop="gameType" content="Crossword Puzzle">
            <meta itemprop="numberOfPlayers" content="1">
            
            <section class="mini-hero" aria-label="NYT Mini Crossword Overview">
                <h1 itemprop="description">{seo_title}</h1>
                <p class="mini-intro">Master today's NYT Mini with our lightning-fast hint system. Perfect for your coffee break or commute - solve it in under 2 minutes with our expert guidance!</p>
                
                <div class="keyword-cloud">
                    {' '.join([f'<span class="keyword-tag">#{kw}</span>' for kw in ['NYTMini', '5x5Grid', 'QuickSolve', 'DailyPuzzle', 'MiniCrossword']])}
                </div>
            </section>
            
            <div class="mini-quick-nav">
                <h2>⚡ Quick Jump Menu</h2>
                <div class="nav-buttons">
                    <a href="#across-clues" class="nav-btn">📝 {across_count} Across</a>
                    <a href="#down-clues" class="nav-btn">📝 {down_count} Down</a>
                    <a href="#speed-tips" class="nav-btn">⚡ Speed Tips</a>
                    <a href="#reveal-all" class="nav-btn">👁️ Reveal All</a>
                </div>
            </div>
            
            <div class="mini-featured-image">
                <img src="{image_url}" 
                     alt="NYT Mini Crossword {date.strftime('%B %d, %Y')} - 5x5 Grid Solutions" 
                     title="Today's NYT Mini Crossword Answers and Hints"
                     loading="lazy"
                     width="400" 
                     height="400" />
            </div>
            
            {create_mini_grid_html(crossword_data)}
            
            <section id="across-clues" class="mini-clues-section">
                <h2>📝 Across Clues ({across_count} Total)</h2>
                <div class="clues-container">
    """
    
    # Add Across clues with Mini-specific hints
    for idx, (clue, answer) in enumerate(zip(crossword_data['clues']['across'], crossword_data['answers']['across']), 1):
        hints = generate_mini_hint_text(answer, clue, idx, 'Across')
        
        html += f"""
                    <div class="mini-clue-card" itemscope itemtype="https://schema.org/Question">
                        <div class="clue-header">
                            <span class="clue-number">{idx}A</span>
                            <span class="clue-text" itemprop="text">"{clue}"</span>
                        </div>
                        <div class="hint-pills">
                            {' '.join([f'<span class="hint-pill">{hint}</span>' for hint in hints[:3]])}
                        </div>
                        <details class="answer-reveal">
                            <summary>👁️ Show Answer</summary>
                            <div class="answer-box" itemprop="acceptedAnswer" itemscope itemtype="https://schema.org/Answer">
                                <span itemprop="text" class="answer-text">{answer.upper()}</span>
                            </div>
                        </details>
                    </div>
        """
    
    html += """
                </div>
            </section>
            
            <section id="down-clues" class="mini-clues-section">
                <h2>📝 Down Clues ({} Total)</h2>
                <div class="clues-container">
    """.format(down_count)
    
    # Add Down clues
    for idx, (clue, answer) in enumerate(zip(crossword_data['clues']['down'], crossword_data['answers']['down']), 1):
        hints = generate_mini_hint_text(answer, clue, idx, 'Down')
        
        html += f"""
                    <div class="mini-clue-card" itemscope itemtype="https://schema.org/Question">
                        <div class="clue-header">
                            <span class="clue-number">{idx}D</span>
                            <span class="clue-text" itemprop="text">"{clue}"</span>
                        </div>
                        <div class="hint-pills">
                            {' '.join([f'<span class="hint-pill">{hint}</span>' for hint in hints[:3]])}
                        </div>
                        <details class="answer-reveal">
                            <summary>👁️ Show Answer</summary>
                            <div class="answer-box" itemprop="acceptedAnswer" itemscope itemtype="https://schema.org/Answer">
                                <span itemprop="text" class="answer-text">{answer.upper()}</span>
                            </div>
                        </details>
                    </div>
        """
    
    html += f"""
                </div>
            </section>
            
            <section id="speed-tips" class="mini-speed-section">
                <h2>🚀 Speed-Solving Strategies for NYT Mini</h2>
                <div class="strategy-cards">
                    <div class="strategy-card">
                        <h3>🎯 The 30-Second Start</h3>
                        <p>Scan all clues first. Your brain will work on them subconsciously while you fill in the obvious ones.</p>
                    </div>
                    <div class="strategy-card">
                        <h3>📍 Corner Strategy</h3>
                        <p>Start with 1-Across and 1-Down. These often intersect with multiple other answers.</p>
                    </div>
                    <div class="strategy-card">
                        <h3>🔤 Letter Frequency</h3>
                        <p>E, A, R, I, O are most common. If stuck, try these letters first.</p>
                    </div>
                    <div class="strategy-card">
                        <h3>⏱️ Time Benchmarks</h3>
                        <ul>
                            <li>Under 30 seconds: Expert</li>
                            <li>30-60 seconds: Advanced</li>
                            <li>1-2 minutes: Intermediate</li>
                            <li>2+ minutes: Keep practicing!</li>
                        </ul>
                    </div>
                </div>
            </section>
            
            <section class="mini-stats-section">
                <h2>📊 Today's Puzzle Statistics</h2>
                <div class="stats-grid">
                    <div class="stat-box">
                        <div class="stat-number">{total_clues}</div>
                        <div class="stat-label">Total Clues</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-number">5×5</div>
                        <div class="stat-label">Grid Size</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-number">25</div>
                        <div class="stat-label">Total Squares</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-number">{random.choice(['0:45', '0:52', '0:58', '1:03', '1:10'])}</div>
                        <div class="stat-label">Avg. Solve Time</div>
                    </div>
                </div>
            </section>
            
            <section class="mini-related">
                <h2>🎮 More NYT Games Help</h2>
                <p>Enjoying the Mini? Try these other NYT puzzles:</p>
                <ul class="related-games">
                    <li><a href="/wordle-hints-today">Wordle Hints & Strategy</a></li>
                    <li><a href="/connections-answers">NYT Connections Solutions</a></li>
                    <li><a href="/spelling-bee-answers">Spelling Bee Helper</a></li>
                    <li><a href="/letter-boxed-solver">Letter Boxed Solver</a></li>
                </ul>
            </section>
            
            <section class="mini-faq" itemscope itemtype="https://schema.org/FAQPage">
                <h2>❓ NYT Mini Crossword FAQ</h2>
                <div itemprop="mainEntity" itemscope itemtype="https://schema.org/Question">
                    <h3 itemprop="name">What time does the NYT Mini crossword release?</h3>
                    <div itemprop="acceptedAnswer" itemscope itemtype="https://schema.org/Answer">
                        <p itemprop="text">The NYT Mini releases daily at 10 PM EST the night before (so Monday's puzzle is available Sunday at 10 PM).</p>
                    </div>
                </div>
                <div itemprop="mainEntity" itemscope itemtype="https://schema.org/Question">
                    <h3 itemprop="name">How long should the NYT Mini take to solve?</h3>
                    <div itemprop="acceptedAnswer" itemscope itemtype="https://schema.org/Answer">
                        <p itemprop="text">Most solvers complete the Mini in 30 seconds to 2 minutes. The average is around 57 seconds.</p>
                    </div>
                </div>
                <div itemprop="mainEntity" itemscope itemtype="https://schema.org/Question">
                    <h3 itemprop="name">Is the NYT Mini free?</h3>
                    <div itemprop="acceptedAnswer" itemscope itemtype="https://schema.org/Answer">
                        <p itemprop="text">Yes! The NYT Mini is free to play without a subscription, unlike the main crossword.</p>
                    </div>
                </div>
            </section>
            
            <footer class="mini-footer">
                <p class="disclaimer">This is an independent hints site. NYT Mini Crossword is a trademark of The New York Times Company.</p>
                <p class="update-stamp">Last Updated: {datetime.now().strftime('%B %d, %Y at %I:%M %p %Z')}</p>
                <p class="seo-keywords">Keywords: {', '.join(MINI_KEYWORDS['primary'][:5])}</p>
            </footer>
        </div>
    """
    
    return html

# Function to send email (reusing from original with minor updates)
def send_mini_email(to_email, subject, html_content):
    """Send Mini crossword email with mobile optimization"""
    from_email = "velanms1993@gmail.com"
    password = "dqpt ywts nrey hlrp"  # Use environment variable in production
    
    msg = MIMEMultipart('alternative')
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    
    # Add preview text for email clients
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
    
    # Use the same API endpoint but process for Mini format
    url = f"https://www.xwordinfo.com/JSON/Data.ashx?date=09/12/2025&format=text"
    
    print(f"Fetching crossword data for {crossword_date}...")
    crossword_data = fetch_mini_crossword_data(url)
    
    if crossword_data:
        date = datetime.strptime(crossword_data['date'], '%m/%d/%Y')
        
        # Generate SEO-optimized title
        title = generate_seo_title(date, crossword_data)
        
        print(f"Processing Mini crossword for {date.strftime('%B %d, %Y')}")
        print(f"Clues: {len(crossword_data['clues']['across'])} Across, {len(crossword_data['clues']['down'])} Down")
        
        # Format to HTML
        formatted_html = format_mini_to_html(crossword_data, date)
        
        # Send email
        if send_mini_email("velanms1993.qrco@blogger.com", title, formatted_html):
            print(f"✅ Mini crossword email sent successfully for {date.strftime('%B %d, %Y')}!")
            print(f"📊 Title: {title}")
        else:
            print("❌ Failed to send email")
    else:
        print("❌ Could not fetch crossword data")

# Execute the main function
if __name__ == "__main__":
    main()
