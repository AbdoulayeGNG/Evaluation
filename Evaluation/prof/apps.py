from django.apps import AppConfig

class ProfConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'prof'

    def ready(self):
        import prof.templatetags.prof_extras
