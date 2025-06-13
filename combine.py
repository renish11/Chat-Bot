import json
import os
import re
import requests
from bs4 import BeautifulSoup
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords, wordnet
from nltk.stem import WordNetLemmatizer
from googlesearch import search
import uuid
import time
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import random
from collections import defaultdict

# Download NLTK resources
nltk.download('punkt', quiet=True)
nltk.download('wordnet', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)

# Configuration
CONFIG = {
    'max_search_results': 10,
    'max_paragraphs_per_site': 2,
    'max_pages_per_site': 1,
    'min_paragraph_length': 50,
    'keyword_match_ratio': 0.7,
    'alpha_char_ratio': 0.7,
    'cache_dir': 'database',
    'search_pause': 0.5,
    'num_results': 10,
    'request_timeout': 5,
    'topic_relevance_threshold': 0.5,
    'max_workers': 4,
    'max_summary_sentences': 2
}

# Initialize NLTK
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))
keyword_cache = {}
used_paragraphs = defaultdict(list)  # Track used paragraphs per query

def hash_query(query):
    """Generate a consistent hash for the query."""
    return hashlib.md5(query.lower().encode('utf-8')).hexdigest()

def normalize_query(query):
    """Convert query to a slug based on nouns or named entities."""
    tokens = word_tokenize(query.lower())
    pos_tags = nltk.pos_tag(tokens)
    nouns = [token for token, pos in pos_tags if pos.startswith('NN') or pos in ('JJ', 'VB')]
    if not nouns:
        nouns = tokens
    slug = '-'.join(nouns)
    slug = re.sub(r'[^a-z0-9\-]', '', slug)
    return slug if slug else 'query-' + str(uuid.uuid4())[:8]

def get_query_keywords(query):
    """Extract lemmatized keywords, using cache."""
    query_hash = hash_query(query)
    if query_hash in keyword_cache:
        return keyword_cache[query_hash]
    tokens = word_tokenize(query.lower())
    keywords = [lemmatizer.lemmatize(token) for token in tokens if token.isalpha() and token not in stop_words]
    keyword_cache[query_hash] = keywords
    return keywords

