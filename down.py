#!/usr/bin/env python3
"""
NYT Crossword Down Clues Processor - All Vertical Clues
Generates SEO-optimized blog posts for Down clues only
"""

import json
import logging
import random
import re
import smtplib
import ssl
import sys
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List, Optional, Tuple

import nltk
from nltk.corpus import wordnet

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Download required NLTK data
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    logger.info("Downloading WordNet data...")
    nltk.download('wordnet', quiet=True)
    nltk.download('omw-1.4', quiet=True)

# Email Configuration
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'sender_email': 'velanms1993@gmail.com',
    'sender_password': 'dqpt ywts nrey hlrp',  # App-specific password
    'recipient_email': 'velanms1993.qrco@blogger.com'
}

# SEO Title Templates for Down Clues
DOWN_TITLE_TEMPLATES = [
    "NYT Down Clues Answers {date} - All {count} Vertical Solutions & Expert Hints",
    "Today's NYT Crossword Down Clues {date} - Complete Top-to-Bottom Answers",
    "NYT Vertical Clues {date} - All {count} Down Solutions with Detailed Hints",
    "{date} NYT Down Clues - Complete Vertical Crossword Answers & Tips",
    "New York Times Down Clues {date} - All {count} Column Solutions",
    "NYT Crossword Vertical Answers {date} - Full Down Clues Guide",
    "Today's NYT Down Puzzle {date} - All {count} Top-to-Bottom Clues Solved",
    "{date} NYT Vertical Clues - Complete Down Answers & Helpful Hints",
    "NYT Down Clues Today {date} - All {count} Column-by-Column Solutions",
    "New York Times Vertical Puzzle {date} - Full Down Clues with Answers"
]

# Meta Description Templates for Down Clues
DOWN_META_TEMPLATES = [
    "Complete NYT Down clues answers for {date}. All {count} vertical solutions with expert hints, synonyms, and detailed explanations for today's puzzle.",
    "Solve all {count} NYT Down clues for {date}. Get vertical answers, helpful hints, and word definitions for today's crossword puzzle.",
    "NYT vertical clues solved for {date}. Find all {count} Down answers with detailed hints and explanations for today's crossword.",
    "Today's NYT Down clues answers - {date}. Complete vertical solutions for all {count} clues with expert hints and tips.",
    "All {count} NYT Down clues for {date} solved. Get top-to-bottom answers with synonyms, hints, and crossword solving strategies."
]

# Down Images Pool (50 images for variety)
DOWN_IMAGES = [
    "nyt-down-crossword-solution-{}.png".format(i) for i in range(1, 51)
]

def fetch_sitemap_links(sitemap_url: str = "https://xwordhint.blogspot.com/sitemap.xml") -> List[str]:
    """Fetch internal links from sitemap for SEO"""
    try:
        response = requests.get(sitemap_url, timeout=10)
        if response.status_code == 200:
            sitemap_content = response.text
            
            root = ET.fromstring(sitemap_content)
            namespaces = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            
            links = []
            for url in root.findall('.//ns:loc', namespaces):
                if url.text and 'xwordhint.blogspot.com' in url.text:
                    links.append(url.text)
            
            # Return random selection of links
            return random.sample(links, min(20, len(links))) if links else []
        else:
            return []
    
    except Exception as e:
        logger.warning(f"Could not fetch sitemap: {e}")
        # Return fallback links
        return [
            "https://xwordhint.blogspot.com/2024/12/nyt-crossword-december-2024.html",
            "https://xwordhint.blogspot.com/2024/12/crossword-solving-tips.html",
            "https://xwordhint.blogspot.com/p/about.html",
            "https://xwordhint.blogspot.com/p/contact.html"
        ]

def fetch_crossword_data(date: datetime) -> Dict:
    """Fetch crossword data from xwordinfo API"""
    formatted_date = date.strftime("%m/%d/%Y")
    url = f"https://www.xwordinfo.com/JSON/Data.ashx?date={formatted_date}&format=text"
    
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
            logger.info(f"Successfully fetched data. Content-Type: {response.headers.get('Content-Type', '')}")
            
            # Try to parse as JSON
            try:
                data = json.loads(response.text)
                return data
            except json.JSONDecodeError:
                logger.error("Could not decode JSON response.")
                return get_sample_crossword_data()
        else:
            logger.error(f"Error fetching data. Status code: {response.status_code}")
            return get_sample_crossword_data()
    except Exception as e:
        logger.error(f"API Error: {e}")
        return get_sample_crossword_data()

