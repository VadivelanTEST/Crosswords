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
            <h2>Interactive Crossword Grid</h2>
            <p class="grid-instructions">Work on the puzzle using the clues below. This is a {rows}x{cols} grid.</p>
            <div class="simple-grid">
                <div class="grid-placeholder">
                    <div class="grid-info">
                        <h3>Puzzle Layout</h3>
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
                    <h4>How to Use This Puzzle:</h4>
                    <ul>
                        <li>Read the clues below to find the answers</li>
                        <li>Use our hints system for guidance</li>
                        <li>Cross-reference Across and Down clues</li>
                        <li>Reveal answers when you're ready!</li>
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
            <h2>Crossword Puzzle</h2>
            <div class="grid-fallback">
                <p><strong>Today's Puzzle Ready!</strong></p>
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
                <p class="puzzle-instruction">Use the clues and hints below to solve the puzzle!</p>
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
    # List of available images for random selection
    image_names = [
        "professional-crossword-solution-keyword-optimized.png",
        "professional-crossword-solution-search-engine-friendly.png",
        "professional-crossword-solution-content-marketing.png",
        "professional-crossword-solution-digital-strategy.png",
        "professional-crossword-solution-on-page-seo.png",
        "professional-crossword-solution-link-building.png",
        "professional-crossword-solution-organic-traffic.png",        
        "professional-crossword-solution-seo-audit.png",
        "professional-crossword-solution-page-speed-optimization.png",
        "professional-crossword-solution-meta-description.png",
        "professional-crossword-solution-keyword-density.png",
        "professional-crossword-solution-mobile-friendliness.png",
        "professional-crossword-solution-rich-snippets.png",
        "professional-crossword-solution-technical-seo.png",
        "professional-crossword-solution-site-architecture.png",
        "professional-crossword-solution-search-console.png",
        "professional-crossword-solution-local-seo.png",
        "professional-crossword-solution-seo-tools.png",
        "professional-crossword-solution-content-update.png",
        "professional-crossword-solution-rank-tracking.png",
        "professional-crossword-solution-schema-markup.png",
        "professional-crossword-solution-user-experience.png",
        "professional-crossword-solution-search-ranking.png",
        "professional-crossword-solution-seo-report.png",
        "professional-crossword-solution-google-analytics.png",
        "professional-crossword-solution-keyword-optimized-2.png",
        "professional-crossword-solution-search-engine-friendly-2.png",
        "professional-crossword-solution-content-marketing-2.png",
        "professional-crossword-solution-digital-strategy-2.png",
        "professional-crossword-solution-on-page-seo-2.png",
        "professional-crossword-solution-link-building-2.png",
        "professional-crossword-solution-organic-traffic-2.png",
        "professional-crossword-solution-backlink-analysis-2.png",
        "professional-crossword-solution-seo-audit-2.png",
        "professional-crossword-solution-page-speed-optimization-2.png",
        "professional-crossword-solution-meta-description-2.png",
        "professional-crossword-solution-keyword-density-2.png",
        "professional-crossword-solution-mobile-friendliness-2.png",
        "professional-crossword-solution-rich-snippets-2.png",
        "professional-crossword-solution-technical-seo-2.png",
        "professional-crossword-solution-site-architecture-2.png",
        "professional-crossword-solution-search-console-2.png",
        "professional-crossword-solution-local-seo-2.png",
        "professional-crossword-solution-seo-tools-2.png",
        "professional-crossword-solution-content-update-2.png",
        "professional-crossword-solution-rank-tracking-2.png",
        "professional-crossword-solution-schema-markup-2.png",
        "professional-crossword-solution-user-experience-2.png",
        "professional-crossword-solution-search-ranking-2.png",
        "professional-crossword-solution-seo-report-2.png",
        "professional-crossword-solution-google-analytics-2.png",
        "professional-crossword-solution-keyword-optimized-3.png",
        "professional-crossword-solution-search-engine-friendly-3.png",
        "professional-crossword-solution-content-marketing-3.png",
        "professional-crossword-solution-digital-strategy-3.png",
        "professional-crossword-solution-on-page-seo-3.png",
        "professional-crossword-solution-link-building-3.png",
        "professional-crossword-solution-organic-traffic-3.png",
        "professional-crossword-solution-backlink-analysis-3.png",
        "professional-crossword-solution-seo-audit-3.png",
        "professional-crossword-solution-page-speed-optimization-3.png",
        "professional-crossword-solution-meta-description-3.png",
        "professional-crossword-solution-keyword-density-3.png",
        "professional-crossword-solution-mobile-friendliness-3.png",
        "professional-crossword-solution-rich-snippets-3.png",
        "professional-crossword-solution-technical-seo-3.png",
        "professional-crossword-solution-site-architecture-3.png",
        "professional-crossword-solution-search-console-3.png",
        "professional-crossword-solution-local-seo-3.png",
        "professional-crossword-solution-seo-tools-3.png",
        "professional-crossword-solution-content-update-3.png",
        "professional-crossword-solution-rank-tracking-3.png",
        "professional-crossword-solution-schema-markup-3.png",
        "professional-crossword-solution-user-experience-3.png",
        "professional-crossword-solution-search-ranking-3.png",
        "professional-crossword-solution-seo-report-3.png",
        "professional-crossword-solution-google-analytics-3.png",
        "professional-crossword-solution-keyword-optimized-4.png",
        "professional-crossword-solution-search-engine-friendly-4.png",
        "professional-crossword-solution-content-marketing-4.png",
        "professional-crossword-solution-digital-strategy-4.png",
        "professional-crossword-solution-on-page-seo-4.png",
        "professional-crossword-solution-link-building-4.png",
        "professional-crossword-solution-organic-traffic-4.png",
        "professional-crossword-solution-backlink-analysis-4.png",
        "professional-crossword-solution-seo-audit-4.png",
        "professional-crossword-solution-page-speed-optimization-4.png",
        "professional-crossword-solution-meta-description-4.png",
        "professional-crossword-solution-keyword-density-4.png",
        "professional-crossword-solution-mobile-friendliness-4.png",
        "professional-crossword-solution-rich-snippets-4.png",
        "professional-crossword-solution-technical-seo-4.png",
        "professional-crossword-solution-site-architecture-4.png",
        "professional-crossword-solution-search-console-4.png",
        "professional-crossword-solution-local-seo-4.png",
        "professional-crossword-solution-seo-tools-4.png",
        "professional-crossword-solution-content-update-4.png",
        "professional-crossword-solution-rank-tracking-4.png",
        "professional-crossword-solution-schema-markup-4.png",
        "professional-crossword-solution-user-experience-4.png",
        "professional-crossword-solution-search-ranking-4.png",
        "professional-crossword-solution-seo-report-4.png",
        "professional-crossword-solution-google-analytics-4.png",
        "professional-crossword-solution-keyword-optimized-5.png",
        "professional-crossword-solution-search-engine-friendly-5.png",
        "professional-crossword-solution-content-marketing-5.png",
        "professional-crossword-solution-digital-strategy-5.png",
        "professional-crossword-solution-on-page-seo-5.png",
        "professional-crossword-solution-link-building-5.png",
        "professional-crossword-solution-organic-traffic-5.png",
        "professional-crossword-solution-backlink-analysis-5.png",
        "professional-crossword-solution-seo-audit-5.png",
        "professional-crossword-solution-page-speed-optimization-5.png",
        "professional-crossword-solution-meta-description-5.png",
        "professional-crossword-solution-keyword-density-5.png",
        "professional-crossword-solution-mobile-friendliness-5.png",
        "professional-crossword-solution-rich-snippets-5.png",
        "professional-crossword-solution-technical-seo-5.png",
        "professional-crossword-solution-site-architecture-5.png",
        "professional-crossword-solution-search-console-5.png",
        "professional-crossword-solution-local-seo-5.png",
        "professional-crossword-solution-seo-tools-5.png",
        "professional-crossword-solution-content-update-5.png",
        "professional-crossword-solution-rank-tracking-5.png",
        "professional-crossword-solution-schema-markup-5.png",
        "professional-crossword-solution-user-experience-5.png",
        "professional-crossword-solution-search-ranking-5.png",
        "professional-crossword-solution-seo-report-5.png",
        "professional-crossword-solution-google-analytics-5.png",
        "professional-crossword-solution-keyword-optimized-6.png",
        "professional-crossword-solution-search-engine-friendly-6.png",
        "professional-crossword-solution-content-marketing-6.png",
        "professional-crossword-solution-digital-strategy-6.png",
        "professional-crossword-solution-on-page-seo-6.png",
        "professional-crossword-solution-link-building-6.png",
        "professional-crossword-solution-organic-traffic-6.png",
        "professional-crossword-solution-backlink-analysis-6.png",
        "professional-crossword-solution-seo-audit-6.png",
        "professional-crossword-solution-page-speed-optimization-6.png",
        "professional-crossword-solution-meta-description-6.png",
        "professional-crossword-solution-keyword-density-6.png",
        "professional-crossword-solution-mobile-friendliness-6.png",
        "professional-crossword-solution-rich-snippets-6.png",
        "professional-crossword-solution-technical-seo-6.png",
        "professional-crossword-solution-site-architecture-6.png",
        "professional-crossword-solution-search-console-6.png",
        "professional-crossword-solution-local-seo-6.png",
        "professional-crossword-solution-seo-tools-6.png",
        "professional-crossword-solution-content-update-6.png",
        "professional-crossword-solution-rank-tracking-6.png",
        "professional-crossword-solution-schema-markup-6.png",
        "professional-crossword-solution-user-experience-6.png",
        "professional-crossword-solution-search-ranking-6.png",
        "professional-crossword-solution-seo-report-6.png",
        "professional-crossword-solution-google-analytics-6.png",
        "professional-crossword-solution-keyword-optimized-7.png",
        "professional-crossword-solution-search-engine-friendly-7.png",
        "professional-crossword-solution-content-marketing-7.png",
        "professional-crossword-solution-digital-strategy-7.png",
        "professional-crossword-solution-on-page-seo-7.png",
        "professional-crossword-solution-link-building-7.png",
        "professional-crossword-solution-organic-traffic-7.png",
        "professional-crossword-solution-backlink-analysis-7.png",
        "professional-crossword-solution-seo-audit-7.png",
        "professional-crossword-solution-page-speed-optimization-7.png",
        "professional-crossword-solution-meta-description-7.png",
        "professional-crossword-solution-keyword-density-7.png",
        "professional-crossword-solution-mobile-friendliness-7.png",
        "professional-crossword-solution-rich-snippets-7.png",
        "professional-crossword-solution-technical-seo-7.png",
        "professional-crossword-solution-site-architecture-7.png",
        "professional-crossword-solution-search-console-7.png",
        "professional-crossword-solution-local-seo-7.png",
        "professional-crossword-solution-seo-tools-7.png",
        "professional-crossword-solution-content-update-7.png",
        "professional-crossword-solution-rank-tracking-7.png",
        "professional-crossword-solution-schema-markup-7.png",
        "professional-crossword-solution-user-experience-7.png",
        "professional-crossword-solution-search-ranking-7.png",
        "professional-crossword-solution-seo-report-7.png",
        "professional-crossword-solution-google-analytics-7.png",
        "professional-crossword-solution-keyword-optimized-8.png",
        "professional-crossword-solution-search-engine-friendly-8.png",
        "professional-crossword-solution-content-marketing-8.png",
        "professional-crossword-solution-digital-strategy-8.png",
        "professional-crossword-solution-on-page-seo-8.png",
        "professional-crossword-solution-link-building-8.png",
        "professional-crossword-solution-organic-traffic-8.png",
        "professional-crossword-solution-backlink-analysis-8.png",
        "professional-crossword-solution-seo-audit-8.png",
        "professional-crossword-solution-page-speed-optimization-8.png",
        "professional-crossword-solution-meta-description-8.png",
        "professional-crossword-solution-keyword-density-8.png",
        "professional-crossword-solution-mobile-friendliness-8.png",
        "professional-crossword-solution-rich-snippets-8.png",
        "professional-crossword-solution-technical-seo-8.png",
        "professional-crossword-solution-site-architecture-8.png",
        "professional-crossword-solution-search-console-8.png",
        "professional-crossword-solution-local-seo-8.png",
        "professional-crossword-solution-seo-tools-8.png",
        "professional-crossword-solution-content-update-8.png",
        "professional-crossword-solution-rank-tracking-8.png",
        "professional-crossword-solution-schema-markup-8.png",
        "professional-crossword-solution-user-experience-8.png",
        "professional-crossword-solution-search-ranking-8.png",
        "professional-crossword-solution-seo-report-8.png",
        "professional-crossword-solution-google-analytics-8.png",
        "professional-crossword-solution-keyword-optimized-9.png",
        "professional-crossword-solution-search-engine-friendly-9.png",
        "professional-crossword-solution-content-marketing-9.png",
        "professional-crossword-solution-digital-strategy-9.png",
        "professional-crossword-solution-on-page-seo-9.png",
        "professional-crossword-solution-link-building-9.png",
        "professional-crossword-solution-organic-traffic-9.png",
        "professional-crossword-solution-backlink-analysis-9.png",
        "professional-crossword-solution-seo-audit-9.png",
        "professional-crossword-solution-page-speed-optimization-9.png",
        "professional-crossword-solution-meta-description-9.png",
        "professional-crossword-solution-keyword-density-9.png",
        "professional-crossword-solution-mobile-friendliness-9.png",
        "professional-crossword-solution-rich-snippets-9.png",
        "professional-crossword-solution-technical-seo-9.png",
        "professional-crossword-solution-site-architecture-9.png",
        "professional-crossword-solution-search-console-9.png",
        "professional-crossword-solution-local-seo-9.png",
        "professional-crossword-solution-seo-tools-9.png",
        "professional-crossword-solution-content-update-9.png",
        "professional-crossword-solution-rank-tracking-9.png",
        "professional-crossword-solution-schema-markup-9.png",
        "professional-crossword-solution-user-experience-9.png",
        "professional-crossword-solution-search-ranking-9.png",
        "professional-crossword-solution-seo-report-9.png",
        "professional-crossword-solution-google-analytics-9.png",
        "professional-crossword-solution-keyword-optimized-10.png",
        "professional-crossword-solution-search-engine-friendly-10.png",
        "professional-crossword-solution-content-marketing-10.png",
        "professional-crossword-solution-digital-strategy-10.png",
        "professional-crossword-solution-on-page-seo-10.png",
        "professional-crossword-solution-link-building-10.png",
        "professional-crossword-solution-organic-traffic-10.png",
        "professional-crossword-solution-backlink-analysis-10.png",
        "professional-crossword-solution-seo-audit-10.png",
        "professional-crossword-solution-page-speed-optimization-10.png",
        "professional-crossword-solution-meta-description-10.png",
        "professional-crossword-solution-keyword-density-10.png",
        "professional-crossword-solution-mobile-friendliness-10.png",
        "professional-crossword-solution-rich-snippets-10.png",
        "professional-crossword-solution-technical-seo-10.png",
        "professional-crossword-solution-site-architecture-10.png",
        "professional-crossword-solution-search-console-10.png",
        "professional-crossword-solution-local-seo-10.png",
        "professional-crossword-solution-seo-tools-10.png",
        "professional-crossword-solution-content-update-10.png",
        "professional-crossword-solution-rank-tracking-10.png",
        "professional-crossword-solution-schema-markup-10.png",
        "professional-crossword-solution-user-experience-10.png",
        "professional-crossword-solution-search-ranking-10.png",
        "professional-crossword-solution-seo-report-10.png",
        "professional-crossword-solution-google-analytics-10.png"
    ]    
    # Select a random image
    selected_image = random.choice(image_names)
    image_url = f"https://raw.githubusercontent.com/xwordhint/answer/main/{selected_image}"
    
    # Day of week for SEO
    day_name = date.strftime('%A')
    
    html = f"""    
        <section aria-label="Crossword Solution Overview">
            <p itemprop="description">Master today's NYT crossword with our expert hint system. We provide synonyms, antonyms, and strategic clues to help you solve without spoiling the fun. Perfect for crossword lovers who want that satisfying "aha!" moment.</p>
        </section>
        
        <h2>Quick Navigation - Table of Contents</h2>
        <ul>
            <li><a href="#puzzle-difficulty">Today's Puzzle Difficulty</a></li>
            <li><a href="#across-table">Across Clues Table ({len(crossword_data['clues']['across'])} clues)</a></li>
            <li><a href="#across-hints">Across Clues - Detailed Hints</a></li>
            <li><a href="#down-table">Down Clues Table ({len(crossword_data['clues']['down'])} clues)</a></li>
            <li><a href="#down-hints">Down Clues - Detailed Hints</a></li>
            <li><a href="#solving-strategies">Expert Solving Strategies</a></li>
            <li><a href="#puzzle-stats">Today's Puzzle Statistics</a></li>
        </ul>
        
        <div class="separator" style="clear: both; text-align: center;">
            <a href="{image_url}" style="margin-left: 1em; margin-right: 1em;">
                <img alt="{date.strftime('%B %d, %Y')} NYT Crossword Solutions" border="0" data-original-height="514" data-original-width="509" height="320" src="{image_url}" title="{date.strftime('%B %d, %Y')} NYT Crossword Solutions" width="317" />
            </a>
        </div>
        
        <div class="difficulty-indicator">
            <h2>Today's Puzzle Difficulty: {random.choice(['Moderate', 'Challenging', 'Medium', 'Tricky'])}</h2>
            <p><strong>Pro Tip:</strong> Start with the fill-in-the-blank clues - they're usually the easiest entry points!</p>
        </div>

        <section id="across-table" aria-label="Across Clues Table">
            <h2>Across Clues - Complete List</h2>
            <table border="1">
                <tr>
                    <th>No.</th>
                    <th>Clue</th>
                    <th>Letters</th>
                </tr>"""
    
    # Create table for Across clues
    for idx, (clue, answer) in enumerate(zip(crossword_data['clues']['across'], crossword_data['answers']['across']), 1):
        letter_count = len(answer.replace(" ", ""))
        html += f"""
                <tr>
                    <td>{idx}A</td>
                    <td>{clue}</td>
                    <td>{letter_count}</td>
                </tr>"""
    
    html += """
            </table>
        </section>

        <section id="across-hints" aria-label="Across Clues Hints">
            <h2>Across Clues - Strategic Hints ({len(crossword_data['clues']['across'])} clues)</h2>
            <div class="clue-group">"""

    for idx, (clue, answer) in enumerate(zip(crossword_data['clues']['across'], crossword_data['answers']['across']), 1):
        letter_count = len(answer.replace(" ", ""))
        hints = generate_hint_text(answer, clue)
        
        html += f"""
                <div class="clue-item" itemscope itemtype="https://schema.org/Question">
                    <h3 class="clue-title">{idx}A: <span itemprop="text">"{clue}"</span></h3>
                    <div class="clue-meta">
                        <span class="letter-count"> {letter_count} letters</span>
                        <span class="theme-hint">Category: {random.choice(['General Knowledge', 'Wordplay', 'Common Word', 'Proper Noun', 'Abbreviation'])}</span>
                    </div>
                    <div class="hint-section">
                        <h4>Solving Hints:</h4>
                        <ul class="hint-list">"""
        
        for hint in hints[:3]:  # Show max 3 hints
            html += f"<li>{hint}</li>"
        
        html += f"""</ul>
        
                        <details class="answer-reveal">
                            <summary>Click to reveal answer (spoiler alert!)</summary>
                            <div class="answer-container">
                                <strong>Answer:</strong> <span class="answer-text">{answer}</span>
                                <p class="answer-explanation"><em>Remember this word for future puzzles!</em></p>
                            </div>
                        </details>
                    </div>
                </div>"""

    html += f"""</div>
        </section>

        <section id="down-table" aria-label="Down Clues Table">
            <h2>Down Clues - Complete List</h2>
            <table border="1">
                <tr>
                    <th>No.</th>
                    <th>Clue</th>
                    <th>Letters</th>
                </tr>"""
    
    # Create table for Down clues
    for idx, (clue, answer) in enumerate(zip(crossword_data['clues']['down'], crossword_data['answers']['down']), 1):
        letter_count = len(answer.replace(" ", ""))
        html += f"""
                <tr>
                    <td>{idx}D</td>
                    <td>{clue}</td>
                    <td>{letter_count}</td>
                </tr>"""
    
    html += """
            </table>
        </section>

        <section id="down-hints" aria-label="Down Clues Hints">
            <h2>Down Clues - Strategic Hints ({len(crossword_data['clues']['down'])} clues)</h2>
            <div class="clue-group">"""

    for idx, (clue, answer) in enumerate(zip(crossword_data['clues']['down'], crossword_data['answers']['down']), 1):
        letter_count = len(answer.replace(" ", ""))
        hints = generate_hint_text(answer, clue)
        
        html += f"""
                <div class="clue-item" itemscope itemtype="https://schema.org/Question">
                    <h3 class="clue-title"> {idx}D: <span itemprop="text">"{clue}"</span></h3>
                    <div class="clue-meta">
                        <span class="letter-count"> {letter_count} letters</span>
                        <span class="theme-hint">💭 Category: {random.choice(['General Knowledge', 'Wordplay', 'Common Word', 'Proper Noun', 'Abbreviation'])}</span>
                    </div>
                    <div class="hint-section">
                        <h4>Solving Hints:</h4>
                        <ul class="hint-list">"""
        
        for hint in hints[:3]:  # Show max 3 hints
            html += f"<li>{hint}</li>"
        
        html += f"""</ul>
        
                        <details class="answer-reveal">
                            <summary> Click to reveal answer (spoiler alert!)</summary>
                            <div class="answer-container">
                                <strong>Answer:</strong> <span class="answer-text">{answer}</span>
                                <p class="answer-explanation"><em>Remember this word for future puzzles!</em></p>
                            </div>
                        </details>
                    </div>
                </div>"""

    html += f"""</div>
        </section>

        <section id="solving-strategies" aria-label="Crossword Solving Strategies">
            <h2>Expert Solving Strategies</h2>
            <div class="strategy-grid">
                <div class="strategy-item">
                    <h3>Start Smart</h3>
                    <p>Begin with fill-in-the-blank clues and short 3-4 letter words. These are your foundation.</p>
                </div>
                <div class="strategy-item">
                    <h3>Decode the Clues</h3>
                    <p>Question marks indicate wordplay or puns. "Maybe" suggests multiple interpretations.</p>
                </div>
                <div class="strategy-item">
                    <h3>Use Cross-References</h3>
                    <p>Let intersecting letters guide you. One correct answer unlocks several others.</p>
                </div>
                <div class="strategy-item">
                    <h3>Build Vocabulary</h3>
                    <p>Common crossword words repeat. Learning them speeds up future solving.</p>
                </div>
            </div>
        </section>

        <section id="puzzle-stats" aria-label="Daily Crossword Stats">
            <h2>Today's Puzzle Stats</h2>
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
            <h2>More NYT Crossword Help</h2>
            <p>Looking for more puzzle solutions? Check out our comprehensive archive of NYT crossword hints and answers. We update daily with expert analysis and solving strategies.</p>
            <ul class="archive-links">
                <li><a href="/search/label/puzzle%20solutions">Complete NYT Crossword Archive</a></li>
                <li><a href="/search/label/Daily%20Puzzle">Advanced Solving Techniques</a></li>
                <li><a href="/search/label/NYT%20Clues">Common Crossword Words</a></li>
            </ul>
        </section>

        <footer>
            <p><strong>Disclaimer:</strong> Crossword clues and grid © The New York Times. This site provides hints and educational content for puzzle enthusiasts. XWordHint is not affiliated with The New York Times.</p>
            <p class="update-info">Last updated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        </footer>
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
        title = f"XWordHint Crossword Answers {date.strftime('%B %d, %Y')} | Expert Breakdown & Tips"
        formatted_html = format_to_html(crossword_data, date)
        send_email("velanms1993.qrco@blogger.com", title, formatted_html)
        print(f"Email sent successfully for {date.strftime('%B %d, %Y')} crossword!")

# Execute the main function
if __name__ == "__main__":
    main()
    
