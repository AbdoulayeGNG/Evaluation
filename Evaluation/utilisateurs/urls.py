from django.urls import path
from . import views
from .views import CustomLoginView
from django.contrib.auth import views as auth_views

app_name = 'utilisateurs'

urlpatterns = [
    path('', views.accueil, name='accueil'),
    path('creation/', views.CreationCompte, name='creerCompte'),
    path('connexion/', views.connecter, name='connecter'),
    path('accueil/', views.accueil, name='accueil'),
    path('deconnexion/', views.deconnecter, name='deconnecter'),
    path('inscription/', views.inscription, name='inscription'),
    path('utilisateur/<int:user_id>/', views.get_user, name='get_user'),
    path('utilisateur/modifier/<int:user_id>/', views.modifier_utilisateur, name='modifier_utilisateur'),
    path('utilisateur/supprimer/<int:user_id>/', views.supprimer_utilisateur, name='supprimer_utilisateur'),
    path('utilisateurs/', views.liste_utilisateurs, name='liste_utilisateurs'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
]


