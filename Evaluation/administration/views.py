from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from administration.forms import FormationForm
from utilisateurs.models import Utilisateur, Professeur, Etudiant, Administrateur
from evaluationProf.models import Formation, Evaluation, NoteCritere, Semestre
from django.db.models import Count, Avg, Q
from .models import LogActivity
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.utils import timezone
from .forms import AdministrateurCreationForm, AdministrateurForm
from django.db.models.functions import TruncMonth
from datetime import datetime, timedelta
from django.core.serializers.json import DjangoJSONEncoder
import json
import logging

logger = logging.getLogger(__name__)

def is_superuser(user):
    return user.is_superuser


def is_admin(user):
    # Un superuser a toujours accès
    if user.is_superuser:
        return True
    # Pour les autres, vérifier s'ils sont staff et ont un profil administrateur
    return user.is_staff and hasattr(user, 'administrateur')

@login_required
@user_passes_test(is_admin)
def dashboard(request):
    # Récupération des filtres
    departement = request.GET.get('departement')
    periode = request.GET.get('periode')
    tri = request.GET.get('tri', '-date_creation')

    # Filtres de base
    evaluations = Evaluation.objects.select_related('formation', 'etudiant').annotate(
        note_moyenne=Avg('notes__note')
    )

    # Application des filtres
    if departement:
        evaluations = evaluations.filter(formation__departement=departement)

    if periode:
        today = timezone.now()
        if periode == 'semaine':
            date_debut = today - timedelta(days=7)
        elif periode == 'mois':
            date_debut = today - timedelta(days=30)
        elif periode == 'trimestre':
            date_debut = today - timedelta(days=90)
        evaluations = evaluations.filter(date_creation__gte=date_debut)

    # Application du tri
    evaluations = evaluations.order_by(tri)

    # Liste des départements pour le filtre
    departements = Formation.objects.values_list('departement', flat=True).distinct()

    # Statistiques générales
    total_profs = Professeur.objects.count()
    total_etudiants = Etudiant.objects.count()
    total_evaluations = Evaluation.objects.count()
    
    # Debug logs
    logger.debug(f"Nombre total d'évaluations: {total_evaluations}")
    
    # Données pour le graphique d'évolution
    six_months_ago = timezone.now() - timedelta(days=180)
    evaluations_par_mois = NoteCritere.objects.filter(
        evaluation__date_creation__gte=six_months_ago
    ).annotate(
        mois=TruncMonth('evaluation__date_creation')
    ).values('mois').annotate(
        moyenne=Avg('note'),
        total=Count('evaluation', distinct=True),
        notes_5=Count('note', filter=Q(note=5)),
        notes_4=Count('note', filter=Q(note=4)),
        notes_3=Count('note', filter=Q(note=3)),
        notes_2=Count('note', filter=Q(note=2)),
        notes_1=Count('note', filter=Q(note=1))
    ).order_by('mois')

    evaluations_data = list(evaluations_par_mois)
    logger.debug(f"Données d'évolution: {evaluations_data}")

    # Si pas de données, créer des données fictives pour test
    if not evaluations_data:
        current_date = timezone.now()
        evaluations_data = []
        for i in range(6):
            month_date = (current_date - timedelta(days=30 * i)).replace(day=1)
            evaluations_data.append({
                'mois': month_date,
                'moyenne': 0,
                'total': 0,
                'notes_5': 0,
                'notes_4': 0,
                'notes_3': 0,
                'notes_2': 0,
                'notes_1': 0
            })

    # Statistiques par département
    stats_departements = Formation.objects.values(
        'departement'
    ).annotate(
        moyenne_notes=Avg('evaluation__notes__note'),
        nb_evaluations=Count('evaluation', distinct=True)
    ).filter(
        nb_evaluations__gt=0
    ).order_by('-moyenne_notes')

    # Vérifier si nous avons des données pour les départements
    departements_data = list(stats_departements)
    if not departements_data:
        # Créer des données exemple si aucune donnée n'existe
        departements_data = [
            {'departement': 'Aucune donnée', 'moyenne_notes': 0, 'nb_evaluations': 0}
        ]

    # Récupérer les évaluations récentes avec leurs notes moyennes
    recent_evaluations = Evaluation.objects.annotate(
        note_moyenne=Avg('notes__note')
    ).select_related(
        'etudiant', 
        'formation'
    ).order_by('-date_creation')[:5]

    context = {
        'total_profs': total_profs,
        'total_etudiants': total_etudiants,
        'total_evaluations': total_evaluations,
        'recent_evaluations': recent_evaluations,
        'evaluations_par_mois': json.dumps(
            evaluations_data,
            cls=DjangoJSONEncoder
        ),
        'stats_departements': json.dumps(
            departements_data,
            cls=DjangoJSONEncoder
        ),
        'departements': departements,
        'recent_evaluations': evaluations[:10],  # Limitons à 10 résultats
        'selected_departement': departement,
        'selected_periode': periode,
        'selected_tri': tri,
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
    # Récupérer le semestre actif
    semestre_actif = Semestre.objects.filter(
        periode_evaluation_debut__lte=timezone.now().date(),
        periode_evaluation_fin__gte=timezone.now().date()
    ).first()
    
    if not semestre_actif:
        messages.warning(request, "Aucune période d'évaluation n'est actuellement ouverte.")
        evaluations = Evaluation.objects.none()
    else:
        # Récupérer les évaluations en attente du semestre actif
        evaluations = Evaluation.objects.select_related(
            'etudiant',
            'formation',
            'formation__professeur'
        ).prefetch_related(
            'notes',
            'notes__critere'
        ).filter(
            statut='en attente',
            formation__semestre=semestre_actif
        ).order_by('-date_creation')
    
    # Debug: afficher les informations
    print(f"Semestre actif : {semestre_actif}")
    print(f"Nombre d'évaluations en attente : {evaluations.count()}")
    
    context = {
        'evaluations': evaluations,
        'semestre_actif': semestre_actif
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
        nom = request.POST.get('nom')
        prenom = request.POST.get('prenom')
        departement = request.POST.get('departement')
        licence = request.POST.get('licence')
        telephone = request.POST.get('telephone')

        # Validation des données
        if not all([username, password, password1, email, nom, prenom, departement, licence]):
            messages.error(request, "Tous les champs sont obligatoires")
            return render(request, 'administration/etudiants/ajouter.html')

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
                # Créer l'utilisateur
                utilisateur = Utilisateur.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    role='etudiant'
                )

                # Créer le profil étudiant
                etudiant = Etudiant.objects.create(
                    user=utilisateur,
                    nom=nom,
                    prenom=prenom,
                    departement=departement,
                    licence=licence,
                    telephone=telephone
                )

                # Log de l'activité
                LogActivity.objects.create(
                    admin=request.user.administrateur,
                    action=f"Ajout de l'étudiant {etudiant.nom} {etudiant.prenom} ({username})"
                )

                messages.success(request, "Étudiant ajouté avec succès")
                return redirect('administration:liste_etudiants')

        except Exception as e:
            messages.error(request, f"Erreur lors de la création: {str(e)}")

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
        nom = request.POST.get('nom')
        prenom = request.POST.get('prenom')
        departement = request.POST.get('departement')
        licence = request.POST.get('licence')
        telephone = request.POST.get('telephone')
        password = request.POST.get('password')
        password1 = request.POST.get('password1')

        # Validation des données
        if not all([email, nom, prenom, departement, licence]):
            messages.error(request, "Les champs marqués d'un * sont obligatoires")
            return render(request, 'administration/etudiants/modifier.html', {'etudiant': etudiant})

        # Vérification de l'email unique
        if Utilisateur.objects.exclude(pk=etudiant.user.pk).filter(email=email).exists():
            messages.error(request, "Cet email est déjà utilisé")
            return render(request, 'administration/etudiants/modifier.html', {'etudiant': etudiant})

        try:
            with transaction.atomic():
                # Mise à jour de l'utilisateur
                user = etudiant.user
                user.email = email
                
                # Mise à jour du mot de passe si fourni
                if password:
                    if password != password1:
                        messages.error(request, "Les mots de passe ne correspondent pas")
                        return render(request, 'administration/etudiants/modifier.html', {'etudiant': etudiant})
                    user.set_password(password)
                
                user.save()

                # Mise à jour de l'étudiant
                etudiant.nom = nom
                etudiant.prenom = prenom
                etudiant.departement = departement
                etudiant.licence = licence
                etudiant.telephone = telephone

                # Gestion de la photo
                if 'photo' in request.FILES:
                    etudiant.photo = request.FILES['photo']
                
                etudiant.save()

                # Log de l'activité
                LogActivity.objects.create(
                    admin=request.user.administrateur,
                    action=f"Modification de l'étudiant {etudiant.nom} {etudiant.prenom} ({user.username})"
                )

                messages.success(request, "Étudiant modifié avec succès")
                return redirect('administration:detail_etudiant', pk=etudiant.pk)

        except Exception as e:
            messages.error(request, f"Erreur lors de la modification: {str(e)}")

    return render(request, 'administration/etudiants/modifier.html', {'etudiant': etudiant})

@login_required
@user_passes_test(is_admin)
def gestion_periodes_evaluation(request):
    formations = Formation.objects.all().order_by('date_fin_module')
    
    if request.method == "POST":
        formation_id = request.POST.get('formation_id')
        date_fin = request.POST.get('date_fin')
        periode = request.POST.get('periode')
        
        formation = get_object_or_404(Formation, id=formation_id)
        formation.date_fin_module = date_fin
        formation.periode_evaluation = int(periode)
        formation.save()
        
        messages.success(request, f"Période d'évaluation mise à jour pour {formation.nom}")
        
    context = {
        'formations': formations,
        'aujourd_hui': timezone.now().date(),
    }
    return render(request, 'administration/formations/periodes_evaluation.html', context)

@login_required
@user_passes_test(is_admin)
def gestion_semestres(request):
    semestres = Semestre.objects.all()
    
    if request.method == "POST":
        annee = request.POST.get('annee_universitaire')
        semestre = request.POST.get('semestre')
        date_debut = request.POST.get('date_debut')
        date_fin = request.POST.get('date_fin')
        eval_debut = request.POST.get('eval_debut')
        eval_fin = request.POST.get('eval_fin')
        
        Semestre.objects.create(
            annee_universitaire=annee,
            semestre=semestre,
            date_debut=date_debut,
            date_fin=date_fin,
            periode_evaluation_debut=eval_debut,
            periode_evaluation_fin=eval_fin
        )
        messages.success(request, "Semestre ajouté avec succès")
        return redirect('administration:gestion_semestres')
        
    return render(request, 'administration/formations/gestion_semestres.html', {
        'semestres': semestres
    })

@login_required
@user_passes_test(is_admin)
def ajouter_semestre(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                annee = request.POST.get('annee_universitaire')
                semestre = request.POST.get('semestre')
                date_debut = request.POST.get('date_debut')
                date_fin = request.POST.get('date_fin')
                periode_debut = request.POST.get('periode_evaluation_debut')
                periode_fin = request.POST.get('periode_evaluation_fin')

                # Validation
                if Semestre.objects.filter(annee_universitaire=annee, semestre=semestre).exists():
                    messages.error(request, "Ce semestre existe déjà pour cette année universitaire.")
                    return redirect('administration:ajouter_semestre')

                semestre = Semestre.objects.create(
                    annee_universitaire=annee,
                    semestre=semestre,
                    date_debut=date_debut,
                    date_fin=date_fin,
                    periode_evaluation_debut=periode_debut,
                    periode_evaluation_fin=periode_fin
                )

                messages.success(request, "Semestre ajouté avec succès.")
                return redirect('administration:liste_semestres')
        except Exception as e:
            messages.error(request, f"Erreur lors de l'ajout du semestre : {str(e)}")
    
    return render(request, 'administration/semestres/ajouter.html')

@login_required
@user_passes_test(is_admin)
def modifier_semestre(request, pk):
    semestre = get_object_or_404(Semestre, pk=pk)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                semestre.annee_universitaire = request.POST.get('annee_universitaire')
                semestre.semestre = request.POST.get('semestre')
                semestre.date_debut = request.POST.get('date_debut')
                semestre.date_fin = request.POST.get('date_fin')
                semestre.periode_evaluation_debut = request.POST.get('periode_evaluation_debut')
                semestre.periode_evaluation_fin = request.POST.get('periode_evaluation_fin')
                
                # Validation des dates
                if semestre.date_fin < semestre.date_debut:
                    messages.error(request, "La date de fin du semestre doit être postérieure à la date de début")
                    return render(request, 'administration/formations/modifier_semestre.html', {'semestre': semestre})
                
                if semestre.periode_evaluation_fin < semestre.periode_evaluation_debut:
                    messages.error(request, "La période d'évaluation n'est pas valide")
                    return render(request, 'administration/formations/modifier_semestre.html', {'semestre': semestre})
                
                semestre.save()
                messages.success(request, "Semestre modifié avec succès")
                return redirect('administration:gestion_semestres')
                
        except Exception as e:
            messages.error(request, f"Erreur lors de la modification : {str(e)}")
            
    return render(request, 'administration/formations/modifier_semestre.html', {'semestre': semestre})

@login_required
@user_passes_test(is_admin)
def supprimer_semestre(request, pk):
    semestre = get_object_or_404(Semestre, pk=pk)
    
    if request.method == 'POST':
        try:
            # Vérifier s'il y a des formations liées
            if Formation.objects.filter(semestre=semestre).exists():
                messages.error(request, 
                    "Impossible de supprimer ce semestre car il contient des formations")
                return redirect('administration:gestion_semestres')
            
            # Vérifier s'il y a des évaluations liées
            if Evaluation.objects.filter(formation__semestre=semestre).exists():
                messages.error(request, 
                    "Impossible de supprimer ce semestre car il contient des évaluations")
                return redirect('administration:gestion_semestres')
            
            # Si aucune dépendance, supprimer le semestre
            semestre.delete()
            messages.success(request, "Semestre supprimé avec succès")
            return redirect('administration:gestion_semestres')
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la suppression : {str(e)}")
            return redirect('administration:gestion_semestres')
    
    return render(request, 'administration/formations/confirmer_suppression_semestre.html', 
                 {'semestre': semestre})

@login_required
@user_passes_test(is_admin)
def liste_semestres(request):
    semestres = Semestre.objects.all().order_by('-annee_universitaire', 'semestre')
    return render(request, 'administration/semestres/liste.html', {'semestres': semestres})

@login_required
@user_passes_test(is_admin)
def detail_semestre(request, pk):
    semestre = get_object_or_404(Semestre, pk=pk)
    formations = Formation.objects.filter(semestre=semestre)
    
    context = {
        'semestre': semestre,
        'formations': formations,
        'total_formations': formations.count(),
        'total_evaluations': Evaluation.objects.filter(formation__semestre=semestre).count(),
        'evaluations_validees': Evaluation.objects.filter(
            formation__semestre=semestre, 
            statut='validé'
        ).count()
    }
    return render(request, 'administration/formations/detail_semestre.html', context)

@login_required
@user_passes_test(is_admin)
def gestion_formations(request):
    formations = Formation.objects.select_related(
        'professeur',
        'semestre'
    ).all().order_by('-semestre__date_debut', 'nom')
    
    context = {
        'formations': formations,
        'total_formations': formations.count(),
        'formations_actives': formations.filter(
            semestre__periode_evaluation_debut__lte=timezone.now(),
            semestre__periode_evaluation_fin__gte=timezone.now()
        ).count()
    }
    return render(request, 'administration/formations/liste.html', context)

@login_required
@user_passes_test(is_admin)
def ajouter_formation(request):
    if request.method == 'POST':
        form = FormationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    formation = form.save()
                    messages.success(request, f'La formation "{formation.nom}" a été créée avec succès.')
                    return redirect('administration:gestion_formations')  # Changed to redirect to list view instead
            except Exception as e:
                messages.error(request, f'Erreur lors de la création de la formation : {str(e)}')
    else:
        form = FormationForm()
    
    context = {
        'form': form,
        'titre': 'Ajouter une formation',
        'button_text': 'Créer',
    }
    return render(request, 'administration/formations/form_formation.html', context)

@login_required
@user_passes_test(is_admin)
def detail_formation(request, pk):
    formation = get_object_or_404(
        Formation.objects.select_related(
            'professeur',
            'semestre'
        ),
        pk=pk
    )
    
    # Récupérer les évaluations
    evaluations = formation.evaluation_set.select_related('etudiant').order_by('-date_creation')[:10]
    total_evaluations = formation.evaluation_set.count()
    evaluations_validees = formation.evaluation_set.filter(statut='validé').count()
    
    context = {
        'formation': formation,
        'evaluations': evaluations,
        'total_evaluations': total_evaluations,
        'evaluations_validees': evaluations_validees,
    }
    
    return render(request, 'administration/formations/detail_formation.html', context)

@login_required
@user_passes_test(is_admin)
def modifier_formation(request, pk):
    formation = get_object_or_404(Formation, pk=pk)
    if request.method == 'POST':
        form = FormationForm(request.POST, instance=formation)
        if form.is_valid():
            try:
                with transaction.atomic():
                    formation = form.save()
                    messages.success(
                        request, 
                        f'La formation "{formation.nom}" a été modifiée avec succès.'
                    )
                    return redirect('administration:detail_formation', pk=formation.pk)
            except Exception as e:
                messages.error(
                    request, 
                    f'Erreur lors de la modification : {str(e)}'
                )
    else:
        form = FormationForm(instance=formation)
    
    context = {
        'form': form,
        'formation': formation,
        'title': 'Modifier la formation',
        'is_modification': True,
        'button_text': 'Enregistrer les modifications'
    }
    return render(request, 'administration/formations/form_formation.html', context)

@login_required
@user_passes_test(is_admin)
def supprimer_formation(request, pk):
    formation = get_object_or_404(Formation, pk=pk)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                nom_formation = formation.nom
                formation.delete()
                messages.success(
                    request, 
                    f'La formation "{nom_formation}" a été supprimée avec succès.'
                )
                # Log de l'activité
                LogActivity.objects.create(
                    admin=request.user.administrateur,
                    action=f"Suppression de la formation {nom_formation}"
                )
                return redirect('administration:gestion_formations')
        except:
            messages.error(
                request, 
                "Impossible de supprimer cette formation car elle est liée à des évaluations."
            )
            return redirect('administration:detail_formation', pk=pk)
        
    
    # Si la méthode n'est pas POST, rediriger vers la page de détail
    return redirect('administration:detail_formation', pk=pk)



@login_required
@user_passes_test(is_superuser)
def gestion_administrateurs(request):
    administrateurs = Administrateur.objects.select_related('user').all()
    context = {
        'administrateurs': administrateurs,
        'total_admins': administrateurs.count()
    }
    return render(request, 'administration/administrateurs/liste.html', context)

@login_required
@user_passes_test(is_superuser)
def ajouter_administrateur(request):
    if request.method == 'POST':
        form = AdministrateurCreationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    admin = form.save()
                    messages.success(
                        request, 
                        f"L'administrateur {admin.administrateur.nom} {admin.administrateur.prenom} a été créé avec succès."
                    )
                    return redirect('administration:gestion_administrateurs')
            except Exception as e:
                messages.error(request, f"Erreur lors de la création : {str(e)}")
    else:
        form = AdministrateurCreationForm()
    
    context = {
        'form': form,
        'title': 'Ajouter un administrateur'
    }
    return render(request, 'administration/administrateurs/form_administrateur.html', context)

@login_required
@user_passes_test(is_superuser)
def modifier_administrateur(request, pk):
    administrateur = get_object_or_404(Administrateur, pk=pk)
    if request.method == 'POST':
        form = AdministrateurForm(request.POST, request.FILES, instance=administrateur)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Mise à jour de l'utilisateur
                    user = administrateur.user
                    user.username = form.cleaned_data['username']
                    user.email = form.cleaned_data['email']
                    user.first_name = form.cleaned_data['prenom']
                    user.last_name = form.cleaned_data['nom']
                    if form.cleaned_data['password']:
                        user.set_password(form.cleaned_data['password'])
                    user.save()

                    admin = form.save()
                    messages.success(request, f"L'administrateur {admin.nom} {admin.prenom} a été modifié avec succès.")
                    return redirect('administration:detail_administrateur', pk=pk)
            except Exception as e:
                messages.error(request, f"Erreur lors de la modification : {str(e)}")
    else:
        form = AdministrateurForm(instance=administrateur)

    return render(request, 'administration/administrateurs/form_administrateur.html', {
        'form': form,
        'administrateur': administrateur,
        'title': 'Modifier un administrateur'
    })

@login_required
@user_passes_test(is_superuser)
def supprimer_administrateur(request, pk):
    administrateur = get_object_or_404(Administrateur, pk=pk)
    if request.method == 'POST':
        try:
            with transaction.atomic():
                user = administrateur.user
                nom_admin = f"{administrateur.nom} {administrateur.prenom}"
                administrateur.delete()
                user.delete()
                messages.success(request, f"L'administrateur {nom_admin} a été supprimé avec succès.")
                return redirect('administration:gestion_administrateurs')
        except Exception as e:
            messages.error(request, f"Erreur lors de la suppression : {str(e)}")
            return redirect('administration:detail_administrateur', pk=pk)
    return redirect('administration:detail_administrateur', pk=pk)

@login_required
@user_passes_test(is_superuser)
def detail_administrateur(request, pk):
    administrateur = get_object_or_404(Administrateur.objects.select_related('user'), pk=pk)
    context = {
        'administrateur': administrateur,
    }
    return render(request, 'administration/administrateurs/detail_administrateur.html', context)