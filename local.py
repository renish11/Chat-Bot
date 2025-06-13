# import json
# import os
# import nltk
# from nltk.tokenize import word_tokenize
# from nltk.corpus import stopwords
# from nltk.stem import PorterStemmer
# import string

# # Download required NLTK data
# nltk.download('punkt', quiet=True)
# nltk.download('stopwords', quiet=True)

# def load_directory_data(directory_path):
#     """Load all JSON files from the specified directory into memory."""
#     data = []
#     try:
#         if not os.path.exists(directory_path):
#             print(f"Error: Directory {directory_path} does not exist.")
#             return []
        
#         for filename in os.listdir(directory_path):
#             if filename.endswith('.json'):
#                 file_path = os.path.join(directory_path, filename)
#                 try:
#                     with open(file_path, 'r', encoding='utf-8') as file:
#                         file_data = json.load(file)
#                         title = file_data.get('title', '')
#                         paragraphs = file_data.get('paragraphs', [])
#                         # Generate synthetic question-answer pairs
#                         for idx, para in enumerate(paragraphs):
#                             # Create a simple question based on the title and paragraph
#                             question = f"Who is {title}?" if idx == 0 else f"What is known about {title} {idx}?"
#                             data.append({'question': question, 'answer': para})
#                 except FileNotFoundError:
#                     print(f"Error: File {file_path} not found.")
#                 except json.JSONDecodeError:
#                     print(f"Error: Invalid JSON format in {file_path}.")
#                 except Exception as e:
#                     print(f"Error loading {file_path}: {str(e)}")
#         return data
#     except Exception as e:
#         print(f"Error accessing directory {directory_path}: {str(e)}")
#         return []

# def preprocess_text(text):
#     """Tokenize, remove stopwords, and stem the input text."""
#     text = text.lower()
#     tokens = word_tokenize(text)
#     stop_words = set(stopwords.words('english') + list(string.punctuation))
#     tokens = [word for word in tokens if word not in stop_words]
#     stemmer = PorterStemmer()
#     tokens = [stemmer.stem(word) for word in tokens]
#     return tokens

# def cache_data(data):
#     """Preprocess and cache question-answer pairs with stemmed questions."""
#     cached_data = []
#     for item in data:
#         if 'question' not in item or 'answer' not in item:
#             continue
#         processed_question = preprocess_text(item['question'])
#         cached_data.append({
#             'processed_question': processed_question,
#             'original_question': item['question'],
#             'answer': item['answer']
#         })
#     return cached_data

# def find_answer(question, cached_data):
#     """Find the best matching answer from the cached data."""
#     processed_question = preprocess_text(question)
#     best_match = None
#     max_matches = 0

#     for item in cached_data:
#         matches = len(set(processed_question) & set(item['processed_question']))
#         if matches > max_matches:
#             max_matches = matches
#             best_match = item['answer']

#     return best_match if best_match else "Sorry, I don't have an answer for that."

# def main():
#     """Run the chatbot."""
#     directory_path = 'data'
#     print(f"Loading data from {directory_path}...")
#     data = load_directory_data(directory_path)
    
#     if not data:
#         print("No valid data loaded. Exiting.")
#         return

#     print("Preprocessing and caching data...")
#     cached_data = cache_data(data)
#     print(f"Loaded {len(cached_data)} question-answer pairs.")

#     print("\nChatbot is ready! Type 'exit' to quit.")
#     while True:
#         user_input = input("You: ")
#         if user_input.lower() == 'exit':
#             print("Goodbye!")
#             break
#         answer = find_answer(user_input, cached_data)
#         print(f"Bot: {answer}")

# if __name__ == "__main__":
#     main()



# import json
# import os
# import nltk
# from nltk.tokenize import word_tokenize
# from nltk.corpus import stopwords
# from nltk.stem import PorterStemmer
# from nltk.corpus import wordnet
# import string
# import random

