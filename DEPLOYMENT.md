# 🚀 Guide de Déploiement NYOS APR sur Google Cloud

Ce guide vous accompagne étape par étape pour déployer l'application NYOS APR sur Google Cloud Platform (GCP).

## 📋 Prérequis

1. **Compte Google Cloud** avec facturation activée
2. **Google Cloud CLI** installé (`gcloud`)
3. **Docker** installé localement
4. **Node.js 18+** et **Python 3.10+**

## 🏗️ Architecture de Déploiement

```
┌─────────────────────────────────────────────────────────────┐
│                    Google Cloud Platform                     │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐ │
│  │   Cloud     │    │  Cloud Run  │    │  Cloud SQL      │ │
│  │   Storage   │◄───│  (Backend)  │───►│  (PostgreSQL)   │ │
│  │  (Frontend) │    └─────────────┘    └─────────────────┘ │
│  └─────────────┘           │                               │
│                            │                               │
│  ┌─────────────┐           │                               │
│  │   Cloud     │◄──────────┘                               │
│  │   CDN       │                                           │
│  └─────────────┘                                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Option 1: Déploiement Simple avec Cloud Run (Recommandé)

### Étape 1: Configuration du Projet GCP

```bash
# Créer un nouveau projet (ou utiliser un existant)
gcloud projects create nyos-apr-prod --name="NYOS APR Production"

# Sélectionner le projet
gcloud config set project nyos-apr-prod

# Activer les APIs nécessaires
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  secretmanager.googleapis.com \
  sqladmin.googleapis.com
```

### Étape 2: Configurer les Secrets

```bash
# Stocker la clé API Gemini de façon sécurisée
echo -n "YOUR_GOOGLE_GEMINI_API_KEY" | \
  gcloud secrets create gemini-api-key --data-file=-

# Donner accès au service Cloud Run
gcloud secrets add-iam-policy-binding gemini-api-key \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Étape 3: Créer le Dockerfile Backend

Créez `backend/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code
COPY . .

# Variables d'environnement
ENV PORT=8080
ENV HOST=0.0.0.0

# Exposer le port
EXPOSE 8080

# Lancer l'application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Étape 4: Déployer le Backend sur Cloud Run

```bash
cd backend

# Construire et déployer en une seule commande
gcloud run deploy nyos-api \
  --source . \
  --region europe-west1 \
  --allow-unauthenticated \
  --set-secrets="GOOGLE_API_KEY=gemini-api-key:latest" \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10

# Récupérer l'URL du service
gcloud run services describe nyos-api --region europe-west1 --format='value(status.url)'
```

### Étape 5: Configurer le Frontend

```bash
cd frontend

# Mettre à jour l'URL de l'API
# Éditez src/api.js et remplacez API_BASE par l'URL Cloud Run
# const API_BASE = 'https://nyos-api-xxxxx-ew.a.run.app';

# Build pour production
npm run build
```

### Étape 6: Déployer le Frontend sur Cloud Storage + CDN

```bash
# Créer un bucket pour le frontend
gsutil mb -l europe-west1 gs://nyos-apr-frontend

# Configurer pour l'hébergement web
gsutil web set -m index.html -e index.html gs://nyos-apr-frontend

# Uploader les fichiers buildés
gsutil -m rsync -r dist/ gs://nyos-apr-frontend

# Rendre public
gsutil iam ch allUsers:objectViewer gs://nyos-apr-frontend
```

### Étape 7: Configurer Cloud CDN et HTTPS (Optionnel)

```bash
# Créer un load balancer avec HTTPS
gcloud compute backend-buckets create nyos-frontend-backend \
  --gcs-bucket-name=nyos-apr-frontend \
  --enable-cdn

# Réserver une IP statique
gcloud compute addresses create nyos-ip --global

# Créer le load balancer (nécessite configuration SSL)
# Voir: https://cloud.google.com/cdn/docs/setting-up-cdn-with-bucket
```

---

## 📦 Option 2: Déploiement avec Cloud SQL (Production)

Pour une base de données persistante en production:

### Étape 1: Créer l'instance Cloud SQL

```bash
# Créer une instance PostgreSQL
gcloud sql instances create nyos-db \
  --database-version=POSTGRES_14 \
  --tier=db-f1-micro \
  --region=europe-west1 \
  --root-password=YOUR_SECURE_PASSWORD

# Créer la base de données
gcloud sql databases create nyos_apr --instance=nyos-db

# Créer un utilisateur
gcloud sql users create nyos_user \
  --instance=nyos-db \
  --password=YOUR_USER_PASSWORD
```

### Étape 2: Configurer la connexion

```bash
# Activer le Cloud SQL Auth Proxy
gcloud run services update nyos-api \
  --add-cloudsql-instances=PROJECT_ID:europe-west1:nyos-db \
  --set-env-vars="DATABASE_URL=postgresql://nyos_user:PASSWORD@/nyos_apr?host=/cloudsql/PROJECT_ID:europe-west1:nyos-db"
```

---

## 🔧 Configuration de l'Environnement

### Variables d'Environnement Backend

Créez `.env.production` dans le dossier backend:

```env
# API Keys
GOOGLE_API_KEY=${GOOGLE_API_KEY}  # Injecté depuis Secret Manager

