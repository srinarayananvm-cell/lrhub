from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile

class SignupSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=Profile.ROLE_CHOICES)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'role']

    def validate(self, data):
        if data['password1'] != data['password2']:
            raise serializers.ValidationError("Passwords don’t match.")
        return data

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password1']
        )
        # ✅ Create profile with role
        Profile.objects.create(user=user, role=validated_data['role'])
        return user

from rest_framework import serializers
from .models import Profile

class ProfileSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(required=False)

    class Meta:
        model = Profile
        fields = ['id', 'user', 'role', 'approved', 'avatar', 'bio', 'phone']

    def update(self, instance, validated_data):
        avatar = validated_data.pop('avatar', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if avatar:
            instance.avatar = avatar  # ✅ Cloudinary handles storage here
        instance.save()
        return instance
