# Script de Deploy Automático para o Google Cloud Run (PowerShell)
$PROJECT_ID = "project-9940e307-bf71-45ef-be0"
$REGION = "us-central1"
$SERVICE_NAME = "whirlpool-ai-portal"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   DEPLOY DO WHIRLPOOL AI OPERATIONS PORTAL NO CLOUD RUN   " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Habilita as APIs necessárias para o Cloud Run e Cloud Build
Write-Host "[1/3] Habilitando APIs Cloud Run e Cloud Build..." -ForegroundColor Yellow
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com --project $PROJECT_ID

# 2. Garante permissões de IAM para a conta de serviço do Cloud Run
Write-Host "[2/3] Configurando permissões de IAM (Vertex AI e BigQuery)..." -ForegroundColor Yellow
$PROJECT_NUMBER = (gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
$COMPUTE_SA = "$PROJECT_NUMBER-compute@developer.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID `
    --member="serviceAccount:$COMPUTE_SA" `
    --role="roles/aiplatform.user" `
    --condition=None

gcloud projects add-iam-policy-binding $PROJECT_ID `
    --member="serviceAccount:$COMPUTE_SA" `
    --role="roles/bigquery.admin" `
    --condition=None

# 3. Executa o deploy do contêiner a partir do código local
Write-Host "[3/3] Compilando contêiner e implantando no Cloud Run..." -ForegroundColor Green
gcloud run deploy $SERVICE_NAME `
    --source . `
    --project $PROJECT_ID `
    --region $REGION `
    --allow-unauthenticated `
    --memory 1Gi `
    --timeout 300

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Deploy finalizado com sucesso! Acesse a URL fornecida acima." -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
