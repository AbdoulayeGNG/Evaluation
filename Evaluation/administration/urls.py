from django.urls import path
from . import views

app_name = 'administration'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('professeurs/', views.gestion_professeurs, name='gestion_professeurs'),
    path('professeurs/', views.liste_professeurs, name='liste_professeurs'),
    path('professeurs/ajouter/', views.ajouter_professeur, name='ajouter_professeur'),
    path('professeurs/<int:pk>/modifier/', views.modifier_professeur, name='modifier_professeur'),
    path('professeurs/<int:pk>/supprimer/', views.supprimer_professeur, name='supprimer_professeur'),
    path('professeurs/<int:pk>/detail/', views.detail_professeur, name='detail_professeur'),
    path('etudiants/', views.gestion_etudiants, name='gestion_etudiants'),
    path('etudiants/ajouter/', views.ajouter_etudiant, name='ajouter_etudiant'),
    path('etudiants/liste/', views.liste_etudiants, name='liste_etudiants'),
    path('etudiants/<int:pk>/detail/', views.detail_etudiant, name='detail_etudiant'),
    path('etudiants/<int:pk>/modifier/', views.modifier_etudiant, name='modifier_etudiant'),  # Ajout de l'URL de modification
    path('etudiants/<int:pk>/supprimer/', views.supprimer_etudiant, name='supprimer_etudiant'),
    path('evaluations/', views.gestion_evaluations, name='gestion_evaluations'),
    path('evaluations/<int:pk>/valider/', views.valider_evaluation, name='valider_evaluation'),
    path('statistiques/', views.statistiques, name='statistiques'),
]