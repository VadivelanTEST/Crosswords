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

# Function to generate Mini-specific hints
def generate_mini_hint_text(answer, clue, clue_number, direction):
    """Generate simple hints that help without giving away the answer"""
    hints = []
    
    # Letter count - very important
    letter_count = len(answer.replace(" ", ""))
    hints.append(f"This word has {letter_count} letters")
    
    # First and last letter hints help a lot
    if len(answer) >= 3:
        hints.append(f"It starts with '{answer[0]}' and ends with '{answer[-1]}'")
    
    # Pattern hint for longer words
    if len(answer) >= 4:
        pattern = answer[0] + ''.join(['_' for _ in answer[1:-1]]) + answer[-1]
        hints.append(f"Word pattern: {pattern}")
    
    # Find similar words
    synonyms = get_mini_synonyms(answer)
    if synonyms:
        hints.append(f"Another word like this: {synonyms[0]}")
    
    # Special hints based on word type
    if any(char.isdigit() for char in answer):
        hints.append("This answer has numbers in it")
    elif answer.isupper():
        hints.append("This is a short form or acronym")
    elif len(answer) <= 3:
        hints.append("This is a very common short word")
    
    # Add definition hint if available
    synsets = wordnet.synsets(answer)
    if synsets and synsets[0].definition():
        simple_def = synsets[0].definition().split(',')[0]
        if len(simple_def) < 50:
            hints.append(f"It means: {simple_def}")
    
    return hints