# # Download required NLTK data
# nltk.download('punkt', quiet=True)
# nltk.download('stopwords', quiet=True)
# nltk.download('wordnet', quiet=True)

# def load_directory_data(directory_path):
#     """Load all JSON files from the specified directory into memory."""
#     data = []
#     try:
#         if not os.path.exists(directory_path):
#             print(f"Error: Directory {directory_path} does not exist.")
#             return []
        
#         for filename in os.listdir(directory_path):
#             if filename.endswith('.json'):
#                 file_path = os.path.join(directory_path, filename)
#                 try:
#                     with open(file_path, 'r', encoding='utf-8') as file:
#                         file_data = json.load(file)
#                         title = file_data.get('title', '')
#                         paragraphs = file_data.get('paragraphs', [])
#                         for idx, para in enumerate(paragraphs):
#                             question = f"Who is {title}?" if idx == 0 else f"What is known about {title} {idx}?"
#                             data.append({'question': question, 'answer': para, 'title': title})
#                 except FileNotFoundError:
#                     print(f"Error: File {file_path} not found.")
#                 except json.JSONDecodeError:
#                     print(f"Error: Invalid JSON format in {file_path}.")
#                 except Exception as e:
#                     print(f"Error loading {file_path}: {str(e)}")
#         return data
#     except Exception as e:
#         print(f"Error accessing directory {directory_path}: {str(e)}")
#         return []

# def preprocess_text(text):
#     """Tokenize, remove stopwords, and stem the input text."""
#     text = text.lower()
#     tokens = word_tokenize(text)
#     stop_words = set(stopwords.words('english') + list(string.punctuation))
#     tokens = [word for word in tokens if word not in stop_words]
#     stemmer = PorterStemmer()
#     tokens = [stemmer.stem(word) for word in tokens]
#     return tokens

# def get_synonyms(word):
#     """Get synonyms for a word using WordNet."""
#     synonyms = set()
#     for syn in wordnet.synsets(word):
#         if syn is not None and hasattr(syn, 'lemmas'):
#             for lemma in syn.lemmas():
#                 synonyms.add(lemma.name().replace('_', ' '))
#     return list(synonyms)

# def paraphrase_sentence(sentence):
#     """Paraphrase a sentence by replacing words with synonyms."""
#     tokens = word_tokenize(sentence)
#     new_tokens = []
#     for token in tokens:
#         if random.random() < 0.3:  # 30% chance to replace a word
#             synonyms = get_synonyms(token)
#             if synonyms and token not in string.punctuation:
#                 new_tokens.append(random.choice(synonyms))
#             else:
#                 new_tokens.append(token)
#         else:
#             new_tokens.append(token)
#     return ' '.join(new_tokens)

# def summarize_text(text, min_words=200):
#     """Summarize text to ensure at least min_words, using paraphrasing."""
#     sentences = nltk.sent_tokenize(text)
#     random.shuffle(sentences)  # Shuffle for variety
#     summary = []
#     word_count = 0
#     for sentence in sentences:
#         paraphrased = paraphrase_sentence(sentence)
#         summary.append(paraphrased)
#         word_count += len(word_tokenize(paraphrased))
#         if word_count >= min_words:
#             break
#     return ' '.join(summary) if summary else text

# def cache_data(data):
#     """Preprocess and cache question-answer pairs with stemmed questions."""
#     cached_data = []
#     for item in data:
#         if 'question' not in item or 'answer' not in item:
#             continue
#         processed_question = preprocess_text(item['question'])
#         cached_data.append({
#             'processed_question': processed_question,
#             'original_question': item['question'],
#             'answer': item['answer'],
#             'title': item.get('title', '')
#         })
#     return cached_data

# def find_answer(question, cached_data, used_answers=None):
#     """Find a varied answer from cached data, ensuring min 200 words."""
#     if used_answers is None:
#         used_answers = {}
    
#     processed_question = preprocess_text(question)
#     best_matches = []
#     max_matches = 0

