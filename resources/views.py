from django.shortcuts import render
from django.db.models import Q
from resources.models import Note, StudentResource
from rest_framework.decorators import api_view
from rest_framework.response import Response
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import re


def resources_home(request):
    query = request.GET.get('q')
    filter_type = request.GET.get('filter')
    results = []

    if query:
        if filter_type == 'notes':
            results = Note.objects.filter(
                Q(title__icontains=query) | Q(topic__icontains=query)
            )
        elif filter_type == 'resources':
            results = StudentResource.objects.filter(
                Q(title__icontains=query) | Q(description__icontains=query)
            )
        else:
            # Search across both
            notes = Note.objects.filter(
                Q(title__icontains=query) | Q(topic__icontains=query)
            )
            resources = StudentResource.objects.filter(
                Q(title__icontains=query) | Q(description__icontains=query)
            )
            results = list(notes) + list(resources)

    return render(request, 'resources/home.html', {
        'query': query,
        'filter': filter_type,
        'results': results,
    })


from django.db.models import Avg
from rest_framework.decorators import api_view
from rest_framework.response import Response
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
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

from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Note, StudentResource
from resources.utils import extract_text_from_pdf, summarize_text

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

    text = extract_text_from_pdf(obj.file.path)
    if not text:
        return Response({"summary": "No text extracted from this PDF."})

    # Debug: see how many sentences we actually get
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    if len(sentences) <= 1:
        # Fallback: trim first 60 words if only one block
        words = text.split()
        summary = " ".join(words[:100]) + "..."
    else:
        # Use summarizer with compression
        summary = summarize_text(text, num_sentences=5, max_words=100)

    return Response({"summary": summary})

