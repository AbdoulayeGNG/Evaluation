from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Utilisateur, Etudiant, Professeur, Administrateur

class UtilisateurAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informations personnelles', {'fields': ('email', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'role', 'password1', 'password2'),
        }),
    )
    search_fields = ('username', 'email')
    ordering = ('username',)

admin.site.register(Utilisateur, UtilisateurAdmin)
admin.site.register(Etudiant)
admin.site.register(Professeur)
admin.site.register(Administrateur)

class EtudiantAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prenom', 'departement', 'licence', 'telephone')
    search_fields = ('nom', 'prenom', 'email')

class ProfesseurAdmin(admin.ModelAdmin):
    list_display = ('user', 'departement')
    search_fields = ('user__username', 'email')

class AdministrateurAdmin(admin.ModelAdmin):
    list_display = ('user',)
    search_fields = ('user__username',)

admin.site.site_header = "Gestion des Utilisateurs - Administration"
admin.site.site_title = "Admin - Plateforme d'Évaluation"
admin.site.index_title = "Gestion des rôles et utilisateurs"
