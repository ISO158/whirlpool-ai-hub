import os
import sys
from typing import Dict, Any

from src.agents.multimodal_agent import MultimodalMeetingAgent
from src.agents.governance_agent import GovernanceAgent
from src.agents.diagram_agent import ProcessDiagramAgent
from src.agents.rag_agent import RagConsultantAgent
from src.pipeline.embeddings import generate_text_embedding
from src.pipeline.bigquery_loader import insert_meeting_chunks
from src.utils.gcp_client import PROJECT_ID, DATASET_ID, TABLE_ID

def process_and_index_audio_meeting(audio_path: str, meeting_id: str = "WP-AUDIO-2026-09-03"):
    """
    Executa o pipeline multimodal completo a partir de um arquivo de Áudio real:
    1. Transcrição & compreensão de áudio nativa no Vertex AI (Gemini 2.5 Flash).
    2. Governança e auditoria de PII (PULSE / PIA).
    3. Geração de embeddings e persistência no BigQuery.
    4. Geração de diagramas operacionais em Mermaid.js e Matriz RACI.
    5. Teste de perguntas e respostas RAG.
    """
    print("\n" + "=" * 70)
    print("   PIPELINE DE ÁUDIO MULTIMODAL NO VERTEX AI (GEMINI 2.5 FLASH)   ")
    print("=" * 70)

    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Arquivo de áudio não encontrado em: {audio_path}")

    file_size_kb = os.path.getsize(audio_path) / 1024
    print(f"[+] Processando arquivo de áudio: {audio_path} ({file_size_kb:.1f} KB)")

    # 1. Ingestão Multimodal: Vertex AI Gemini ouve o áudio diretamente
    print("[+] Enviando áudio para o Vertex AI Gemini 2.5 Flash para transcrição e análise...")
    multi_agent = MultimodalMeetingAgent()
    audio_analysis = multi_agent.process_audio_file(
        audio_path=audio_path,
        meeting_id=meeting_id,
        department="Operações Industriais e Logística"
    )

    print("\n--- TRANSCRIÇÃO EXTRAÍDA DO ÁUDIO ---")
    raw_transcript = audio_analysis.get("raw_transcription") or audio_analysis.get("summary", "")
    print(raw_transcript)
    print(f"Resumo Executivo: {audio_analysis.get('summary')}")
    print(f"Participantes Identificados: {audio_analysis.get('participants')}")

    # 2. Governança de Dados (Compliance PULSE / PIA)
    print("\n[+] Aplicando Governança e Mascaramento de PII no texto transcrito...")
    gov_agent = GovernanceAgent()
    gov_result = gov_agent.sanitize_transcript(raw_transcript)
    sanitized_text = gov_result["sanitized_text"]
    print(f"    - Auditoria PULSE: {gov_result['metrics']}")
    print(f"    - Status: {gov_result['compliance_status']}")

    # 3. Geração de Embeddings e Ingestão no BigQuery
    chunks = audio_analysis.get("chunks", [])
    if not chunks:
        # Cria chunk único caso o modelo tenha retornado resumo direto
        chunks = [{
            "chunk_id": f"{meeting_id}-CHK-01",
            "speaker": "Marcos (Supervisor Joinville)",
            "topic": "Alinhamento Crítico de Compressores e Transporte",
            "content": sanitized_text,
            "action_items": audio_analysis.get("action_items", [])
        }]

    print(f"\n[+] Vetorizando {len(chunks)} trechos de áudio com text-embedding-004...")
    bq_rows = []
    for i, chk in enumerate(chunks, 1):
        if isinstance(chk, dict):
            content = chk.get("content") or chk.get("text") or sanitized_text
            speaker = chk.get("speaker", "Supervisor")
            topic = chk.get("topic", "Logística")
            raw_actions = chk.get("action_items") or audio_analysis.get("action_items", [])
            chunk_id = chk.get("chunk_id", f"{meeting_id}-CHK-{i:02d}")
        else:
            content = str(chk)
            speaker = "Marcos (Supervisor Joinville)"
            topic = "Logística e Manufatura"
            raw_actions = audio_analysis.get("action_items", [])
            chunk_id = f"{meeting_id}-CHK-{i:02d}"
        
        emb = generate_text_embedding(f"{speaker}: {content}")
        
        # Formata action_items como lista de strings
        clean_actions = []
        if isinstance(raw_actions, list):
            for a in raw_actions:
                if isinstance(a, dict):
                    clean_actions.append(f"{a.get('action', '')} (Resp: {a.get('owner', 'N/A')})")
                elif isinstance(a, str):
                    clean_actions.append(str(a))
        elif isinstance(raw_actions, str):
            clean_actions.append(raw_actions)

        bq_rows.append({
            "chunk_id": chunk_id,
            "meeting_id": meeting_id,
            "meeting_title": audio_analysis.get("meeting_title", "Alinhamento de Compressores Joinville-Rio Claro"),
            "meeting_date": "2026-09-03",
            "department": "Operações Industriais e Logística",
            "speaker": speaker,
            "content_sanitized": content,
            "action_items": clean_actions,
            "embedding": emb
        })

    print(f"[+] Inserindo novos dados de áudio na tabela {PROJECT_ID}.{DATASET_ID}.{TABLE_ID}...")
    insert_meeting_chunks(bq_rows)

    # 4. Geração de Diagrama Mermaid e Matriz RACI
    print("\n[+] Gerando Fluxograma de Decisões Operacionais (Mermaid) e Matriz RACI...")
    diagram_agent = ProcessDiagramAgent()
    mermaid_chart = diagram_agent.generate_operational_diagram(audio_analysis)
    raci_table = diagram_agent.generate_raci_matrix(audio_analysis)

    report_path = os.path.join("reports", "relatorio_audio_joinville_rioclaro.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# Relatório de Áudio Multimodal - Fábricas Joinville & Rio Claro\n\n")
        f.write(f"**Origem:** Arquivo de Áudio `{os.path.basename(audio_path)}`\n")
        f.write(f"**Título:** {audio_analysis.get('meeting_title')}\n\n")
        f.write(f"## Transcrição Sanitizada (PULSE/LGPD)\n{sanitized_text}\n\n")
        f.write(f"## Resumo Executivo\n{audio_analysis.get('summary')}\n\n")
        f.write(f"## Fluxograma de Contingência Operacional (Mermaid)\n{mermaid_chart}\n\n")
        f.write(f"## Matriz RACI de Tarefas\n{raci_table}\n")
    print(f"[OK] Relatório gerado com sucesso em: {report_path}")

    # 5. Consulta RAG validando o áudio indexado
    print("\n" + "=" * 70)
    print("CONSULTA RAG TESTANDO A RECUPERAÇÃO DO ÁUDIO NO BIGQUERY")
    print("=" * 70)
    rag = RagConsultantAgent()
    pergunta = "Quais defeitos foram encontrados nos compressores V-300 em Joinville e o que aconteceu na Serra Dona Francisca?"
    print(f"PERGUNTA: {pergunta}")
    resp = rag.answer_query(pergunta, top_k=2)
    print(f"\nRESPOSTA RAG:\n{resp['answer']}\n")
    print("FONTES CITADAS DO BIGQUERY:")
    for s in resp["sources"]:
        print(f"  • {s['meeting_title']} (Falante: {s['speaker']} | Score: {s['similarity_score']})")

if __name__ == "__main__":
    audio_file = "data/raw_audio/alinhamento_joinville_rioclaro.mp3"
    process_and_index_audio_meeting(audio_file)
