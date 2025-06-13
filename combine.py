# import json
# import os
# import re
# import requests
# from bs4 import BeautifulSoup
# import nltk
# from nltk.tokenize import word_tokenize, sent_tokenize
# from nltk.corpus import stopwords, wordnet
# from nltk.stem import WordNetLemmatizer
# from googlesearch import search
# import uuid
# import time
# from urllib.parse import urlparse, urljoin
# from concurrent.futures import ThreadPoolExecutor, as_completed
# import hashlib
# import random
# from collections import defaultdict

# # Download NLTK resources
# nltk.download('punkt', quiet=True)
# nltk.download('wordnet', quiet=True)
# nltk.download('stopwords', quiet=True)
# nltk.download('averaged_perceptron_tagger', quiet=True)

# # Configuration
# CONFIG = {
#     'max_search_results': 10,
#     'max_paragraphs_per_site': 2,
#     'max_pages_per_site': 1,
#     'min_paragraph_length': 50,
#     'keyword_match_ratio': 0.7,
#     'alpha_char_ratio': 0.7,
#     'cache_dir': 'database',
#     'search_pause': 0.5,
#     'num_results': 10,
#     'request_timeout': 5,
#     'topic_relevance_threshold': 0.5,
#     'max_workers': 4,
#     'max_summary_sentences': 2
# }

# # Initialize NLTK
# lemmatizer = WordNetLemmatizer()
# stop_words = set(stopwords.words('english'))
# keyword_cache = {}
# used_paragraphs = defaultdict(list)  # Track used paragraphs per query

# def hash_query(query):
#     """Generate a consistent hash for the query."""
#     return hashlib.md5(query.lower().encode('utf-8')).hexdigest()

# def normalize_query(query):
#     """Convert query to a slug based on nouns or named entities."""
#     tokens = word_tokenize(query.lower())
#     pos_tags = nltk.pos_tag(tokens)
#     nouns = [token for token, pos in pos_tags if pos.startswith('NN') or pos in ('JJ', 'VB')]
#     if not nouns:
#         nouns = tokens
#     slug = '-'.join(nouns)
#     slug = re.sub(r'[^a-z0-9\-]', '', slug)
#     return slug if slug else 'query-' + str(uuid.uuid4())[:8]

# def get_query_keywords(query):
#     """Extract lemmatized keywords, using cache."""
#     query_hash = hash_query(query)
#     if query_hash in keyword_cache:
#         return keyword_cache[query_hash]
#     tokens = word_tokenize(query.lower())
#     keywords = [lemmatizer.lemmatize(token) for token in tokens if token.isalpha() and token not in stop_words]
#     keyword_cache[query_hash] = keywords
#     return keywords

# def clean_text(text):
#     """Clean extracted text."""
#     text = re.sub(r'(access denied|captcha|advertisement|subscribe now|log in)', '', text, flags=re.IGNORECASE)
#     text = re.sub(r'\s+', ' ', text).strip()
#     return text

# def is_relevant_paragraph(paragraph, query_keywords):
#     """Check if paragraph is relevant based on keyword overlap."""
#     if len(paragraph) < CONFIG['min_paragraph_length']:
#         return False, 0
#     alpha_count = sum(1 for c in paragraph if c.isalpha())
#     alpha_ratio = alpha_count / len(paragraph) if len(paragraph) > 0 else 0
#     if alpha_ratio < CONFIG['alpha_char_ratio']:
#         return False, 0
#     tokens = word_tokenize(paragraph.lower())
#     lemmatized = [lemmatizer.lemmatize(token) for token in tokens if token.isalpha() and token not in stop_words]
#     if not lemmatized:
#         return False, 0
#     matches = len(set(query_keywords) & set(lemmatized))
#     match_ratio = matches / len(set(query_keywords)) if query_keywords else 0
#     is_definition = paragraph.lower().startswith(('is ', 'refers to ', 'means ', 'defined as '))
#     return (match_ratio >= CONFIG['keyword_match_ratio'] or is_definition), match_ratio

# def summarize_text(text, query_keywords, max_sentences=2):
#     """Summarize text to 1–2 sentences, prioritizing sentences with query keywords."""
#     sentences = sent_tokenize(text)
#     if not sentences:
#         return text
#     # Score sentences based on keyword overlap
#     scored_sentences = []
#     for sentence in sentences:
#         tokens = word_tokenize(sentence.lower())
#         lemmatized = [lemmatizer.lemmatize(token) for token in tokens if token.isalpha() and token not in stop_words]
#         matches = len(set(query_keywords) & set(lemmatized))
#         score = matches / len(set(query_keywords)) if query_keywords else 0
#         scored_sentences.append((sentence, score))
#     # Sort by score and select top sentences
#     scored_sentences.sort(key=lambda x: x[1], reverse=True)
#     selected = [s[0] for s in scored_sentences[:min(max_sentences, len(scored_sentences))]]
#     return ' '.join(selected) if selected else text[:200]

