import pdfplumber
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def extract_pdf_text(file_path_or_obj):
    text = ""
    with pdfplumber.open(file_path_or_obj) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def relevance_score(pdf_text, query):
    docs = [pdf_text, query]
    vectorizer = TfidfVectorizer()
    tfidf = vectorizer.fit_transform(docs)
    similarity = cosine_similarity(tfidf[0:1], tfidf[1:2])
    return float(similarity[0][0])
