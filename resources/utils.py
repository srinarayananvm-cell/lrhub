import requests
from io import BytesIO
import pdfplumber
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from asgiref.sync import sync_to_async

# --- PDF Extraction (Cloudinary-ready) ---
def extract_pdf_text_from_url(url: str) -> str:
    """Fetch and extract text from a Cloudinary-hosted PDF using pdfplumber."""
    try:
        response = requests.get(url)
        if response.status_code != 200:
            return ""
        pdf_file = BytesIO(response.content)
        text = ""
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text.strip()
    except Exception:
        return ""

# --- Relevance Scoring ---
def relevance_score(pdf_text: str, query: str, max_words: int = 40) -> dict:
    """
    Compute relevance between PDF text and query.
    Splits into sentences/paragraphs, finds best match, and returns score + snippet.
    """
    sentences = re.split(r'(?<=[.!?])\s+|\n+', pdf_text.strip())
    if not sentences:
        return {"score": 0.0, "match": "No content available"}

    docs = sentences + [query]
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf = vectorizer.fit_transform(docs)
    query_vec = tfidf[-1]

    sims = cosine_similarity(tfidf[:-1], query_vec).ravel()
    best_idx = sims.argmax()
    best_sentence = sentences[best_idx]

    words = best_sentence.split()
    if len(words) > max_words:
        best_sentence = " ".join(words[:max_words]) + "..."

    return {
        "score": round(float(sims.max()) * 100, 2),
        "match": best_sentence
    }

# ✅ Async wrapper for non-blocking use in async views
@sync_to_async
def relevance_score_async(pdf_text: str, query: str, max_words: int = 40) -> dict:
    return relevance_score(pdf_text, query, max_words)

# --- Summarization ---
def summarize_text(text: str, num_sentences: int = 5, max_words: int = 100) -> str:
    sentences = re.split(r'(?<=[.!?])\s+|\n+', text.strip())
    if not sentences:
        return "No content available to summarize."

    if len(sentences) <= 1:
        words = text.split()
        return " ".join(words[:max_words]) + "..."

    vectorizer = TfidfVectorizer(stop_words="english")
    X = vectorizer.fit_transform(sentences)
    scores = np.array(X.sum(axis=1)).ravel()

    top_indices = scores.argsort()[-num_sentences:][::-1]
    summary_sentences = [sentences[i] for i in sorted(top_indices)]
    summary_text = " ".join(summary_sentences)

    words = summary_text.split()
    if len(words) > max_words:
        summary_text = " ".join(words[:max_words]) + "..."

    return summary_text
