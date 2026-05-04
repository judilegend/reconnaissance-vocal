# Reconnaissance Vocale (Speech Recognition System)

Ce projet est une application complète de reconnaissance vocale utilisant une architecture de microservices avec **FastAPI** (Backend) et **Nuxt.js** (Frontend). Il utilise les modèles pré-entraînés de Hugging Face (`facebook/wav2vec2-base-960h` et `openai/whisper-tiny`) et est entièrement conteneurisé avec Docker.

## Prérequis

1. **Docker** : Assurez-vous d'avoir [Docker Desktop](https://www.docker.com/products/docker-desktop/) installé et en cours d'exécution sur votre machine.

## Guide de démarrage rapide avec Docker

L'application est configurée avec Docker Compose pour faciliter l'installation des dépendances et le lancement des services.

### 1. Démarrer les services

Ouvrez un terminal (PowerShell ou Command Prompt) à la racine du projet (`d:\Projet M2\reconnaissance-vocal`) et exécutez la commande suivante :

```bash
docker compose up --build -d
```

Cette commande va :
- Télécharger les images de base (Python et Node.js).
- Installer les dépendances Python du backend (incluant PyTorch, FastAPI, Hugging Face Transformers).
- Installer les dépendances Node.js du frontend (Nuxt.js, Vue.js, TailwindCSS).
- Démarrer les deux serveurs en arrière-plan (mode détaché `-d`).

*(Note : Le premier lancement prendra quelques minutes le temps de télécharger les librairies, notamment PyTorch qui est volumineux).*

### 2. Accéder à l'application

Une fois les conteneurs démarrés, vous pouvez accéder aux interfaces via votre navigateur :

- **Frontend (Application Web)** : [http://localhost:3000](http://localhost:3000)
- **Backend (Documentation API Swagger)** : [http://localhost:8000/docs](http://localhost:8000/docs)

### 3. Voir les journaux (Logs)

Pour voir ce qui se passe en arrière-plan (par exemple, suivre le téléchargement des modèles Hugging Face lors de la première requête) :

```bash
# Pour voir les logs de tous les services
docker compose logs -f

# Pour voir spécifiquement les logs du backend
docker compose logs -f backend

# Pour voir spécifiquement les logs du frontend
docker compose logs -f frontend
```

### 4. Arrêter les services

Pour arrêter l'application, exécutez :

```bash
docker compose down
```

## Structure du Projet

- `/backend` : API FastAPI, gestion de l'authentification JWT et orchestration des modèles de transcription.
- `/frontend` : Application Nuxt.js avec TailwindCSS offrant une interface utilisateur moderne et accessible.
- `docker-compose.yml` : Configuration d'orchestration Docker.
