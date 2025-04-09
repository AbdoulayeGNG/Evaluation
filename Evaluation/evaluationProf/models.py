from django.db import models
from django.conf import settings
from django.utils.timezone import now
from datetime import timedelta
from django.core.validators import MinValueValidator, MaxValueValidator
from utilisateurs.models import Professeur

# Modèle des Critères d'Évaluation
class Critere(models.Model):
    nom = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.nom

# Modèle Formation
class Formation(models.Model):
    NIVEAUX_CHOICES = [
        ('L1', 'Licence 1'),
        ('L2', 'Licence 2'),
        ('L3', 'Licence 3'),
        ('M1', 'Master 1'),
        ('M2', 'Master 2'),
    ]
    nom = models.CharField(max_length=255)
    description = models.TextField()
    professeur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'professeur'})
    niveau = models.CharField(max_length=2, choices=NIVEAUX_CHOICES)
    departement = models.CharField(max_length=255)

    def __str__(self):
        return self.nom

class Evaluation(models.Model):
    etudiant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'etudiant'})
    formation = models.ForeignKey(Formation, on_delete=models.CASCADE)
    commentaire = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    statut = models.CharField(max_length=20, choices=[('validé', 'Validé'), ('en attente', 'En attente')], default='validé')

    def peut_modifier(self):
        return now() - self.date_creation <= timedelta(minutes=1440)

    def __str__(self):
        return f"{self.etudiant.username} - {self.formation.nom} - {self.date_creation}"
    
# Modèle Notes par Critère (chaque évaluation contient plusieurs notes selon les critères)
class NoteCritere(models.Model):
    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE, related_name='notes')
    critere = models.ForeignKey(Critere, on_delete=models.CASCADE)
    note = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    commentaire = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ['evaluation', 'critere']

    def __str__(self):
        return f"{self.evaluation} - {self.critere}: {self.note}"
