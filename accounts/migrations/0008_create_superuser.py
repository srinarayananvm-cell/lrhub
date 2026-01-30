from django.db import migrations
from django.contrib.auth.hashers import make_password

def create_superuser(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    if not User.objects.filter(username="arivuverseceo").exists():
        User.objects.create(
            username="arivuverseceo",
            email="srinarayananvm@gmail.com",
            password=make_password("arivuverse@2026"),
            is_superuser=True,
            is_staff=True,
            is_active=True,
        )

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_alter_profile_role'),  # adjust to latest migration
    ]

    operations = [
        migrations.RunPython(create_superuser),
    ]
