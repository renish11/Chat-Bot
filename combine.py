import json
import os
import re
import requests
from bs4 import BeautifulSoup
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords, wordnet
from nltk.stem import WordNetLemmatizer, PorterStemmer
from googlesearch import search
import uuid
import time
from urllib.parse import urlparse, urljoin
import string
import random
import datetime

# Download NLTK resources
nltk.download('punkt', quiet=True)
nltk.download('wordnet', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)

# Configuration for web scraping
CONFIG = {
    'max_search_results': 10,
    'max_paragraphs_per_site': 2,
    'max_pages_per_site': 2,
    'min_paragraph_length': 50,
    'keyword_match_ratio': 0.7,
    'alpha_char_ratio': 0.7,
    'cache_dir': 'database',
    'search_pause': 2.0,
    'num_results': 10,
    'request_timeout': 5,
    'topic_relevance_threshold': 0.5
}

# Initialize NLTK
lemmatizer = WordNetLemmatizer()
stemmer = PorterStemmer()
stop_words = set(stopwords.words('english') + list(string.punctuation))

def preprocess_text(text):
    """Tokenize, remove stopwords, and stem the input text for local search."""
    text = text.lower()
    tokens = word_tokenize(text)
    tokens = [word for word in tokens if word not in stop_words]
    tokens = [stemmer.stem(word) for word in tokens]
    return tokens

def get_synonyms(word):
    """Get synonyms for a word using WordNet."""
    synonyms = set()
    for syn in wordnet.synsets(word):
        if syn is not None and hasattr(syn, 'lemmas'):
            for lemma in syn.lemmas():
                synonyms.add(lemma.name().replace('_', ' '))
    return list(synonyms)

def paraphrase_sentence(sentence):
    """Paraphrase a sentence by replacing words with synonyms."""
    tokens = word_tokenize(sentence)
    new_tokens = []
    for token in tokens:
        if random.random() < 0.3:  # 30% chance to replace a word
            synonyms = get_synonyms(token)
            if synonyms and token not in string.punctuation:
                new_tokens.append(random.choice(synonyms))
            else:
                new_tokens.append(token)
        else:
            new_tokens.append(token)
    return ' '.join(new_tokens)

def summarize_text(text, min_words=200):
    """Summarize text to ensure at least min_words, using paraphrasing."""
    sentences = nltk.sent_tokenize(text)
    random.shuffle(sentences)
    summary = []
    word_count = 0
    for sentence in sentences:
        paraphrased = paraphrase_sentence(sentence)
        summary.append(paraphrased)
        word_count += len(word_tokenize(paraphrased))
        if word_count >= min_words:
            break
    return ' '.join(summary) if summary else text

