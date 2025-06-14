# import nltk
# import re
# import time
# import json
# import os
# from bs4 import BeautifulSoup
# from nltk.stem import WordNetLemmatizer
# from nltk.corpus import stopwords
# from nltk import pos_tag, word_tokenize, ne_chunk
# from nltk.tree import Tree
# import undetected_chromedriver as uc
# from urllib.parse import quote_plus

# # Download required NLTK resources
# for res in ['punkt', 'wordnet', 'stopwords', 'averaged_perceptron_tagger', 'maxent_ne_chunker', 'words']:
#     nltk.download(res, quiet=True)

# CONFIG = {
#     'NUM_RESULTS': 100,
#     'MAX_PARAS_PER_SITE': 2,
#     'MIN_TEXT_LENGTH': 70,
#     'ALPHA_RATIO': 0.7,
#     'HEADLESS': False,
#     'MIN_KEYWORD_MATCH_RATIO': 0.7
# }

# SKIP_RESPONSES = {
#     "[Info] No relevant content found on this page.",
#     "[Info] Failed to fetch or parse the page.",
#     "[Info] No accurate and relevant content found. Try rephrasing your question."
# }
# SKIP_PATTERNS = [r"cloudflare", r"access denied", r"captcha", r"404 error", r"subscribe", r"register", r"advertisement"]

# def clean_text(text):
#     for pattern in SKIP_PATTERNS:
#         if re.search(pattern, text, re.IGNORECASE):
#             return ""
#     return text

# def clean_answer_text(text):
#     return re.sub(r'\s+', ' ', re.sub(r'\[[^\]]*\]', '', text)).strip()

# def lemmatize_words(text, lemmatizer, stop_words):
#     return set(lemmatizer.lemmatize(w) for w in word_tokenize(text.lower()) if w.isalpha() and w not in stop_words)

# def is_meaningful_text(text, query_keywords, lemmatizer, stop_words):
#     if len(text) < CONFIG['MIN_TEXT_LENGTH']:
#         return False
#     lemmas = lemmatize_words(text, lemmatizer, stop_words)
#     overlap = query_keywords & lemmas
#     alpha_ratio = sum(c.isalpha() for c in text) / max(len(text), 1)
#     return len(overlap) / max(len(query_keywords), 1) >= CONFIG['MIN_KEYWORD_MATCH_RATIO'] and alpha_ratio > CONFIG['ALPHA_RATIO']

# def is_definition_like(text, query):
#     query = query.lower().strip().rstrip('?')
#     terms = [query]
#     if query.startswith(('what is ', 'who is ', 'why ', 'how ')):
#         terms.append(query.split(' ', 2)[-1])
#     for term in terms:
#         if re.match(rf"^{re.escape(term)}\s+(is|was|are|refers to|means|can be defined as|is known as)\b", text.lower()):
#             return True
#     return False

# def extract_relevant_paragraphs(soup, query, lemmatizer, stop_words):
#     query_keywords = lemmatize_words(query, lemmatizer, stop_words)
#     candidates = []
#     for para in soup.find_all('p'):
#         text = clean_text(para.get_text(separator=' ', strip=True))
#         if not text:
#             continue
#         text = clean_answer_text(text)
#         if text in SKIP_RESPONSES or len(text.split()) < 10:
#             continue
#         lemmas = lemmatize_words(text, lemmatizer, stop_words)
#         overlap = len(query_keywords & lemmas)
#         is_def = is_definition_like(text, query)
#         candidates.append((is_def, overlap, text))
#     candidates.sort(key=lambda x: (not x[0], -x[1]))
#     return [x[2] for x in candidates[:CONFIG['MAX_PARAS_PER_SITE']] if is_meaningful_text(x[2], query_keywords, lemmatizer, stop_words)]

# def search_google_urls(query, driver):
#     driver.get(f"https://www.bing.com/search?q={quote_plus(query)}")
#     time.sleep(3)
#     soup = BeautifulSoup(driver.page_source, 'html.parser')
#     return [str(href) for a in soup.select('li.b_algo h2 a') if (href := a.get('href')) and str(href).startswith('http')][:CONFIG['NUM_RESULTS']]

# def extract_named_entities(query):
#     chunked = ne_chunk(pos_tag(word_tokenize(query)))
#     return [" ".join(leaf[0] for leaf in subtree.leaves()).lower() for subtree in chunked if isinstance(subtree, Tree)]

