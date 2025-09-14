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

# SEO-optimized title templates for Down clues only
DOWN_TITLE_TEMPLATES = [
    "NYT Down Clues Answers {date} - All {count} Vertical Solutions & Expert Hints",
    "Today's NYT Crossword Down Clues {date} - Complete Top-to-Bottom Answers",
    "{day} NYT Down Solutions {date} - Every Vertical Clue Decoded with Hints",
    "NYT Crossword Down {date}: All {count} Vertical Answers & Strategic Tips",
    "Down Clues NYT {date} - Today's Complete Vertical Solutions",
    "NYT Down Crossword {date} - Master All {count} Top-to-Bottom Clues",
    "{day}'s NYT Down {short_date} - Full Vertical Grid Solutions",
    "NYT Down Today {date}: Complete Vertical Clues Walkthrough",
    "All NYT Down Clues {date} - {count} Vertical Answers with Hints",
    "Today's Down Crossword NYT {date} - Every Vertical Solution Explained"
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

# Down-specific high-traffic keywords for SEO
DOWN_KEYWORDS = {
    'primary': ['NYT Down', 'Down clues', 'vertical', 'crossword answers', 'top to bottom', 'today'],
    'long_tail': [
        'NYT crossword down clues today',
        'how to solve down clues',
        'today\'s vertical crossword answers',
        'NYT down solutions',
        'crossword vertical hints',
        'top to bottom crossword help',
        'down clues explained',
        'NYT vertical crossword answers'
    ],
    'voice_search': [
        'What are today\'s NYT down clues answers',
        'How do I solve the down clues',
        'Give me hints for down crossword clues',
        'Show me NYT vertical solutions'
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

# Function to generate Down-specific hints
def generate_down_hint_text(answer, clue, clue_number):
    """Generate hints for Down clues without revealing answer"""
    hints = []

    # Letter count - very important
    letter_count = len(answer.replace(" ", ""))
    hints.append(f"This word has {letter_count} letters going top to bottom")
    
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
    hints.append(f"This is Down clue number {clue_number}")
    
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
            'across': [],  # We don't need across clues for down.py
            'down': [
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
            ]
        },
        'answers': {
            'across': [],
            'down': [
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
            ]
        }
    }

# Function to generate SEO-optimized title
def generate_seo_title(date, crossword_data):
    """Generate SEO-optimized title for Down clues"""
    template = random.choice(DOWN_TITLE_TEMPLATES)

    down_count = len(crossword_data['clues']['down'])
    
    title = template.format(
        date=date.strftime('%B %d, %Y'),
        short_date=date.strftime('%b %d'),
        day=date.strftime('%A'),
        count=down_count
    )
    
    return title

# Images list for variety
DOWN_IMAGES = [
    "nyt-down-crossword-solution-{}.png".format(i) for i in range(1, 51)
]

def format_down_to_html(crossword_data, date):
    """Format ONLY Down clues to professional HTML with comprehensive SEO"""

    # Select random image
    selected_image = random.choice(DOWN_IMAGES)
    image_url = f"https://raw.githubusercontent.com/xwordhint/answer/main/down/{selected_image}"
    
    # Generate SEO title
    seo_title = generate_seo_title(date, crossword_data)
    
    # Get count of Down clues
    down_count = len(crossword_data['clues']['down'])
    
    # Fetch internal links from sitemap
    internal_links = fetch_sitemap_urls(max_links=15)
    
    # Start HTML with comprehensive SEO tags and schema markup
    html = f"""
        <header>
            <h1>{seo_title}</h1>
            <p><strong>Quick Summary:</strong> Today's NYT Crossword has {down_count} Down clues. We have all the vertical answers plus helpful hints to make solving easier!</p>
            
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
                <li><a href="#down-table">All Down Clues ({down_count} total)</a></li>
                <li><a href="#down-hints">Detailed Hints & Answers</a></li>
                <li><a href="#solving-tips">Down Solving Strategies</a></li>
                <li><a href="#related">More Crossword Help</a></li>
                <li><a href="#faq">Down Clues FAQ</a></li>
            </ul>
        </nav>
            
        <section id="puzzle-info">
            <h2>About Today's Down Clues</h2>
            <figure>
                <img src="{image_url}" 
                     alt="NYT Down clues solutions for {date.strftime('%B %d, %Y')}"
                     title="Complete vertical answers for today's NYT Crossword"
                     width="400" 
                     height="400" />
                <figcaption>NYT Down Clues - {date.strftime('%A, %B %d, %Y')}</figcaption>
            </figure>
            
            <table border="1" cellpadding="5">
                <caption>Down Clues Statistics</caption>
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
                        <td>Total Down Clues</td>
                        <td>{down_count} clues</td>
                    </tr>
                    <tr>
                        <td>Direction</td>
                        <td>Vertical (Top to Bottom)</td>
                    </tr>
                    <tr>
                        <td>Difficulty</td>
                        <td>{random.choice(['Easy', 'Medium', 'Challenging', 'Tricky'])}</td>
                    </tr>
                </tbody>
            </table>
        </section>
        
        <section id="down-table">
            <h2>All Down Clues - Complete List</h2>
            <p>Here are all {down_count} Down clues for today's puzzle. These go vertically from top to bottom.</p>
            
            <table border="1" cellpadding="10" cellspacing="0" width="100%">
                <caption>Complete Down Clues List</caption>
                <thead>
                    <tr>
                        <th width="10%">Number</th>
                        <th width="90%">Clue</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    # Add ALL Down clues in a table
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
        </section>
        
        <section id="down-hints">
            <h2>Detailed Hints and Answers for All Down Clues</h2>
            <p>Need help? Here are comprehensive hints and answers for each Down clue. Also check these helpful guides:</p>
            <ul>
    """
    
    # Add internal links
    if internal_links:
        for link in random.sample(internal_links, min(4, len(internal_links))):
            html += f'        <li><a href="{link["url"]}">{link["title"]}</a></li>\n'
    
    html += f"""
            </ul>
            
            <h3>Complete Down Solutions:</h3>
    """
    
    # Add hints and answers for ALL Down clues
    for idx, (clue, answer) in enumerate(zip(crossword_data['clues']['down'], crossword_data['answers']['down']), 1):
        hints = generate_down_hint_text(answer, clue, idx)
        
        html += f"""
            <hr>
            <div itemscope itemtype="https://schema.org/Question">
                <h4 itemprop="name">{idx} Down: "{clue}"</h4>
                <div itemprop="suggestedAnswer" itemscope itemtype="https://schema.org/Answer">
                    <p><strong>Helpful hints for this Down clue:</strong></p>
                    <ul>
        """
        
        for hint in hints:
            html += f"        <li>{hint}</li>\n"
            
        html += f"""
                    </ul>
                    <p><strong>Answer:</strong> 
                        <details>
                            <summary>Click to reveal the Down answer</summary>
                            <strong itemprop="text">{answer.upper()}</strong>
                        </details>
                    </p>
                </div>
            </div>
        """
    
    html += f"""
        </section>
        
        <section id="solving-tips">
            <h2>Expert Strategies for Solving Down Clues</h2>
            <p>Master the vertical clues with these professional tips:</p>

            <h3>Why Start with Down Clues?</h3>
            <ul>
                <li>Down clues often reveal key letters for intersecting words</li>
                <li>Vertical patterns can unlock difficult sections</li>
                <li>Many prefixes and suffixes run vertically</li>
                <li>Down answers often help solve Across clues</li>
            </ul>
            
            <h3>Down Clue Patterns to Recognize</h3>
            <ol>
                <li><strong>Fill-in-the-blank clues:</strong> These are usually the easiest Down entries</li>
                <li><strong>Prefixes and suffixes:</strong> Common word parts often run vertically</li>
                <li><strong>Abbreviations:</strong> Look for clues with "Abbr." or shortened forms</li>
                <li><strong>Plural indicators:</strong> Words ending in 'S' are common in Down</li>
                <li><strong>Pop culture references:</strong> Names and titles often appear vertically</li>
            </ol>
            
            <h3>Time-Saving Down Techniques</h3>
            <table border="1" cellpadding="5">
                <thead>
                    <tr>
                        <th>Technique</th>
                        <th>How It Helps</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Scan all Down first</td>
                        <td>Get a mental map of the vertical flow</td>
                    </tr>
                    <tr>
                        <td>Fill short Down words</td>
                        <td>3-4 letter words are often prefixes or connectors</td>
                    </tr>
                    <tr>
                        <td>Use crossing letters</td>
                        <td>Across letters help confirm Down answers</td>
                    </tr>
                    <tr>
                        <td>Look for themes</td>
                        <td>Related Down answers often share a theme</td>
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
            
            <h3>Other Puzzle Directions:</h3>
            <ul>
                <li><a href="/nyt-across-clues">Today's Across Clues Solutions</a></li>
                <li><a href="/nyt-mini-crossword">NYT Mini Crossword Answers</a></li>
                <li><a href="/crossword-archive">Complete Crossword Archive</a></li>
            </ul>
        </section>
        
        <section id="faq" itemscope itemtype="https://schema.org/FAQPage">
            <h2>Frequently Asked Questions About Down Clues</h2>
            
            <div itemprop="mainEntity" itemscope itemtype="https://schema.org/Question">
                <h3 itemprop="name">What are Down clues in crossword puzzles?</h3>
                <div itemprop="acceptedAnswer" itemscope itemtype="https://schema.org/Answer">
                    <p itemprop="text">Down clues are the vertical entries in a crossword puzzle that read from top to bottom. They're numbered and correspond to specific columns in the grid.</p>
                </div>
            </div>
            
            <div itemprop="mainEntity" itemscope itemtype="https://schema.org/Question">
                <h3 itemprop="name">Should I solve Down or Across clues first?</h3>
                <div itemprop="acceptedAnswer" itemscope itemtype="https://schema.org/Answer">
                    <p itemprop="text">Many solvers alternate between Down and Across clues to build momentum. Down clues can help unlock difficult sections by providing key intersecting letters. The best approach is to solve the clues you find easiest first, regardless of direction.</p>
                </div>
            </div>
            
            <div itemprop="mainEntity" itemscope itemtype="https://schema.org/Question">
                <h3 itemprop="name">How many Down clues are in today's puzzle?</h3>
                <div itemprop="acceptedAnswer" itemscope itemtype="https://schema.org/Answer">
                    <p itemprop="text">Today's NYT crossword has {down_count} Down clues.</p>
                </div>
            </div>
            
            <div itemprop="mainEntity" itemscope itemtype="https://schema.org/Question">
                <h3 itemprop="name">Are Down clues easier than Across clues?</h3>
                <div itemprop="acceptedAnswer" itemscope itemtype="https://schema.org/Answer">
                    <p itemprop="text">Neither direction is inherently easier. The difficulty depends on the specific clues and your knowledge. However, Down clues often contain helpful prefixes, suffixes, and word parts that can be easier to guess.</p>
                </div>
            </div>
            
            <div itemprop="mainEntity" itemscope itemtype="https://schema.org/Question">
                <h3 itemprop="name">How do Down clues interact with Across clues?</h3>
                <div itemprop="acceptedAnswer" itemscope itemtype="https://schema.org/Answer">
                    <p itemprop="text">Down and Across clues intersect at various points in the grid. Solving one can provide letters that help solve the other, making the puzzle easier as you progress.</p>
                </div>
            </div>
        </section>
        
        <footer>
            <hr>
            <p><strong>About This Page:</strong> We provide comprehensive Down clues solutions and hints for the NYT Crossword to help you improve your solving skills. This site is not affiliated with The New York Times.</p>
            <p><strong>Last Updated:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
            <p><small>Search terms: {', '.join(DOWN_KEYWORDS['primary'][:5])}, {date.strftime('%B %d %Y')} down clues</small></p>
        </footer>    
    """
    
    return html

# Function to send email
def send_down_email(to_email, subject, html_content):
    """Send Down clues email"""
    from_email = "velanms1993@gmail.com"
    password = "dqpt ywts nrey hlrp"  # Use environment variable in production
    
    msg = MIMEMultipart('alternative')
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    
    # Add preview text for email clients
    text_part = MIMEText("Solve today's NYT Down clues with our expert hints!", 'plain')
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

# Main function for Down clues
def main():
    """Main execution function for NYT Down clues processor"""
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
        
        print(f"Processing Down clues for {date.strftime('%B %d, %Y')}")
        print(f"Total Down Clues: {len(crossword_data['clues']['down'])}")
        
        # Format to HTML
        formatted_html = format_down_to_html(crossword_data, date)
        
        # Send email
        if send_down_email("velanms1993.qrco@blogger.com", title, formatted_html):
            print(f"Down clues email sent successfully for {date.strftime('%B %d, %Y')}!")
            print(f"Title: {title}")
        else:
            print("Failed to send email")
    else:
        print("Could not fetch crossword data")

# Execute the main function
if __name__ == "__main__":
    main()
