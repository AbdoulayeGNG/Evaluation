from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from evaluationProf.models import Evaluation, Formation
from utilisateurs.models import Etudiant, Professeur
from django.contrib.auth.models import User

# Create your views here.
@login_required
def dashboard_etudiant(request):
    # Récupérer les évaluations avec leurs relations
    evaluations_recentes = Evaluation.objects.filter(
        etudiant=request.user
    ).select_related(
        'formation',
        'formation__professeur'  # On charge directement le professeur lié à la formation
    ).order_by('-date_creation')[:5]

    context = {
        'evaluations_recentes': evaluations_recentes,
        'total_evaluations': Evaluation.objects.filter(etudiant=request.user).count(),
        'evaluations_en_attente': Evaluation.objects.filter(etudiant=request.user, statut='en attente').count(),
        'profs_evalues': Formation.objects.filter(evaluation__etudiant=request.user).values('professeur').distinct().count(),
    }
    
    return render(request, 'etudiants/index.html', context)


@login_required
def evaluationEtudiantTout(request):
    evaluations = Evaluation.objects.filter(
        etudiant=request.user
    ).select_related(
        'formation',
        'formation__professeur'
    ).prefetch_related(
        'notes',  # Utilisation du related_name défini dans le modèle
        'notes__critere'
    ).order_by('-date_creation')

    context = {
        'evaluations': evaluations,
        'total_evaluations': evaluations.count(),
        'evaluations_en_attente': evaluations.filter(statut='en_attente').count(),
        'profs_evalues': evaluations.values('formation__professeur').distinct().count(),
    }

    return render(request, 'etudiants/evaluationEtudiant.html', context)


@login_required
def profil(request):
    if request.method == 'POST':
        if request.FILES.get('photo'):
            etudiant = request.user.etudiant
            if etudiant.photo:
                # Supprimer l'ancienne photo si elle existe
                etudiant.photo.delete()
            etudiant.photo = request.FILES['photo']
            etudiant.save()
            messages.success(request, 'Photo de profil mise à jour avec succès!')
            return redirect('etudiants:profil')
    
    return render(request, 'etudiants/profileEtudiant.html')


@login_required
def update_profile(request):
    if request.method == 'POST':
        user = request.user
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        if email:
            user.email = email
        
        if password and password2 and password == password2:
            user.set_password(password)
        
        user.save()
        messages.success(request, 'Profil mis à jour avec succès!')
        
        return redirect('etudiants:profil')
    
    return redirect('etudiants:profil')


@login_required
def liste_professeurs(request):
    try:
        # Récupérer l'étudiant connecté
        etudiant = Etudiant.objects.get(user=request.user)
        
        # Récupérer les évaluations avec leurs formations et professeurs
        evaluations = Evaluation.objects.filter(
            etudiant=request.user
        ).select_related(
            'formation',
            'formation__professeur'
        )
        
        # Créer un dictionnaire pour stocker les infos uniques des professeurs
        professeurs_dict = {}
        
        for eval in evaluations:
            prof = eval.formation.professeur
            prof_detail = Professeur.objects.get(user=prof)
            prof_id = prof.id
            
            if prof_id not in professeurs_dict:
                professeurs_dict[prof_id] = {
                    'id': prof_id,
                    'nom': prof_detail.nom,
                    'prenom': prof_detail.prenom,
                    'departement': prof_detail.departement,
                    'formations': set(),
                    'evaluations_count': 0
                }
            professeurs_dict[prof_id]['formations'].add(eval.formation.nom)
            professeurs_dict[prof_id]['evaluations_count'] += 1
        
        context = {
            'professeurs': sorted(professeurs_dict.values(), key=lambda x: x['nom']),
            'total_evaluations': evaluations.count()
        }
        
        return render(request, 'etudiants/formateur.html', context)
        
    except Etudiant.DoesNotExist:
        messages.error(request, "Profil étudiant non trouvé")
        return redirect('etudiants:dashboard_etudiant')