# def normalize_topic_name(query, stop_words):
#     query = query.lower().strip().rstrip('?')
#     lemmatizer = WordNetLemmatizer()
#     entities = extract_named_entities(query)
#     existing_topics = [f[:-5] for f in os.listdir('database') if f.endswith('.json')]

#     for entity in entities:
#         slug = entity.replace(' ', '_')
#         for topic in existing_topics:
#             if slug == topic or slug in topic or topic in slug:
#                 return topic
#         return slug

#     nouns = [w for w, pos in pos_tag(word_tokenize(query)) if pos.startswith('NN') and w not in stop_words]
#     if nouns:
#         base = '_'.join(sorted(set(lemmatizer.lemmatize(w) for w in nouns)))
#         for topic in existing_topics:
#             if base == topic or base in topic or topic in base:
#                 return topic
#         return base
#     return "_".join(query.split())

# class DocChatBot:
#     def __init__(self):
#         self.lemmatizer = WordNetLemmatizer()
#         self.stop_words = set(stopwords.words('english'))

#         if not os.path.exists('database'):
#             os.makedirs('database')

#         options = uc.ChromeOptions()
#         if CONFIG['HEADLESS']:
#             options.add_argument("--headless")
#         self.driver = uc.Chrome(options=options)

#     def get_from_json(self, question):
#         topic = normalize_topic_name(question, self.stop_words)
#         path = f'database/{topic}.json'
#         if os.path.exists(path):
#             with open(path, 'r', encoding='utf-8') as f:
#                 data = json.load(f)
#                 for q, answers in data.items():
#                     if question.lower() in q.lower():
#                         return answers, topic
#         return None, topic

#     def update_json(self, topic, question, answers):
#         path = f'database/{topic}.json'
#         if os.path.exists(path):
#             with open(path, 'r', encoding='utf-8') as f:
#                 data = json.load(f)
#         else:
#             data = {}
#         data[question] = answers
#         with open(path, 'w', encoding='utf-8') as f:
#             json.dump(data, f, indent=2)

#     def get_next_answer(self, query):
#         stored_answers, topic = self.get_from_json(query)
#         if isinstance(stored_answers, list) and stored_answers:
#             return stored_answers[0]
#         elif isinstance(stored_answers, str):  # fallback if stored string
#             return stored_answers

#         urls = search_google_urls(query, self.driver)
#         all_answers = []

#         for url in urls:
#             try:
#                 self.driver.get(url)
#                 time.sleep(2)
#                 soup = BeautifulSoup(self.driver.page_source, 'html.parser')
#                 paras = extract_relevant_paragraphs(soup, query, self.lemmatizer, self.stop_words)
#                 all_answers.extend(paras)
#                 if len(all_answers) >= CONFIG['MAX_PARAS_PER_SITE']:
#                     break
#             except Exception:
#                 continue

#         if all_answers:
#             self.update_json(topic, query, all_answers)
#             return all_answers[0]

#         return "[Info] No accurate and relevant content found. Try rephrasing your question."

#     def chat(self):
#         print("🤖 DocChatBot is ready! Ask me anything.")
#         while True:
#             user_input = input("\nYou: ").strip()
#             if user_input.lower() in {"exit", "quit"}:
#                 print("Bot: Goodbye!")
#                 self.driver.quit()  # Safe Chrome quit
#                 break
#             try:
#                 response = self.get_next_answer(user_input)
#             except Exception as e:
#                 response = f"[Error] Something went wrong: {e}"
#             print(f"Bot: {response}")

# # Run the chatbot
# if __name__ == "__main__":
#     bot = DocChatBot()
#     bot.chat()
















import json
import os
import re
import requests
from bs4 import BeautifulSoup
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords, wordnet
from nltk.stem import WordNetLemmatizer
from googlesearch import search
import uuid
import time
from urllib.parse import urlparse, urljoin


#fdg
# Download NLTK resources
nltk.download('punkt', quiet=True)
nltk.download('wordnet', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)

# Configuration
CONFIG = {
    'max_search_results': 10,
    'max_paragraphs_per_site': 2,
    'max_pages_per_site': 2,  # Max number of internal pages to scrape per site
    'min_paragraph_length': 50,
    'keyword_match_ratio': 0.7,
    'alpha_char_ratio': 0.7,
    'cache_dir': 'database',
    'search_pause': 2.0,
    'num_results': 10,
    'request_timeout': 5,
    'topic_relevance_threshold': 0.5  # Minimum keyword match ratio for site relevance
}

