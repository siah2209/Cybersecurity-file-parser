import os
import re
import base64
import chardet
import sqlite3
import hashlib
from collections import Counter
import docx
from stegano import lsb  # Steganography decoder

from transformers import AutoTokenizer, AutoModel
from huggingface_hub import login
import torch
from sklearn.metrics.pairwise import cosine_similarity

#tweak with scoring system and volume
#scoring criteria

login(token="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")  # Replace with your actual Hugging Face token

# Load DarkBERT
MODEL_NAME = "s2w-ai/DarkBERT"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)


# ========== Context Cancellers ==========
context_cancellers = [
    # 🏥 Medical / Clinical
    "doctor", "prescribed", "prescription", "hospital", "pharmacy", "clinic",
    "treatment", "care", "clinical", "nurse", "medicine", "medically", "medical",
    "surgery", "recovery", "hospice", "dispensary", "diagnosis", "therapist", "rehab",
    "pain relief", "patient", "physician", "approved use",

    # 👟 Business / Retail
    "resale", "retail", "wholesale price", "inventory", "supplier", "shipment of shoes",
    "stock", "restock", "limited edition", "order", "product", "store", "shop", "shopping",
    "boutique", "footwear", "sneaker", "kicks", "pairs", "size 10", "drop", "drops",
    "shipping", "cash flow", "supply chain", "fulfillment", "purchase", "online store",
    "customer", "merch", "business", "vendor", "brand", "exclusive", "distribution center",

    # 🍳 Culinary / Social
    "cookout", "barbecue", "wings", "grill", "seasoning", "chef", "cooking", "recipe",
    "kitchen", "herb seasoning", "potluck", "dinner", "meal prep", "bake", "ingredients",
    "flavor", "food", "restaurant", "spice", "culinary", "marinade",

    # 📚 Education / Research
    "study", "experiment", "research", "academic", "university", "conference", "seminar",
    "clinical trial", "lab", "scientific", "paper", "results", "treatment study",

    # 💬 Communication / Social Context
    "invitation", "event", "party", "gathering", "celebration", "birthday", "graduation",
    "reunion", "wedding", "social", "friend group", "hang out", "get together"
]

# ========== Warning Words (Contextual Suspicion) ==========
warning_words = [
    "restock", "stock", "limited edition", "drop", "drops", "my guy got it", "link me later",
    "ping me when it's in", "got the cash app ready", "my connect hitting me up", "street price",
    "waiting on the drop", "say less, i got you", "hit the line", "shipment lands tomorrow",
    "out of state delivery", "transporting through the mail", "drug", "for the low", "tabs",
    "a pop", "package coming in", "crack", "a zip"

]

# ========== Database Keyword Fetch ==========
def fetch_keywords_from_db(db_file="drug_keywords.db"):
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT keyword FROM keywords")
        keywords = [row[0] for row in cursor.fetchall()]
        conn.close()
        return keywords
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return []

# ========== File Readers ==========
def read_txt(file_path):
    with open(file_path, 'rb') as file:
        rawdata = file.read()
        result = chardet.detect(rawdata)
        encoding = result['encoding']
        try:
            return rawdata.decode(encoding)
        except UnicodeDecodeError:
            return ""

def read_pdf(file_path):
    from PyPDF2 import PdfReader
    try:
        reader = PdfReader(file_path)
        return " ".join([page.extract_text() for page in reader.pages if page.extract_text()])
    except Exception as e:
        print(f"Error reading PDF {file_path}: {e}")
        return ""

def read_docx(file_path):
    from docx import Document
    try:
        doc = docx.Document(file_path)
        return " ".join([paragraph.text for paragraph in doc.paragraphs])
    except Exception as e:
        print(f"Error reading DOCX {file_path}: {e}")
        return ""

def read_html(file_path):
    from bs4 import BeautifulSoup
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file, 'html.parser')
            return soup.get_text()
    except Exception as e:
        print(f"Error reading HTML {file_path}: {e}")
        return ""

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
    
# ========== Semantic Similarity ==========
def get_context_similarity(text, keyword):
    inputs = tokenizer([text, keyword], padding=True, truncation=True, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**inputs)
    text_embedding = outputs.last_hidden_state[0].mean(dim=0).numpy()
    keyword_embedding = outputs.last_hidden_state[1].mean(dim=0).numpy()
    similarity = cosine_similarity([text_embedding], [keyword_embedding])
    return similarity[0][0]

# ========== Base64 Decrypt ==========
def decrypt_base64(text):
    try:
        decoded_bytes = base64.b64decode(text)
        result = chardet.detect(decoded_bytes)
        encoding = result['encoding']
        return decoded_bytes.decode(encoding)
    except Exception:
        return text