# def extract_text(data, texts=None):
#     """Recursively extract text from JSON data."""
#     if texts is None:
#         texts = []
#     if isinstance(data, str):
#         cleaned = clean_text(data)
#         if cleaned:
#             texts.append(cleaned)
#     elif isinstance(data, list):
#         for item in data:
#             extract_text(item, texts)
#     elif isinstance(data, dict):
#         for value in data.values():
#             extract_text(value, texts)
#     return texts

# def load_cache(topic, query):
#     """Load and parse cached JSON files, selecting a random unused relevant paragraph."""
#     cache_dir = CONFIG['cache_dir']
#     query_keywords = get_query_keywords(query)
#     query_hash = hash_query(query)
#     relevant_paragraphs = []

#     for filename in os.listdir(cache_dir):
#         if filename.endswith('.json') and topic.lower() in filename.lower().replace('_', '-'):
#             try:
#                 with open(os.path.join(cache_dir, filename), 'r', encoding='utf-8') as f:
#                     data = json.load(f)
#                     paragraphs = extract_text(data)
#                     for paragraph in paragraphs:
#                         is_relevant, score = is_relevant_paragraph(paragraph, query_keywords)
#                         if is_relevant and paragraph not in used_paragraphs[query_hash]:
#                             relevant_paragraphs.append((paragraph, score))
#             except Exception:
#                 continue

#     if not relevant_paragraphs:
#         return None
#     # Sort by score and randomly select one from top-scoring paragraphs
#     relevant_paragraphs.sort(key=lambda x: x[1], reverse=True)
#     top_paragraphs = [p for p, s in relevant_paragraphs if s >= relevant_paragraphs[0][1] * 0.9]
#     selected_paragraph = random.choice(top_paragraphs) if top_paragraphs else relevant_paragraphs[0][0]
#     used_paragraphs[query_hash].append(selected_paragraph)
#     # Summarize the selected paragraph
#     return summarize_text(selected_paragraph, query_keywords, CONFIG['max_summary_sentences'])

# def save_cache(topic, query, answer):
#     """Save answer to JSON cache."""
#     os.makedirs(CONFIG['cache_dir'], exist_ok=True)
#     cache_file = os.path.join(CONFIG['cache_dir'], f'{topic}.json')
#     data = {'query': query, 'answer': answer}
#     with open(cache_file, 'w', encoding='utf-8') as f:
#         json.dump(data, f, ensure_ascii=False, indent=2)

# def get_internal_links(soup, base_url, domain):
#     """Extract limited internal links."""
#     internal_links = set()
#     for a_tag in soup.find_all('a', href=True):
#         href = a_tag['href']
#         full_url = urljoin(base_url, href)
#         parsed_url = urlparse(full_url)
#         if parsed_url.netloc == domain and parsed_url.scheme in ('http', 'https'):
#             internal_links.add(full_url)
#         if len(internal_links) >= 2:
#             break
#     return list(internal_links)

# def is_site_relevant(url, query_keywords):
#     """Check site relevance using metadata."""
#     try:
#         response = requests.head(url, timeout=CONFIG['request_timeout'], allow_redirects=True)
#         if response.status_code != 200:
#             return False
#         response = requests.get(url, timeout=CONFIG['request_timeout'])
#         response.raise_for_status()
#         soup = BeautifulSoup(response.text, 'html.parser')
#         title = soup.title.get_text() if soup.title else ''
#         meta_desc = soup.find('meta', attrs={'name': 'description'})
#         description = meta_desc.get('content', '') if meta_desc else '' # type: ignore
#         url_path = urlparse(url).path
#         combined_text = f"{title} {description} {url_path}".lower()
#         tokens = word_tokenize(combined_text)
#         lemmatized = [lemmatizer.lemmatize(token) for token in tokens if token.isalpha() and token not in stop_words]
#         if not lemmatized:
#             return False
#         matches = len(set(query_keywords) & set(lemmatized))
#         match_ratio = matches / len(set(query_keywords)) if query_keywords else 0
#         return match_ratio >= CONFIG['topic_relevance_threshold']
#     except Exception:
#         return False

# def scrape_site(url, query_keywords, visited_urls, query_hash):
#     """Scrape a site and its internal links for relevant paragraphs."""
#     relevant_paragraphs = []
#     domain = urlparse(url).netloc
#     pages_to_scrape = [url]
#     pages_scraped = 0

