from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.timezone import now
from datetime import timedelta
from django.core.validators import MinValueValidator, MaxValueValidator
from utilisateurs.models import Professeur

# Modèle des Critères d'Évaluation
class Critere(models.Model):
    nom = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.nom

# Modèle Semestre
class Semestre(models.Model):
    SEMESTRE_CHOICES = [
        ('S1', 'Semestre 1'),
        ('S2', 'Semestre 2'),
    ]
    annee_universitaire = models.CharField(
        max_length=9,
        help_text="Format: 2024-2025"
    )
    semestre = models.CharField(
        max_length=2,
        choices=SEMESTRE_CHOICES
    )
    date_debut = models.DateField("Début du semestre")
    date_fin = models.DateField("Fin du semestre")
    periode_evaluation_debut = models.DateField("Début des évaluations")
    periode_evaluation_fin = models.DateField("Fin des évaluations")

    class Meta:
        unique_together = ['annee_universitaire', 'semestre']
        ordering = ['-annee_universitaire', 'semestre']

    def __str__(self):
        return f"{self.get_semestre_display()} {self.annee_universitaire}"

    def est_periode_evaluation(self):
        aujourd_hui = timezone.now().date()
        return self.periode_evaluation_debut <= aujourd_hui <= self.periode_evaluation_fin

# Modèle Formation
class Formation(models.Model):
    NIVEAUX_CHOICES = [
        ('1', 'Licence 1'),
        ('2', 'Licence 2'),
        ('3', 'Licence 3'),
        ('1', 'Master 1'),
        ('2', 'Master 2'),
    ]
    nom = models.CharField(max_length=255)
    description = models.TextField()
    professeur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'professeur'})
    niveau = models.CharField(max_length=2, choices=NIVEAUX_CHOICES)
    departement = models.CharField(max_length=255)
    
    semestre = models.ForeignKey(
        Semestre,
        on_delete=models.CASCADE,
        related_name='formations'
    )

    def est_evaluable(self):
        if not self.semestre:
            return False
        aujourd_hui = timezone.now().date()
        return (self.semestre.periode_evaluation_debut <= aujourd_hui <= 
                self.semestre.periode_evaluation_fin)

    def __str__(self):
        return f"{self.nom} - {self.semestre}"

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
