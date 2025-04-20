from django.urls import path
from . import views
from django.conf import settings

app_name = 'prof'

urlpatterns = [
    path('dashboard/', views.dashboard_professeur, name='dashboard_professeur'),
    path('evaluations/', views.liste_evaluations, name='liste_evaluations'),
    path('profil/', views.profil_professeur, name='profil'),
]