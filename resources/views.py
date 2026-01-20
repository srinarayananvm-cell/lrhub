from django.shortcuts import render
from django.db.models import Q
from resources.models import Note, StudentResource

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