# ========== SHA-256 Hash ==========
def compute_file_hash(file_path, algo="sha256"):
    hash_func = hashlib.new(algo)
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except Exception as e:
        print(f"Error computing hash for {file_path}: {e}")
        return None

# ========== Steganography Decoder ==========
def decode_steganography_from_image(image_path):
    try:
        hidden_message = lsb.reveal(image_path)
        if hidden_message:
            print(f"[STEGO FOUND] Hidden message in {image_path}:\n{hidden_message}")
        else:
            print(f"[NO STEGO] No hidden message found in {image_path}")
        return hidden_message
    except Exception as e:
        print(f"Error decoding steganography in {image_path}: {e}")
        return None

# ========== Keyword Scanner ==========
def scan_text_with_context(text, phrases, cancellers, semantic_threshold=0.15):
    matches = {}
    text = text.lower()
    phrases = [p.lower() for p in phrases]
    cancellers = [c.lower() for c in cancellers]
    sentences = re.split(r'(?<=[.!?])\s+', text)

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        scanned_phrases = set()  # <-- Fix: Track already matched phrases in this sentence

        for phrase in phrases:
            if phrase in scanned_phrases:
                continue  # Skip if already matched in this sentence

            if re.search(rf'\b{re.escape(phrase)}\b', sentence):
                try:
                    semantic_score = get_context_similarity(sentence, phrase)
                except Exception as e:
                    print(f"[ERROR] Semantic check failed for '{phrase}': {e}")
                    continue

                if any(cancel in sentence for cancel in cancellers):
                    print(f"[SUPPRESSED 🚫] '{phrase}' in: \"{sentence}\" (Semantic Score: {semantic_score:.4f})")
                    continue

                if semantic_score >= semantic_threshold:
                    print(f"[MATCHED ✅] '{phrase}' in: \"{sentence}\" (Semantic Score: {semantic_score:.4f})")
                    if phrase not in matches:
                        matches[phrase] = []
                    matches[phrase].append((semantic_score, sentence))
                    scanned_phrases.add(phrase)  # <-- Mark as matched
                else:
                    print(f"[FILTERED ❌] '{phrase}' in: \"{sentence}\" (Semantic Score: {semantic_score:.4f})")
    return matches

# ========== Warning Word Scanner ==========
def scan_warning_words_with_context(text, warning_words):
    warnings = {}
    text = text.lower()
    warning_words = [w.lower() for w in warning_words]
    sentences = re.split(r'(?<=[.!?])\s+', text)

    for sentence in sentences:
        for word in warning_words:
            if re.search(rf'\b{re.escape(word)}\b', sentence):
                print(f"[⚠️ WARNING] '{word}' in: \"{sentence.strip()}\"")
                warnings[word] = warnings.get(word, 0) + 1
    return warnings

