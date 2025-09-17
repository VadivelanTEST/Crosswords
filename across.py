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

# SEO-optimized title templates for Across clues only
ACROSS_TITLE_TEMPLATES = [
    "NYT Across Clues Answers {date} - All {count} Horizontal Solutions & Expert Hints",
    "Today's NYT Crossword Across Clues {date} - Complete Left-to-Right Answers",
    "{day} NYT Across Solutions {date} - Every Horizontal Clue Decoded with Hints",
    "NYT Crossword Across {date}: All {count} Horizontal Answers & Strategic Tips",
    "Across Clues NYT {date} - Today's Complete Horizontal Solutions",
    "NYT Across Crossword {date} - Master All {count} Left-to-Right Clues",
    "{day}'s NYT Across {short_date} - Full Horizontal Grid Solutions",
    "NYT Across Today {date}: Complete Horizontal Clues Walkthrough",
    "All NYT Across Clues {date} - {count} Horizontal Answers with Hints",
    "Today's Across Crossword NYT {date} - Every Horizontal Solution Explained"
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

# Across-specific high-traffic keywords for SEO
ACROSS_KEYWORDS = {
    'primary': ['NYT Across', 'Across clues', 'horizontal', 'crossword answers', 'left to right', 'today'],
    'long_tail': [
        'NYT crossword across clues today',
        'how to solve across clues',
        'today\'s horizontal crossword answers',
        'NYT across solutions',
        'crossword horizontal hints',
        'left to right crossword help',
        'across clues explained',
        'NYT horizontal crossword answers'
    ],
    'voice_search': [
        'What are today\'s NYT across clues answers',
        'How do I solve the across clues',
        'Give me hints for across crossword clues',
        'Show me NYT horizontal solutions'
    ]
}

# Function to get synonyms (from start_mini.py)
def get_synonyms(word):
    """Get relevant synonyms for crossword words"""
    synonyms = set()
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            synonym = lemma.name().replace('_', ' ')
            if synonym.lower() != word.lower() and len(synonym) <= 15:
                synonyms.add(synonym)
    return list(synonyms)[:3]  # Return up to 3 synonyms

# Function to get antonyms
def get_antonyms(word):
    """Get antonyms for crossword hints"""
    antonyms = set()
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            if lemma.antonyms():
                antonym = lemma.antonyms()[0].name().replace('_', ' ')
                if antonym.lower() != word.lower() and len(antonym) <= 15:
                    antonyms.add(antonym)
    return list(antonyms)[:2]  # Return up to 2 antonyms

# Function to generate Across-specific hints
def generate_across_hint_text(answer, clue, clue_number):
    """Generate hints for Across clues without revealing answer"""
    hints = []
    
    # Letter count - very important
    letter_count = len(answer.replace(" ", ""))
    hints.append(f"This word has {letter_count} letters going left to right")
    
    # First and last letter hints
    if len(answer) >= 3:
        hints.append(f"It starts with '{answer[0]}' and ends with '{answer[-1]}'")
    
    # Pattern hint for longer words
    if len(answer) >= 4:
        pattern = answer[0] + ''.join(['_' for _ in answer[1:-1]]) + answer[-1]
        hints.append(f"Word pattern: {pattern}")
    
    # Find similar words
    synonyms = get_synonyms(answer)
    if synonyms:
        hints.append(f"Similar words: {', '.join(synonyms[:2])}")
    
    # Find opposite words
    antonyms = get_antonyms(answer)
    if antonyms:
        hints.append(f"Opposite of: {antonyms[0]}")
    
    # Special hints based on word type
    if any(char.isdigit() for char in answer):
        hints.append("This answer contains numbers")
    elif answer.isupper():
        hints.append("This is an abbreviation or acronym")
    elif len(answer) <= 3:
        hints.append("This is a common short word")
    
    # Add definition hint if available
    synsets = wordnet.synsets(answer)
    if synsets and synsets[0].definition():
        simple_def = synsets[0].definition().split(',')[0]
        if len(simple_def) < 60:
            hints.append(f"Definition: {simple_def}")
    
    # Position hint
    hints.append(f"This is Across clue number {clue_number}")
    
    return hints

# Function to fetch crossword data
def fetch_crossword_data(url):
    """Fetch crossword data and return all clues"""
    # Use the same headers as start_mini.py for successful fetching
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
            
            # Handle response based on content type
            if 'text/plain' in response.headers.get('Content-Type', ''):
                try:
                    data = json.loads(response.text)
                    return data
                except json.JSONDecodeError:
                    print("Error: Could not decode JSON response.")
                    return get_sample_data()
            else:
                # Try to parse as JSON anyway
                try:
                    data = json.loads(response.text)
                    return data
                except:
                    print(f"Error: Unexpected content type {response.headers.get('Content-Type')}")
                    return get_sample_data()
        else:
            print(f"Error fetching data. Status code: {response.status_code}")
            return get_sample_data()
    except Exception as e:
        print(f"Exception fetching crossword: {e}")
        return get_sample_data()

# Function to provide sample data for testing
def get_sample_data():
    """Provide sample crossword data for testing"""
    return {
        'date': datetime.now().strftime("%m/%d/%Y"),
        'clues': {
            'across': [
                'Capital of France',
                'Opposite of "no"',
                'Tree with acorns',
                'Feline pet',
                'Not off',
                'Eggs on sushi',
                'Frozen water',
                'Cheer for a matador',
                'Period of time',
                'Large body of water',
                'Common greeting',
                'Type of bread',
                'Morning beverage',
                'Color of grass',
                'Quick movement'
            ],
            'down': []  # We don't need down clues for across.py
        },
        'answers': {
            'across': [
                'PARIS',
                'YES',
                'OAK',
                'CAT',
                'ON',
                'ROE',
                'ICE',
                'OLE',
                'ERA',
                'OCEAN',
                'HELLO',
                'RYE',
                'COFFEE',
                'GREEN',
                'DASH'
            ],
            'down': []
        }
    }

# Function to generate SEO-optimized title
def generate_seo_title(date, crossword_data):
    """Generate SEO-optimized title for Across clues"""
    template = random.choice(ACROSS_TITLE_TEMPLATES)
    
    across_count = len(crossword_data['clues']['across'])
    
    title = template.format(
        date=date.strftime('%B %d, %Y'),
        short_date=date.strftime('%b %d'),
        day=date.strftime('%A'),
        count=across_count
    )
    
    return title

# Images list for variety
ACROSS_IMAGES = [
    "acros_puzzle_{}.png".format(i) for i in range(1, 51)
]

def format_across_to_html(crossword_data, date):
    """Format ONLY Across clues to professional HTML with comprehensive SEO"""
    
    # Select random image
    selected_image = random.choice(ACROSS_IMAGES)
    image_url = f"https://raw.githubusercontent.com/xwordhint/answer/main/across/{selected_image}"
    
    # Generate SEO title
    seo_title = generate_seo_title(date, crossword_data)
    
    # Get count of Across clues
    across_count = len(crossword_data['clues']['across'])
    
    # Fetch internal links from sitemap
    internal_links = fetch_sitemap_urls(max_links=15)
    
    # Start HTML with comprehensive SEO tags and schema markup
    html = f"""        
        <header>
            <h1>{seo_title}</h1>
            <p><strong>Quick Summary:</strong> Today's NYT Crossword has {across_count} Across clues. We have all the horizontal answers plus helpful hints to make solving easier!</p>
            
            <p><strong>Related Puzzles:</strong> 
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
                <li><a href="#across-table">All Across Clues ({across_count} total)</a></li>
                <li><a href="#across-hints">Detailed Hints & Answers</a></li>
                <li><a href="#solving-tips">Across Solving Strategies</a></li>
                <li><a href="#related">More Crossword Help</a></li>
                <li><a href="#faq">Across Clues FAQ</a></li>
            </ul>
        </nav>
            
        <section id="puzzle-info">
            <h2>About Today's Across Clues</h2>
            <figure>
                <img src="{image_url}" 
                     alt="NYT Across clues solutions for {date.strftime('%B %d, %Y')}" 
                     title="Complete horizontal answers for today's NYT Crossword"
                     width="400" 
                     height="400" />
                <figcaption>NYT Across Clues - {date.strftime('%A, %B %d, %Y')}</figcaption>
            </figure>
            
            <table border="1" cellpadding="5">
                <caption>Across Clues Statistics</caption>
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
                        <td>Day of Week</td>
                        <td>{date.strftime('%A')}</td>
                    </tr>
                    <tr>
                        <td>Total Across Clues</td>
                        <td>{across_count} clues</td>
                    </tr>
                    <tr>
                        <td>Direction</td>
                        <td>Horizontal (Left to Right)</td>
                    </tr>
                    <tr>
                        <td>Difficulty</td>
                        <td>{random.choice(['Easy', 'Medium', 'Challenging', 'Tricky'])}</td>
                    </tr>
                </tbody>
            </table>
        </section>
        
        <section id="across-table">
            <h2>All Across Clues - Complete List</h2>
            <p>Here are all {across_count} Across clues for today's puzzle. These go horizontally from left to right.</p>
            
            <table border="1" cellpadding="10" cellspacing="0" width="100%">
                <caption>Complete Across Clues List</caption>
                <thead>
                    <tr>
                        <th width="10%">Number</th>
                        <th width="90%">Clue</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    # Add ALL Across clues in a table
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
        </section>
        
        <section id="across-hints">
            <h2>Detailed Hints and Answers for All Across Clues</h2>
            <p>Need help? Here are comprehensive hints and answers for each Across clue. Also check these helpful guides:</p>
            <ul>
    """
    
    # Add internal links
    if internal_links:
        for link in random.sample(internal_links, min(4, len(internal_links))):
            html += f'        <li><a href="{link["url"]}">{link["title"]}</a></li>\n'
    
    html += f"""
            </ul>
            
            <h3>Complete Across Solutions:</h3>
    """
    
    # Add hints and answers for ALL Across clues
    for idx, (clue, answer) in enumerate(zip(crossword_data['clues']['across'], crossword_data['answers']['across']), 1):
        hints = generate_across_hint_text(answer, clue, idx)
        
        html += f"""
            <hr>
            <div itemscope itemtype="https://schema.org/Question">
                <h4 itemprop="name">{idx} Across: "{clue}"</h4>
                <div itemprop="suggestedAnswer" itemscope itemtype="https://schema.org/Answer">
                    <p><strong>Helpful hints for this Across clue:</strong></p>
                    <ul>
        """
        
        for hint in hints:
            html += f"        <li>{hint}</li>\n"
            
        html += f"""
                    </ul>
                    <p><strong>Answer:</strong> 
                        <details>
                            <summary>Click to reveal the Across answer</summary>
                            <strong itemprop="text">{answer.upper()}</strong>
                        </details>
                    </p>
                </div>
            </div>
        """
    
    html += f"""
        </section>
        
        <section id="solving-tips">
            <h2>Expert Strategies for Solving Across Clues</h2>
            <p>Master the horizontal clues with these professional tips:</p>
            
            <h3>Why Start with Across Clues?</h3>
            <ul>
                <li>Across clues often provide more letter intersections</li>
                <li>Reading left to right feels more natural</li>
                <li>Many common phrases run horizontally</li>
                <li>Across answers often help solve Down clues</li>
            </ul>
            
            <h3>Across Clue Patterns to Recognize</h3>
            <ol>
                <li><strong>Fill-in-the-blank clues:</strong> These are usually the easiest Across entries</li>
                <li><strong>Common phrases:</strong> Many idioms run horizontally</li>
                <li><strong>Abbreviations:</strong> Look for clues with "Abbr." or shortened forms</li>
                <li><strong>Plural indicators:</strong> Words ending in 'S' are common in Across</li>
                <li><strong>Pop culture references:</strong> Names and titles often appear horizontally</li>
            </ol>
            
            <h3>Time-Saving Across Techniques</h3>
            <table border="1" cellpadding="5">
                <thead>
                    <tr>
                        <th>Technique</th>
                        <th>How It Helps</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Scan all Across first</td>
                        <td>Get a mental map of the horizontal flow</td>
                    </tr>
                    <tr>
                        <td>Fill short Across words</td>
                        <td>3-4 letter words are often articles or prepositions</td>
                    </tr>
                    <tr>
                        <td>Use crossing letters</td>
                        <td>Down letters help confirm Across answers</td>
                    </tr>
                    <tr>
                        <td>Look for themes</td>
                        <td>Related Across answers often share a theme</td>
                    </tr>
                </tbody>
            </table>
        </section>
        
        <section id="related">
            <h2>More Crossword Resources</h2>
            
            <h3>Recent Crossword Solutions:</h3>
            <nav>
                <ul>
    """
    
    # Add more internal links
    if internal_links:
        for link in random.sample(internal_links, min(8, len(internal_links))):
            html += f'                    <li><a href="{link["url"]}">{link["title"]}</a></li>\n'
    
    html += f"""
                </ul>
            </nav>
            
            
        </section>
        
        <section id="faq" itemscope itemtype="https://schema.org/FAQPage">
            <h2>Frequently Asked Questions About Across Clues</h2>
            
            <div itemprop="mainEntity" itemscope itemtype="https://schema.org/Question">
                <h3 itemprop="name">What are Across clues in crossword puzzles?</h3>
                <div itemprop="acceptedAnswer" itemscope itemtype="https://schema.org/Answer">
                    <p itemprop="text">Across clues are the horizontal entries in a crossword puzzle that read from left to right. They're numbered and correspond to specific rows in the grid.</p>
                </div>
            </div>
            
            <div itemprop="mainEntity" itemscope itemtype="https://schema.org/Question">
                <h3 itemprop="name">Should I solve Across or Down clues first?</h3>
                <div itemprop="acceptedAnswer" itemscope itemtype="https://schema.org/Answer">
                    <p itemprop="text">Many solvers prefer starting with Across clues because reading left-to-right feels more natural. However, the best approach is to solve the clues you find easiest first, regardless of direction.</p>
                </div>
            </div>
            
            <div itemprop="mainEntity" itemscope itemtype="https://schema.org/Question">
                <h3 itemprop="name">How many Across clues are in today's puzzle?</h3>
                <div itemprop="acceptedAnswer" itemscope itemtype="https://schema.org/Answer">
                    <p itemprop="text">Today's NYT crossword has {across_count} Across clues.</p>
                </div>
            </div>
            
            <div itemprop="mainEntity" itemscope itemtype="https://schema.org/Question">
                <h3 itemprop="name">Are Across clues easier than Down clues?</h3>
                <div itemprop="acceptedAnswer" itemscope itemtype="https://schema.org/Answer">
                    <p itemprop="text">Neither direction is inherently easier. The difficulty depends on the specific clues and your knowledge. However, Across clues often contain more common phrases and expressions.</p>
                </div>
            </div>
            
            <div itemprop="mainEntity" itemscope itemtype="https://schema.org/Question">
                <h3 itemprop="name">How do Across clues interact with Down clues?</h3>
                <div itemprop="acceptedAnswer" itemscope itemtype="https://schema.org/Answer">
                    <p itemprop="text">Across and Down clues intersect at various points in the grid. Solving one can provide letters that help solve the other, making the puzzle easier as you progress.</p>
                </div>
            </div>
        </section>
        
        <footer>
            <hr>
            <p><strong>About This Page:</strong> We provide comprehensive Across clues solutions and hints for the NYT Crossword to help you improve your solving skills. This site is not affiliated with The New York Times.</p>
            <p><strong>Last Updated:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
            <p><small>Search terms: {', '.join(ACROSS_KEYWORDS['primary'][:5])}, {date.strftime('%B %d %Y')} across clues</small></p>
        </footer>   
    """
    
    return html

# Function to send email
def send_across_email(to_email, subject, html_content):
    """Send Across clues email"""
    from_email = "velanms1993@gmail.com"
    password = "dqpt ywts nrey hlrp"  # Use environment variable in production
    
    msg = MIMEMultipart('alternative')
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    
    # Add preview text for email clients
    text_part = MIMEText("Solve today's NYT Across clues with our expert hints!", 'plain')
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

# Main function for Across clues
def main():
    """Main execution function for NYT Across clues processor"""
    # Use today's date
    crossword_date = datetime.now().strftime("%m/%d/%Y")
    
    # Use the same API endpoint
    url = f"https://www.xwordinfo.com/JSON/Data.ashx?date={crossword_date}&format=text"
    
    print(f"Fetching crossword data for {crossword_date}...")
    crossword_data = fetch_crossword_data(url)
    
    if crossword_data:
        date = datetime.strptime(crossword_data['date'], '%m/%d/%Y')
        
        # Generate SEO-optimized title
        title = generate_seo_title(date, crossword_data)
        
        print(f"Processing Across clues for {date.strftime('%B %d, %Y')}")
        print(f"Total Across Clues: {len(crossword_data['clues']['across'])}")
        
        # Format to HTML
        formatted_html = format_across_to_html(crossword_data, date)
        
        # Send email
        if send_across_email("velanms1993.qrco@blogger.com", title, formatted_html):
            print(f"Across clues email sent successfully for {date.strftime('%B %d, %Y')}!")
            print(f"Title: {title}")
        else:
            print("Failed to send email")
    else:
        print("Could not fetch crossword data")

# Execute the main function
if __name__ == "__main__":
    main()
