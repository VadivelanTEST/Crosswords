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

# Download wordnet
nltk.download('wordnet')

# Function to get synonyms
def get_synonyms(word):
    synonyms = set()
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            synonyms.add(lemma.name())
    return list(synonyms)

# Function to get antonyms
def get_antonyms(word):
    antonyms = set()
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            if lemma.antonyms():
                antonyms.add(lemma.antonyms()[0].name())
    return list(antonyms)

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
            <h1 itemprop="headline">XWordHint Crossword Complete Solution: {date.strftime('%B %d, %Y')}</h1>
            <p class="post-meta">Published on {date.strftime('%A, %B %d, %Y')} • Updated daily</p>
        </header>

        <section aria-label="Crossword Solution Overview">
            <p itemprop="description">Our expert breakdown helps you solve the {date.strftime('%B %d')} XWordHint crossword while expanding your vocabulary. Learn answer strategies and discover word connections.</p>
        </section>

        <section aria-label="Across Clues Solutions">
            <h2>Across Clues and Answers ({len(crossword_data['clues']['across'])})</h2>
            <div class="clue-group">"""

    for idx, (clue, answer) in enumerate(zip(crossword_data['clues']['across'], crossword_data['answers']['across']), 1):
        letter_count = len(answer.replace(" ", ""))
        synonyms = get_synonyms(answer)
        antonyms = get_antonyms(answer)

        html += f"""
                <div class="clue-item" itemscope itemtype="https://schema.org/Question">
                    <h3 class="clue-title">Clue #{idx}: <span itemprop="text">{clue}</span></h3>
                    <div class="clue-meta">
                        <span class="letter-count">{letter_count}-letter answer</span>
                        <span class="answer" itemscope itemtype="https://schema.org/Answer">
                            Answer: <a itemprop="text" href="/crossword-answers/{answer.lower().replace(' ', '-')}/">{answer}</a>
                        </span>
                    </div>"""

        if synonyms:
            html += f"""<div class="word-info">
                        <strong>Word Help:</strong>
                        <span class="synonyms"><strong>Synonyms: </strong>{", ".join(synonyms[:3])}</span>
                        {f'<br><span class="antonyms"><strong>Antonyms:</strong> {", ".join(antonyms[:2])}</span>' if antonyms else ''}
                    </div>"""

        html += """</div>"""

    html += f"""</div></section>

        <section aria-label="Across Clues Solutions">
            <h2>Across Clues and Answers ({len(crossword_data['clues']['across'])})</h2>
            <div class="clue-group">"""

    for idx, (clue, answer) in enumerate(zip(crossword_data['clues']['down'], crossword_data['answers']['down']), 1):
        letter_count = len(answer.replace(" ", ""))
        synonyms = get_synonyms(answer)
        antonyms = get_antonyms(answer)

        html += f"""
                <div class="clue-item" itemscope itemtype="https://schema.org/Question">
                    <h3 class="clue-title">Clue #{idx}: <span itemprop="text">{clue}</span></h3>
                    <div class="clue-meta">
                        <span class="letter-count">{letter_count}-letter answer</span>
                        <span class="answer" itemscope itemtype="https://schema.org/Answer">
                            Answer: <a itemprop="text" href="/crossword-answers/{answer.lower().replace(' ', '-')}/">{answer}</a>
                        </span>
                    </div>"""

        if synonyms:
            html += f"""<div class="word-info">
                    <strong>Word Help:</strong>
                    <span class="synonyms"><strong>Synonyms:</strong> {", ".join(synonyms[:3])}</span>
                    {f'<br><span class="antonyms"><strong>Antonyms:</strong> {", ".join(antonyms[:2])}</span>' if antonyms else ''}
                </div>"""

    # Similar structure for down clues
    # ... (repeat the clue-item structure for down clues)

    html += f"""</div></section>

        <section aria-label="Crossword Solving Tips">
            <h2>Expert Solving Strategies</h2>
            <ul class="tip-list">
                <li>Look for fill-in-the-blank clues first (they're often easiest)</li>
                <li>Watch for question marks indicating wordplay</li>
                <li>Check vowel patterns in partially solved words</li>
            </ul>
        </section>

        <section aria-label="Related Keywords">
            <h2 class="sr-only">Related Search Terms</h2>
            <div class="keyword-cloud">
                <span>NYT Crossword Help, </span>
                <span>Daily Puzzle Solutions, </span>
                <span>Crossword Answer Finder, </span>
                <span>{date.strftime('%B')} Crossword Answers</span>
            </div>
        </section>"""


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
    #url = "https://www.xwordinfo.com/JSON/Data.ashx?date=04/11/2025&format=text"
    crossword_date = datetime.now().strftime("%m/%d/%Y")  # Using today's date
    url = f"https://www.xwordinfo.com/JSON/Data.ashx?date={crossword_date}&format=text"
    crossword_data = fetch_crossword_data(url)

    if crossword_data:
        date_str = crossword_data['date']
        date = datetime.strptime(date_str, '%m/%d/%Y')
        title = f"XWordHint Crossword Answers {date.strftime('%B %d, %Y')} | Expert Breakdown & Tips"
        formatted_html = format_to_html(crossword_data, date)
        send_email("velanms1993.qrco@blogger.com", title, formatted_html)


# Execute the main function
if __name__ == "__main__":
    main()
    time.sleep(60)


