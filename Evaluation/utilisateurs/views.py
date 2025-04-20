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
            Administrateur.objects.create(
                user=utilisateur,
                nom=request.POST.get('nom'),
                prenom=request.POST.get('prenom'),
                contact=request.POST.get('contact'),
            )
            content_type = ContentType.objects.get_for_model(Utilisateur)
            permissions = Permission.objects.filter(content_type=content_type)
            
            # Définir les permissions spécifiques
            admin_permissions = [
                'view_utilisateur',
                'add_utilisateur',
                'change_utilisateur',
                'delete_utilisateur',
                'view_etudiant',
                'view_professeur',
                'view_administrateur',
            ]
            
            # Attribuer les permissions
            for perm in permissions:
                if perm.codename in admin_permissions:
                    utilisateur.user_permissions.add(perm)
            
            utilisateur.is_staff = True  # Permet l'accès à l'interface d'administration
            utilisateur.save()
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