#     while pages_to_scrape and pages_scraped < CONFIG['max_pages_per_site']:
#         current_url = pages_to_scrape.pop(0)
#         if current_url in visited_urls:
#             continue
#         visited_urls.add(current_url)
#         try:
#             response = requests.get(current_url, timeout=CONFIG['request_timeout'])
#             response.raise_for_status()
#             soup = BeautifulSoup(response.text, 'html.parser')
#             paragraphs = soup.find_all('p')
#             count = 0
#             for p in paragraphs:
#                 text = clean_text(p.get_text())
#                 if text and is_relevant_paragraph(text, query_keywords)[0] and text not in used_paragraphs[query_hash]:
#                     relevant_paragraphs.append(text)
#                     count += 1
#                     if count >= CONFIG['max_paragraphs_per_site']:
#                         break
#             if count < CONFIG['max_paragraphs_per_site']:
#                 internal_links = get_internal_links(soup, current_url, domain)
#                 pages_to_scrape.extend([link for link in internal_links if link not in visited_urls])
#             pages_scraped += 1
#             time.sleep(CONFIG['search_pause'])
#         except Exception:
#             continue
#     return relevant_paragraphs

# def scrape_web(query):
#     """Scrape web, checking cache first."""
#     topic = normalize_query(query)
#     query_hash = hash_query(query)
#     cached_answer = load_cache(topic, query)
#     if cached_answer:
#         return cached_answer

#     query_keywords = get_query_keywords(query)
#     visited_urls = set()
#     urls = list(search(query, num_results=CONFIG['num_results'], sleep_interval=CONFIG['search_pause']))

#     # Parallel relevance checking
#     relevant_urls = []
#     with ThreadPoolExecutor(max_workers=CONFIG['max_workers']) as executor:
#         future_to_url = {executor.submit(is_site_relevant, url, query_keywords): url for url in urls}
#         for future in as_completed(future_to_url):
#             url = future_to_url[future]
#             try:
#                 if future.result():
#                     relevant_urls.append(url)
#             except Exception:
#                 continue

#     # Parallel scraping
#     relevant_paragraphs = []
#     with ThreadPoolExecutor(max_workers=CONFIG['max_workers']) as executor:
#         future_to_url = {executor.submit(scrape_site, url, query_keywords, visited_urls, query_hash): url for url in relevant_urls}
#         for future in as_completed(future_to_url):
#             try:
#                 paragraphs = future.result()
#                 relevant_paragraphs.extend(paragraphs)
#             except Exception:
#                 continue
#             time.sleep(CONFIG['search_pause'])

#     if not relevant_paragraphs:
#         return None
#     # Randomly select a paragraph
#     selected_paragraph = random.choice(relevant_paragraphs)
#     used_paragraphs[query_hash].append(selected_paragraph)
#     # Summarize the selected paragraph
#     answer = summarize_text(selected_paragraph, query_keywords, CONFIG['max_summary_sentences'])
#     save_cache(topic, query, answer)
#     return answer

# def main():
#     """Main chatbot loop."""
#     print("Bot: Hello! Ask me anything or type 'exit'/'quit' to stop.")
#     while True:
#         query = input("You: ").strip()
#         if query.lower() in ('exit', 'quit'):
#             print("Bot: Goodbye!")
#             break
#         if not query:
#             print("Bot: Please enter a valid query.")
#             continue

#         answer = scrape_web(query)
#         if answer:
#             print(f"Bot: {answer}")
#         else:
#             print("Bot: [Info] No relevant content found.")

# if __name__ == "__main__":
#     main()











# import json
# import os
# import re
# import requests
# from bs4 import BeautifulSoup
# import nltk
# from nltk.tokenize import word_tokenize, sent_tokenize
# from nltk.corpus import stopwords
# from nltk.stem import WordNetLemmatizer
# from googlesearch import search
# import uuid
# import time
# from urllib.parse import urlparse, urljoin
# from concurrent.futures import ThreadPoolExecutor, as_completed
# import hashlib
# import random
# from collections import defaultdict

# # Download NLTK resources
# nltk.download('punkt', quiet=True)
# nltk.download('wordnet', quiet=True)
# nltk.download('stopwords', quiet=True)
# nltk.download('averaged_perceptron_tagger', quiet=True)

# # Configuration
# CONFIG = {
#     'max_search_results': 10,
#     'max_pages_per_site': 5,  # Increased to scrape more pages
#     'max_text_segments': 100,  # Max text segments to save per query
#     'min_text_length': 30,  # Reduced to include headings, list items
#     'keyword_match_ratio': 0.7,
#     'alpha_char_ratio': 0.7,
#     'cache_dir': 'database',
#     'search_pause': 0.5,
#     'num_results': 10,
#     'request_timeout': 5,
#     'topic_relevance_threshold': 0.5,
#     'max_workers': 4,
#     'max_summary_sentences': 2
# }

# # Initialize NLTK
# lemmatizer = WordNetLemmatizer()
# stop_words = set(stopwords.words('english'))
# keyword_cache = {}
# used_paragraphs = defaultdict(list)  # Track used paragraphs per query

# def hash_query(query):
#     """Generate a consistent hash for the query."""
#     return hashlib.md5(query.lower().encode('utf-8')).hexdigest()

