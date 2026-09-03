import os
import sys
from typing import List, Dict, Any

from data.sample_meetings import SAMPLE_MEETINGS
from src.pipeline.bigquery_loader import init_bigquery_schema, insert_meeting_chunks, get_bigquery_client
from src.pipeline.embeddings import generate_text_embedding
from src.agents.multimodal_agent import MultimodalMeetingAgent
from src.agents.governance_agent import GovernanceAgent
from src.agents.diagram_agent import ProcessDiagramAgent
from src.agents.rag_agent import RagConsultantAgent
from src.utils.gcp_client import PROJECT_ID, DATASET_ID, TABLE_ID

def run_ingestion_pipeline() -> List[Dict[str, Any]]:
    """
    Executa o pipeline completo de ingestão, sanitização e indexação vetorial no BigQuery.
    """
    print("\n" + "=" * 70)
    print("ETAPA 1: INGESTÃO, GOVERNANÇA (PULSE/PIA) E INDEXAÇÃO NO BIGQUERY")
    print("=" * 70)

    # 1. Garante dataset e tabela no BigQuery
    init_bigquery_schema()

    multi_agent = MultimodalMeetingAgent()
    gov_agent = GovernanceAgent()

    all_bq_rows = []
    processed_meetings = []

    for item in SAMPLE_MEETINGS:
        print(f"\n[+] Processando Reunião: '{item['meeting_title']}'")
        
        # Governança: Sanitiza PII antes de qualquer processamento estruturado
        gov_result = gov_agent.sanitize_transcript(item["raw_text"])
        sanitized_text = gov_result["sanitized_text"]
        print(f"    - Governança PULSE aplicada: {gov_result['metrics']}")

        # Agente Multimodal: Estruturação dos diálogos
        structured = multi_agent.process_transcript_text(
            meeting_id=item["meeting_id"],
            title=item["meeting_title"],
            raw_text=sanitized_text,
            department=item["department"],
            date=item["meeting_date"]
        )
        processed_meetings.append(structured)

        # Geração de Embeddings para cada chunk
        print(f"    - Gerando embeddings vetoriais (text-embedding-004) para {len(structured.get('chunks', []))} trechos...")
        for chk in structured.get("chunks", []):
            content_to_embed = f"{chk.get('speaker', '')}: {chk.get('content', '')}"
            emb_vector = generate_text_embedding(content_to_embed)

            # Garante que action_items seja estritamente uma lista de strings (ARRAY<STRING>)
            raw_actions = chk.get("action_items", [])
            clean_actions = []
            if isinstance(raw_actions, list):
                for act in raw_actions:
                    if isinstance(act, dict):
                        owner = act.get("owner", "N/A")
                        desc = act.get("action") or act.get("description") or str(act)
                        clean_actions.append(f"{desc} [Resp: {owner}]")
                    elif isinstance(act, str):
                        clean_actions.append(act)
            elif isinstance(raw_actions, str):
                clean_actions.append(raw_actions)

            all_bq_rows.append({
                "chunk_id": chk.get("chunk_id", f"{item['meeting_id']}-CHK"),
                "meeting_id": item["meeting_id"],
                "meeting_title": item["meeting_title"],
                "meeting_date": item["meeting_date"],
                "department": item["department"],
                "speaker": chk.get("speaker", "N/A"),
                "content_sanitized": chk.get("content", ""),
                "action_items": clean_actions,
                "embedding": emb_vector
            })

    # Inserção em batch no BigQuery
    print(f"\n[+] Inserindo {len(all_bq_rows)} chunks com vetores na tabela {PROJECT_ID}.{DATASET_ID}.{TABLE_ID}...")
    insert_meeting_chunks(all_bq_rows)

    # Criação do VECTOR INDEX após os dados estarem populados
    print("[+] Criando / Atualizando o VECTOR INDEX nativo no BigQuery...")
    bq = get_bigquery_client()
    index_sql = f"""
    CREATE VECTOR INDEX IF NOT EXISTS meeting_vector_idx
    ON `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`(embedding)
    OPTIONS(distance_type='COSINE', index_type='IVF');
    """
    try:
        job = bq.query(index_sql)
        job.result()
        print("[OK] VECTOR INDEX operacional no BigQuery!")
    except Exception as e:
        print(f"[INFO] Status do índice vetorial: {e}")

    return processed_meetings

