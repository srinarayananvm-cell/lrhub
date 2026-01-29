from django.contrib import admin
from .models import Note, StudentResource, Rating, Recommendation

class RatingInline(admin.TabularInline):
    model = Rating
    extra = 0

class RecommendationInline(admin.TabularInline):
    model = Recommendation
    extra = 0

@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('title', 'topic', 'version', 'uploaded_by', 'uploaded_at','downloads', 'category')
    inlines = [RatingInline, RecommendationInline]

@admin.register(StudentResource)
class StudentResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'uploaded_by', 'uploaded_at','downloads', 'category')
    inlines = [RatingInline, RecommendationInline]

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'value', 'note', 'resource', 'created_at')
    list_filter = ('value', 'created_at')
    search_fields = ('user__username',)

@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ('user', 'note', 'resource', 'comment', 'created_at')
    search_fields = ('user__username', 'comment')
