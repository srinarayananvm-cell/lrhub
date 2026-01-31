from rest_framework import serializers
from .models import Note

class NoteSerializer(serializers.ModelSerializer):
    file = serializers.FileField(required=True)

    class Meta:
        model = Note
        fields = ['id', 'title', 'topic', 'version', 'file', 'uploaded_by',
                  'uploaded_at', 'category', 'downloads']

    def create(self, validated_data):
        return Note.objects.create(**validated_data)
from rest_framework import serializers
from .models import StudentResource

class StudentResourceSerializer(serializers.ModelSerializer):
    file = serializers.FileField(required=True)

    class Meta:
        model = StudentResource
        fields = ['id', 'title', 'description', 'file', 'uploaded_by',
                  'uploaded_at', 'verified', 'category', 'downloads']

    def create(self, validated_data):
        return StudentResource.objects.create(**validated_data)
