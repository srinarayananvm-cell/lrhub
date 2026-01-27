import pdfplumber
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from a PDF file using pdfplumber."""
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()

def summarize_text(text: str, num_sentences: int = 5, max_words: int = 100) -> str:
    # Split into sentences (handle punctuation and newlines)
    sentences = re.split(r'(?<=[.!?])\s+|\n+', text.strip())
    if not sentences:
        return "No content available to summarize."

    # Fallback: if only one block, trim words
    if len(sentences) <= 1:
        words = text.split()
        return " ".join(words[:max_words]) + "..."

    # TF-IDF scoring
    vectorizer = TfidfVectorizer(stop_words="english")
    X = vectorizer.fit_transform(sentences)
    scores = np.array(X.sum(axis=1)).ravel()

    # Pick top sentences
    top_indices = scores.argsort()[-num_sentences:][::-1]
    summary_sentences = [sentences[i] for i in sorted(top_indices)]
    summary_text = " ".join(summary_sentences)

    # Trim to max_words
    words = summary_text.split()
    if len(words) > max_words:
        summary_text = " ".join(words[:max_words]) + "..."

    return summary_text