# def normalize_query(query):
#     """Convert query to a slug based on nouns or named entities."""
#     tokens = word_tokenize(query.lower())
#     pos_tags = nltk.pos_tag(tokens)
#     nouns = [token for token, pos in pos_tags if pos.startswith('NN') or pos in ('JJ', 'VB')]
#     if not nouns:
#         nouns = tokens
#     slug = '-'.join(nouns)
#     slug = re.sub(r'[^a-z0-9\-]', '', slug)
#     return slug if slug else 'query-' + str(uuid.uuid4())[:8]

# def get_query_keywords(query):
#     """Extract lemmatized keywords, using cache."""
#     query_hash = hash_query(query)
#     if query_hash in keyword_cache:
#         return keyword_cache[query_hash]
#     tokens = word_tokenize(query.lower())
#     keywords = [lemmatizer.lemmatize(token) for token in tokens if token.isalpha() and token not in stop_words]
#     keyword_cache[query_hash] = keywords
#     return keywords

# def clean_text(text):
#     """Clean extracted text."""
#     text = re.sub(r'(access denied|captcha|advertisement|subscribe now|log in|navigation|footer)', '', text, flags=re.IGNORECASE)
#     text = re.sub(r'\s+', ' ', text).strip()
#     return text

# def is_relevant_text(text, query_keywords):
#     """Check if text is relevant based on keyword overlap."""
#     if len(text) < CONFIG['min_text_length']:
#         return False, 0
#     alpha_count = sum(1 for c in text if c.isalpha())
#     alpha_ratio = alpha_count / len(text) if len(text) > 0 else 0
#     if alpha_ratio < CONFIG['alpha_char_ratio']:
#         return False, 0
#     tokens = word_tokenize(text.lower())
#     lemmatized = [lemmatizer.lemmatize(token) for token in tokens if token.isalpha() and token not in stop_words]
#     if not lemmatized:
#         return False, 0
#     matches = len(set(query_keywords) & set(lemmatized))
#     match_ratio = matches / len(set(query_keywords)) if query_keywords else 0
#     is_definition = text.lower().startswith(('is ', 'refers to ', 'means ', 'defined as '))
#     return (match_ratio >= CONFIG['keyword_match_ratio'] or is_definition), match_ratio

# def summarize_text(text, query_keywords, max_sentences=2):
#     """Summarize text to 1–2 sentences, prioritizing sentences with query keywords."""
#     sentences = sent_tokenize(text)
#     if not sentences:
#         return text[:200]
#     scored_sentences = []
#     for sentence in sentences:
#         tokens = word_tokenize(sentence.lower())
#         lemmatized = [lemmatizer.lemmatize(token) for token in tokens if token.isalpha() and token not in stop_words]
#         matches = len(set(query_keywords) & set(lemmatized))
#         score = matches / len(set(query_keywords)) if query_keywords else 0
#         scored_sentences.append((sentence, score))
#     scored_sentences.sort(key=lambda x: x[1], reverse=True)
#     selected = [s[0] for s in scored_sentences[:min(max_sentences, len(scored_sentences))]]
#     return ' '.join(selected) if selected else text[:200]

# def extract_text_from_soup(soup):
#     """Extract all relevant text from a BeautifulSoup object."""
#     texts = []
#     # Extract paragraphs
#     for p in soup.find_all('p'):
#         text = clean_text(p.get_text())
#         if text:
#             texts.append(text)
#     # Extract headings
#     for h in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
#         text = clean_text(h.get_text())
#         if text:
#             texts.append(text)
#     # Extract list items
#     for li in soup.find_all('li'):
#         text = clean_text(li.get_text())
#         if text:
#             texts.append(text)
#     # Extract text from divs (common for article content)
#     for div in soup.find_all('div', class_=lambda x: x and 'content' in x.lower()):
#         text = clean_text(div.get_text())
#         if text:
#             texts.append(text)
#     return texts

# def get_internal_links(soup, base_url, domain, max_links=10):
#     """Extract internal links, limited to max_links."""
#     internal_links = set()
#     for a_tag in soup.find_all('a', href=True):
#         href = a_tag['href']
#         full_url = urljoin(base_url, href)
#         parsed_url = urlparse(full_url)
#         if parsed_url.netloc == domain and parsed_url.scheme in ('http', 'https'):
#             internal_links.add(full_url)
#         if len(internal_links) >= max_links:
#             break
#     return list(internal_links)

