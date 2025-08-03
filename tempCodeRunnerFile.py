ace with your actual Hugging Face token

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
    "a pop", "package coming in"

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