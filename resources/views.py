from django.shortcuts import render
from django.db.models import Q
from resources.models import Note, StudentResource
from rest_framework.decorators import api_view
from rest_framework.response import Response
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import re
from collections import defaultdict

def resources_home(request):
    query = request.GET.get('q')
    filter_type = request.GET.get('filter')

    notes = Note.objects.all()
    resources = StudentResource.objects.all()

    if query:
        if filter_type == 'notes':
            notes = notes.filter(Q(title__icontains=query) | Q(topic__icontains=query))
            resources = StudentResource.objects.none()
        elif filter_type == 'resources':
            resources = resources.filter(Q(title__icontains=query) | Q(description__icontains=query))
            notes = Note.objects.none()
        else:
            notes = notes.filter(Q(title__icontains=query) | Q(topic__icontains=query))
            resources = resources.filter(Q(title__icontains=query) | Q(description__icontains=query))

    # ✅ Build categories dictionary
    categories = defaultdict(list)

    for n in notes:
        category = n.category or "Uncategorized"
        categories[category].append(n)

    for r in resources:
        category = r.category or "Uncategorized"
        categories[category].append(r)

    return render(request, 'resources/home.html', {
        'query': query,
        'filter': filter_type,
        'results': list(notes) + list(resources),  # search results
        'categories': dict(categories),            # categories always available
    })


from django.db.models import Avg
from .models import Note, StudentResource

# Build corpus dynamically
def build_corpus():
    notes = Note.objects.all()
    resources = StudentResource.objects.all()
    corpus, mapping = [], []

    for n in notes:
        corpus.append(f"{n.title} {n.topic}")
        mapping.append({
            "type": "note",
            "id": n.id,
            "title": n.title,
            "topic": n.topic,
            "uploaded_by": n.uploaded_by.username,
            "file_url": n.file.url if n.file else None,
            "average_rating": n.average_rating(),
        })

    for r in resources:
        corpus.append(f"{r.title} {r.description}")
        mapping.append({
            "type": "resource",
            "id": r.id,
            "title": r.title,
            "description": r.description,
            "uploaded_by": r.uploaded_by.username,
            "file_url": r.file.url if r.file else None,
            "average_rating": r.average_rating(),
        })

    return corpus, mapping


@api_view(["GET"])
def search_recommendations(request):
    query = request.GET.get("q", "")
    filter_type = request.GET.get("filter", "")  # "notes" or "resources"

    if not query:
        return Response({"recommendations": []})

    notes = Note.objects.all() if filter_type in ["", "notes"] else []
    resources = StudentResource.objects.all() if filter_type in ["", "resources"] else []

    corpus, mapping = [], []
    for n in notes:
        corpus.append(f"{n.title} {n.topic}")
        mapping.append({
            "type": "note",
            "id": n.id,
            "title": n.title,
            "topic": n.topic,
            "uploaded_by": n.uploaded_by.username,
            "file_url": n.file.url if n.file else None,
        })
    for r in resources:
        corpus.append(f"{r.title} {r.description}")
        mapping.append({
            "type": "resource",
            "id": r.id,
            "title": r.title,
            "description": r.description,
            "uploaded_by": r.uploaded_by.username,
            "file_url": r.file.url if r.file else None,
        })

    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(corpus)
    q_vec = vectorizer.transform([query])
    scores = (X * q_vec.T).toarray().ravel()
    top_indices = np.argsort(scores)[::-1][:5]
    results = [mapping[i] for i in top_indices]

    return Response({"query": query, "recommendations": results})


from resources.utils import summarize_text
import requests
from io import BytesIO
from PyPDF2 import PdfReader

@api_view(["GET"])
def summarize_pdf(request, type, pk):
    """
    Summarize either a Note or a StudentResource PDF.
    type = 'note' or 'resource'
    """
    if type == "note":
        obj = Note.objects.get(pk=pk)
    elif type == "resource":
        obj = StudentResource.objects.get(pk=pk)
    else:
        return Response({"summary": "Invalid type."})

    # ✅ Use Cloudinary URL directly instead of .path
    response = requests.get(obj.file.url)
    pdf_file = BytesIO(response.content)
    reader = PdfReader(pdf_file)
    text = " ".join(page.extract_text() for page in reader.pages if page.extract_text())

    if not text:
        return Response({"summary": "No text extracted from this PDF."})

    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    if len(sentences) <= 1:
        words = text.split()
        summary = " ".join(words[:100]) + "..."
    else:
        summary = summarize_text(text, num_sentences=5, max_words=100)

    return Response({"summary": summary})