# def is_site_relevant(url, query_keywords):
#     """Check site relevance using metadata."""
#     try:
#         response = requests.head(url, timeout=CONFIG['request_timeout'], allow_redirects=True)
#         if response.status_code != 200:
#             return False
#         response = requests.get(url, timeout=CONFIG['request_timeout'])
#         response.raise_for_status()
#         soup = BeautifulSoup(response.text, 'html.parser')
#         title = soup.title.get_text() if soup.title else ''
#         meta_desc = soup.find('meta', attrs={'name': 'description'})
#         description = meta_desc.get('content', '') if meta_desc else ''
#         url_path = urlparse(url).path
#         combined_text = f"{title} {description} {url_path}".lower()
#         tokens = word_tokenize(combined_text)
#         lemmatized = [lemmatizer.lemmatize(token) for token in tokens if token.isalpha() and token not in stop_words]
#         if not lemmatized:
#             return False
#         matches = len(set(query_keywords) & set(lemmatized))
#         match_ratio = matches / len(set(query_keywords)) if query_keywords else 0
#         return match_ratio >= CONFIG['topic_relevance_threshold']
#     except Exception:
#         return False

# def scrape_site(url, query_keywords, visited_urls, query_hash):
#     """Scrape all content from a site and its internal links."""
#     all_texts = []
#     domain = urlparse(url).netloc
#     pages_to_scrape = [url]
#     pages_scraped = 0

#     while pages_to_scrape and pages_scraped < CONFIG['max_pages_per_site'] and len(all_texts) < CONFIG['max_text_segments']:
#         current_url = pages_to_scrape.pop(0)
#         if current_url in visited_urls:
#             continue
#         visited_urls.add(current_url)
#         try:
#             response = requests.get(current_url, timeout=CONFIG['request_timeout'])
#             response.raise_for_status()
#             soup = BeautifulSoup(response.text, 'html.parser')
#             texts = extract_text_from_soup(soup)
#             for text in texts:
#                 if is_relevant_text(text, query_keywords)[0] and text not in used_paragraphs[query_hash]:
#                     all_texts.append(text)
#             internal_links = get_internal_links(soup, current_url, domain)
#             pages_to_scrape.extend([link for link in internal_links if link not in visited_urls])
#             pages_scraped += 1
#             time.sleep(CONFIG['search_pause'])
#         except Exception:
#             continue
#     return all_texts

# def save_cache(topic, texts):
#     """Save scraped texts to JSON cache in the same structure as provided files."""
#     os.makedirs(CONFIG['cache_dir'], exist_ok=True)
#     cache_file = os.path.join(CONFIG['cache_dir'], f'{topic}.json')
#     with open(cache_file, 'w', encoding='utf-8') as f:
#         json.dump(texts, f, ensure_ascii=False, indent=2)

# def load_cache(topic, query):
#     """Load and parse cached JSON files, selecting a random unused relevant paragraph."""
#     cache_dir = CONFIG['cache_dir']
#     query_keywords = get_query_keywords(query)
#     query_hash = hash_query(query)
#     relevant_paragraphs = []

#     cache_file = os.path.join(cache_dir, f'{topic}.json')
#     if os.path.exists(cache_file):
#         try:
#             with open(cache_file, 'r', encoding='utf-8') as f:
#                 paragraphs = json.load(f)
#                 for paragraph in paragraphs:
#                     is_relevant, score = is_relevant_text(paragraph, query_keywords)
#                     if is_relevant and paragraph not in used_paragraphs[query_hash]:
#                         relevant_paragraphs.append((paragraph, score))
#         except Exception:
#             pass

#     if not relevant_paragraphs:
#         return None
#     relevant_paragraphs.sort(key=lambda x: x[1], reverse=True)
#     top_paragraphs = [p for p, s in relevant_paragraphs if s >= relevant_paragraphs[0][1] * 0.9]
#     selected_paragraph = random.choice(top_paragraphs) if top_paragraphs else relevant_paragraphs[0][0]
#     used_paragraphs[query_hash].append(selected_paragraph)
#     return summarize_text(selected_paragraph, query_keywords, CONFIG['max_summary_sentences'])

# def scrape_web(query):
#     """Scrape web, checking cache first, and save all scraped content."""
#     topic = normalize_query(query)
#     query_hash = hash_query(query)
#     cached_answer = load_cache(topic, query)
#     if cached_answer:
#         return cached_answer

#     query_keywords = get_query_keywords(query)
#     visited_urls = set()
#     urls = list(search(query, num_results=CONFIG['num_results'], sleep_interval=CONFIG['search_pause']))

#     # Parallel relevance checking
#     relevant_urls = []
#     with ThreadPoolExecutor(max_workers=CONFIG['max_workers']) as executor:
#         future_to_url = {executor.submit(is_site_relevant, url, query_keywords): url for url in urls}
#         for future in as_completed(future_to_url):
#             url = future_to_url[future]
#             try:
#                 if future.result():
#                     relevant_urls.append(url)
#             except Exception:
#                 continue

#     # Parallel scraping
#     all_texts = []
#     with ThreadPoolExecutor(max_workers=CONFIG['max_workers']) as executor:
#         future_to_url = {executor.submit(scrape_site, url, query_keywords, visited_urls, query_hash): url for url in relevant_urls}
#         for future in as_completed(future_to_url):
#             try:
#                 texts = future.result()
#                 all_texts.extend(texts)
#             except Exception:
#                 continue
#             time.sleep(CONFIG['search_pause'])