def get_sample_crossword_data() -> Dict:
    """Fallback sample data for Down clues"""
    return {
        "title": "NY Times Crossword",
        "author": "NYT Puzzles",
        "dow": "Today",
        "date": datetime.now().strftime("%m/%d/%Y"),
        "clues": {
            "down": [
                "1. Capital of France",
                "2. Morning beverage",
                "3. Computer brand",
                "4. Ocean motion",
                "5. Flying mammal",
                "6. Red planet",
                "7. Largest continent",
                "8. Olympic medal metal",
                "9. Shakespeare's theater",
                "10. Italian volcano",
                "11. Desert plant",
                "12. Chess piece",
                "13. Musical note",
                "14. Weather phenomenon",
                "15. Garden tool",
                "16. Time period",
                "17. Body part",
                "18. Tree type",
                "19. Color shade",
                "20. Kitchen appliance",
                "21. Sports equipment",
                "22. Ocean creature",
                "23. Mountain range",
                "24. River in Egypt",
                "25. Ancient civilization",
                "26. Precious stone",
                "27. Dance style",
                "28. Food ingredient",
                "29. Weather condition",
                "30. Musical instrument"
            ],
            "across": []
        },
        "answers": {
            "down": [
                "PARIS",
                "COFFEE",
                "APPLE",
                "TIDE",
                "BAT",
                "MARS",
                "ASIA",
                "GOLD",
                "GLOBE",
                "ETNA",
                "CACTUS",
                "ROOK",
                "NOTE",
                "STORM",
                "RAKE",
                "ERA",
                "ARM",
                "OAK",
                "BLUE",
                "OVEN",
                "BALL",
                "WHALE",
                "ALPS",
                "NILE",
                "MAYA",
                "RUBY",
                "TANGO",
                "SALT",
                "RAIN",
                "PIANO"
            ],
            "across": []
        }
    }

def clean_text(text: str) -> str:
    """Clean text for HTML output"""
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    text = text.replace('"', '&quot;').replace("'", '&#39;')
    return text.strip()

def generate_hints(word: str) -> List[str]:
    """Generate hints using WordNet"""
    hints = []
    word_clean = re.sub(r'[^a-zA-Z]', '', word.lower())
    
    if not word_clean:
        return ["Word puzzle clue"]
    
    try:
        synsets = wordnet.synsets(word_clean)
        
        for syn in synsets[:3]:
            # Add definition
            definition = syn.definition()
            if definition:
                hints.append(f"Could mean: {definition}")
            
            # Add synonyms
            for lemma in syn.lemmas()[:3]:
                synonym = lemma.name().replace('_', ' ')
                if synonym.lower() != word_clean.lower():
                    hints.append(f"Similar to: {synonym}")
            
            # Add examples
            for example in syn.examples()[:1]:
                hints.append(f"Example: {example}")
        
        # Add antonyms
        for syn in synsets[:2]:
            for lemma in syn.lemmas():
                for antonym in lemma.antonyms()[:1]:
                    hints.append(f"Opposite of: {antonym.name().replace('_', ' ')}")
        
        # Ensure we have at least one hint
        if not hints:
            hints.append(f"Think about words related to {word_clean}")
    
    except Exception as e:
        logger.warning(f"Error generating hints for '{word}': {e}")
        hints.append(f"Consider the context of this clue")
    
    return hints[:3] if hints else ["Word puzzle clue"]

