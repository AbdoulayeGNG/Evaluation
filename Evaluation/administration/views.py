from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from utilisateurs.models import Utilisateur, Professeur, Etudiant, Administrateur
from evaluationProf.models import Formation, Evaluation, NoteCritere
from django.db.models import Count, Avg
from .models import LogActivity
from django.contrib.auth.hashers import make_password
from django.db import transaction




def is_admin(user):
    return hasattr(user, 'administrateur')

@login_required
@user_passes_test(is_admin)
def dashboard(request):
    context = {
        'total_profs': Professeur.objects.count(),
        'total_etudiants': Etudiant.objects.count(),
        'total_evaluations': Evaluation.objects.count(),
        'recent_evaluations': Evaluation.objects.order_by('-date_creation')[:5],
        'recent_activities': LogActivity.objects.all()[:5]
    }
    return render(request, 'administration/dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def gestion_professeurs(request):
    professeurs = Professeur.objects.all()
    return render(request, 'administration/professeurs/liste.html', {'professeurs': professeurs})

@login_required
@user_passes_test(is_admin)
def gestion_etudiants(request):
    etudiants = Etudiant.objects.all()
    return render(request, 'administration/etudiants/liste.html', {'etudiants': etudiants})

@login_required
@user_passes_test(is_admin)
def gestion_evaluations(request):
    # Récupérer toutes les évaluations en attente
    evaluations = Evaluation.objects.filter(statut='en attente').select_related(
        'etudiant', 
        'formation', 
        'formation__professeur'
    )
    
    context = {
        'evaluations': evaluations,
    }
    return render(request, 'administration/evaluations/liste.html', context)

@login_required
@user_passes_test(is_admin)
def valider_evaluation(request, pk):
    evaluation = get_object_or_404(Evaluation, pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        try:
            with transaction.atomic():
                if action == 'valider':
                    evaluation.statut = 'validé'
                    message = "Évaluation validée avec succès"
                elif action == 'rejeter':
                    evaluation.statut = 'rejeté'
                    message = "Évaluation rejetée"
                
                evaluation.save()
                
                # Log de l'activité
                LogActivity.objects.create(
                    admin=request.user.administrateur,
                    action=f"{message} - Évaluation de {evaluation.etudiant.get_full_name()}"
                )
                
                messages.success(request, message)
        except Exception as e:
            messages.error(request, f"Erreur lors du traitement: {str(e)}")
            
    return redirect('administration:gestion_evaluations')

@login_required
@user_passes_test(is_admin)
def statistiques(request):
    stats = {
        'evaluations_par_prof': Formation.objects.annotate(total_evals=Count('evaluation')),
        'evaluations_par_mois': Evaluation.objects.extra(
            select={'month': 'MONTH(date_creation)'}
        ).values('month').annotate(total=Count('id'))
    }
    return render(request, 'administration/statistiques.html', stats)



#GESTION DES PROFESSEURS
def is_admin(user):
    return hasattr(user, 'administrateur')

@login_required
@user_passes_test(is_admin)
def liste_professeurs(request):
    professeurs = Professeur.objects.select_related('user').all()
    return render(request, 'administration/professeurs/liste.html', {
        'professeurs': professeurs
    })

@login_required
@user_passes_test(is_admin)
def ajouter_professeur(request):
    if request.method == 'POST':
        # Get form data
        username = request.POST.get('matricule')
        password = request.POST.get('password')
        password1 = request.POST.get('password1')
        email = request.POST.get('email')
        
        # Validate data
        if password != password1:
            messages.error(request, "Les mots de passe ne correspondent pas")
            return render(request, 'administration/professeurs/ajouter.html')

        if Utilisateur.objects.filter(username=username).exists():
            messages.error(request, "Ce matricule existe déjà")
            return render(request, 'administration/professeurs/ajouter.html')

        if Utilisateur.objects.filter(email=email).exists():
            messages.error(request, "Cet email est déjà utilisé")
            return render(request, 'administration/professeurs/ajouter.html')

        try:
            with transaction.atomic():
                # Create base user
                utilisateur = Utilisateur.objects.create(
                    username=username,
                    email=email,
                    role='professeur',
                    password=make_password(password)
                )

                # Create professor profile
                Professeur.objects.create(
                    user=utilisateur,
                    nom=request.POST.get('nom'),
                    prenom=request.POST.get('prenom'),
                    departement=request.POST.get('departement'),
                )

                messages.success(request, "Professeur ajouté avec succès")
                return redirect('administration:liste_professeurs')

        except Exception as e:
            messages.error(request, f"Erreur lors de la création du professeur: {str(e)}")
            return render(request, 'administration/professeurs/ajouter.html')

    # If GET request, show the form
    return render(request, 'administration/professeurs/ajouter.html')

@login_required
@user_passes_test(is_admin)
def modifier_professeur(request, pk):
    professeur = get_object_or_404(Professeur, pk=pk)
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Vérifier si l'email existe déjà pour un autre utilisateur
        if Utilisateur.objects.exclude(pk=professeur.user.pk).filter(email=email).exists():
            messages.error(request, "Cet email est déjà utilisé")
            return render(request, 'administration/professeurs/modifier.html', {'professeur': professeur})

        # Vérifier les mots de passe si fournis
       

        try:
            with transaction.atomic():
                # Mettre à jour l'utilisateur
                user = professeur.user
                user.email = email
                
                # Mettre à jour le mot de passe si fourni
                if password:
                    user.password = make_password(password)
                
                user.save()
                
                # Mettre à jour le professeur
                professeur.nom = request.POST.get('nom')
                professeur.prenom = request.POST.get('prenom')
                professeur.departement = request.POST.get('departement')
                
                # Gérer la photo si fournie
                if 'photo' in request.FILES:
                    professeur.photo = request.FILES['photo']
                
                professeur.save()
                
                # Enregistrer l'activité
                LogActivity.objects.create(
                    admin=request.user.administrateur,
                    action=f"Modification du professeur {professeur.user.username}"
                )
                
                messages.success(request, "Professeur modifié avec succès")
                return redirect('administration:detail_professeur', pk=professeur.pk)
                
        except Exception as e:
            messages.error(request, f"Erreur lors de la modification: {str(e)}")
            
    return render(request, 'administration/professeurs/modifier.html', {
        'professeur': professeur
    })

@login_required
@user_passes_test(is_admin)
def supprimer_professeur(request, pk):
    professeur = get_object_or_404(Professeur, pk=pk)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Stocker les informations pour le log
                username = professeur.user.username
                full_name = professeur.user.get_full_name()
                
                # Supprimer l'utilisateur (cascade vers professeur)
                professeur.user.delete()
                
                # Enregistrer l'activité
                LogActivity.objects.create(
                    admin=request.user.administrateur,
                    action=f"Suppression du professeur {full_name} ({username})"
                )
                
                messages.success(request, "Professeur supprimé avec succès")
                return redirect('administration:liste_professeurs')
                
        except Exception as e:
            messages.error(request, f"Erreur lors de la suppression: {str(e)}")
            return redirect('administration:detail_professeur', pk=pk)
    
    return render(request, 'administration/professeurs/supprimer.html', {
        'professeur': professeur
    })

@login_required
@user_passes_test(is_admin)
def detail_professeur(request, pk):
    try:
        # Récupérer le professeur avec ses relations
        professeur = get_object_or_404(Professeur, pk=pk)
        
        # Récupérer les formations liées au professeur
        formations = Formation.objects.filter(professeur=professeur.user).annotate(
            total_evaluations=Count('evaluation')
        )
        
        # Récupérer les évaluations liées aux formations du professeur
        evaluations = Evaluation.objects.filter(
            formation__professeur=professeur.user
        ).select_related('formation', 'etudiant')
        
        # Calculer la moyenne des notes
        notes_moyennes = NoteCritere.objects.filter(
            evaluation__formation__professeur=professeur.user
        ).aggregate(Avg('note'))['note__avg']
        
        stats = {
            'total_formations': formations.count(),
            'total_evaluations': evaluations.count(),
            'moyenne_evaluations': notes_moyennes if notes_moyennes else 0
        }
        
        context = {
            'professeur': professeur,
            'formations': formations,
            'evaluations': evaluations,
            'stats': stats
        }
        
        return render(request, 'administration/professeurs/detail.html', context)
        
    except Exception as e:
        messages.error(request, f"Erreur lors de la récupération des détails: {str(e)}")
        return redirect('administration:liste_professeurs')

@login_required
@user_passes_test(is_admin)
def supprimer_etudiant(request, pk):
    etudiant = get_object_or_404(Etudiant, pk=pk)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Stocker les informations pour le log
                username = etudiant.user.username
                full_name = etudiant.user.get_full_name()
                
                # Supprimer l'utilisateur (cascade vers étudiant)
                etudiant.user.delete()
                
                # Enregistrer l'activité
                LogActivity.objects.create(
                    admin=request.user.administrateur,
                    action=f"Suppression de l'étudiant {full_name} ({username})"
                )
                
                messages.success(request, "Étudiant supprimé avec succès")
                return redirect('administration:liste_etudiants')
                
        except Exception as e:
            messages.error(request, f"Erreur lors de la suppression: {str(e)}")
            return redirect('administration:detail_etudiant', pk=pk)
    
    return render(request, 'administration/etudiants/supprimer.html', {
        'etudiant': etudiant
    })

@login_required
@user_passes_test(is_admin)
def ajouter_etudiant(request):
    if request.method == 'POST':
        # Récupérer les données du formulaire
        username = request.POST.get('matricule')
        password = request.POST.get('password')
        password1 = request.POST.get('password1')
        email = request.POST.get('email')

        # Validation des données
        if password != password1:
            messages.error(request, "Les mots de passe ne correspondent pas")
            return render(request, 'administration/etudiants/ajouter.html')

        if Utilisateur.objects.filter(username=username).exists():
            messages.error(request, "Ce matricule existe déjà")
            return render(request, 'administration/etudiants/ajouter.html')

        if Utilisateur.objects.filter(email=email).exists():
            messages.error(request, "Cet email est déjà utilisé")
            return render(request, 'administration/etudiants/ajouter.html')

        try:
            with transaction.atomic():
                # Créer l'utilisateur de base
                utilisateur = Utilisateur.objects.create(
                    username=username,
                    email=email,
                    role='etudiant',
                    password=make_password(password)
                )

                # Créer le profil étudiant
                Etudiant.objects.create(
                    user=utilisateur,
                    nom=request.POST.get('nom'),
                    prenom=request.POST.get('prenom'),
                    departement=request.POST.get('departement'),
                    licence=request.POST.get('licence'),
                    telephone=request.POST.get('telephone')
                )

                # Enregistrer l'activité
                LogActivity.objects.create(
                    admin=request.user.administrateur,
                    action=f"Ajout de l'étudiant {username}"
                )

                messages.success(request, "Étudiant ajouté avec succès")
                return redirect('administration:liste_etudiants')

        except Exception as e:
            messages.error(request, f"Erreur lors de la création: {str(e)}")
            return render(request, 'administration/etudiants/ajouter.html')

    return render(request, 'administration/etudiants/ajouter.html')

@login_required
@user_passes_test(is_admin)
def liste_etudiants(request):
    etudiants = Etudiant.objects.select_related('user').all()
    return render(request, 'administration/etudiants/liste.html', {
        'etudiants': etudiants
    })

@login_required
@user_passes_test(is_admin)
def detail_etudiant(request, pk):
    try:
        # Récupérer l'étudiant avec ses relations
        etudiant = get_object_or_404(Etudiant.objects.select_related('user'), pk=pk)
        
        # Récupérer les évaluations de l'étudiant
        evaluations = Evaluation.objects.filter(
            etudiant=etudiant.user
        ).select_related('formation')
        
        # Calculer les statistiques
        stats = {
            'total_evaluations': evaluations.count(),
            'evaluations_validees': evaluations.filter(statut='validé').count(),
            'moyenne_notes': NoteCritere.objects.filter(
                evaluation__etudiant=etudiant.user,
                evaluation__statut='validé'
            ).aggregate(Avg('note'))['note__avg'] or 0
        }
        
        context = {
            'etudiant': etudiant,
            'evaluations': evaluations,
            'stats': stats
        }
        
        return render(request, 'administration/etudiants/detail.html', context)
        
    except Exception as e:
        messages.error(request, f"Erreur lors de la récupération des détails: {str(e)}")
        return redirect('administration:liste_etudiants')

@login_required
@user_passes_test(is_admin)
def modifier_etudiant(request, pk):
    etudiant = get_object_or_404(Etudiant, pk=pk)
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        password1 = request.POST.get('password1')

        # Vérifier si l'email existe déjà pour un autre utilisateur
        if Utilisateur.objects.exclude(pk=etudiant.user.pk).filter(email=email).exists():
            messages.error(request, "Cet email est déjà utilisé")
            return render(request, 'administration/etudiants/modifier.html', {'etudiant': etudiant})

        # Vérifier les mots de passe si fournis
        if password:
            if password != password1:
                messages.error(request, "Les mots de passe ne correspondent pas")
                return render(request, 'administration/etudiants/modifier.html', {'etudiant': etudiant})

        try:
            with transaction.atomic():
                # Mettre à jour l'utilisateur
                user = etudiant.user
                user.email = email
                user.first_name = request.POST.get('prenom')
                user.last_name = request.POST.get('nom')
                
                # Mettre à jour le mot de passe si fourni
                if password:
                    user.password = make_password(password)
                
                user.save()
                
                # Mettre à jour l'étudiant
                etudiant.departement = request.POST.get('departement')
                etudiant.licence = request.POST.get('licence')
                etudiant.telephone = request.POST.get('telephone')
                
                # Gérer la photo si fournie
                if 'photo' in request.FILES:
                    etudiant.photo = request.FILES['photo']
                
                etudiant.save()
                
                # Enregistrer l'activité
                LogActivity.objects.create(
                    admin=request.user.administrateur,
                    action=f"Modification de l'étudiant {etudiant.user.username}"
                )
                
                messages.success(request, "Étudiant modifié avec succès")
                return redirect('administration:detail_etudiant', pk=etudiant.pk)
                
        except Exception as e:
            messages.error(request, f"Erreur lors de la modification: {str(e)}")
            
    return render(request, 'administration/etudiants/modifier.html', {
        'etudiant': etudiant
    })