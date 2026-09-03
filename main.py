import os
import glob
from typing import List, Dict, Any

from data.sample_meetings import SAMPLE_MEETINGS
from src.pipeline.bigquery_loader import init_bigquery_schema, insert_meeting_chunks, get_bigquery_client
from src.pipeline.embeddings import generate_text_embedding
from src.agents.multimodal_agent import MultimodalMeetingAgent
from src.agents.governance_agent import GovernanceAgent
from src.agents.diagram_agent import ProcessDiagramAgent
from src.agents.rag_agent import RagConsultantAgent
from src.utils.gcp_client import PROJECT_ID, DATASET_ID, TABLE_ID

def process_audio_directory(audio_dir: str = "data/raw_audio") -> List[Dict[str, Any]]:
    """
    Escaneia a pasta data/raw_audio e processa automaticamente qualquer
    arquivo de áudio (.m4a, .mp3, .wav, .aac, .mp4) com o Gemini Multimodal.
    """
    supported_extensions = ("*.m4a", "*.mp3", "*.wav", "*.aac", "*.ogg", "*.mp4")
    audio_files = []
    for ext in supported_extensions:
        audio_files.extend(glob.glob(os.path.join(audio_dir, ext)))

    if not audio_files:
        print(f"[INFO] Nenhum arquivo de áudio encontrado em {audio_dir}.")
        return []

    print(f"\n[+] Encontrados {len(audio_files)} arquivo(s) de áudio em {audio_dir} para processamento multimodal:")
    for f in audio_files:
        print(f"    • {os.path.basename(f)} ({os.path.getsize(f) / 1024:.1f} KB)")

    multi_agent = MultimodalMeetingAgent()
    gov_agent = GovernanceAgent()
    diagram_agent = ProcessDiagramAgent()

    processed_audios = []
    all_audio_rows = []

    for idx, audio_path in enumerate(audio_files, 1):
        filename = os.path.basename(audio_path)
        meeting_id = f"WP-AUDIO-{idx:03d}"
        print(f"\n" + "-" * 60)
        print(f"[ÁUDIO MULTIMODAL {idx}/{len(audio_files)}] Processando: {filename}")
        print("-" * 60)

        # 1. Envio para o Vertex AI Gemini 2.5 Flash
        audio_analysis = multi_agent.process_audio_file(
            audio_path=audio_path,
            meeting_id=meeting_id,
            department="Inovação e Automação de Processos"
        )

        title = audio_analysis.get("meeting_title", f"Reunião de Áudio: {filename}")
        raw_transcript = audio_analysis.get("raw_transcription") or audio_analysis.get("summary", "")
        print(f"Título Identificado: {title}")
        print(f"Participantes: {audio_analysis.get('participants')}")
        print(f"\nTranscrição:\n{raw_transcript}\n")

        # 2. Governança PULSE/PIA
        gov_result = gov_agent.sanitize_transcript(raw_transcript)
        sanitized_text = gov_result["sanitized_text"]
        print(f"Auditoria PULSE/PIA aplicada: {gov_result['metrics']}")

        # 3. Chunks e Embeddings
        chunks = audio_analysis.get("chunks", [])
        if not chunks:
            chunks = [{
                "chunk_id": f"{meeting_id}-CHK-01",
                "speaker": audio_analysis.get("participants", ["Interlocutor"])[0] if audio_analysis.get("participants") else "Interlocutor",
                "topic": "Demanda de Automação de Tarefas",
                "content": sanitized_text,
                "action_items": audio_analysis.get("action_items", [])
            }]

        for i, chk in enumerate(chunks, 1):
            if isinstance(chk, dict):
                content = chk.get("content") or chk.get("text") or sanitized_text
                speaker = chk.get("speaker", "Interlocutor")
                topic = chk.get("topic", "Automação e Processos")
                raw_actions = chk.get("action_items") or audio_analysis.get("action_items", [])
                chunk_id = chk.get("chunk_id", f"{meeting_id}-CHK-{i:02d}")
            else:
                content = str(chk)
                speaker = "Interlocutor"
                topic = "Automação e Processos"
                raw_actions = audio_analysis.get("action_items", [])
                chunk_id = f"{meeting_id}-CHK-{i:02d}"

            emb = generate_text_embedding(f"{speaker}: {content}")

            clean_actions = []
            if isinstance(raw_actions, list):
                for a in raw_actions:
                    if isinstance(a, dict):
                        clean_actions.append(f"{a.get('action', '')} (Resp: {a.get('owner', 'N/A')})")
                    elif isinstance(a, str):
                        clean_actions.append(str(a))

            all_audio_rows.append({
                "chunk_id": chunk_id,
                "meeting_id": meeting_id,
                "meeting_title": title,
                "meeting_date": "2026-09-03",
                "department": "Inovação e Automação de Processos",
                "speaker": speaker,
                "content_sanitized": content,
                "action_items": clean_actions,
                "embedding": emb
            })

        # 4. Geração de Diagrama Mermaid e Matriz RACI para o áudio
        print(f"[+] Gerando fluxograma de decisão Mermaid e Matriz RACI para {filename}...")
        mermaid_chart = diagram_agent.generate_operational_diagram(audio_analysis)
        raci_table = diagram_agent.generate_raci_matrix(audio_analysis)

        os.makedirs("reports", exist_ok=True)
        base_name = os.path.splitext(filename)[0]
        report_path = os.path.join("reports", f"relatorio_{base_name}.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"# Relatório Operacional - Áudio: {filename}\n\n")
            f.write(f"**Título:** {title}\n")
            f.write(f"**Departamento:** Inovação e Automação de Processos | **Data:** 2026-09-03\n\n")
            f.write(f"## Transcrição Sanitizada (PULSE/LGPD)\n{sanitized_text}\n\n")
            f.write(f"## Resumo Executivo\n{audio_analysis.get('summary')}\n\n")
            f.write(f"## Fluxograma de Processo (Mermaid)\n{mermaid_chart}\n\n")
            f.write(f"## Matriz RACI de Responsabilidades\n{raci_table}\n")

        print(f"[OK] Relatório gerado em: {report_path}")
        processed_audios.append(audio_analysis)

    # Inserção em batch no BigQuery
    if all_audio_rows:
        print(f"\n[+] Inserindo {len(all_audio_rows)} trechos de áudio no BigQuery...")
        insert_meeting_chunks(all_audio_rows)

    return processed_audios

def run_ingestion_pipeline() -> List[Dict[str, Any]]:
    """
    Executa o pipeline completo:
    1. Ingestão de áudios reais da pasta data/raw_audio/
    2. Ingestão das reuniões simuladas corporativas
    """
    print("\n" + "=" * 70)
    print("ETAPA 1: INGESTÃO MULTIMODAL, GOVERNANÇA (PULSE) E BIGQUERY VECTOR SEARCH")
    print("=" * 70)

    # Garante dataset e tabela no BigQuery
    init_bigquery_schema()

    # 1. Processa todos os áudios reais presentes em data/raw_audio
    audios = process_audio_directory("data/raw_audio")

    # 2. Processa as atas textuais
    multi_agent = MultimodalMeetingAgent()
    gov_agent = GovernanceAgent()

    all_bq_rows = []
    processed_meetings = []

    for item in SAMPLE_MEETINGS:
        print(f"\n[+] Processando Reunião: '{item['meeting_title']}'")
        
        gov_result = gov_agent.sanitize_transcript(item["raw_text"])
        sanitized_text = gov_result["sanitized_text"]

        structured = multi_agent.process_transcript_text(
            meeting_id=item["meeting_id"],
            title=item["meeting_title"],
            raw_text=sanitized_text,
            department=item["department"],
            date=item["meeting_date"]
        )
        processed_meetings.append(structured)

        for chk in structured.get("chunks", []):
            content_to_embed = f"{chk.get('speaker', '')}: {chk.get('content', '')}"
            emb_vector = generate_text_embedding(content_to_embed)

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

    print(f"\n[+] Inserindo {len(all_bq_rows)} chunks no BigQuery...")
    insert_meeting_chunks(all_bq_rows)

    return processed_meetings + audios

def run_rag_demonstration():
    """
    Executa consultas analíticas demonstrando o poder do BigQuery Vector Search,
    incluindo perguntas sobre os áudios gravados e reuniões corporativas.
    """
    print("\n" + "=" * 70)
    print("ETAPA 2: CONSULTAS ANALÍTICAS COM BIGQUERY VECTOR SEARCH (RAG)")
    print("=" * 70)

    rag = RagConsultantAgent()
    demo_questions = [
        "Quais setores da empresa foram contatados sobre demandas de automação de tarefas e quais necessidades foram mapeadas?",
        "O que a equipe de logística decidiu sobre os atrasos de compressores na fábrica de Rio Claro e qual o frete aprovado?",
        "Qual o orçamento anual de computação em nuvem e ROI projetado para os projetos de IA no Google Cloud?"
    ]

    for q in demo_questions:
        print("\n" + "-" * 60)
        print(f"PERGUNTA: {q}")
        print("-" * 60)
        result = rag.answer_query(q, top_k=3)
        print(f"\nRESPOSTA RAG:\n{result['answer']}\n")
        print("FONTES RECUPERADAS DO BIGQUERY:")
        for s in result["sources"]:
            print(f"  • [{s['department']}] {s['meeting_title']} (Falante: {s['speaker']} | Score Cosine: {s['similarity_score']})")

def main():
    print("=" * 70)
    print("   WHIRLPOOL AI OPERATIONS HUB: MULTI-AGENT & BIGQUERY VECTOR SEARCH   ")
    print("=" * 70)
    
    # 1. Executa Ingestão (Áudios em data/raw_audio + Atas)
    run_ingestion_pipeline()

    # 2. Executa Demonstração RAG
    run_rag_demonstration()

    print("\n" + "=" * 70)
    print("PROCESSO COMPLETO FINALIZADO COM SUCESSO!")
    print("Todos os áudios e reuniões estão indexados e operacionais no BigQuery.")
    print("=" * 70)

if __name__ == "__main__":
    main()