#     if not all_texts:
#         return None
#     # Save all scraped texts
#     all_texts = all_texts[:CONFIG['max_text_segments']]  # Limit total segments
#     save_cache(topic, all_texts)
#     # Select a random paragraph for the answer
#     relevant_paragraphs = [(text, is_relevant_text(text, query_keywords)[1]) for text in all_texts if is_relevant_text(text, query_keywords)[0]]
#     if not relevant_paragraphs:
#         return None
#     selected_paragraph = random.choice([p[0] for p in relevant_paragraphs])
#     used_paragraphs[query_hash].append(selected_paragraph)
#     answer = summarize_text(selected_paragraph, query_keywords, CONFIG['max_summary_sentences'])
#     return answer

# def main():
#     """Main chatbot loop."""
#     print("Bot: Hello! Ask me anything or type 'exit'/'quit' to stop.")
#     while True:
#         query = input("You: ").strip()
#         if query.lower() in ('exit', 'quit'):
#             print("Bot: Goodbye!")
#             break
#         if not query:
#             print("Bot: Please enter a valid query.")
#             continue

#         answer = scrape_web(query)
#         if answer:
#             print(f"Bot: {answer}")
#         else:
#             print("Bot: [Info] No relevant content found.")

# if __name__ == "__main__":
#     main()












import json
import os
import re
import requests
from bs4 import BeautifulSoup
from googlesearch import search
import uuid
import time
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import random
from collections import defaultdict

# Configuration
CONFIG = {
    'max_search_results': 20,
    'max_pages_per_site': 10,
    'max_text_segments': 100,
    'min_text_length': 30,
    'keyword_match_ratio': 0.7,
    'alpha_char_ratio': 0.7,
    'cache_dir': 'database',
    'search_pause': 1.0,
    'request_timeout': 5,
    'topic_relevance_threshold': 0.5,
    'max_workers': 4,
    'max_summary_sentences': 2
}

# User agents for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
]

# Initialize data structures
keyword_cache = {}
used_paragraphs = defaultdict(set)

def hash_query(query):
    """Generate a consistent hash for the query."""
    return hashlib.md5(query.lower().encode('utf-8')).hexdigest()

def normalize_query(query):
    """Convert query to a slug based on keywords."""
    tokens = query.lower().split()
    slug = '-'.join(tokens)
    slug = re.sub(r'[^a-z0-9\-]', '', slug)
    return slug if slug else 'query-' + str(uuid.uuid4())[:8]

def get_query_keywords(query):
    """Extract keywords from query."""
    query_hash = hash_query(query)
    if query_hash in keyword_cache:
        return keyword_cache[query_hash]
    tokens = query.lower().split()
    keywords = [token for token in tokens if token.isalpha()]
    keyword_cache[query_hash] = keywords
    return keywords

