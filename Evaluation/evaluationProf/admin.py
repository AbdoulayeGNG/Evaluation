from django.contrib import admin
from .models import Formation, Critere,NoteCritere,Evaluation
# Register your models here.
admin.site.register(Formation)
admin.site.register(Critere)
admin.site.register(NoteCritere)
admin.site.register(Evaluation)