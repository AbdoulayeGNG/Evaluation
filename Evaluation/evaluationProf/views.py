from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.utils.timezone import now
from django.contrib.auth.decorators import login_required
from django.db import transaction
from .models import Evaluation, Formation, Critere, NoteCritere, Semestre

# Ajouter une évaluation
@login_required
def ajouter_evaluation(request):
    etudiant = request.user.etudiant
    
    # Récupérer le semestre actif
    semestre_actif = Semestre.objects.filter(
        periode_evaluation_debut__lte=timezone.now().date(),
        periode_evaluation_fin__gte=timezone.now().date()
    ).first()
    
    if not semestre_actif:
        messages.warning(request, "Aucune période d'évaluation n'est actuellement ouverte.")
        return redirect('etudiants:dashboard_etudiant')
    
    # Filtrer les formations évaluables
    formations = Formation.objects.filter(
    semestre=semestre_actif,
    niveau=etudiant.licence,
    departement=etudiant.departement
).exclude(
    evaluation__etudiant=request.user  # Exclure les formations déjà évaluées
).order_by('nom')
    if request.method == "POST":
        formation_id = request.POST.get("formation")
        formation = get_object_or_404(Formation, id=formation_id)
        
        # Vérifier si la formation est déjà évaluée par cet étudiant
        if Evaluation.objects.filter(etudiant=request.user, formation=formation).exists():
            messages.error(request, "Vous avez déjà évalué cette formation.")
            return redirect("evaluationProf:ajouter_evaluation")
        
        # Vérifier si la formation est évaluable
        if not formation.est_evaluable():
            messages.error(request, "La période d'évaluation pour ce module n'est pas active.")
            return redirect("evaluationProf:ajouter_evaluation")
        
        commentaire = request.POST.get("commentaire", "").strip()
        
        if not commentaire:
            messages.error(request, "Le commentaire est obligatoire.")
            return redirect("evaluationProf:ajouter_evaluation")
        
        try:
            with transaction.atomic():
                evaluation = Evaluation.objects.create(
                    etudiant=request.user,
                    formation=formation,
                    commentaire=commentaire,
                    statut='en attente'
                )
                
                # Sauvegarde des notes
                for critere in Critere.objects.all():
                    note = request.POST.get(f"critere_{critere.id}")
                    if note:
                        NoteCritere.objects.create(
                            evaluation=evaluation,
                            critere=critere,
                            note=int(note)
                        )
                
                messages.success(request, "Évaluation ajoutée avec succès ! En attente de validation.")
                return redirect('etudiants:dashboard_etudiant')
                
        except Exception as e:
            messages.error(request, f"Erreur lors de l'ajout de l'évaluation : {str(e)}")
    
    context = {
        "formations": formations,
        "criteres": Critere.objects.all(),
        "semestre_actif": semestre_actif
    }
    return render(request, "evaluationProf/evaluation.html", context)

# Afficher les évaluations validées
@login_required
def liste_evaluations(request):
    evaluation = Evaluation.objects.all()
    evaluations = Evaluation.objects.filter(statut="validé").order_by("-date_creation")
    return render(request, "evaluationProf/affichageEvaluation.html", {"evaluations": evaluation})


@login_required
def evaluationEtudiant(request):
    """Affiche les évaluations de l'étudiant connecté avec options de modification/suppression si autorisé"""
    evaluations = Evaluation.objects.filter(etudiant=request.user)

    return render(request, "evaluationProf/afficheEvaluationEtu.html", {"evaluationEtudiant": evaluations})

def modifier_evaluation(request, evaluation_id):
    """Permet de modifier une évaluation si elle est encore dans le délai de modification"""
    evaluation = get_object_or_404(Evaluation, id=evaluation_id, etudiant=request.user)

    # Vérifier si l'évaluation peut encore être modifiée (moins de 30 minutes)
   

    if request.method == "POST":
        commentaire = request.POST.get("commentaire", "").strip()

        if not commentaire:
            messages.error(request, "Le commentaire est obligatoire.")
            return redirect("evaluationProf:modifier_evaluation", evaluation_id=evaluation.id)

        evaluation.commentaire = commentaire
        evaluation.statut = "en attente"  # Remettre l'évaluation en attente après modification
        evaluation.date_modification = now()
        evaluation.save()

        # Mettre à jour les notes par critère
        for critere in Critere.objects.all():
            note = request.POST.get(f"critere_{critere.id}")
            if note:
                note_critere, created = NoteCritere.objects.get_or_create(
                    evaluation=evaluation, critere=critere,
                    defaults={"note": int(note)}
                )
                if not created:
                    note_critere.note = int(note)
                    note_critere.save()

        messages.success(request, "Évaluation modifiée avec succès.")
        return redirect("etudiants:dashboard_etudiant")

    criteres = Critere.objects.all()
    notes_existantes = {note.critere.id: note.note for note in NoteCritere.objects.filter(evaluation=evaluation)}

    return render(request, "evaluationProf/modifier_evaluation.html", {
        "evaluation": evaluation,
        "criteres": criteres,
        "notes_existantes": notes_existantes})


def supprimer_evaluation(request, evaluation_id):
    """Permet de supprimer une évaluation dans un délai donné"""
    evaluation = get_object_or_404(Evaluation, id=evaluation_id, etudiant=request.user)

    if request.method == "POST":
        evaluation.delete()
        messages.success(request, "Évaluation supprimée avec succès.")
        return redirect("etudiants:dashboard_etudiant")

    return render(request, "evaluationProf/confirmer_suppression.html", {"evaluation": evaluation})
