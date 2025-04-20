from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Avg, Count
from django.contrib import messages
from evaluationProf.models import Evaluation, NoteCritere
from datetime import datetime, timedelta
from utilisateurs.models import Professeur
from .forms import ProfesseurProfileForm
import logging

logger = logging.getLogger(__name__)

def is_professeur(user):
    return hasattr(user, 'professeur')

@login_required
@user_passes_test(is_professeur)
def dashboard_professeur(request):
    try:
        # Get the professor instance and ID
        professeur = request.user.professeur
        professeur_id = professeur.id
        
        logger.info(f"Loading dashboard for professor ID: {professeur_id}")

        # Get evaluations
        evaluations = Evaluation.objects.filter(
            formation__professeur_id=professeur_id,
            statut='validé'
        ).select_related(
            'formation',
            'etudiant'
        ).prefetch_related(
            'notes',
            'notes__critere'
        )

        logger.info(f"Found {evaluations.count()} evaluations")

        # Calculate statistics
        total_evaluations = evaluations.count()
        moyenne_stats = evaluations.aggregate(
            moyenne=Avg('notes__note')
        )
        moyenne_generale = moyenne_stats['moyenne'] or 0

        # Get criteria statistics
        criteres_stats = NoteCritere.objects.filter(
            evaluation__formation__professeur_id=professeur_id,
            evaluation__statut='validé'
        ).values(
            'critere__nom'
        ).annotate(
            moyenne=Avg('note'),
            total=Count('id')
        ).order_by('critere__nom')

        # Get monthly statistics
        aujourd_hui = datetime.now()
        debut_mois = aujourd_hui.replace(day=1)
        stats_mensuelles = evaluations.filter(
            date_creation__gte=debut_mois
        ).count()

        # Recent evaluations with details
        evaluations_recentes = evaluations.order_by('-date_creation')[:5]

        # Prepare context with detailed information
        context = {
            'professeur': professeur,
            'total_evaluations': total_evaluations,
            'moyenne_generale': round(moyenne_generale, 2),
            'criteres_stats': list(criteres_stats),
            'stats_mensuelles': stats_mensuelles,
            'evaluations_recentes': evaluations_recentes,
            'debug_info': {
                'professeur_id': professeur_id,
                'total_found': total_evaluations,
                'has_data': total_evaluations > 0
            }
        }

        logger.info("Dashboard data prepared successfully")
        return render(request, 'prof/dashboard.html', context)

    except Exception as e:
        logger.error(f"Error in dashboard_professeur: {str(e)}", exc_info=True)
        return render(request, 'prof/dashboard.html', {
            'error': str(e),
            'debug_info': {
                'user_id': request.user.id,
                'username': request.user.username,
                'is_prof': hasattr(request.user, 'professeur'),
                'prof_id': getattr(getattr(request.user, 'professeur', None), 'id', None)
            }
        })

@login_required
@user_passes_test(is_professeur)
def liste_evaluations(request):
    # Récupérer l'instance du professeur à partir de l'utilisateur connecté
    professeur = request.user.professeur
    
    evaluations = Evaluation.objects.filter(
        formation__professeur=professeur
    ).select_related(
        'formation',
        'etudiant'
    ).order_by('-date_creation')
    
    return render(request, 'prof/liste_evaluations.html', {
        'evaluations': evaluations
    })

@login_required
@user_passes_test(is_professeur)
def profil_professeur(request):
    try:
        professeur = request.user.professeur
        total_evaluations = Evaluation.objects.filter(
            formation__professeur=professeur,
            statut='validé'
        ).count()

        if request.method == 'POST':
            # Update profile information
            user = request.user
            user.first_name = request.POST.get('prenom')
            user.last_name = request.POST.get('nom')
            user.email = request.POST.get('email')
            user.save()

            # Update professor information
            professeur.departement = request.POST.get('departement')
            professeur.specialite = request.POST.get('specialite')
            
            # Handle photo upload
            if 'photo' in request.FILES:
                professeur.photo = request.FILES['photo']
            
            professeur.save()
            messages.success(request, 'Profil mis à jour avec succès!')
            return redirect('prof:profil')

        context = {
            'professeur': professeur,
            'total_evaluations': total_evaluations,
        }
        return render(request, 'prof/profil.html', context)

    except Exception as e:
        messages.error(request, f"Une erreur s'est produite: {str(e)}")
        return render(request, 'prof/profil.html', {'error': str(e)})