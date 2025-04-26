from django.shortcuts import render, redirect
from django.contrib.auth import login,authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.hashers import make_password

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from django.shortcuts import render, redirect, get_object_or_404
#from django.contrib.auth import login, logout
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Utilisateur, Etudiant, Professeur, Administrateur
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.contrib import messages

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    
    def get_success_url(self):
        user = self.request.user
        # Redirection selon les permissions
        if user.is_staff:
            return reverse_lazy('administration:dashboard')
        elif user.role == 'professeur':
            return reverse_lazy('prof:dashboard_professeur')
        elif user.role == 'etudiant':
            return reverse_lazy('etudiants:dashboard_etudiant')
        return reverse_lazy('home')

    def form_invalid(self, form):
        messages.error(self.request, 'Identifiants invalides. Veuillez réessayer.')
        return super().form_invalid(form)

def accueil(request):
    return render(request, 'index.html')
def CreationCompte(request):
    if request.method == 'POST':
        # Récupérer les données communes
        username = request.POST.get('matricule')
        password = request.POST.get('password')
        password1 = request.POST.get('password1')
        email = request.POST.get('email')
        role = request.POST.get('role')  # 'etudiant', 'professeur', ou 'admin'

        # Validation des données
        if password != password1:
            return render(request, 'user/register.html', 
                        {"error": "Les mots de passe ne correspondent pas"})

        if Utilisateur.objects.filter(username=username).exists():
            return render(request, 'user/register.html',
                        {"error": "Ce matricule existe déjà"})

        if Utilisateur.objects.filter(email=email).exists():
            return render(request, 'user/register.html',
                        {"error": "Cet email est déjà utilisé"})

        # Créer l'utilisateur de base
        utilisateur = Utilisateur.objects.create(
            username=username,
            email=email,
            role=role,
            password=make_password(password)
        )

        # Créer le profil spécifique selon le rôle
        if role == 'etudiant':
            Etudiant.objects.create(
                user=utilisateur,
                nom=request.POST.get('nom'),
                prenom=request.POST.get('prenom'),
                departement=request.POST.get('departement'),
                licence=request.POST.get('licence'),
                telephone=request.POST.get('contact'),
    
            )
        elif role == 'professeur':
            Professeur.objects.create(
                user=utilisateur,
                nom=request.POST.get('nom'),
                prenom=request.POST.get('prenom'),
                departement=request.POST.get('departement'),
            )
        elif role == 'admin':
            with transaction.atomic():
                utilisateur = Utilisateur.objects.create(
                    username=username,
                    email=email,
                    role='admin',
                    password=make_password(password),
                    is_staff=True  # Définir is_staff à True pour tous les admins
                )
                
                # Si c'est un super administrateur
                if request.POST.get('is_superadmin'):
                    utilisateur.is_superuser = True
                    utilisateur.save()
                
                Administrateur.objects.create(
                    user=utilisateur,
                    nom=request.POST.get('nom'),
                    prenom=request.POST.get('prenom'),
                    contact=request.POST.get('contact'),
                )
                
                # Ajouter les permissions nécessaires
                content_type = ContentType.objects.get_for_model(Utilisateur)
                permissions = Permission.objects.filter(content_type=content_type)
                
                for perm in permissions:
                    utilisateur.user_permissions.add(perm)
        else:
            # Supprimer l'utilisateur si le rôle n'est pas valide
            utilisateur.delete()
            return render(request, 'user/register.html',
                        {"error": "Rôle d'utilisateur non valide"})

        # Connecter l'utilisateur
        login(request, utilisateur)

        # Rediriger vers le tableau de bord approprié
        if role == 'etudiant':
            return redirect('etudiants:dashboard_etudiant')
        elif role == 'professeur':
            return redirect('prof:dashboard_professeur')
        elif role == 'admin':
            return redirect('administration:dashboard')

    # Si méthode GET, afficher le formulaire
    return render(request, 'user/register.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Redirection selon les permissions
            if user.is_staff:
                # Redirection vers le dashboard admin pour tous les staffs
                return redirect('administration:dashboard')
            elif user.role == 'professeur':
                return redirect('prof:dashboard_professeur')
            elif user.role == 'etudiant':
                return redirect('etudiants:dashboard_etudiant')
                
        else:
            messages.error(request, 'Identifiants invalides')
    
    return render(request, 'registration/login.html')

def connecter(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username or not password:
            return render(request, 'user/login.html', 
                        {'erreur': 'Veuillez remplir tous les champs'})

        utilisateur = authenticate(request, username=username, password=password)
        
        if utilisateur is not None:
            login(request, utilisateur)
            # Redirection selon le rôle
            if hasattr(utilisateur, 'etudiant'):
                return redirect('etudiants:dashboard_etudiant')
            elif hasattr(utilisateur, 'professeur'):
                return redirect('prof:dashboard_professeur')
            elif hasattr(utilisateur, 'administrateur'):
                return redirect('admin_dashboard')
            return redirect('administration:dashboard')

    # Afficher le formulaire de connexion
    return render(request, 'user/login.html')
def deconnecter(request):
    # Déconnecter l'utilisateur
    logout(request)
    return redirect('utilisateurs:accueil')

def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'Vous avez été déconnecté avec succès')
        return render(request, 'registration/logged_out.html')


# Inscription d'un utilisateur (étudiant, professeur ou admin)
@csrf_exempt  # Désactiver CSRF temporairement pour les tests via Postman (à retirer en production)
def inscription(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        role = request.POST.get('role')

        if Utilisateur.objects.filter(username=username).exists():
            return JsonResponse({"error": "Ce nom d'utilisateur existe déjà"}, status=400)

        if Utilisateur.objects.filter(email=email).exists():
            return JsonResponse({"error": "Cet email est déjà utilisé"}, status=400)

        # Création de l'utilisateur de base
        user = Utilisateur.objects.create(
            username=username,
            email=email,
            role=role,
            password=make_password(password)  # Hash du mot de passe
        )

        # Associer l'utilisateur à son modèle spécifique
        if role == 'etudiant':
            Etudiant.objects.create(
                user=user,
                nom=request.POST.get('nom'),
                prenom=request.POST.get('prenom'),
                departement=request.POST.get('departement'),
                licence=request.POST.get('licence'),
                telephone=request.POST.get('telephone'),
                email=email
            )
        elif role == 'professeur':
            Professeur.objects.create(user=user, email=email, departement=request.POST.get('departement'))
        elif role == 'admin':
            Administrateur.objects.create(user=user,telephone=request.POST.get('telephone'), email=email)

        login(request, user)  # Connexion automatique après l'inscription
        return JsonResponse({"message": "Utilisateur créé avec succès", "role": role}, status=201)

    return JsonResponse({"error": "Méthode non autorisée"}, status=405)

# Lire les informations d'un utilisateur spécifique
@login_required
def get_user(request, user_id):
    user = get_object_or_404(Utilisateur, id=user_id)
    
    data = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role
    }

    if user.role == "etudiant":
        etudiant = get_object_or_404(Etudiant, user=user)
        data.update({
            "nom": etudiant.nom,
            "prenom": etudiant.prenom,
            "departement": etudiant.departement,
            "licence": etudiant.licence,
            "telephone": etudiant.telephone
        })
    elif user.role == "professeur":
        professeur = get_object_or_404(Professeur, user=user)
        data.update({
            "departement": professeur.departement
        })
    
    return JsonResponse(data)

# Modifier les informations d'un utilisateur
@login_required
@csrf_exempt
def modifier_utilisateur(request, user_id):
    user = get_object_or_404(Utilisateur, id=user_id)

    if request.method == 'POST':
        user.username = request.POST.get('username', user.username)
        user.email = request.POST.get('email', user.email)
        
        if request.POST.get('password'):
            user.password = make_password(request.POST.get('password'))
        
        user.save()

        if user.role == "etudiant":
            etudiant = get_object_or_404(Etudiant, user=user)
            etudiant.nom = request.POST.get('nom', etudiant.nom)
            etudiant.prenom = request.POST.get('prenom', etudiant.prenom)
            etudiant.departement = request.POST.get('departement', etudiant.departement)
            etudiant.licence = request.POST.get('licence', etudiant.licence)
            etudiant.telephone = request.POST.get('telephone', etudiant.telephone)
            etudiant.save()

        elif user.role == "professeur":
            professeur = get_object_or_404(Professeur, user=user)
            professeur.departement = request.POST.get('departement', professeur.departement)
            professeur.save()

        return JsonResponse({"message": "Utilisateur modifié avec succès"})

    return JsonResponse({"error": "Méthode non autorisée"}, status=405)

# Supprimer un utilisateur
@login_required
@csrf_exempt
def supprimer_utilisateur(request, user_id):
    user = get_object_or_404(Utilisateur, id=user_id)

    if request.method == 'DELETE':
        user.delete()
        return JsonResponse({"message": "Utilisateur supprimé avec succès"})

    return JsonResponse({"error": "Méthode non autorisée"}, status=405)

# Liste de tous les utilisateurs
@login_required
def liste_utilisateurs(request):
    utilisateurs = Utilisateur.objects.all()
    
    data = []
    for user in utilisateurs:
        user_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role
        }
        data.append(user_data)

    return JsonResponse({"utilisateurs": data})
