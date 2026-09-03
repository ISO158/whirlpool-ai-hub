from typing import Dict, Any, List
from src.utils.gcp_client import get_genai_client, GEMINI_MODEL
from src.pipeline.embeddings import generate_query_embedding
from src.pipeline.bigquery_loader import search_similar_chunks

class RagConsultantAgent:
    """
    Agente Consultivo de RAG (Retrieval-Augmented Generation) integrado ao BigQuery Vector Search.
    Permite que gestores e analistas consultem histórico de decisões operacionais,
    fornecedores, problemas de qualidade e finanças em linguagem natural.
    """

    def __init__(self):
        self.client = get_genai_client()
        self.model = GEMINI_MODEL

    def answer_query(self, user_question: str, top_k: int = 3) -> Dict[str, Any]:
        """
        Executa o pipeline RAG completo:
        1. Geração de embedding da query (text-embedding-004).
        2. Busca vetorial por similaridade de cosseno no BigQuery (VECTOR_SEARCH).
        3. Síntese fundamentada no contexto com Gemini 2.5 Flash no Vertex AI.
        """
        print(f"\n[RAG] Processando pergunta: '{user_question}'")

        # 1. Gera embedding da pergunta
        query_emb = generate_query_embedding(user_question)

        # 2. Busca trechos mais similares no BigQuery
        relevant_chunks = search_similar_chunks(query_emb, top_k=top_k)

        if not relevant_chunks:
            return {
                "question": user_question,
                "answer": "Não foram encontrados registros relevantes na base corporativa de reuniões.",
                "sources": []
            }

        # 3. Monta o contexto para o LLM
        context_parts = []
        sources = []
        for i, chunk in enumerate(relevant_chunks, 1):
            context_parts.append(
                f"[Fonte {i}] Reunião: '{chunk['meeting_title']}' ({chunk['meeting_date']})\n"
                f"Departamento: {chunk['department']} | Participante/Falante: {chunk['speaker']}\n"
                f"Conteúdo: {chunk['content']}\n"
                f"Ações associadas: {', '.join(chunk['action_items']) if chunk['action_items'] else 'Nenhuma'}\n"
            )
            sources.append({
                "meeting_id": chunk["meeting_id"],
                "meeting_title": chunk["meeting_title"],
                "date": chunk["meeting_date"],
                "department": chunk["department"],
                "speaker": chunk["speaker"],
                "similarity_score": chunk["similarity_score"]
            })

        context_text = "\n---\n".join(context_parts)

        # 4. Prompt de Síntese RAG
        prompt = f"""
Você é o Assistente Executivo de Inteligência Operacional da Whirlpool.
Responda à pergunta do usuário utilizando EXCLUSIVAMENTE os trechos das atas de reuniões recuperadas do BigQuery listadas abaixo.

Diretrizes de resposta:
- Seja direto, claro e profissional.
- Cite explicitamente quem tomou a decisão ou forneceu a informação (ex: "Conforme Carlos Silva em 15/08/2026...").
- Mencione os valores aprovados, prazos e responsabilidades quando aplicável.
- Se a informação não constar no contexto, declare expressamente que o dado não foi discutido nas reuniões recuperadas.

Contexto Recuperado do BigQuery:
{context_text}

Pergunta do Usuário:
{user_question}

Resposta Executiva:
"""
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt
        )

        return {
            "question": user_question,
            "answer": response.text.strip(),
            "sources": sources
        }

if __name__ == "__main__":
    print("Testando RagConsultantAgent...")
    agent = RagConsultantAgent()
    res = agent.answer_query("O que foi decidido sobre os compressores de Rio Claro e quanto custará?")
    print("\n--- Resposta Gerada pelo RAG ---")
    print(res["answer"])
    print("\n--- Fontes do BigQuery Citadas ---")
    for s in res["sources"]:
        print(f"- {s['meeting_title']} | Falante: {s['speaker']} | Similaridade: {s['similarity_score']}")