def process_down_clues(crossword_data: Dict) -> List[Tuple[str, str, str]]:
    """Process all Down clues from crossword data"""
    down_pairs = []
    
    if 'clues' in crossword_data and 'down' in crossword_data['clues']:
        down_clues = crossword_data['clues']['down']
        down_answers = crossword_data.get('answers', {}).get('down', [])
        
        for i, clue_text in enumerate(down_clues):
            if i < len(down_answers):
                answer = down_answers[i]
                # Extract number from clue if present
                match = re.match(r'^(\d+)[.\s]+(.+)', clue_text)
                if match:
                    number = match.group(1)
                    clue = match.group(2)
                else:
                    number = str(i + 1)
                    clue = clue_text
                
                down_pairs.append((number, clue, answer))
    
    return down_pairs

def create_down_html(date: datetime, crossword_data: Dict) -> str:
    """Create SEO-optimized HTML for Down clues only"""
    
    # Process all Down clues
    down_clues = process_down_clues(crossword_data)
    down_count = len(down_clues)
    
    # Get internal links for SEO
    internal_links = fetch_sitemap_links()
    
    # Select random image
    selected_image = random.choice(DOWN_IMAGES)
    image_url = f"https://raw.githubusercontent.com/xwordhint/answer/main/down/{selected_image}"
    
    # Select random SEO title and meta description
    title_template = random.choice(DOWN_TITLE_TEMPLATES)
    meta_template = random.choice(DOWN_META_TEMPLATES)
    
    seo_title = title_template.format(
        date=date.strftime("%B %d, %Y"),
        count=down_count
    )
    
    meta_description = meta_template.format(
        date=date.strftime("%B %d, %Y"),
        count=down_count
    )
    
   
    # Main heading
    html = f"""
    <h1>{seo_title}</h1>
    
    <p>Welcome to today's complete NYT Down clues guide for {date.strftime('%B %d, %Y')}. We have all {down_count} vertical clues solved with detailed hints and explanations. Down clues run from top to bottom in the crossword grid.</p>
    
    <h2>Quick Navigation</h2>
    <ul>
        <li><a href="#down-clues-table">View All Down Clues</a></li>
        <li><a href="#down-solutions">Complete Down Solutions</a></li>
        <li><a href="#solving-tips">Vertical Solving Tips</a></li>
        <li><a href="#related-puzzles">Related Crossword Resources</a></li>
    </ul>
"""

    # Add some internal links naturally
    if internal_links:
        html += f"""
    <h2>Today's Crossword Resources</h2>
    <p>Looking for more crossword help? Check out our <a href="{random.choice(internal_links)}">complete puzzle archive</a> or visit our <a href="{random.choice(internal_links)}">crossword solving guide</a> for expert tips.</p>
"""

    # Down Clues Table
    html += f"""
    <h2 id="down-clues-table">Down Clues - {down_count} Total Vertical Clues</h2>
    <p>Here are all the Down clues for today's NYT crossword puzzle. These clues run vertically from top to bottom in the grid.</p>
    
    <table border="1">
        <thead>
            <tr>
                <th>Number</th>
                <th>Clue</th>
            </tr>
        </thead>
        <tbody>
"""
    
    for number, clue, _ in down_clues:
        html += f"""
            <tr>
                <td>{number}D</td>
                <td>{clean_text(clue)}</td>
            </tr>
"""
    
    html += """
        </tbody>
    </table>
"""

    # Down Solutions Section
    html += f"""
    <h2 id="down-solutions">Complete Down Solutions with Hints</h2>
    <p>Below are all the answers for today's Down clues, along with helpful hints to understand each solution better.</p>
"""

    for number, clue, answer in down_clues:
        hints = generate_hints(answer)
        html += f"""
    <h3>{number} Down: {clean_text(clue)}</h3>
    <p><strong>Answer:</strong> {clean_text(answer)}</p>
    <ul>
"""
        for hint in hints:
            html += f"        <li>{clean_text(hint)}</li>\n"
        
        html += "    </ul>\n"
        
        # Add internal link occasionally
        if random.random() < 0.2 and internal_links:
            html += f'    <p>Find more clues like this in our <a href="{random.choice(internal_links)}">crossword collection</a>.</p>\n'

    # Solving Tips Section
    html += f"""
    <h2 id="solving-tips">Tips for Solving Down Clues</h2>
    <ol>
        <li><strong>Start with shorter words:</strong> 3-letter and 4-letter Down clues are often easier to solve first</li>
        <li><strong>Use crossing letters:</strong> Down clues intersect with Across clues, giving you helpful letters</li>
        <li><strong>Look for patterns:</strong> Common endings like -ING, -ED, or -ER can help with vertical words</li>
        <li><strong>Consider word breaks:</strong> Vertical phrases might break naturally at certain points</li>
        <li><strong>Check theme connections:</strong> Down clues often relate to the puzzle's overall theme</li>
    </ol>
"""

    # Add more internal links
    if internal_links:
        html += f"""
    <h2>Master Your Crossword Skills</h2>
    <p>Improve your solving speed with our <a href="{random.choice(internal_links)}">advanced solving techniques</a>. For beginners, start with our <a href="{random.choice(internal_links)}">crossword basics guide</a>.</p>
"""

    # Statistics section
    html += f"""
    <h2>Today's Down Clues Statistics</h2>
    <ul>
        <li>Total Down clues: {down_count}</li>
        <li>Puzzle date: {date.strftime('%A, %B %d, %Y')}</li>
        <li>Difficulty: Standard NYT level</li>
        <li>Grid orientation: Vertical (top to bottom)</li>
    </ul>
"""

    # Related Resources
    html += f"""
    <h2 id="related-puzzles">Related Puzzle Resources</h2>
    <p>Continue improving your crossword skills with these resources:</p>
    <ul>
"""
    
    if internal_links:
        for i, link in enumerate(internal_links[:5]):
            resource_names = [
                "Previous puzzle solutions",
                "Crossword terminology guide",
                "Common crossword patterns",
                "Puzzle solving strategies",
                "Daily puzzle archive"
            ]
            html += f'        <li><a href="{link}">{resource_names[i % 5]}</a></li>\n'
    
    html += """
    </ul>
"""

    # Footer with image
    html += f"""
    <h2>About Today's Down Clues</h2>
    <figure>
        <img src="{image_url}"
             alt="NYT Down clues solutions for {date.strftime('%B %d, %Y')}"
             title="Complete vertical answers for today's NYT Crossword"
             loading="lazy"
             width="800"
             height="600">
        <figcaption>Today's NYT Down Clues - All {down_count} Vertical Solutions</figcaption>
    </figure>
    <p>This complete guide to NYT Down clues for {date.strftime('%B %d, %Y')} includes all {down_count} vertical answers. Down clues are an essential part of the crossword grid, running from top to bottom and intersecting with Across clues to create the complete puzzle solution.</p>
    
    <p>Remember, solving Down clues becomes easier when you work them together with Across clues, as the intersecting letters provide valuable hints for both directions.</p>
"""

    # Add final internal links
    if internal_links:
        html += f"""
    <p>Explore more puzzles in our <a href="{random.choice(internal_links)}">complete archive</a> or check <a href="{random.choice(internal_links)}">tomorrow's puzzle preview</a>.</p>
"""


    
    return html

def send_email(subject: str, html_content: str) -> bool:
    """Send email with HTML content"""
    try:
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = EMAIL_CONFIG['sender_email']
        message["To"] = EMAIL_CONFIG['recipient_email']
        
        html_part = MIMEText(html_content, "html")
        message.attach(html_part)
        
        context = ssl.create_default_context()
        
        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
            server.starttls(context=context)
            server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
            server.send_message(message)
        
        logger.info(f"Email sent successfully with subject: {subject}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False

def main():
    """Main function to process Down clues and send email"""
    try:
        # Get today's date
        today = datetime.now()
        
        logger.info(f"Processing NYT Down clues for {today.strftime('%Y-%m-%d')}")
        
        # Fetch crossword data
        crossword_data = fetch_crossword_data(today)
        
        # Create HTML content for Down clues only
        html_content = create_down_html(today, crossword_data)
        
        # Create email subject
        subject = f"NYT Down Clues - {today.strftime('%B %d, %Y')} - All Vertical Solutions"
        
        # Send email
        if send_email(subject, html_content):
            logger.info("Down clues blog post sent successfully!")
        else:
            logger.error("Failed to send Down clues blog post")
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
