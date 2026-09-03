from google.genai import types
from src.utils.gcp_client import get_genai_client, EMBEDDING_MODEL

def generate_text_embedding(text: str, model: str = EMBEDDING_MODEL) -> list[float]:
    """
    Gera embedding vetorial usando o modelo text-embedding-004 do Vertex AI.
    Retorna uma lista de floats representando o vetor (dimensão 768).
    """
    client = get_genai_client()
    response = client.models.embed_content(
        model=model,
        contents=text,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT",
            output_dimensionality=768
        )
    )
    # response.embeddings é uma lista de ContentEmbedding
    return response.embeddings[0].values

def generate_query_embedding(query: str, model: str = EMBEDDING_MODEL) -> list[float]:
    """
    Gera embedding para a query de busca (otimizado para RETRIEVAL_QUERY).
    """
    client = get_genai_client()
    response = client.models.embed_content(
        model=model,
        contents=query,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=768
        )
    )
    return response.embeddings[0].values

if __name__ == "__main__":
    test_text = "Reunião de operações da fábrica de refrigerantes Whirlpool em Rio Claro."
    print("Testando geração de embedding com:", EMBEDDING_MODEL)
    emb = generate_text_embedding(test_text)
    print(f"[OK] Embedding gerado com sucesso! Dimensões: {len(emb)}")
    print(f"Primeiros 5 valores: {emb[:5]}")
