from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Administrateur'),
        ('metier', 'Métier'),
        ('analyste', 'Analyste'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='analyste')
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    class Meta:
        ordering = ['username']

class KPI(models.Model):
    CATEGORIES = [
        ('financier', 'Financier'),
        ('operationnel', 'Opérationnel'),
        ('autre', 'Autre'),
    ]

    STATUT_CHOICES = [
        ('normal', 'Normal'),
        ('warning', 'Attention'),
        ('critique', 'Critique'),
    ]

    nom = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    valeur_actuelle = models.FloatField()
    objectif = models.FloatField()
    date = models.DateField()
    categorie = models.CharField(max_length=50, choices=CATEGORIES, default='autre')
    seuil_warning = models.FloatField(default=0)
    seuil_critique = models.FloatField(default=0)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    #created_at = models.DateTimeField(default=timezone.now)
    #updated_at = models.DateTimeField(default=timezone.now)

    def ecart(self):
        return self.valeur_actuelle - self.objectif

    def statut(self):
        ecart = abs(self.ecart())
        if ecart >= self.seuil_critique:
            return 'critique'
        elif ecart >= self.seuil_warning:
            return 'warning'
        return 'normal'

    def __str__(self):
        return f"{self.nom} - {self.date}"

    class Meta:
        ordering = ['-date', 'nom']
        verbose_name = "KPI"
        verbose_name_plural = "KPIs"

class Commentaire(models.Model):
    kpi = models.ForeignKey(KPI, on_delete=models.CASCADE, related_name='commentaires')
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE)
    contenu = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    is_insight = models.BooleanField(default=False)

    def __str__(self):
        return f"Commentaire de {self.utilisateur.username} sur {self.kpi.nom}"

    class Meta:
        ordering = ['-date_creation']

class PowerBIReport(models.Model):
    titre = models.CharField(max_length=200)
    fichier = models.FileField(upload_to='powerbi_reports/')
    date_upload = models.DateTimeField(auto_now_add=True)
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.titre} - {self.date_upload.strftime('%d/%m/%Y')}"

    class Meta:
        ordering = ['-date_upload']