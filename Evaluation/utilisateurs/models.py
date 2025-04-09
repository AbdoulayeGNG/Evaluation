from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

class Utilisateur(AbstractUser):
    ROLES = [
        ('etudiant', 'Étudiant'),
        ('professeur', 'Professeur'),
        ('admin', 'Administrateur'),
    ]
    
    role = models.CharField(max_length=10, choices=ROLES)
    
    def save(self, *args, **kwargs):
        if not self.pk and self.role == 'admin':  # Si nouvel utilisateur admin
            self.is_staff = True  # Permet l'accès à l'interface d'administration
            self.is_superuser = False  # N'accorde pas tous les droits super-utilisateur
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.username} - {self.role}"

class Etudiant(models.Model):
    NIVEAUX_CHOICES = [
        ('L1', 'Licence 1'),
        ('L2', 'Licence 2'),
        ('L3', 'Licence 3'),
        ('M1', 'Master 1'),
        ('M2', 'Master 2'),
    ]
    user = models.OneToOneField(Utilisateur, on_delete=models.CASCADE)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    departement = models.CharField(max_length=100)
    licence  = models.CharField(max_length=2, choices=NIVEAUX_CHOICES)
    telephone = models.CharField(max_length=100)
    photo = models.ImageField(upload_to='photos_profil/', null=True, blank=True)
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
        return f"Prof: {self.prenom} - {self.departement}"

# Modèle Administrateur
class Administrateur(models.Model):
    user = models.OneToOneField(Utilisateur, on_delete=models.CASCADE)
    nom=models.CharField(max_length=50)
    prenom=models.CharField(max_length=100)
    contact=models.CharField(max_length=15)
    
    def __str__(self):
        return f"Admin: {self.user.username}"