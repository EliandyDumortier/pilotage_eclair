# 💡 Pilot'Éclair

**Pilot'Éclair** est une application web de pilotage opérationnel en temps réel, conçue pour suivre les indicateurs clés de performance (KPI) et faciliter l’analyse à chaud des écarts.

---

## 🎯 Objectif

Fournir aux équipes métier et aux analystes un outil simple et rapide pour :
- Visualiser les KPI en temps réel
- Détecter les écarts par rapport aux objectifs
- Ajouter des commentaires pour aider à la compréhension
- Centraliser les retours métiers dans une interface claire

---

## 🧱 Stack Technique

- **Backend** : Django (Python)
- **Frontend** : Tailwind CSS
- **Base de données** : SQLite (dev) / PostgreSQL (prod)
- **Graphiques** : Plotly.js
- **Authentification** : Système personnalisé avec rôles (`admin`, `analyste`, `métier`)

---

## 🔧 Fonctionnalités (version V1)

- 👤 Authentification avec rôles utilisateurs
- 📊 Dashboard avec affichage des KPI
- 📉 Calcul automatique des écarts par rapport aux objectifs
- 💬 Zone de commentaires par KPI
- 🧪 Structure prête pour intégrer des alertes ou analyses plus poussées

---

## 🚀 Lancer le projet en local

```bash
git clone https://github.com/votre-utilisateur/pilot-eclair.git
cd pilot-eclair

# Création de l'environnement virtuel
python -m venv env
source env/bin/activate  # ou .\\env\\Scripts\\activate sous Windows

# Installation des dépendances
pip install -r requirements.txt

# Lancement du projet
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

```

## 📌 Idées pour la suite
Envoi d’alertes automatiques si un écart dépasse un seuil

Intégration Power BI / fichiers Excel

Tableau de bord dynamique filtré par période ou par équipe

API REST pour exposer les données à d'autres services

---
## 👤 Auteure
Eliandy Rymer
Data Scientist | Analyste | Développeuse IA
📫 rymer.eliandy@gmail.com
📍 Lille, France
🎓 Simplon x Microsoft - Développement en Intelligence Artificielle



---

