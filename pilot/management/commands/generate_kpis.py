import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from pilot.models import KPI

class Command(BaseCommand):
    help = 'Génère des KPI simulés pour les tests'

    def handle(self, *args, **kwargs):
        categories = ['financier', 'operationnel', 'autre']
        noms_kpi = {
            'financier': ['Taux d’acceptation', 'Montant moyen', 'Revenus', 'Coût du risque'],
            'operationnel': ['Délai de traitement', 'Taux de réclamation', 'Appels traités'],
            'autre': ['Satisfaction client', 'Équipe formée', 'Incidents']
        }

        today = date.today()

        for days_ago in range(30):
            jour = today - timedelta(days=days_ago)
            for cat in categories:
                for nom in noms_kpi[cat]:
                    objectif = random.uniform(50, 100)
                    ecart = random.uniform(-15, 15)
                    valeur_actuelle = round(objectif + ecart, 2)
                    KPI.objects.create(
                        nom=nom,
                        valeur_actuelle=valeur_actuelle,
                        objectif=round(objectif, 2),
                        date=jour,
                        categorie=cat
                    )

        self.stdout.write(self.style.SUCCESS('✔️ Données KPI simulées générées avec succès !'))
        self.stdout.write(self.style.WARNING('⚠️ Veuillez supprimer ces données après les tests !'))
        self.stdout.write(self.style.NOTICE('ℹ️ Utilisez la commande `python manage.py flush` pour supprimer toutes les données.'))