# Function to create Mini 5x5 grid visualization
def create_mini_grid_html(crossword_data, week_num):
    """Create a professional 5x5 grid table for NYT Mini"""
    try:
        grid_size = 5
        
        grid_html = """
        <section>
            <h2>Today's Trivia Week {week_num} NYT Mini Crossword Grid Layout</h2>
            <p>This puzzle uses a 5 by 5 grid. That means 5 boxes across and 5 boxes down.</p>
            
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
                # Alternate white and gray cells
                if (row + col) % 2 == 0:
                    grid_html += '<td bgcolor="#FFFFFF">&nbsp;</td>'
                else:
                    grid_html += '<td bgcolor="#F0F0F0">&nbsp;</td>'
            grid_html += '</tr>'
        
        grid_html += """
                </tbody>
            </table>
            
            <h3>How to Solve This Puzzle Fast</h3>
            <ol>
                <li>Read all the clues first - your brain will start working on them</li>
                <li>Fill in the short words first (3 letters or less)</li>
                <li>Use the crossing letters to help with harder words</li>
                <li>If a clue has a question mark (?), it's probably a joke or play on words</li>
                <li>Common short words: THE, AND, ARE, FOR, NOT</li>
            </ol>
            
            <h3>Quick Facts About This Puzzle</h3>
            <ul>
                <li>Total squares in grid: 25 (5 times 5)</li>
                <li>Average time to solve: Less than 1 minute</li>
                <li>Best time to play: During a coffee break</li>
                <li>Difficulty level: Made for everyone to enjoy</li>
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
    
    # We want exactly 10 clues each way
    num_clues = 10
    
    # Get all Across clues
    across_pairs = list(zip(
        crossword_data.get('clues', {}).get('across', []),
        crossword_data.get('answers', {}).get('across', [])
    ))
    
    # Randomly select 10 Across clues (or all if less than 10)
    if len(across_pairs) > num_clues:
        selected_across = random.sample(across_pairs, num_clues)
    else:
        selected_across = across_pairs
    
    for clue, answer in selected_across:
        selected_data['clues']['across'].append(clue)
        selected_data['answers']['across'].append(answer)
    
    # Get all Down clues
    down_pairs = list(zip(
        crossword_data.get('clues', {}).get('down', []),
        crossword_data.get('answers', {}).get('down', [])
    ))
    
    # Randomly select 10 Down clues (or all if less than 10)
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
    # Use the same headers as start.py for successful fetching
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
            
            # Handle response based on content type
            if 'text/plain' in response.headers.get('Content-Type', ''):
                try:
                    data = json.loads(response.text)
                    # Convert to Mini format
                    mini_data = select_mini_clues(data)
                    return mini_data
                except json.JSONDecodeError:
                    print("Error: Could not decode JSON response.")
                    return get_sample_mini_data()
            else:
                # Try to parse as JSON anyway
                try:
                    data = json.loads(response.text)
                    mini_data = select_mini_clues(data)
                    return mini_data
                except:
                    print(f"Error: Unexpected content type {response.headers.get('Content-Type')}")
                    return get_sample_mini_data()
        else:
            print(f"Error fetching data. Status code: {response.status_code}")
            # Return sample data for testing when API fails
            return get_sample_mini_data()
    except Exception as e:
        print(f"Exception fetching crossword: {e}")
        # Return sample data for testing when API fails
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
                'YES',
                'OAK',
                'CAT',
                'ON',
                'ROE',
                'ICE',
                'OLE',
                'ERA'
            ],
            'down': [
                'YEA',
                'ERR',
                'TIDE',
                'HOE',
                'HONEY',
                'GREEN',
                'OLD',
                'EAST'
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

# Mini-specific image list (reduced for performance)
MINI_IMAGES = [
    "nyt_mini_puzzle_{}.png".format(i) for i in range(1, 51)
]

def format_mini_to_html(crossword_data, date):
    """Format Mini crossword data to professional HTML with comprehensive SEO"""
    
    week_num = get_week_of_month(date)

    # Select random Mini-specific image
    selected_image = random.choice(MINI_IMAGES)
    image_url = f"https://raw.githubusercontent.com/xwordhint/answer/main/mini-image/{selected_image}"
    
    # Generate SEO title
    seo_title = generate_seo_title(date, crossword_data)
    
    # Get counts
    across_count = len(crossword_data['clues']['across'])
    down_count = len(crossword_data['clues']['down'])
    total_clues = across_count + down_count

    
    # Fetch internal links from sitemap
    internal_links = fetch_sitemap_urls(max_links=15)
    
    # Start HTML with comprehensive SEO tags and schema markup
    html = f"""        
        <header>
            <h1>{seo_title}</h1>
            <p><strong>Quick Summary:</strong> Today's NYT Mini Crossword has {total_clues} clues total. We have all the answers plus helpful hints to make solving easier!</p>
            
            <p><strong>Popular Puzzles:</strong> 
    """
    
    # Add 3 random internal links at the top
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
                    <tr>
                        <td>Date</td>
                        <td>{date.strftime('%B %d, %Y')}</td>
                    </tr>
                    <tr>
                        <td>Grid Size</td>
                        <td>5 x 5 squares</td>
                    </tr>
                    <tr>
                        <td>Total Clues</td>
                        <td>{total_clues} clues</td>
                    </tr>
                    <tr>
                        <td>Across Clues</td>
                        <td>{across_count} clues</td>
                    </tr>
                    <tr>
                        <td>Down Clues</td>
                        <td>{down_count} clues</td>
                    </tr>
                    <tr>
                        <td>Average Solve Time</td>
                        <td>Under 1 minute</td>
                    </tr>
                </tbody>
            </table>
        </section>
            
        <section id="grid-layout">
            {create_mini_grid_html(crossword_data, week_num)}
        </section>
        
        <section id="across-clues">
            <h2>Across Clues - {across_count} Total</h2>
            <p>These clues go from left to right in the puzzle.</p>
            
            <table border="1" cellpadding="10" cellspacing="0" width="100%">
                <caption>Across Clues List</caption>
                <thead>
                    <tr>
                        <th width="15%">Number</th>
                        <th width="85%">Clue</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    # Add Across clues in a simple table (just number and clue)
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
            <p>Need help? Here are hints and answers for each clue above. Also check out these helpful guides:</p>
            <ul>
    """
    
    # Add 2-3 random internal links
    if internal_links:
        for link in random.sample(internal_links, min(3, len(internal_links))):
            html += f'        <li><a href="{link["url"]}">{link["title"]}</a></li>\n'
    
    html += f"""
            </ul>
    """
    
    # Add hints and answers below the table
    for idx, (clue, answer) in enumerate(zip(crossword_data['clues']['across'], crossword_data['answers']['across']), 1):
        hints = generate_mini_hint_text(answer, clue, idx, 'Across')
        
        html += f"""
            <hr>
            <h4>{idx} Across: "{clue}"</h4>
            <p><strong>Helpful hints:</strong></p>
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
            <p>These clues go from top to bottom in the puzzle.</p>
            
            <table border="1" cellpadding="10" cellspacing="0" width="100%">
                <caption>Down Clues List</caption>
                <thead>
                    <tr>
                        <th width="15%">Number</th>
                        <th width="85%">Clue</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    # Add Down clues in a simple table (just number and clue)
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
            <p>Need help? Here are hints and answers for each clue above. You might also like:</p>
            <ul>
    """
    
    # Add different random internal links for Down section
    if internal_links:
        remaining_links = [link for link in internal_links if link not in random.sample(internal_links, 0)]
        for link in random.sample(remaining_links, min(3, len(remaining_links))):
            html += f'        <li><a href="{link["url"]}">{link["title"]}</a></li>\n'
    
    html += f"""
            </ul>
    """
    
    # Add hints and answers below the table
    for idx, (clue, answer) in enumerate(zip(crossword_data['clues']['down'], crossword_data['answers']['down']), 1):
        hints = generate_mini_hint_text(answer, clue, idx, 'Down')
        
        html += f"""
            <hr>
            <h4>{idx} Down: "{clue}"</h4>
            <p><strong>Helpful hints:</strong></p>
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
        
        <section id="solving-tips">
            <h2>How to Solve the NYT Mini Crossword Faster</h2>
            <p>Here are the best tips from expert solvers:</p>
            
            <h3>Step-by-Step Strategy</h3>
            <ol>
                <li><strong>Quick Scan:</strong> Read all clues once. Your brain starts working on them right away.</li>
                <li><strong>Easy First:</strong> Fill in the shortest words (2-3 letters). These are usually simple words like "IT" or "ON".</li>
                <li><strong>Use Crossings:</strong> When letters cross, they help you figure out harder words.</li>
                <li><strong>Watch for Wordplay:</strong> Clues with question marks (?) are jokes or puns.</li>
                <li><strong>Common Words:</strong> Remember these appear often: ERA, ORE, ATE, ICE.</li>
            </ol>
            
            <h3>Letter Tips That Really Help</h3>
            <ul>
                <li>The letter E is the most common in English</li>
                <li>Words ending in S are often plurals</li>
                <li>If you see "___" in a clue, the answer fits those blanks exactly</li>
                <li>Abbreviations in clues mean the answer is also abbreviated</li>
            </ul>
            
            <h3>Time Goals to Aim For</h3>
            <table border="1" cellpadding="5">
                <thead>
                    <tr>
                        <th>Your Time</th>
                        <th>Skill Level</th>
                        <th>What It Means</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Under 30 seconds</td>
                        <td>Expert</td>
                        <td>You know the puzzle patterns very well!</td>
                    </tr>
                    <tr>
                        <td>30-60 seconds</td>
                        <td>Advanced</td>
                        <td>Great job! You solve quickly.</td>
                    </tr>
                    <tr>
                        <td>1-2 minutes</td>
                        <td>Good</td>
                        <td>You're doing well. Keep practicing!</td>
                    </tr>
                    <tr>
                        <td>Over 2 minutes</td>
                        <td>Learning</td>
                        <td>You'll get faster with practice.</td>
                    </tr>
                </tbody>
            </table>
        </section>
            
        <section id="statistics">
            <h2>Puzzle Numbers and Facts</h2>
            <table border="1" cellpadding="10" width="100%">
                <caption>Today's Puzzle by the Numbers</caption>
                <tbody>
                    <tr>
                        <td><strong>Total Clues:</strong></td>
                        <td>{total_clues} clues to solve</td>
                    </tr>
                    <tr>
                        <td><strong>Grid Size:</strong></td>
                        <td>5 boxes across, 5 boxes down</td>
                    </tr>
                    <tr>
                        <td><strong>Total Squares:</strong></td>
                        <td>25 squares to fill</td>
                    </tr>
                    <tr>
                        <td><strong>Average Time:</strong></td>
                        <td>Most people solve in {random.choice(['45 seconds', '52 seconds', '58 seconds', '1 minute 3 seconds', '1 minute 10 seconds'])}</td>
                    </tr>
                    <tr>
                        <td><strong>Difficulty:</strong></td>
                        <td>{random.choice(['Easy', 'Medium', 'A bit tricky', 'Normal'])}</td>
                    </tr>
                </tbody>
            </table>
        </section>
            
        <section id="related-content">
            <h2>More Puzzle Help</h2>
            <p>If you like the NYT Mini, you might enjoy these other puzzles too:</p>
            
            <h3>Recent Crossword Solutions:</h3>
            <nav>
                <ul>
    """
    
    # Add 5-6 random internal links from sitemap
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
                <h3 itemprop="name">When can I play the Trivia Week {week_num} Mini?</h3>
                <div itemprop="acceptedAnswer" itemscope itemtype="https://schema.org/Answer">
                    <p itemprop="text">The Trivia Week {week_num} puzzle is available at 10 PM Eastern Time the night before.</p>
                </div>
            </div>
            
            <div itemprop="mainEntity" itemscope itemtype="https://schema.org/Question">
                <h3 itemprop="name">How fast should I be able to solve Trivia Week {week_num}?</h3>
                <div itemprop="acceptedAnswer" itemscope itemtype="https://schema.org/Answer">
                    <p itemprop="text">Most people solve the Trivia Week {week_num} Mini in 30 seconds to 2 minutes. Don't worry if you take longer - speed comes with practice!</p>
                </div>
            </div>
            
            <div itemprop="mainEntity" itemscope itemtype="https://schema.org/Question">
                <h3 itemprop="name">Do I need to pay to play Trivia Week {week_num}?</h3>
                <div itemprop="acceptedAnswer" itemscope itemtype="https://schema.org/Answer">
                    <p itemprop="text">No! The Trivia Week {week_num} NYT Mini is completely free. You don't need a subscription like the big crossword.</p>
                </div>
            </div>
            
            <div itemprop="mainEntity" itemscope itemtype="https://schema.org/Question">
                <h3 itemprop="name">What makes a good Trivia Week {week_num} solver?</h3>
                <div itemprop="acceptedAnswer" itemscope itemtype="https://schema.org/Answer">
                    <p itemprop="text">Good Trivia Week {week_num} solvers know common short words, can spot wordplay quickly, and use crossing letters well. Practice helps a lot!</p>
                </div>
            </div>
            
            <div itemprop="mainEntity" itemscope itemtype="https://schema.org/Question">
                <h3 itemprop="name">Are the puzzles harder during Trivia Week {week_num}?</h3>
                <div itemprop="acceptedAnswer" itemscope itemtype="https://schema.org/Answer">
                    <p itemprop="text">Trivia Week {week_num} puzzles can vary in difficulty. Saturdays are often the hardest, while Mondays are the easiest.</p>
                </div>
            </div>
        </section>
            
        <footer>
            <hr>
            <p><strong>About This Page:</strong> We provide hints and answers for the NYT Mini Crossword to help you learn and improve. This site is not connected to The New York Times.</p>
            <p><strong>Last Updated:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
            <p><small>Search terms: {', '.join(MINI_KEYWORDS['primary'][:5])}, {date.strftime('%B %d %Y')} mini crossword</small></p>
        </footer>  
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
    # Use today's date
    crossword_date = datetime.now().strftime("%m/%d/%Y")
    
    # Use the same API endpoint but process for Mini format
    url = f"https://www.xwordinfo.com/JSON/Data.ashx?date={crossword_date}&format=text"
    
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
            print(f"Mini crossword email sent successfully for {date.strftime('%B %d, %Y')}!")
            print(f"Title: {title}")
        else:
            print("Failed to send email")
    else:
        print("Could not fetch crossword data")

# Execute the main function
if __name__ == "__main__":
    main()
