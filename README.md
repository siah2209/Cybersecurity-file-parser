# Cybersecurity-file-parser
# NSUTriage File Scanner

This repository contains the source code for the NSUTriage File Scanner, a cybersecurity tool designed to identify and flag suspicious content, particularly related to illicit drug activities, within various file types. The scanner leverages natural language processing (NLP) techniques, including semantic similarity with a specialized DarkBERT model, and steganography detection to provide a comprehensive risk assessment of scanned files.

---

## Features

* **Multi-format File Parsing**: Capable of extracting text from `.txt`, `.pdf`, `.docx`, and `.html` files.
* **Keyword Detection**: Identifies predefined drug-related keywords and phrases within the extracted text.
* **Contextual Semantic Analysis**: Utilizes a fine-tuned DarkBERT model to assess the semantic similarity between identified keywords and their surrounding sentences, filtering out benign mentions and highlighting truly suspicious contexts.
* **Warning Word Identification**: Flags general "warning" words that might indicate suspicious communication or activities.
* **Base64 Decryption**: Automatically decrypts Base64 encoded strings found within text content, expanding the scope of analysis.
* **Steganography Detection**: Scans image files (`.jpg`, `.jpeg`, `.png`) for hidden messages using LSB (Least Significant Bit) steganography, and subjects any found messages to the same text analysis.
* **File Hashing**: Computes SHA-256 hashes for all scanned files to ensure integrity and provide a unique identifier.
* **Risk Scoring**: Assigns a numerical risk score to each file based on the volume and semantic relevance of detected keywords, warning words, and steganographic content.
* **Database Integration**: Stores and retrieves drug-related keywords from a SQLite database (`drug_keywords.db`), allowing for easy updates and expansion of the keyword list.
* **Interactive Web Interface**: Provides a user-friendly web interface (Flask-based) for inputting directory paths, initiating scans, and downloading detailed PDF reports.

---

## Installation

To set up and run the NSUTriage File Scanner, follow these steps:

### Prerequisites

* Python 3.8+
* `pip` (Python package installer)

### Steps

1.  **Clone the Repository**:
    ```bash
    git clone [https://github.com/your-username/NSUTriage-File-Scanner.git](https://github.com/your-username/NSUTriage-File-Scanner.git)
    cd NSUTriage-File-Scanner
    ```

2.  **Install Dependencies**:
    Create a virtual environment (recommended) and install the required Python packages:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```
    *(Note: A `requirements.txt` file is not provided but can be generated using `pip freeze > requirements.txt` after manually installing the necessary libraries such as `Flask`, `torch`, `transformers`, `scikit-learn`, `PyPDF2`, `python-docx`, `beautifulsoup4`, `chardet`, `stegano`, `huggingface_hub`, and `reportlab`)*

3.  **Hugging Face Authentication**:
    The DarkBERT model requires authentication with Hugging Face.
    * Go to [Hugging Face Settings](https://huggingface.co/settings/tokens) and create a new access token (with `read` role).
    * Replace `"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"` in `test_parser.py` (line 12) with your actual Hugging Face token.

4.  **Initialize the Keyword Database**:
    The `drug_keywords.db` database contains the predefined keywords used for scanning. Run the `database.py` script to create and populate this database:
    ```bash
    python database.py
    ```
    This will create `drug_keywords.db` and insert an initial set of drug-related phrases into it.

---

## Usage

There are two ways to use the NSUTriage File Scanner:

### 1. Web Interface (Recommended)

To run the application with the web interface:

1.  **Start the Flask Application**:
    ```bash
    python app.py
    ```
    The application will typically run on `http://127.0.0.1:5000/`.

2.  **Access the Interface**:
    Open your web browser and navigate to `http://127.0.0.1:5000/`. 

3.  **Scan a Directory**:
    * [cite_start]Enter the full path to the directory you want to scan in the input field. 
    * [cite_start]Click "Analyze File" to start the scan. 
    * [cite_start]Once the scan is complete, click "View File Contents" to download a PDF report of the findings. [cite: 1, 3]

### 2. Command-Line Interface (for basic testing)

You can run the `test_parser.py` script directly from the command line for basic scanning:

```bash
python test_parser.py
The script will prompt you to enter the directory path you want to scan. The results will be printed directly to the console.

Project Structure
app.py: The Flask application that provides the web interface and handles API requests for scanning and reporting.

test_parser.py: Contains the core logic for file parsing, text extraction, semantic analysis, steganography detection, hashing, and risk scoring.

database.py: Script to initialize and populate the drug_keywords.db SQLite database with drug-related keywords.

drug_keywords.db: The SQLite database file storing the keywords for the scanner.


File-parse-test.html: The HTML template for the web interface. 

testphoto.jpg: An example image file that can be used for steganography testing.

other.py: (Optional) A utility script that might contain examples for steganography encoding/decoding or directory testing.

How it Works
Keyword Database: A SQLite database (drug_keywords.db) is pre-populated with an extensive list of phrases categorized by drug types (Marijuana, Cocaine, Oxycodone, Fentanyl, MDMA/Ecstasy, Heroin) and related categories like "Sales/Pricing" and "Dealer/Communication".

File Traversal and Text Extraction: The scan_directory function recursively walks through the specified directory, identifies various file types, and extracts their textual content. For images, it attempts to detect hidden steganographic messages.

Text Preprocessing: Extracted text undergoes Base64 decryption and is split into individual sentences for more granular analysis.

Semantic Analysis with DarkBERT:

For each sentence and each predefined keyword, the system calculates a semantic similarity score using the DarkBERT model. DarkBERT is a BERT-based model specifically trained on dark web data, making it effective for identifying illicit content.

Context Cancellers: A list of "context cancellers" (e.g., "doctor," "hospital," "retail," "cooking") is used to suppress false positives. If a keyword appears in a sentence alongside a context canceller, it's considered less suspicious and potentially filtered out, indicating a benign context (e.g., "doctor prescribed oxycodone").

Warning Word Scan: Separately, a list of "warning words" (e.g., "restock," "drop," "street price") is scanned for in the text to identify general indicators of suspicious activity.

Steganography Analysis: If an image file is encountered, the stegano library is used to detect and extract any hidden LSB messages. If a message is found, it is then subjected to the same keyword and warning word analysis as regular text.

Risk Scoring: A comprehensive risk score is calculated for each file based on:

The sum of amplified semantic scores from keyword matches (scores are raised to a power to give more weight to stronger matches).

The count of warning word hits.

The "volume" or count of distinct keywords found.

A "density score" which considers the proportion of suspicious sentences to the total sentences in the document, amplifying the overall risk for documents with high concentrations of flagged content.

Steganographic content also contributes to the score, albeit with a customizable lower weight.

Reporting: The results, including file details, hash, keyword matches (with semantic scores and original sentences), warning word counts, any decoded steganographic messages, and the final risk score, are presented in the console and can be downloaded as a formatted PDF report via the web interface.