# ========== Directory Scanner ==========
def scan_directory(directory_path, keywords):

    results = []

    for root, _, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)
            print(f"Found file: {file_path}")  # <-- ADD THI

            if file.lower().endswith((".jpg", ".jpeg", ".png")):
                text = ""
            else:
                text = extract_text(file_path)
                if not text:
                    print(f"Could not extract text from {file_path}")
                    continue

            decrypted_text = decrypt_base64(text)

            stego_keywords = {}
            stego_warnings = {}

            # Always initialize
            stego_message = None
            is_image_file = file.lower().endswith((".jpg", ".jpeg", ".png"))

            # Extract stego if it's an image
            if is_image_file:
                stego_message = decode_steganography_from_image(file_path)

                # Deduplicate overlapping sentences
                if stego_message:
                    main_sentences = set(re.split(r'(?<=[.!?])\s+', decrypted_text.lower()))
                    stego_sentences = re.split(r'(?<=[.!?])\s+', stego_message)

                    filtered_stego = []
                    for sentence in stego_sentences:
                        stripped = sentence.strip().lower()
                        if stripped and stripped not in main_sentences:
                            filtered_stego.append(sentence)

                    stego_message = " ".join(filtered_stego)

            keyword_matches = scan_text_with_context(decrypted_text, keywords, context_cancellers)
            warning_matches = scan_warning_words_with_context(decrypted_text, warning_words)
            file_hash = compute_file_hash(file_path)

            # Decode steganography if image
            if file.lower().endswith((".jpg", ".jpeg", ".png")):
                stego_message = decode_steganography_from_image(file_path)
            else:
                stego_message = None

            is_image_file = file.lower().endswith((".jpg", ".jpeg", ".png"))

            # Only scan stego message if the file isn't already textual
            if stego_message and is_image_file:
                stego_keywords = scan_text_with_context(stego_message, keywords, context_cancellers)
                for key, value_list in stego_keywords.items():
                    if key not in keyword_matches:
                        keyword_matches[key] = []
                    keyword_matches[key].extend(value_list)

                stego_warnings = scan_warning_words_with_context(stego_message, warning_words)
                for key, value in stego_warnings.items():
                    warning_matches[key] = warning_matches.get(key, 0) + value


            # Calculate risk score
            # Sum of all semantic scores across all matched keywords
            #This multiplies the sum of semantic scores by 5 and adds the usual +2 for each warning.
            # Total number of sentences
            total_sentences = len(re.split(r'(?<=[.!?])\s+', decrypted_text))
            total_sentences = max(total_sentences, 1)  # Avoid division by zero

            # Suspicious sentence count (based on matches)
            suspicious_sentences = sum(len(entries) for entries in keyword_matches.values())

            # Risk density: suspicious matches per sentence
            density_score = suspicious_sentences / total_sentences
            density_score = min(density_score, 1.5)


            # Base semantic + warning score
            # Sum both normal and stego semantic scores
            # Primary content scores
            primary_semantic_score = sum(score for entries in keyword_matches.values() for score, _ in entries)
            primary_warning_hits = sum(warning_matches.values())

            # Stego content scores (downweighted)
            stego_semantic_score = sum(score for entries in (stego_keywords or {}).values() for score, _ in entries)
            stego_warning_hits = sum((stego_warnings or {}).values())

            # Weight the stego content less (adjust weight as needed)
            stego_weight = 0.5

            # Final base score
            # Amplify based on volume and high semantic values
            amplified_primary_score = sum((score ** 1.5) for entries in keyword_matches.values() for score, _ in entries)
            amplified_stego_score = sum((score ** 1.5) for entries in (stego_keywords or {}).values() for score, _ in entries)

            # Emphasize keyword *count*
            keyword_volume = sum(len(entries) for entries in keyword_matches.values())
            stego_volume = sum(len(entries) for entries in (stego_keywords or {}).values())

            # Final base score: combines semantic strength + volume + warning hits
            base_score = (
                amplified_primary_score * 6 +
                primary_warning_hits * 2 +
                keyword_volume * 1.5 +
                (amplified_stego_score * 6 + stego_warning_hits * 1 + stego_volume * 1.2) * stego_weight
            )


            # Risk density based on total matches (text + stego)
            total_sentences = len(re.split(r'(?<=[.!?])\s+', decrypted_text + " " + (stego_message or "")))
            total_sentences = max(total_sentences, 1)
            suspicious_sentences = (
                sum(len(entries) for entries in keyword_matches.values()) +
                sum(len(entries) for entries in (stego_keywords or {}).values())
            )
            density_score = suspicious_sentences / total_sentences
            density_score = min(density_score, 1.5)

            # Final risk score
            score = base_score * (1 + 2 * density_score)


            results.append({
                "file": file,
                "path": file_path,
                "hash": file_hash,
                "keywords": keyword_matches,
                "warnings": warning_matches,
                "stego": stego_message,
                "score": score
            })

    return results

# ========== Print Results ==========
# Updated version of your script that stores and prints semantic scores

def print_results(results):
    counter = 1
    for result in results:
        print(f"\nDocument: {counter}")
        print(f"File: {result['file']}\nPath: {result['path']}")
        print(f"SHA-256 Hash: {result['hash']}")
        print("Keyword Matches:")
        if result['keywords']:
            for word, entries in result['keywords'].items():
                print(f"\n  {word}:")
                for score, sentence in entries:
                    print(f"    🔹 Sentence: {sentence}")
                    print(f"    🔹 Semantic Score: {score:.4f}")
        else:
            print("  No flagged keywords in this document.")

        print("Warning Word Matches:")
        if result['warnings']:
            for word, count in result['warnings'].items():
                print(f"   {word}: {count}")
        else:
            print("  No warning words detected.")

        if result.get("stego"):
            print("Stego Message Found:")
            print(f"  {result['stego']}")

        print(f"📊 Risk Score: {result['score']}")
        counter += 1


# ========== Main ==========

        """
       if __name__ == "__main__":
    db_file = "drug_keywords.db"
    keywords = fetch_keywords_from_db(db_file)

    if not keywords:
        print("No keywords found in the database.")
    else:
        print("Welcome to the NSUTriage scanner!")
        directory = input("Enter the directory/folder path you want to scan: ").strip()
        # Optional: hardcode during testing
        directory = "C:\\Users\\c2m3j\\OneDrive\\Documents\\test2"
        results = scan_directory(directory, keywords)
        print_results(results) 
        """

    if __name__ == "__main__":
        db_file = "drug_keywords.db"
        keywords = fetch_keywords_from_db(db_file)

        if not keywords:
            print("No keywords found in the database.")
        else:
            print("Welcome to the NSUTriage scanner!")
        directory = input("Enter the directory/folder path you want to scan: ").strip()
        results = scan_directory(directory, keywords)
        print_results(results)

