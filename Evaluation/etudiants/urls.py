from django.urls import path
from . import views

urlpatterns = [
    # ...existing code...
    path('dashboard/', views.dashboard_etudiant, name='dashboard_etudiant'),
    path('evaluationEtudiant/', views.liste_evaluations, name='evaluationEtudiantTout'),
    path('profil/', views.profil_etudiant, name='profil'),
    path('profil/update/', views.update_profile, name='update_profile'),
     path('professeurs/', views.liste_professeurs, name='formateur'),

]