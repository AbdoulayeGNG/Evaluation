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

    formations = Formation.objects.all()
    criteres = Critere.objects.all()
    return render(request, "evaluationProf/evaluation.html", {"formations": formations, "criteres": criteres})

# Afficher les évaluations validées
@login_required
def liste_evaluations(request):
    evaluation = Evaluation.objects.all()
    evaluations = Evaluation.objects.filter(statut="validé").order_by("-date_creation")
    return render(request, "evaluationProf/affichageEvaluation.html", {"evaluations": evaluation})
