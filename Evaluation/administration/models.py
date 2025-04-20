from django.db import models
from django.utils import timezone
from utilisateurs.models import Administrateur, Professeur, Etudiant
from evaluationProf.models import Formation, Evaluation

class LogActivity(models.Model):
    admin = models.ForeignKey(Administrateur, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