def load_directory_data(directory_path='data'):
    """Load all JSON files from the specified directory into memory."""
    data = []
    try:
        if not os.path.exists(directory_path):
            print(f"Error: Directory {directory_path} does not exist.")
            return []
        
        for filename in os.listdir(directory_path):
            if filename.endswith('.json'):
                file_path = os.path.join(directory_path, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        file_data = json.load(file)
                        title = file_data.get('title', '')
                        paragraphs = file_data.get('paragraphs', [])
                        for idx, para in enumerate(paragraphs):
                            question = f"Who is {title}?" if idx == 0 else f"What is known about {title} {idx}?"
                            data.append({'question': question, 'answer': para, 'title': title})
                except Exception as e:
                    print(f"Error loading {file_path}: {str(e)}")
        return data
    except Exception as e:
        print(f"Error accessing directory {directory_path}: {str(e)}")
        return []

def cache_data(data):
    """Preprocess and cache question-answer pairs with stemmed questions."""
    cached_data = []
    for item in data:
        if 'question' not in item or 'answer' not in item:
            continue
        processed_question = preprocess_text(item['question'])
        cached_data.append({
            'processed_question': processed_question,
            'original_question': item['question'],
            'answer': item['answer'],
            'title': item.get('title', '')
        })
    return cached_data

def save_chat_history(question, answer, chat_file='chat.json'):
    """Save question-answer pair to chat.json."""
    chat_history = []
    try:
        if os.path.exists(chat_file):
            with open(chat_file, 'r', encoding='utf-8') as file:
                try:
                    chat_history = json.load(file)
                    if not isinstance(chat_history, list):
                        chat_history = []
                except json.JSONDecodeError:
                    chat_history = []
    except Exception as e:
        print(f"Error reading {chat_file}: {str(e)}")
    
    chat_history.append({
        'question': question,
        'answer': answer,
        'timestamp': str(datetime.datetime.now())
    })
    
    try:
        with open(chat_file, 'w', encoding='utf-8') as file:
            json.dump(chat_history, file, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving to {chat_file}: {str(e)}")

def find_local_answer(question, cached_data, used_answers=None):
    """Find a varied answer from cached local data, ensuring min 200 words."""
    if used_answers is None:
        used_answers = {}
    
    processed_question = preprocess_text(question)
    best_matches = []
    max_matches = 0

    for item in cached_data:
        matches = len(set(processed_question) & set(item['processed_question']))
        if matches > 0:
            if matches == max_matches:
                best_matches.append(item)
            elif matches > max_matches:
                best_matches = [item]
                max_matches = matches

    if not best_matches:
        return None

    question_key = ' '.join(processed_question)
    used_for_question = used_answers.get(question_key, set())
    available_matches = [item for item in best_matches if item['answer'] not in used_for_question]

    if not available_matches:
        used_answers[question_key] = set()
        available_matches = best_matches

    selected_item = random.choice(available_matches)
    selected_answer = selected_item['answer']
    
    word_count = len(word_tokenize(selected_answer))
    if word_count < 200:
        same_title_items = [item['answer'] for item in cached_data if item['title'] == selected_item['title']]
        combined_answer = ' '.join(same_title_items[:max(2, len(same_title_items))])
        selected_answer = combined_answer
        word_count = len(word_tokenize(selected_answer))
        if word_count < 200:
            selected_answer = (selected_answer + ' ' + selected_answer)[:1000]

    final_answer = summarize_text(selected_answer, min_words=200)
    
    if question_key not in used_answers:
        used_answers[question_key] = set()
    used_answers[question_key].add(selected_item['answer'])
    
    return final_answer

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
        title = soup.title.get_text() if soup.title else ''
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        description = meta_desc.get('content', '') if meta_desc and 'content' in getattr(meta_desc, 'attrs', {}) else ''
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
                    return summarize_text(relevant_paragraphs[0], min_words=200)
            time.sleep(CONFIG['search_pause'])
    except Exception as e:
        print(f"Error during search: {e}")
        return None
    return None

def main():
    """Run the combined chatbot."""
    directory_path = 'data'
    chat_file = 'chat.json'
    print(f"Loading data from {directory_path}...")
    data = load_directory_data(directory_path)
    
    if not data:
        print("No valid data loaded. Will rely on web search.")
    else:
        print("Preprocessing and caching data...")
        cached_data = cache_data(data)
        print(f"Loaded {len(cached_data)} question-answer pairs.")
    
    used_answers = {}
    print("\nChatbot is ready! Type 'exit' or 'quit' to quit.")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ('exit', 'quit'):
            print("Bot: Goodbye!")
            break
        if not user_input:
            print("Bot: Please enter a valid query.")
            continue

        # Check local cache first
        answer = None
        if data:
            answer = find_local_answer(user_input, cached_data, used_answers)
        
        if answer:
            print(f"Bot: {answer}")
            save_chat_history(user_input, answer, chat_file)
            continue
        
        # If no local answer, check web cache and search online
        topic = normalize_query(user_input)
        cached = load_cache(topic)
        if cached and cached['query'].lower() == user_input.lower():
            print(f"Bot: {cached['answer']}")
            save_chat_history(user_input, cached['answer'], chat_file)
            continue
        
        answer = scrape_web(user_input)
        if answer:
            save_cache(topic, user_input, answer)
            print(f"Bot: {answer}")
            save_chat_history(user_input, answer, chat_file)
        else:
            print("Bot: [Info] No relevant information found.")
            save_chat_history(user_input, "No relevant information found.", chat_file)

if __name__ == "__main__":
    main()