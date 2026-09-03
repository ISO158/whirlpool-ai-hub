import os
from dotenv import load_dotenv
from google import genai
from google.cloud import bigquery

# Carrega variáveis do arquivo .env
load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID", "project-9940e307-bf71-45ef-be0")
LOCATION = os.getenv("GCP_LOCATION", "us-central1")
DATASET_ID = os.getenv("BIGQUERY_DATASET", "whirlpool_intelligence")
TABLE_ID = os.getenv("BIGQUERY_TABLE", "meeting_knowledge_base")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-004")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

def get_bigquery_client() -> bigquery.Client:
    """Retorna o cliente BigQuery configurado com o projeto ativo."""
    return bigquery.Client(project=PROJECT_ID)

def get_genai_client() -> genai.Client:
    """
    Retorna o cliente unificado Google GenAI apontando para o Vertex AI.
    Autenticação automática via Application Default Credentials (ADC).
    """
    return genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

def test_connections():
    """Testa a conectividade com o BigQuery e Vertex AI."""
    print("=" * 60)
    print(f"Testando conexões no projeto: {PROJECT_ID} ({LOCATION})")
    print("=" * 60)

    # 1. Teste BigQuery
    try:
        bq = get_bigquery_client()
        datasets = list(bq.list_datasets())
        print(f"[OK] BigQuery conectado com sucesso! Datasets encontrados: {len(datasets)}")
    except Exception as e:
        print(f"[ERRO] Falha ao conectar ao BigQuery: {e}")
        return False

    # 2. Teste Vertex AI (Gemini)
    try:
        ai_client = get_genai_client()
        response = ai_client.models.generate_content(
            model=GEMINI_MODEL,
            contents="Responda em uma frase curta: Qual a missão da Whirlpool?",
        )
        print(f"[OK] Vertex AI ({GEMINI_MODEL}) conectado com sucesso!")
        print(f"     Resposta de teste: {response.text.strip()}")
    except Exception as e:
        print(f"[ERRO] Falha ao conectar ao Vertex AI: {e}")
        return False

    print("=" * 60)
    print("Todos os serviços Google Cloud estão operacionais!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    test_connections()
