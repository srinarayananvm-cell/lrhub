from django.apps import AppConfig
class ResourcesConfig(AppConfig):
    name = 'resources'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        import resources.signals   # 👈 ensures signals are registered
