from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Utilisateur, Professeur, Etudiant, Administrateur

@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    list_filter = ('is_staff', 'is_superuser', 'is_active')

@admin.register(Professeur)
class ProfesseurAdmin(admin.ModelAdmin):
    list_display = ('user', 'departement')
    search_fields = ('user__username', 'user__first_name', 'departement')
    list_filter = ('departement',)

@admin.register(Etudiant)
class EtudiantAdmin(admin.ModelAdmin):
    list_display = ('user', 'licence', 'departement')
    search_fields = ('user__username', 'licence', 'departement')
    list_filter = ('departement',)

@admin.register(Administrateur)
class AdministrateurAdmin(admin.ModelAdmin):
    list_display = ('user', 'contact', 'fonction')
    search_fields = ('user__username', 'fonction')
    list_filter = ('fonction',)