# Database (pour Cloud SQL)
DATABASE_URL=postgresql://user:pass@/dbname?host=/cloudsql/PROJECT:REGION:INSTANCE

# CORS (URL de votre frontend)
CORS_ORIGINS=https://nyos-apr.example.com,https://storage.googleapis.com

# Mode production
ENVIRONMENT=production
```

### Mise à jour du Backend pour Production

Mettez à jour `backend/app/config.py`:

```python
import os
from urllib.parse import quote_plus

# API Key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./nyos.db")

# CORS
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

# Environment
IS_PRODUCTION = os.getenv("ENVIRONMENT") == "production"
```

---

## 🌐 Configuration du Domaine Personnalisé

### Avec Cloud Run

```bash
# Mapper un domaine personnalisé
gcloud run domain-mappings create \
  --service=nyos-api \
  --domain=api.nyos-apr.com \
  --region=europe-west1
```

### Configuration DNS

Ajoutez ces enregistrements DNS:

| Type  | Nom     | Valeur                           |
|-------|---------|----------------------------------|
| CNAME | api     | ghs.googlehosted.com             |
| CNAME | www     | c.storage.googleapis.com         |
| A     | @       | [IP du Load Balancer]            |

---

## 📊 Monitoring et Logs

### Configurer Cloud Monitoring

```bash
# Voir les logs en temps réel
gcloud logs tail "resource.type=cloud_run_revision"

# Créer une alerte sur les erreurs
gcloud monitoring policies create \
  --policy-from-file=monitoring-policy.yaml
```

### Dashboard recommandé

1. Allez dans **Cloud Console > Monitoring > Dashboards**
2. Créez un nouveau dashboard avec:
   - Request count
   - Latency (p50, p95, p99)
   - Error rate
   - Memory usage
   - CPU usage

---

## 💰 Estimation des Coûts

| Service | Configuration | Coût estimé/mois |
|---------|--------------|------------------|
| Cloud Run | 1 vCPU, 1GB RAM, ~100k req | ~$5-15 |
| Cloud Storage | 1GB frontend | ~$0.02 |
| Cloud SQL | db-f1-micro | ~$10 |
| Cloud CDN | 10GB transfer | ~$1 |
| **Total** | | **~$15-30** |

> 💡 Avec le Free Tier GCP, les premiers mois peuvent être gratuits!

---

## 🔄 CI/CD avec Cloud Build

Créez `cloudbuild.yaml` à la racine:

```yaml
steps:
  # Build backend
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/nyos-api', './backend']

  # Push to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/nyos-api']

  # Deploy to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'nyos-api'
      - '--image'
      - 'gcr.io/$PROJECT_ID/nyos-api'
      - '--region'
      - 'europe-west1'
      - '--allow-unauthenticated'

  # Build frontend
  - name: 'node:18'
    dir: 'frontend'
    entrypoint: npm
    args: ['ci']

  - name: 'node:18'
    dir: 'frontend'
    entrypoint: npm
    args: ['run', 'build']

  # Deploy frontend to Storage
  - name: 'gcr.io/cloud-builders/gsutil'
    args: ['-m', 'rsync', '-r', 'frontend/dist/', 'gs://nyos-apr-frontend']

images:
  - 'gcr.io/$PROJECT_ID/nyos-api'
```

### Configurer le déploiement automatique

```bash
# Connecter à GitHub
gcloud builds triggers create github \
  --repo-name=NYOS-APR \
  --repo-owner=YOUR_GITHUB_USERNAME \
  --branch-pattern="^main$" \
  --build-config=cloudbuild.yaml
```

---

## ✅ Checklist de Déploiement

- [ ] Projet GCP créé et configuré
- [ ] APIs nécessaires activées
- [ ] Clé Gemini dans Secret Manager
- [ ] Backend déployé sur Cloud Run
- [ ] Base de données configurée (SQLite ou Cloud SQL)
- [ ] Frontend buildé et uploadé
- [ ] CORS configuré correctement
- [ ] Domaine personnalisé (optionnel)
- [ ] HTTPS activé
- [ ] Monitoring configuré
- [ ] CI/CD en place

---

## 🆘 Dépannage

### Erreur CORS

Vérifiez que l'URL du frontend est dans la liste CORS du backend.

### Erreur de connexion à la base de données

Vérifiez que le Cloud SQL Auth Proxy est correctement configuré.

### Timeout sur Cloud Run

Augmentez le timeout:
```bash
gcloud run services update nyos-api --timeout=300
```

### Logs d'erreur

```bash
gcloud logs read "resource.type=cloud_run_revision AND severity>=ERROR" --limit=50
```

---

## 📚 Ressources

- [Documentation Cloud Run](https://cloud.google.com/run/docs)
- [Documentation Cloud SQL](https://cloud.google.com/sql/docs)
- [Documentation Cloud Storage](https://cloud.google.com/storage/docs)
- [Pricing Calculator](https://cloud.google.com/products/calculator)

---

*Document créé pour NYOS APR v2.0 - Février 2026*
