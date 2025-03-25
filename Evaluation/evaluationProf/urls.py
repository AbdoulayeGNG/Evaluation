from django.urls import path
from . import views



urlpatterns = [
    path('ajouter_evaluation/', views.ajouter_evaluation, name='ajouter_evaluation'),
    path('liste_evaluations/', views.liste_evaluations, name='liste_evaluations'),
]