def clean_text(text):
    """Clean extracted text."""
    text = re.sub(r'(access denied|captcha|advertisement|subscribe now|log in|navigation|footer)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def levenshtein(s1, s2):
    """Compute Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

def is_relevant_text(text, query_keywords, threshold=0.8):
    """Check if text is relevant based on fuzzy keyword matching."""
    if len(text) < CONFIG['min_text_length'] or len(text) > 1000:
        return False, 0
    alpha_count = sum(1 for c in text if c.isalpha())
    alpha_ratio = alpha_count / len(text) if len(text) > 0 else 0
    if alpha_ratio < CONFIG['alpha_char_ratio']:
        return False, 0
    text_lower = text.lower()
    matches = sum(1 for kw in query_keywords if any(levenshtein(kw.lower(), word.lower()) / len(kw) < (1 - threshold) for word in text_lower.split()))
    match_ratio = matches / len(query_keywords) if query_keywords else 0
    is_definition = text_lower.startswith(('is ', 'refers to ', 'means ', 'defined as '))
    return (match_ratio >= CONFIG['keyword_match_ratio'] or is_definition), match_ratio

def summarize_text(paragraphs, query, used_paragraphs):
    """Extract a concise answer based on query keywords."""
    query_keywords = get_query_keywords(query)
    candidates = []
    for p in paragraphs:
        if p in used_paragraphs.get(query, set()):
            continue
        p_lower = p.lower()
        score = sum(1 for kw in query_keywords if kw in p_lower)
        if "won" in p_lower and any(kw in p_lower for kw in ["2024", "2025", "prize", "award"]):
            score += 10
        sentences = p.split(". ")
        for s in sentences:
            if any(c.isupper() for c in s) and score > 0:
                candidates.append((s.strip(), score))
                break
    if not candidates:
        return "[Info] No relevant content found."
    best_sentence, _ = max(candidates, key=lambda x: x[1], default=("", 0))
    if best_sentence:
        used_paragraphs.setdefault(query, set()).add(next(p for p in paragraphs if best_sentence in p))
        return best_sentence + "." if not best_sentence.endswith(".") else best_sentence
    return "[Info] No relevant content found."

def extract_text_from_soup(soup):
    """Extract all relevant text from a BeautifulSoup object."""
    texts = []
    for tag in soup.find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6", "li"]):
        text = clean_text(tag.get_text())
        if text:
            texts.append(text)
    return texts

def get_urls_to_crawl(start_url, max_pages=10, query_keywords=None):
    """Recursively crawl internal links up to max_pages."""
    domain = urlparse(start_url).netloc
    visited = set()
    to_crawl = [(start_url, 0)]
    urls = []
    while to_crawl and len(urls) < max_pages:
        url, depth = to_crawl.pop(0)
        if url in visited or depth > 3:
            continue
        parsed_url = urlparse(url)
        if parsed_url.netloc != domain:
            continue
        visited.add(url)
        try:
            headers = {"User-Agent": random.choice(USER_AGENTS)}
            response = requests.get(url, headers=headers, timeout=CONFIG['request_timeout'])
            if response.ok:
                soup = BeautifulSoup(response.text, "html.parser")
                urls.append(url)
                for link in soup.find_all("a", href=True):
                    href = link["href"]
                    full_url = urljoin(url, href)
                    if query_keywords and any(kw.lower() in full_url.lower() for kw in query_keywords):
                        to_crawl.append((full_url, depth + 1))
            time.sleep(random.uniform(CONFIG['search_pause'], CONFIG['search_pause'] * 2))
        except Exception as e:
            with open(os.path.join(CONFIG['cache_dir'], 'logs', 'scrape_errors.txt'), "a") as f:
                f.write(f"{url}: {str(e)}\n")
    return urls[:max_pages]

def rank_sources(urls, query):
    """Rank URLs by domain trust and recency, prioritizing .gov."""
    trusted_domains = [".gov", ".org", ".edu", ".int"]
    ranked = []
    for url in urls:
        score = 0
        parsed_url = urlparse(url)
        if ".gov" in parsed_url.netloc.lower():
            score += 70  # Higher priority for .gov
        elif any(domain in parsed_url.netloc.lower() for domain in trusted_domains[1:]):
            score += 50
        if any(year in url.lower() for year in ["2024", "2025"]):
            score += 30
        try:
            headers = {"User-Agent": random.choice(USER_AGENTS)}
            response = requests.head(url, headers=headers, timeout=3)
            last_modified = response.headers.get("Last-Modified", "")
            if any(year in last_modified for year in ["2024", "2025"]):
                score += 20
        except:
            pass
        ranked.append((url, score))
    return [url for url, _ in sorted(ranked, key=lambda x: x[1], reverse=True)]

def reformulate_query(query):
    """Generate query variants for better search results."""
    variants = [query]
    query_lower = query.lower()
    if "who" in query_lower:
        variants.append(query.replace("who", "winner").replace("Who", "Winner"))
    if any(year in query_lower for year in ["2024", "2025"]):
        variants.extend([f"{query} announcement", f"{query} official"])
    return variants[:3]

def is_site_relevant(url, query_keywords):
    """Check site relevance using metadata."""
    try:
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        response = requests.head(url, headers=headers, timeout=CONFIG['request_timeout'], allow_redirects=True)
        if response.status_code != 200:
            return False
        response = requests.get(url, headers=headers, timeout=CONFIG['request_timeout'])
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.title.get_text() if soup.title else ''
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        description = meta_desc.get('content', '') if meta_desc else ''
        url_path = urlparse(url).path
        combined_text = f"{title} {description} {url_path}".lower()
        matches = sum(1 for kw in query_keywords if kw in combined_text)
        match_ratio = matches / len(query_keywords) if query_keywords else 0
        return match_ratio >= CONFIG['topic_relevance_threshold']
    except Exception as e:
        with open(os.path.join(CONFIG['cache_dir'], 'logs', 'scrape_errors.txt'), "a") as f:
            f.write(f"{url}: {str(e)}\n")
        return False

def scrape_site(url, query_keywords, visited_urls, query_hash):
    """Scrape all content from a site with rate safeguards."""
    texts = []
    domain = urlparse(url).netloc
    pages_to_scrape = [url]
    pages_scraped = 0

    while pages_to_scrape and pages_scraped < CONFIG['max_pages_per_site'] and len(texts) < CONFIG['max_text_segments']:
        current_url = pages_to_scrape.pop(0)
        if current_url in visited_urls:
            continue
        visited_urls.add(current_url)
        try:
            headers = {"User-Agent": random.choice(USER_AGENTS)}
            response = requests.get(current_url, headers=headers, timeout=CONFIG['request_timeout'])
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            for text in extract_text_from_soup(soup):
                if text not in used_paragraphs[query_hash] and is_relevant_text(text, query_keywords)[0]:
                    texts.append(text)
            internal_links = get_urls_to_crawl(current_url, max_pages=2, query_keywords=query_keywords)
            pages_to_scrape.extend([link for link in internal_links if link not in visited_urls])
            pages_scraped += 1
            time.sleep(random.uniform(CONFIG['search_pause'], CONFIG['search_pause'] * 2))
        except Exception as e:
            with open(os.path.join(CONFIG['cache_dir'], 'logs', 'scrape_errors.txt'), "a") as f:
                f.write(f"{current_url}: {str(e)}\n")
    return texts

def save_cache(topic, texts):
    """Save scraped texts to JSON cache."""
    os.makedirs(CONFIG['cache_dir'], exist_ok=True)
    os.makedirs(os.path.join(CONFIG['cache_dir'], 'logs'), exist_ok=True)
    cache_file = os.path.join(CONFIG['cache_dir'], f'{topic}.json')
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(texts, f, ensure_ascii=False, indent=2)

def load_cache(topic, query):
    """Load cached JSON and select a random relevant paragraph."""
    cache_dir = CONFIG['cache_dir']
    query_keywords = get_query_keywords(query)
    query_hash = hash_query(query)
    relevant_paragraphs = []

    cache_file = os.path.join(cache_dir, f'{topic}.json')
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                paragraphs = json.load(f)
                for paragraph in paragraphs:
                    is_relevant, score = is_relevant_text(paragraph, query_keywords)
                    if is_relevant and paragraph not in used_paragraphs[query_hash]:
                        relevant_paragraphs.append((paragraph, score))
        except Exception as e:
            with open(os.path.join(CONFIG['cache_dir'], 'logs', 'cache_errors.txt'), "a") as f:
                f.write(f"{cache_file}: {str(e)}\n")

    if not relevant_paragraphs:
        return None
    relevant_paragraphs.sort(key=lambda x: x[1], reverse=True)
    top_paragraphs = [p for p, s in relevant_paragraphs if s >= relevant_paragraphs[0][1] * 0.9]
    selected_paragraph = random.choice(top_paragraphs) if top_paragraphs else relevant_paragraphs[0][0]
    used_paragraphs[query_hash].add(selected_paragraph)
    return summarize_text([selected_paragraph], query, used_paragraphs)

def log_interaction(query, answer, source, success):
    """Log interaction details for analysis."""
    log_entry = {
        "query": query,
        "answer": answer,
        "source": source,
        "success": answer != "[Info] No relevant content found.",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    os.makedirs(os.path.join(CONFIG['cache_dir'], 'logs'), exist_ok=True)
    with open(os.path.join(CONFIG['cache_dir'], 'logs', 'interactions.json'), "a") as f:
        json.dump(log_entry, f)
        f.write("\n")

def scrape_web(query):
    """Scrape web, checking cache first, and save all scraped content."""
    topic = normalize_query(query)
    query_hash = hash_query(query)
    cached_answer = load_cache(topic, query)
    if cached_answer:
        log_interaction(query, cached_answer, f"{topic}.json", True)
        return cached_answer

    query_keywords = get_query_keywords(query)
    visited_urls = set()
    urls = []
    for q in reformulate_query(query):
        urls.extend(list(search(q, num_results=CONFIG['max_search_results'])))
        if len(urls) >= 10:
            break
        time.sleep(CONFIG['search_pause'])

    relevant_urls = []
    with ThreadPoolExecutor(max_workers=CONFIG['max_workers']) as executor:
        future_to_url = {executor.submit(is_site_relevant, url, query_keywords): url for url in rank_sources(urls, query)}
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                if future.result():
                    relevant_urls.append(url)
            except:
                pass

    all_texts = []
    with ThreadPoolExecutor(max_workers=CONFIG['max_workers']) as executor:
        future_to_url = {executor.submit(scrape_site, url, query_keywords, visited_urls, query_hash): url for url in relevant_urls}
        for future in as_completed(future_to_url):
            try:
                texts = future.result()
                all_texts.extend(texts)
            except Exception as e:
                with open(os.path.join(CONFIG['cache_dir'], 'logs', 'scrape_errors.txt'), "a") as f:
                    f.write(f"{future_to_url[future]}: {str(e)}\n")
            time.sleep(CONFIG['search_pause'])

    if not all_texts:
        log_interaction(query, "[Info] No relevant content found.", "web", False)
        return "[Info] No relevant content found."
    save_cache(topic, all_texts)
    answer = summarize_text(all_texts, query, used_paragraphs)
    log_interaction(query, answer, f"{topic}.json", answer != "[Info] No relevant content found.")
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
        print(f"Bot: {answer}")

if __name__ == "__main__":
    main()