def generate_business_deliverables(meetings: List[Dict[str, Any]]):
    """
    Executa o Agente de Diagramas e Matriz RACI para o caso de estudo de Supply Chain.
    """
    print("\n" + "=" * 70)
    print("ETAPA 2: GERAÇÃO DE ENTREGÁVEIS DE PROCESSO (MERMAID & MATRIZ RACI)")
    print("=" * 70)

    diagram_agent = ProcessDiagramAgent()
    target_meeting = meetings[0] # Reunião de compressores da Brastemp

    print(f"Gerando artefatos operacionais para: '{target_meeting['meeting_title']}'...")
    diagram = diagram_agent.generate_operational_diagram(target_meeting)
    raci = diagram_agent.generate_raci_matrix(target_meeting)

    os.makedirs("reports", exist_ok=True)
    report_path = os.path.join("reports", "relatorio_operacional_compressores.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# Relatório de Inteligência Operacional - Whirlpool\n\n")
        f.write(f"**Reunião:** {target_meeting['meeting_title']}\n")
        f.write(f"**Departamento:** {target_meeting['department']} | **Data:** {target_meeting['meeting_date']}\n\n")
        f.write(f"## Resumo Executivo\n{target_meeting.get('summary')}\n\n")
        f.write(f"## Fluxograma Operacional do Processo (Mermaid)\n{diagram}\n\n")
        f.write(f"## Matriz de Governança de Tarefas (RACI)\n{raci}\n")

    print(f"[OK] Relatório executivo com fluxograma Mermaid e Matriz RACI salvo em: {report_path}")

def run_rag_demonstration():
    """
    Executa consultas analíticas demonstrando o poder do BigQuery Vector Search.
    """
    print("\n" + "=" * 70)
    print("ETAPA 3: CONSULTAS DE ALTO VALOR COM BIGQUERY VECTOR SEARCH (RAG)")
    print("=" * 70)

    rag = RagConsultantAgent()
    demo_questions = [
        "O que a equipe de logística decidiu sobre os atrasos de compressores na fábrica de Rio Claro e qual o valor economizado?",
        "Qual problema de qualidade foi identificado na linha de Lava e Seca e qual a ação corretiva com o lote de amortecedores?",
        "Qual o orçamento de Capex e ROI aprovados pela diretoria financeira para os projetos de IA no Google Cloud?"
    ]

    for q in demo_questions:
        print("\n" + "-" * 60)
        print(f"PERGUNTA: {q}")
        print("-" * 60)
        result = rag.answer_query(q, top_k=2)
        print(f"\nRESPOSTA RAG:\n{result['answer']}\n")
        print("FONTES RECUPERADAS DO BIGQUERY:")
        for s in result["sources"]:
            print(f"  • [{s['department']}] {s['meeting_title']} (Falante: {s['speaker']} | Score Cosine: {s['similarity_score']})")

def main():
    print("=" * 70)
    print("   WHIRLPOOL AI OPERATIONS HUB: MULTI-AGENT & BIGQUERY VECTOR SEARCH   ")
    print("=" * 70)
    
    # 1. Pipeline de Dados & Governança
    meetings = run_ingestion_pipeline()

    # 2. Geração de Diagramas e RACI
    generate_business_deliverables(meetings)

    # 3. Demonstração do RAG com BigQuery Vector Search
    run_rag_demonstration()

    print("\n" + "=" * 70)
    print("PROCESSO COMPLETO FINALIZADO COM SUCESSO!")
    print("Todos os dados estão indexados e operacionais no BigQuery e Vertex AI.")
    print("=" * 70)

if __name__ == "__main__":
    main()