#     for item in cached_data:
#         matches = len(set(processed_question) & set(item['processed_question']))
#         if matches > 0:
#             if matches == max_matches:
#                 best_matches.append(item)
#             elif matches > max_matches:
#                 best_matches = [item]
#                 max_matches = matches

#     if not best_matches:
#         return "Sorry, I don't have an answer for that."

#     # Filter out previously used answers for this question
#     question_key = ' '.join(processed_question)
#     used_for_question = used_answers.get(question_key, set())
#     available_matches = [item for item in best_matches if item['answer'] not in used_for_question]

#     if not available_matches:
#         # Reset used answers if all have been used
#         used_answers[question_key] = set()
#         available_matches = best_matches

#     # Select a random match from available ones
#     selected_item = random.choice(available_matches)
#     selected_answer = selected_item['answer']
    
#     # Ensure answer is at least 200 words
#     word_count = len(word_tokenize(selected_answer))
#     if word_count < 200:
#         # Combine with other paragraphs from the same title
#         same_title_items = [item['answer'] for item in cached_data if item['title'] == selected_item['title']]
#         combined_answer = ' '.join(same_title_items[:max(2, len(same_title_items))])
#         selected_answer = combined_answer
#         word_count = len(word_tokenize(selected_answer))
#         if word_count < 200:
#             # Repeat content if still short
#             selected_answer = (selected_answer + ' ' + selected_answer)[:1000]  # Cap to avoid excessive length

#     # Summarize and paraphrase
#     final_answer = summarize_text(selected_answer, min_words=200)
    
#     # Track used answer
#     if question_key not in used_answers:
#         used_answers[question_key] = set()
#     used_answers[question_key].add(selected_item['answer'])
    
#     return final_answer

# def main():
#     """Run the chatbot."""
#     directory_path = 'data'
#     print(f"Loading data from {directory_path}...")
#     data = load_directory_data(directory_path)
    
#     if not data:
#         print("No valid data loaded. Exiting.")
#         return

#     print("Preprocessing and caching data...")
#     cached_data = cache_data(data)
#     print(f"Loaded {len(cached_data)} question-answer pairs.")

#     used_answers = {}  # Track used answers per question
#     print("\nChatbot is ready! Type 'exit' to quit.")
#     while True:
#         user_input = input("You: ")
#         if user_input.lower() == 'exit':
#             print("Goodbye!")
#             break
#         answer = find_answer(user_input, cached_data, used_answers)
#         print(f"Bot: {answer}")

# if __name__ == "__main__":
#     main()



# import json
# import os
# import nltk
# from nltk.tokenize import word_tokenize
# from nltk.corpus import stopwords
# from nltk.stem import PorterStemmer
# from nltk.corpus import wordnet
# import string
# import random
# import datetime

# # Download required NLTK data
# nltk.download('punkt', quiet=True)
# nltk.download('stopwords', quiet=True)
# nltk.download('wordnet', quiet=True)

# def load_directory_data(directory_path):
#     """Load all JSON files from the specified directory into memory."""
#     data = []
#     try:
#         if not os.path.exists(directory_path):
#             print(f"Error: Directory {directory_path} does not exist.")
#             return []
        
#         for filename in os.listdir(directory_path):
#             if filename.endswith('.json'):
#                 file_path = os.path.join(directory_path, filename)
#                 try:
#                     with open(file_path, 'r', encoding='utf-8') as file:
#                         file_data = json.load(file)
#                         title = file_data.get('title', '')
#                         paragraphs = file_data.get('paragraphs', [])
#                         for idx, para in enumerate(paragraphs):
#                             question = f"Who is {title}?" if idx == 0 else f"What is known about {title} {idx}?"
#                             data.append({'question': question, 'answer': para, 'title': title})
#                 except FileNotFoundError:
#                     print(f"Error: File {file_path} not found.")
#                 except json.JSONDecodeError:
#                     print(f"Error: Invalid JSON format in {file_path}.")
#                 except Exception as e:
#                     print(f"Error loading {file_path}: {str(e)}")
#         return data
#     except Exception as e:
#         print(f"Error accessing directory {directory_path}: {str(e)}")
#         return []