# Initialize NLTK
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

def normalize_query(query):
    """Convert query to a slug for caching based on nouns or named entities."""
    tokens = word_tokenize(query.lower())
    pos_tags = nltk.pos_tag(tokens)
    nouns = [token for token, pos in pos_tags if pos.startswith('NN') or pos in ('JJ', 'VB')]
    if not nouns:
        nouns = tokens
    slug = '-'.join(nouns)
    slug = re.sub(r'[^a-z0-9\-]', '', slug)
    return slug if slug else 'query-' + str(uuid.uuid4())[:8]

def get_query_keywords(query):
    """Extract lemmatized keywords from query, excluding stopwords."""
    tokens = word_tokenize(query.lower())
    return [lemmatizer.lemmatize(token) for token in tokens if token.isalpha() and token not in stop_words]

def clean_text(text):
    """Clean extracted text by removing unwanted patterns and normalizing whitespace."""
    text = re.sub(r'(access denied|captcha|advertisement|subscribe now|log in)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def is_relevant_paragraph(paragraph, query_keywords):
    """Check if paragraph is relevant based on keyword overlap and alphabetic ratio."""
    if len(paragraph) < CONFIG['min_paragraph_length']:
        return False
    alpha_count = sum(1 for c in paragraph if c.isalpha())
    alpha_ratio = alpha_count / len(paragraph) if len(paragraph) > 0 else 0
    if alpha_ratio < CONFIG['alpha_char_ratio']:
        return False
    tokens = word_tokenize(paragraph.lower())
    lemmatized = [lemmatizer.lemmatize(token) for token in tokens if token.isalpha() and token not in stop_words]
    if not lemmatized:
        return False
    matches = len(set(query_keywords) & set(lemmatized))
    match_ratio = matches / len(set(query_keywords)) if query_keywords else 0
    is_definition = paragraph.lower().startswith(('is ', 'refers to ', 'means ', 'defined as '))
    return match_ratio >= CONFIG['keyword_match_ratio'] or is_definition

def load_cache(topic):
    """Load cached answer from JSON file."""
    cache_file = os.path.join(CONFIG['cache_dir'], f'{topic}.json')
    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def save_cache(topic, query, answer):
    """Save answer to JSON cache."""
    os.makedirs(CONFIG['cache_dir'], exist_ok=True)
    cache_file = os.path.join(CONFIG['cache_dir'], f'{topic}.json')
    data = {'query': query, 'answer': answer}
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
def get_internal_links(soup, base_url, domain):
    """Extract internal links from a page, staying within the same domain."""
    internal_links = set()
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        full_url = urljoin(base_url, href)
        parsed_url = urlparse(full_url)
        if parsed_url.netloc == domain and parsed_url.scheme in ('http', 'https'):
            internal_links.add(full_url)
    return list(internal_links)

def is_site_relevant(url, query_keywords):
    """Check if a site is relevant to the query based on title, description, or URL."""
    try:
        response = requests.get(url, timeout=CONFIG['request_timeout'])
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        # Extract title
        title = soup.title.get_text() if soup.title else ''
        # Extract meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        description = meta_desc.get('content', '') if meta_desc else '' # type: ignore
        # Extract URL path
        url_path = urlparse(url).path
        # Combine text to analyze
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

def scrape_site(url, query_keywords, visited_urls):
    """Scrape a single site and its internal links for relevant paragraphs."""
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
                if text and is_relevant_paragraph(text, query_keywords):
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
    """Scrape web for query using googlesearch-python, only visiting topic-relevant sites."""
    query_keywords = get_query_keywords(query)
    visited_urls = set()
    try:
        urls = search(query, num_results=CONFIG['num_results'], sleep_interval=CONFIG['search_pause'])
        for url in urls:
            if is_site_relevant(url, query_keywords):
                relevant_paragraphs = scrape_site(url, query_keywords, visited_urls)
                if relevant_paragraphs:
                    return relevant_paragraphs[0]
            time.sleep(CONFIG['search_pause'])
    except Exception as e:
        print(f"Error during search: {e}")
        return None
    return None

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

        topic = normalize_query(query)
        cached = load_cache(topic)
        if cached and cached['query'].lower() == query.lower():
            print(f"Bot: {cached['answer']}")
            continue

        answer = scrape_web(query)
        if answer:
            save_cache(topic, query, answer)
            print(f"Bot: {answer}")
        else:
            print("Bot: [Info] No relevant content found.")

if __name__ == "__main__":
    main()
