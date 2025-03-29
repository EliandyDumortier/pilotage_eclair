from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Administrateur'),
        ('metier', 'Métier'),
        ('analyste', 'Analyste'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='analyste')


class KPI(models.Model):
    CATEGORIES = [
        ('financier', 'Financier'),
        ('operationnel', 'Opérationnel'),
        ('autre', 'Autre'),
    ]

    nom = models.CharField(max_length=100)
    valeur_actuelle = models.FloatField()
    objectif = models.FloatField()
    date = models.DateField()
    categorie = models.CharField(max_length=50, choices=CATEGORIES, default='autre')

    def ecart(self):
        return self.valeur_actuelle - self.objectif

    def __str__(self):
        return f"{self.nom} - {self.date}"



class Commentaire(models.Model):
    kpi = models.ForeignKey(KPI, on_delete=models.CASCADE, related_name='commentaires')
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE)
    contenu = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Commentaire de {self.utilisateur.username} sur {self.kpi.nom}"