# def preprocess_text(text):
#     """Tokenize, remove stopwords, and stem the input text."""
#     text = text.lower()
#     tokens = word_tokenize(text)
#     stop_words = set(stopwords.words('english') + list(string.punctuation))
#     tokens = [word for word in tokens if word not in stop_words]
#     stemmer = PorterStemmer()
#     tokens = [stemmer.stem(word) for word in tokens]
#     return tokens

# def get_synonyms(word):
#     """Get synonyms for a word using WordNet."""
#     synonyms = set()
#     for syn in wordnet.synsets(word):
#         if syn is not None and hasattr(syn, 'lemmas'):
#             for lemma in syn.lemmas():
#                 synonyms.add(lemma.name().replace('_', ' '))
#     return list(synonyms)

# def paraphrase_sentence(sentence):
#     """Paraphrase a sentence by replacing words with synonyms."""
#     tokens = word_tokenize(sentence)
#     new_tokens = []
#     for token in tokens:
#         if random.random() < 0.3:  # 30% chance to replace a word
#             synonyms = get_synonyms(token)
#             if synonyms and token not in string.punctuation:
#                 new_tokens.append(random.choice(synonyms))
#             else:
#                 new_tokens.append(token)
#         else:
#             new_tokens.append(token)
#     return ' '.join(new_tokens)

# def summarize_text(text, min_words=200):
#     """Summarize text to ensure at least min_words, using paraphrasing."""
#     sentences = nltk.sent_tokenize(text)
#     random.shuffle(sentences)  # Shuffle for variety
#     summary = []
#     word_count = 0
#     for sentence in sentences:
#         paraphrased = paraphrase_sentence(sentence)
#         summary.append(paraphrased)
#         word_count += len(word_tokenize(paraphrased))
#         if word_count >= min_words:
#             break
#     return ' '.join(summary) if summary else text

# def cache_data(data):
#     """Preprocess and cache question-answer pairs with stemmed questions."""
#     cached_data = []
#     for item in data:
#         if 'question' not in item or 'answer' not in item:
#             continue
#         processed_question = preprocess_text(item['question'])
#         cached_data.append({
#             'processed_question': processed_question,
#             'original_question': item['question'],
#             'answer': item['answer'],
#             'title': item.get('title', '')
#         })
#     return cached_data

# def save_chat_history(question, answer, chat_file='chat.json'):
#     """Save question-answer pair to chat.json."""
#     chat_history = []
#     try:
#         # Load existing chat history if file exists
#         if os.path.exists(chat_file):
#             with open(chat_file, 'r', encoding='utf-8') as file:
#                 try:
#                     chat_history = json.load(file)
#                     if not isinstance(chat_history, list):
#                         chat_history = []
#                 except json.JSONDecodeError:
#                     print(f"Error: Invalid JSON format in {chat_file}. Starting with empty history.")
#                     chat_history = []
#     except Exception as e:
#         print(f"Error reading {chat_file}: {str(e)}. Starting with empty history.")
#         chat_history = []

#     # Append new question-answer pair
#     chat_history.append({
#         'question': question,
#         'answer': answer,
#         'timestamp': str(datetime.datetime.now())
#     })

#     # Save updated history
#     try:
#         with open(chat_file, 'w', encoding='utf-8') as file:
#             json.dump(chat_history, file, indent=4, ensure_ascii=False)
#     except Exception as e:
#         print(f"Error saving to {chat_file}: {str(e)}")

# def find_answer(question, cached_data, used_answers=None):
#     """Find a varied answer from cached data, ensuring min 200 words."""
#     if used_answers is None:
#         used_answers = {}
    
