from google.cloud import bigquery
from src.utils.gcp_client import get_bigquery_client, PROJECT_ID, DATASET_ID, TABLE_ID, LOCATION

def init_bigquery_schema():
    """
    Inicializa o Dataset e a Tabela no BigQuery para o repositório de reuniões.
    Cria também o VECTOR INDEX para busca por similaridade de cosseno.
    """
    bq = get_bigquery_client()
    dataset_ref = bigquery.DatasetReference(PROJECT_ID, DATASET_ID)
    
    # 1. Cria o Dataset se não existir
    try:
        bq.get_dataset(dataset_ref)
        print(f"[OK] Dataset '{DATASET_ID}' já existe.")
    except Exception:
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = LOCATION
        dataset.description = "Dataset de inteligência operacional e reuniões corporativas - Whirlpool"
        bq.create_dataset(dataset, timeout=30)
        print(f"[OK] Dataset '{DATASET_ID}' criado com sucesso na região {LOCATION}.")

    # 2. Cria a Tabela com suporte a vetores
    table_ref = dataset_ref.table(TABLE_ID)
    schema = [
        bigquery.SchemaField("chunk_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("meeting_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("meeting_title", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("meeting_date", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("department", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("speaker", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("content_sanitized", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("action_items", "STRING", mode="REPEATED"),
        bigquery.SchemaField("embedding", "FLOAT64", mode="REPEATED"),
    ]

    try:
        bq.get_table(table_ref)
        print(f"[OK] Tabela '{TABLE_ID}' já existe.")
    except Exception:
        table = bigquery.Table(table_ref, schema=schema)
        table.description = "Tabela contendo transcrições tratadas e embeddings vetoriais de reuniões"
        bq.create_table(table)
        print(f"[OK] Tabela '{TABLE_ID}' criada com sucesso com schema vetorial.")

    # 3. Criação do Índice Vetorial (VECTOR INDEX)
    index_query = f"""
    CREATE VECTOR INDEX IF NOT EXISTS meeting_vector_idx
    ON `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`(embedding)
    OPTIONS(distance_type='COSINE', index_type='IVF');
    """
    try:
        query_job = bq.query(index_query)
        query_job.result()
        print("[OK] VECTOR INDEX configurado com sucesso (COSINE distance).")
    except Exception as e:
        # Em tabelas muito pequenas ou recém-criadas, o BigQuery pode avisar que o índice será construído conforme os dados crescerem
        print(f"[INFO] Criação do índice vetorial submetida: {e}")

def insert_meeting_chunks(chunks: list[dict]) -> bool:
    """
    Insere uma lista de trechos de reuniões processados com embeddings no BigQuery.
    """
    bq = get_bigquery_client()
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    
    errors = bq.insert_rows_json(table_ref, chunks)
    if not errors:
        print(f"[OK] {len(chunks)} trechos inseridos com sucesso no BigQuery.")
        return True
    else:
        print(f"[ERRO] Falha ao inserir registros no BigQuery: {errors}")
        return False

def search_similar_chunks(query_embedding: list[float], top_k: int = 3) -> list[dict]:
    """
    Executa a busca vetorial nativa no BigQuery usando VECTOR_SEARCH.
    Retorna os trechos mais relevantes ordenados por proximidade de cosseno.
    """
    bq = get_bigquery_client()
    query = f"""
    SELECT
        base.chunk_id,
        base.meeting_id,
        base.meeting_title,
        base.meeting_date,
        base.department,
        base.speaker,
        base.content_sanitized,
        base.action_items,
        distance
    FROM VECTOR_SEARCH(
        TABLE `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`,
        'embedding',
        (SELECT @query_embedding AS embedding),
        top_k => @top_k,
        distance_type => 'COSINE'
    )
    ORDER BY distance ASC
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ArrayQueryParameter("query_embedding", "FLOAT64", query_embedding),
            bigquery.ScalarQueryParameter("top_k", "INT64", top_k),
        ]
    )

    query_job = bq.query(query, job_config=job_config)
    results = query_job.result()

    hits = []
    for row in results:
        hits.append({
            "chunk_id": row.chunk_id,
            "meeting_id": row.meeting_id,
            "meeting_title": row.meeting_title,
            "meeting_date": row.meeting_date,
            "department": row.department,
            "speaker": row.speaker,
            "content": row.content_sanitized,
            "action_items": list(row.action_items) if row.action_items else [],
            "distance": float(row.distance),
            "similarity_score": round(1.0 - float(row.distance), 4) # Cosine similarity
        })
    return hits

if __name__ == "__main__":
    print("Inicializando infraestrutura no BigQuery...")
    init_bigquery_schema()
