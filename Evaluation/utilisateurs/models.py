from django.contrib.auth.models import AbstractUser
from django.db import models

# Modèle utilisateur personnalisé
class Utilisateur(AbstractUser):
    ROLES = [
        ('etudiant', 'Étudiant'),
        ('professeur', 'Professeur'),
        ('admin', 'Administrateur'),
    ]
    
    role = models.CharField(max_length=10, choices=ROLES)
    def __str__(self):
        return f"{self.username} - {self.role}"
class Etudiant(models.Model):
    user = models.OneToOneField(Utilisateur, on_delete=models.CASCADE)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    departement = models.CharField(max_length=100)
    licence = models.CharField(max_length=100)
    telephone = models.CharField(max_length=100)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nom + ' ' + self.prenom
    
# Modèle Professeur
class Professeur(models.Model):
    user = models.OneToOneField(Utilisateur, on_delete=models.CASCADE)
    nom=models.CharField(max_length=50)
    prenom=models.CharField(max_length=100)
    departement = models.CharField(max_length=100)

    def __str__(self):
        return f"Prof: {self.user.username} - {self.departement}"

# Modèle Administrateur
class Administrateur(models.Model):
    user = models.OneToOneField(Utilisateur, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"Admin: {self.user.username}"    