#     processed_question = preprocess_text(question)
#     best_matches = []
#     max_matches = 0

#     for item in cached_data:
#         matches = len(set(processed_question) & set(item['processed_question']))
#         if matches > 0:
#             if matches == max_matches:
#                 best_matches.append(item)
#             elif matches > max_matches:
#                 best_matches = [item]
#                 max_matches = matches

#     if not best_matches:
#         return "Sorry, I don't have an answer for that."

#     # Filter out previously used answers for this question
#     question_key = ' '.join(processed_question)
#     used_for_question = used_answers.get(question_key, set())
#     available_matches = [item for item in best_matches if item['answer'] not in used_for_question]

#     if not available_matches:
#         # Reset used answers if all have been used
#         used_answers[question_key] = set()
#         available_matches = best_matches

#     # Select a random match from available ones
#     selected_item = random.choice(available_matches)
#     selected_answer = selected_item['answer']
    
#     # Ensure answer is at least 200 words
#     word_count = len(word_tokenize(selected_answer))
#     if word_count < 200:
#         # Combine with other paragraphs from the same title
#         same_title_items = [item['answer'] for item in cached_data if item['title'] == selected_item['title']]
#         combined_answer = ' '.join(same_title_items[:max(2, len(same_title_items))])
#         selected_answer = combined_answer
#         word_count = len(word_tokenize(selected_answer))
#         if word_count < 200:
#             # Repeat content if still short
#             selected_answer = (selected_answer + ' ' + selected_answer)[:1000]  # Cap to avoid excessive length

#     # Summarize and paraphrase
#     final_answer = summarize_text(selected_answer, min_words=200)
    
#     # Track used answer
#     if question_key not in used_answers:
#         used_answers[question_key] = set()
#     used_answers[question_key].add(selected_item['answer'])
    
#     return final_answer

# def main():
#     """Run the chatbot."""
#     directory_path = 'data'
#     chat_file = 'chat.json'
#     print(f"Loading data from {directory_path}...")
#     data = load_directory_data(directory_path)
    
#     if not data:
#         print("No valid data loaded. Exiting.")
#         return

#     print("Preprocessing and caching data...")
#     cached_data = cache_data(data)
#     print(f"Loaded {len(cached_data)} question-answer pairs.")

#     used_answers = {}  # Track used answers per question
#     print("\nChatbot is ready! Type 'exit' to quit.")
#     while True:
#         user_input = input("You: ")
#         if user_input.lower() == 'exit':
#             print("Goodbye!")
#             break
#         answer = find_answer(user_input, cached_data, used_answers)
#         print(f"Bot: {answer}")
#         # Save the question and answer to chat.json
#         save_chat_history(user_input, answer, chat_file)

# if __name__ == "__main__":
#     main()





import json
import os
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.corpus import wordnet
import string
import random
import datetime

# Download required NLTK data
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)

def load_directory_data(directory_path):
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
                        if not title or not paragraphs:
                            
                            continue
                        for idx, para in enumerate(paragraphs):
                            question = f"Who is {title}?" if idx == 0 else f"What is known about {title} {idx}?"
                            data.append({'question': question, 'answer': para, 'title': title})
                except FileNotFoundError:
                    print(f"Error: File {file_path} not found.")
                except json.JSONDecodeError:
                    print(f"Error: Invalid JSON format in {file_path}.")
                except Exception as e:
                    print(f"Error loading {file_path}: {str(e)}")
        return data
    except Exception as e:
        print(f"Error accessing directory {directory_path}: {str(e)}")
        return []

def preprocess_text(text):
    """Tokenize, remove stopwords, and stem the input text."""
    text = text.lower()
    tokens = word_tokenize(text)
    stop_words = set(stopwords.words('english') + list(string.punctuation))
    tokens = [word for word in tokens if word not in stop_words]
    stemmer = PorterStemmer()
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
    random.shuffle(sentences)  # Shuffle for variety
    summary = []
    word_count = 0
    for sentence in sentences:
        paraphrased = paraphrase_sentence(sentence)
        summary.append(paraphrased)
        word_count += len(word_tokenize(paraphrased))
        if word_count >= min_words:
            break
    return ' '.join(summary) if summary else text

