from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
# from .models import Utilisateurs

# class UtilisateurPersonnaliseAdmin(UserAdmin):
#     list_display = ('username', 'nom', 'prenom', 'departement', 'is_staff')
#     fieldsets = (
#         (None, {'fields': ('username', 'password')}),
#         ('Informations personnelles', {'fields': ('nom', 'prenom', 'departement')}),
#         ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
#         ('Dates importantes', {'fields': ('last_login', 'date_joined')}),
#     )

# admin.site.register(Utilisateurs, UtilisateurPersonnaliseAdmin)

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Utilisateur, Etudiant, Professeur, Administrateur

# Personnalisation de l'affichage du modèle Utilisateur
class UtilisateurAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_superuser', 'is_staff')
    list_filter = ('role', 'is_superuser', 'is_staff')
    search_fields = ('username', 'email')
    ordering = ('role',)

    fieldsets = (
        ("Informations personnelles", {'fields': ('username', 'email', 'password')}),
        ("Permissions", {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ("Rôle", {'fields': ('role',)}),
    )

    add_fieldsets = (
        ("Créer un nouvel utilisateur", {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role'),
        }),
    )

# Enregistrement des autres modèles
class EtudiantAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prenom', 'departement', 'licence', 'telephone')
    search_fields = ('nom', 'prenom', 'email')

class ProfesseurAdmin(admin.ModelAdmin):
    list_display = ('user', 'departement')
    search_fields = ('user__username', 'email')

class AdministrateurAdmin(admin.ModelAdmin):
    list_display = ('user',)
    search_fields = ('user__username',)

# Enregistrement des modèles dans Django Admin
#admin.site.register(Utilisateur, UtilisateurAdmin)
admin.site.register(Etudiant, EtudiantAdmin)
admin.site.register(Professeur, ProfesseurAdmin)
admin.site.register(Administrateur, AdministrateurAdmin)

# Personnalisation du titre de l'admin Django
admin.site.site_header = "Gestion des Utilisateurs - Administration"
admin.site.site_title = "Admin - Plateforme d'Évaluation"
admin.site.index_title = "Gestion des rôles et utilisateurs"
