import pdfplumber
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from asgiref.sync import sync_to_async

def extract_pdf_text(file_path_or_obj):
    """Extract text from a PDF file using pdfplumber."""
    text = ""
    with pdfplumber.open(file_path_or_obj) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()

def relevance_score(pdf_text: str, query: str, max_words: int = 40) -> dict:
    """
    Compute relevance between PDF text and query.
    Splits into sentences/paragraphs, finds best match, and returns score + snippet.
    """
    # Split into sentences/paragraphs (handle punctuation + newlines)
    sentences = re.split(r'(?<=[.!?])\s+|\n+', pdf_text.strip())
    if not sentences:
        return {"score": 0.0, "match": "No content available"}

    # Build corpus: all sentences + query
    docs = sentences + [query]
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf = vectorizer.fit_transform(docs)
    query_vec = tfidf[-1]

    # Compute similarities
    sims = cosine_similarity(tfidf[:-1], query_vec).ravel()
    best_idx = sims.argmax()
    best_sentence = sentences[best_idx]

    # Trim snippet
    words = best_sentence.split()
    if len(words) > max_words:
        best_sentence = " ".join(words[:max_words]) + "..."

    return {
        "score": round(float(sims.max()) * 100, 2),  # normalized 0–100
        "match": best_sentence
    }

# ✅ Async wrapper for non-blocking use in async views
@sync_to_async
def relevance_score_async(pdf_text: str, query: str, max_words: int = 40) -> dict:
    return relevance_score(pdf_text, query, max_words)