def cache_data(data):
    """Preprocess and cache question-answer pairs with stemmed questions and answers."""
    cached_data = []
    for item in data:
        if 'question' not in item or 'answer' not in item:
            print(f"Warning: Skipping invalid item - missing question or answer: {item}")
            continue
        processed_question = preprocess_text(item['question'])
        processed_answer = preprocess_text(item['answer'])  # Preprocess answer for matching
        cached_data.append({
            'processed_question': processed_question,
            'processed_answer': processed_answer,
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
                    print(f"Error: Invalid JSON format in {chat_file}. Starting with empty history.")
                    chat_history = []
    except Exception as e:
        print(f"Error reading {chat_file}: {str(e)}. Starting with empty history.")
        chat_history = []

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

def find_answer(question, cached_data, used_answers=None):
    """Find a varied answer from cached data, searching both questions and answers, ensuring min 200 words."""
    if used_answers is None:
        used_answers = {}
    
    processed_question = preprocess_text(question)
    best_matches = []
    max_matches = 0

    for item in cached_data:
        # Match against question and answer tokens
        question_matches = len(set(processed_question) & set(item['processed_question']))
        answer_matches = len(set(processed_question) & set(item['processed_answer']))
        matches = max(question_matches, answer_matches)  # Use the higher match score
        if matches > 0:
            if matches == max_matches:
                best_matches.append(item)
            elif matches > max_matches:
                best_matches = [item]
                max_matches = matches

    if not best_matches:
        print(f"No matches found for question: {question}")
        return "Sorry, I don't have an answer for that."

    # Filter out previously used answers for this question
    question_key = ' '.join(processed_question)
    used_for_question = used_answers.get(question_key, set())
    available_matches = [item for item in best_matches if item['answer'] not in used_for_question]

    if not available_matches:
        # Reset used answers if all have been used
        used_answers[question_key] = set()
        available_matches = best_matches

    # Select a random match from available ones
    selected_item = random.choice(available_matches)
    selected_answer = selected_item['answer']
    
    # Ensure answer is at least 200 words
    word_count = len(word_tokenize(selected_answer))
    if word_count < 200:
        # Combine with other paragraphs from the same title
        same_title_items = [item['answer'] for item in cached_data if item['title'] == selected_item['title']]
        combined_answer = ' '.join(same_title_items[:max(2, len(same_title_items))])
        selected_answer = combined_answer
        word_count = len(word_tokenize(selected_answer))
        if word_count < 200:
            # Repeat content if still short
            selected_answer = (selected_answer + ' ' + selected_answer)[:1000]  # Cap to avoid excessive length

    # Summarize and paraphrase
    final_answer = summarize_text(selected_answer, min_words=200)
    
    # Track used answer
    if question_key not in used_answers:
        used_answers[question_key] = set()
    used_answers[question_key].add(selected_item['answer'])
    
    return final_answer

def main():
    """Run the chatbot, reloading data on each input."""
    directory_path = 'data'
    chat_file = 'chat.json'
    used_answers = {}  # Track used answers per question
    print("\nChatbot is ready! Type 'exit' to quit.")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            print("Goodbye!")
            break
        
        # Reload data and recache on each input
        
        data = load_directory_data(directory_path)
        if not data:
            print("No valid data loaded. Please add valid JSON files to the data directory.")
            continue
        
        cached_data = cache_data(data)
        
        
        answer = find_answer(user_input, cached_data, used_answers)
        print(f"Bot: {answer}")
        # Save the question and answer to chat.json
        save_chat_history(user_input, answer, chat_file)

if __name__ == "__main__":
    main()