def clean_text(text):
    """Clean extracted text."""
    text = re.sub(r'(access denied|captcha|advertisement|subscribe now|log in)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def is_relevant_paragraph(paragraph, query_keywords):
    """Check if paragraph is relevant based on keyword overlap."""
    if len(paragraph) < CONFIG['min_paragraph_length']:
        return False, 0
    alpha_count = sum(1 for c in paragraph if c.isalpha())
    alpha_ratio = alpha_count / len(paragraph) if len(paragraph) > 0 else 0
    if alpha_ratio < CONFIG['alpha_char_ratio']:
        return False, 0
    tokens = word_tokenize(paragraph.lower())
    lemmatized = [lemmatizer.lemmatize(token) for token in tokens if token.isalpha() and token not in stop_words]
    if not lemmatized:
        return False, 0
    matches = len(set(query_keywords) & set(lemmatized))
    match_ratio = matches / len(set(query_keywords)) if query_keywords else 0
    is_definition = paragraph.lower().startswith(('is ', 'refers to ', 'means ', 'defined as '))
    return (match_ratio >= CONFIG['keyword_match_ratio'] or is_definition), match_ratio

def summarize_text(text, query_keywords, max_sentences=2):
    """Summarize text to 1–2 sentences, prioritizing sentences with query keywords."""
    sentences = sent_tokenize(text)
    if not sentences:
        return text
    # Score sentences based on keyword overlap
    scored_sentences = []
    for sentence in sentences:
        tokens = word_tokenize(sentence.lower())
        lemmatized = [lemmatizer.lemmatize(token) for token in tokens if token.isalpha() and token not in stop_words]
        matches = len(set(query_keywords) & set(lemmatized))
        score = matches / len(set(query_keywords)) if query_keywords else 0
        scored_sentences.append((sentence, score))
    # Sort by score and select top sentences
    scored_sentences.sort(key=lambda x: x[1], reverse=True)
    selected = [s[0] for s in scored_sentences[:min(max_sentences, len(scored_sentences))]]
    return ' '.join(selected) if selected else text[:200]

def extract_text(data, texts=None):
    """Recursively extract text from JSON data."""
    if texts is None:
        texts = []
    if isinstance(data, str):
        cleaned = clean_text(data)
        if cleaned:
            texts.append(cleaned)
    elif isinstance(data, list):
        for item in data:
            extract_text(item, texts)
    elif isinstance(data, dict):
        for value in data.values():
            extract_text(value, texts)
    return texts

def load_cache(topic, query):
    """Load and parse cached JSON files, selecting a random unused relevant paragraph."""
    cache_dir = CONFIG['cache_dir']
    query_keywords = get_query_keywords(query)
    query_hash = hash_query(query)
    relevant_paragraphs = []

    for filename in os.listdir(cache_dir):
        if filename.endswith('.json') and topic.lower() in filename.lower().replace('_', '-'):
            try:
                with open(os.path.join(cache_dir, filename), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    paragraphs = extract_text(data)
                    for paragraph in paragraphs:
                        is_relevant, score = is_relevant_paragraph(paragraph, query_keywords)
                        if is_relevant and paragraph not in used_paragraphs[query_hash]:
                            relevant_paragraphs.append((paragraph, score))
            except Exception:
                continue

    if not relevant_paragraphs:
        return None
    # Sort by score and randomly select one from top-scoring paragraphs
    relevant_paragraphs.sort(key=lambda x: x[1], reverse=True)
    top_paragraphs = [p for p, s in relevant_paragraphs if s >= relevant_paragraphs[0][1] * 0.9]
    selected_paragraph = random.choice(top_paragraphs) if top_paragraphs else relevant_paragraphs[0][0]
    used_paragraphs[query_hash].append(selected_paragraph)
    # Summarize the selected paragraph
    return summarize_text(selected_paragraph, query_keywords, CONFIG['max_summary_sentences'])

def save_cache(topic, query, answer):
    """Save answer to JSON cache."""
    os.makedirs(CONFIG['cache_dir'], exist_ok=True)
    cache_file = os.path.join(CONFIG['cache_dir'], f'{topic}.json')
    data = {'query': query, 'answer': answer}
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_internal_links(soup, base_url, domain):
    """Extract limited internal links."""
    internal_links = set()
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        full_url = urljoin(base_url, href)
        parsed_url = urlparse(full_url)
        if parsed_url.netloc == domain and parsed_url.scheme in ('http', 'https'):
            internal_links.add(full_url)
        if len(internal_links) >= 2:
            break
    return list(internal_links)

def is_site_relevant(url, query_keywords):
    """Check site relevance using metadata."""
    try:
        response = requests.head(url, timeout=CONFIG['request_timeout'], allow_redirects=True)
        if response.status_code != 200:
            return False
        response = requests.get(url, timeout=CONFIG['request_timeout'])
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.title.get_text() if soup.title else ''
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        description = meta_desc.get('content', '') if meta_desc else ''
        url_path = urlparse(url).path
        combined_text = f"{title} {description} {url_path}".lower()
        tokens = word_tokenize(combined_text)
        lemmatized = [lemmatizer.lemmatize(token) for token in tokens if token.isalpha() and token not in stop_words]
        if not lemmatized:
            return False
        matches = len(set(query_keywords) & set(lemmatized))
        match_ratio = matches / len(set(query_keywords)) if query_keywords else 0
        return match_ratio >= CONFIG['topic_relevance_threshold']
    except Exception:
        return False

def scrape_site(url, query_keywords, visited_urls, query_hash):
    """Scrape a site and its internal links for relevant paragraphs."""
    relevant_paragraphs = []
    domain = urlparse(url).netloc
    pages_to_scrape = [url]
    pages_scraped = 0

    while pages_to_scrape and pages_scraped < CONFIG['max_pages_per_site']:
        current_url = pages_to_scrape.pop(0)
        if current_url in visited_urls:
            continue
        visited_urls.add(current_url)
        try:
            response = requests.get(current_url, timeout=CONFIG['request_timeout'])
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            paragraphs = soup.find_all('p')
            count = 0
            for p in paragraphs:
                text = clean_text(p.get_text())
                if text and is_relevant_paragraph(text, query_keywords)[0] and text not in used_paragraphs[query_hash]:
                    relevant_paragraphs.append(text)
                    count += 1
                    if count >= CONFIG['max_paragraphs_per_site']:
                        break
            if count < CONFIG['max_paragraphs_per_site']:
                internal_links = get_internal_links(soup, current_url, domain)
                pages_to_scrape.extend([link for link in internal_links if link not in visited_urls])
            pages_scraped += 1
            time.sleep(CONFIG['search_pause'])
        except Exception:
            continue
    return relevant_paragraphs

def scrape_web(query):
    """Scrape web, checking cache first."""
    topic = normalize_query(query)
    query_hash = hash_query(query)
    cached_answer = load_cache(topic, query)
    if cached_answer:
        return cached_answer

    query_keywords = get_query_keywords(query)
    visited_urls = set()
    urls = list(search(query, num_results=CONFIG['num_results'], sleep_interval=CONFIG['search_pause']))

    # Parallel relevance checking
    relevant_urls = []
    with ThreadPoolExecutor(max_workers=CONFIG['max_workers']) as executor:
        future_to_url = {executor.submit(is_site_relevant, url, query_keywords): url for url in urls}
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                if future.result():
                    relevant_urls.append(url)
            except Exception:
                continue

    # Parallel scraping
    relevant_paragraphs = []
    with ThreadPoolExecutor(max_workers=CONFIG['max_workers']) as executor:
        future_to_url = {executor.submit(scrape_site, url, query_keywords, visited_urls, query_hash): url for url in relevant_urls}
        for future in as_completed(future_to_url):
            try:
                paragraphs = future.result()
                relevant_paragraphs.extend(paragraphs)
            except Exception:
                continue
            time.sleep(CONFIG['search_pause'])

    if not relevant_paragraphs:
        return None
    # Randomly select a paragraph
    selected_paragraph = random.choice(relevant_paragraphs)
    used_paragraphs[query_hash].append(selected_paragraph)
    # Summarize the selected paragraph
    answer = summarize_text(selected_paragraph, query_keywords, CONFIG['max_summary_sentences'])
    save_cache(topic, query, answer)
    return answer

def main():
    """Main chatbot loop."""
    print("Bot: Hello! Ask me anything or type 'exit'/'quit' to stop.")
    while True:
        query = input("You: ").strip()
        if query.lower() in ('exit', 'quit'):
            print("Bot: Goodbye!")
            break
        if not query:
            print("Bot: Please enter a valid query.")
            continue

        answer = scrape_web(query)
        if answer:
            print(f"Bot: {answer}")
        else:
            print("Bot: [Info] No relevant content found.")

if __name__ == "__main__":
    main()