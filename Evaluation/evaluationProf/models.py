from django.db import models

from utilisateurs.models import Etudiant, Professeur

# Create your models here.
class Formation(models.Model):
    id = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=255)
    professeur = models.ForeignKey(Professeur, on_delete=models.CASCADE, related_name="formations")

    def __str__(self):
        return self.nom

class Critere(models.Model):
    id = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.nom
    
class Evaluation(models.Model):
    id = models.AutoField(primary_key=True)
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE, related_name="evaluations")
    professeur = models.ForeignKey(Professeur, on_delete=models.CASCADE, related_name="evaluations")
    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name="evaluations")
    critere = models.ForeignKey(Critere, on_delete=models.CASCADE, related_name="evaluations")
    note = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # Note de 1 à 5
    commentaire = models.TextField(blank=True, null=True)
    date_evaluation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Évaluation de {self.professeur.nom} par {self.etudiant.nom} ({self.note}/5)"    