from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.timezone import now
from django.contrib.auth.decorators import login_required
from .models import Evaluation, Formation, Critere, NoteCritere

# Ajouter une évaluation
@login_required
def ajouter_evaluation(request):
    if request.method == "POST":
        formation_id = request.POST["formation"]
        commentaire = request.POST.get("commentaire", "").strip()  # Récupérer et supprimer les espaces inutiles

        if not commentaire:
            messages.error(request, "Le commentaire est obligatoire.")
            return redirect("ajouter_evaluation")

        formation = get_object_or_404(Formation, id=formation_id)

        evaluation = Evaluation.objects.create(
            etudiant=request.user,
            formation=formation,
            commentaire=commentaire,
            statut='en attente'
        )

        # Sauvegarde des notes par critère
        for critere in Critere.objects.all():
            note = request.POST.get(f"critere_{critere.id}")
            if note:
                NoteCritere.objects.create(
                    evaluation=evaluation,
                    critere=critere,
                    note=int(note)
                )

        messages.success(request, "Évaluation ajoutée avec succès ! En attente de validation.")
        return redirect("liste_evaluations")
    etudiant = request.user.etudiant
    formations = Formation.objects.filter(niveau=etudiant.licence, departement=etudiant.departement)
    # formations = Formation.objects.all()
    criteres = Critere.objects.all()
    return render(request, "evaluationProf/evaluation.html", {"formations": formations, "criteres": criteres})

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
    if now() - evaluation.date_creation > timedelta(minutes=30):
        messages.error(request, "Le délai de modification est expiré.")
        return redirect("evaluationEtudiant")

    if request.method == "POST":
        commentaire = request.POST.get("commentaire", "").strip()

        if not commentaire:
            messages.error(request, "Le commentaire est obligatoire.")
            return redirect("modifier_evaluation", evaluation_id=evaluation.id)

        evaluation.commentaire = commentaire
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
        return redirect("evaluationEtudiant")

    criteres = Critere.objects.all()
    notes_existantes = {note.critere.id: note.note for note in NoteCritere.objects.filter(evaluation=evaluation)}

    return render(request, "evaluationProf/modifier_evaluation.html", {
        "evaluation": evaluation,
        "criteres": criteres,
        "notes_existantes": notes_existantes})


def supprimer_evaluation(request, evaluation_id):
    """Permet de supprimer une évaluation dans un délai donné"""
    evaluation = get_object_or_404(Evaluation, id=evaluation_id, etudiant=request.user)

    # Vérifier si le délai de suppression est encore valable
    if now() - evaluation.date_creation > timedelta(minutes=30):
        messages.error(request, "Le délai de suppression est expiré.")
        return redirect("liste_evaluations")

    if request.method == "POST":
        evaluation.delete()
        messages.success(request, "Évaluation supprimée avec succès.")
        return redirect("liste_evaluations")

    return render(request, "evaluationProf/confirmer_suppression.html", {"evaluation": evaluation})
