import os
import re
import base64
import chardet
import sqlite3
from collections import Counter
from transformers import AutoTokenizer, AutoModel
from sklearn.feature_extraction.text import TfidfVectorizer
import torch
from sklearn.metrics.pairwise import cosine_similarity
from huggingface_hub import login

from stegano import lsb

"""
# Original image must be PNG (use a clean image)
input_image = "testphoto.png"
output_image = "hidden_message_image.png"
secret_message = "This is a secret drug drop."

# Encode
lsb.hide(input_image, secret_message).save(output_image)
print(f"✅ Stego message saved in {output_image}")
"""



#found out how to download darkbert from hugging face

# Authenticate with Hugging Face (REPLACE WITH YOUR ACTUAL TOKEN)
#login(token="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")

# Load RoBERTa-Twitter model and tokenizer




MODEL_NAME = "s2w-as"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)

# Function to fetch keywords from the database
def fetch_keywords_from_db(db_file="drug_keywords.db"):
    try:
        conn = sqlite3.connect(db_file)  # Connect to the database
        cursor = conn.cursor()
        cursor.execute("SELECT keyword FROM keywords")  # Fetch all keywords
        keywords = [row[0] for row in cursor.fetchall()]  # Retrieve the keywords from the database
        conn.close()
        return keywords
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return []

# Function to read text from a .txt file
def read_txt(file_path):
    with open(file_path, 'rb') as file:  # Open in binary mode for encoding detection
        rawdata = file.read()
        result = chardet.detect(rawdata)
        encoding = result['encoding']
        try:
            return rawdata.decode(encoding)
        except UnicodeDecodeError:
            return ""  # Return empty string if decoding fails

# Function to read text from a .pdf file
def read_pdf(file_path):
    from PyPDF2 import PdfReader
    try:
        reader = PdfReader(file_path)
        return " ".join([page.extract_text() for page in reader.pages])
    except Exception as e:
        print(f"Error reading PDF {file_path}: {e}")
        return ""

# Function to read text from a .docx file
def read_docx(file_path):
    import docx
    try:
        doc = docx.Document(file_path)
        return " ".join([paragraph.text for paragraph in doc.paragraphs])
    except Exception as e:
        print(f"Error reading DOCX {file_path}: {e}")
        return ""

# Function to read text from an .html file
def read_html(file_path):
    from bs4 import BeautifulSoup
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file, 'html.parser')
            return soup.get_text()
    except Exception as e:
        print(f"Error reading HTML {file_path}: {e}")
        return ""

# Function to determine file type and extract text
def extract_text(file_path):
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    if ext == ".txt":
        return read_txt(file_path)
    elif ext == ".pdf":
        return read_pdf(file_path)
    elif ext == ".docx":
        return read_docx(file_path)
    elif ext == ".html":
        return read_html(file_path)
    else:
        return ""

# Function to decrypt base64
def decrypt_base64(text):
    try:
        decoded_bytes = base64.b64decode(text)
        result = chardet.detect(decoded_bytes)
        encoding = result['encoding']
        return decoded_bytes.decode(encoding)
    except Exception:
        return text

# Function to compute semantic similarity using RoBERTa
def get_context_similarity(text, keyword):
    inputs = tokenizer([text, keyword], padding=True, truncation=True, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**inputs)

    # Compute mean pooling to get a more general embedding representation
    text_embedding = outputs.last_hidden_state[0].mean(dim=0).numpy()
    keyword_embedding = outputs.last_hidden_state[1].mean(dim=0).numpy()

    similarity = cosine_similarity([text_embedding], [keyword_embedding])
    return similarity[0][0]

# Function to scan text for keywords and apply semantic filtering
def scan_text(text, keywords, similarity_threshold=0.1):
    keyword_matches = {}

    sentences = re.split(r'[.\n!?]', text)  # Split text into sentences for better context
    for sentence in sentences:
        for keyword in keywords:
            # Use \b to ensure the keyword is matched as a whole word and not part of another word
            pattern = rf"\b{re.escape(keyword)}\b"
            if re.search(pattern, sentence, re.IGNORECASE):  # Case-insensitive search
                semantic_score = get_context_similarity(sentence.strip(), keyword)
                if semantic_score >= similarity_threshold:
                    if keyword not in keyword_matches:
                        keyword_matches[keyword] = []
                    keyword_matches[keyword].append((semantic_score, sentence.strip()))  # Store the score and sentence

    return keyword_matches

# Function to compute TF-IDF scores
def compute_tfidf(text):
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([text])
    scores = dict(zip(vectorizer.get_feature_names_out(), tfidf_matrix.toarray()[0]))
    return scores

# Main function to scan a directory for files and analyze them
def scan_directory(directory_path, keywords):
    results = []

    for root, _, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)
            print(f"Scanning {file_path}...")

            text = extract_text(file_path)
            if not text:
                print(f"Could not extract text from {file_path}")
                continue

            decrypted_text = decrypt_base64(text)  # Decrypt text if needed

            # Scan with semantic filtering
            keyword_matches = scan_text(decrypted_text, keywords)
            tfidf_scores = compute_tfidf(decrypted_text)

            results.append({
                "file": file,
                "path": file_path,
                "keywords": keyword_matches,
                "tfidf_scores": {k: v for k, v in tfidf_scores.items() if k in keywords},
            })

    return results

# Print scan results
def print_results(results):
    counter = 1
    for result in results:
        print(f"\nDocument: {counter}")
        print(f"File: {result['file']}")
        print(f"Path: {result['path']}")
        print("=" * 40)

        print("Keyword Matches:")
        if result['keywords']:
            for word, matches in result['keywords'].items():
                print(f"\n  {word}:")
                for semantic_score, sentence in matches:
                    print(f"    🔹 Sentence: {sentence}")
                    print(f"    🔹 Semantic Score: {semantic_score:.4f}")
        else:
            print("  No keywords found in this document.")

        print("\nTop TF-IDF Scores:")
        if result['tfidf_scores']:
            for word, score in sorted(result['tfidf_scores'].items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {word}: {score:.4f}")
        else:
            print("  No TF-IDF scores available.")

        print("-" * 40)
        counter += 1


# Example usage
if __name__ == "__main__":
    db_file = "drug_keywords.db"  # Path to your database
    keywords = fetch_keywords_from_db(db_file)  # Fetch keywords from the database
    if not keywords:
        print("No keywords found in the database.")
    else:
        directory = input("Enter the directory/folder path you want to scan: ").strip()
        directory = "C:\\Users\\c2m3j\\OneDrive\\Documents\\test2"
        results = scan_directory(directory, keywords)
        print_results(results)
