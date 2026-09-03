#!/bin/bash
# Script de Deploy Automático para o Google Cloud Run (Bash)

set -e

PROJECT_ID="project-9940e307-bf71-45ef-be0"
REGION="us-central1"
SERVICE_NAME="whirlpool-ai-portal"

echo "============================================================"
echo "   DEPLOY DO WHIRLPOOL AI OPERATIONS PORTAL NO CLOUD RUN   "
echo "============================================================"

# 1. Habilita as APIs necessárias
echo "[1/3] Habilitando APIs Cloud Run e Cloud Build..."
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com --project $PROJECT_ID

# 2. Configura permissões de IAM para a conta de serviço padrão do Cloud Run
echo "[2/3] Configurando permissões de IAM (Vertex AI e BigQuery)..."
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
COMPUTE_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${COMPUTE_SA}" \
    --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${COMPUTE_SA}" \
    --role="roles/bigquery.admin"

# 3. Executa o deploy do contêiner a partir do código fonte local
echo "[3/3] Compilando contêiner e implantando no Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --source . \
    --project $PROJECT_ID \
    --region $REGION \
    --allow-unauthenticated \
    --memory 1Gi \
    --timeout 300

echo "============================================================"
echo "Deploy finalizado com sucesso! Acesse a URL fornecida acima."
echo "============================================================"
