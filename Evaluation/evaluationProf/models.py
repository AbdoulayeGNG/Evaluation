from django.db import models
from django.conf import settings
from django.utils.timezone import now
from datetime import timedelta

# Modèle des Critères d'Évaluation
class Critere(models.Model):
    nom = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.nom

# Modèle Formation
class Formation(models.Model):
    nom = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    professeur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'professeur'})

    def __str__(self):
        return self.nom

# Modèle Évaluation (chaque évaluation contient plusieurs critères)
class Evaluation(models.Model):
    etudiant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'etudiant'})
    formation = models.ForeignKey(Formation, on_delete=models.CASCADE)
    commentaire = models.TextField()  # Suppression de "blank=True, null=True" pour le rendre obligatoire
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    statut = models.CharField(max_length=20, choices=[('validé', 'Validé'), ('en attente', 'En attente')], default='en attente')

    def peut_modifier(self):
        """ Vérifie si l'évaluation peut encore être modifiée (ex: sous 24h) """
        return now() - self.date_creation <= timedelta(hours=24)

    def __str__(self):
        return f"{self.etudiant.username} - {self.formation.nom} - {self.date_creation}"

# Modèle Notes par Critère (chaque évaluation contient plusieurs notes selon les critères)
class NoteCritere(models.Model):
    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE, related_name="notes")
    critere = models.ForeignKey(Critere, on_delete=models.CASCADE)
    note = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])

    def __str__(self):
        return f"{self.evaluation} - {self.critere.nom} : {self.note}"
