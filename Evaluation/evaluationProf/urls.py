from django.urls import path
from . import views



urlpatterns = [
    path('ajouter_evaluation/', views.ajouter_evaluation, name='ajouter_evaluation'),
    path('liste_evaluations/', views.liste_evaluations, name='liste_evaluations'),
    path("evaluations/", views.evaluationEtudiant, name="evaluationEtudiant"),
    path("evaluations/modifier/<int:evaluation_id>/", views.modifier_evaluation, name="modifier_evaluation"),
    path("evaluations/supprimer/<int:evaluation_id>/", views.supprimer_evaluation, name="supprimer_evaluation"),
]