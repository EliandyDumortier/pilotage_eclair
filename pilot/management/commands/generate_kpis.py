import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from pilot.models import KPI

class Command(BaseCommand):
    help = 'Génère des KPI simulés avec les nouveaux champs du modèle'

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
                    objectif = round(random.uniform(60, 100), 2)
                    ecart = round(random.uniform(-20, 20), 2)
                    valeur = round(objectif + ecart, 2)
                    seuil_warning = round(abs(objectif * 0.1), 2)
                    seuil_critique = round(abs(objectif * 0.2), 2)

                    KPI.objects.create(
                        nom=nom,
                        description=f"Indicateur {nom.lower()} pour la catégorie {cat}",
                        valeur_actuelle=valeur,
                        objectif=objectif,
                        date=jour,
                        categorie=cat,
                        seuil_warning=seuil_warning,
                        seuil_critique=seuil_critique,
                        created_at=timezone.now(),
                        updated_at=timezone.now(),
                    )

        self.stdout.write(self.style.SUCCESS("✅ 30 jours de données KPI générées avec succès."))
