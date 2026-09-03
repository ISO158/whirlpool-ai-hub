import os
import shutil
import time
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from src.agents.multimodal_agent import MultimodalMeetingAgent
from src.agents.governance_agent import GovernanceAgent
from src.agents.diagram_agent import ProcessDiagramAgent
from src.agents.rag_agent import RagConsultantAgent
from src.pipeline.embeddings import generate_text_embedding
from src.pipeline.bigquery_loader import insert_meeting_chunks, get_bigquery_client
from src.utils.gcp_client import PROJECT_ID, DATASET_ID, TABLE_ID

app = FastAPI(
    title="Whirlpool AI Operations Hub API",
    description="API para ingestão multimodal de reuniões, governança de dados (PULSE/PIA) e BigQuery Vector Search.",
    version="1.0.0"
)

# Habilita CORS para permitir chamadas do GitHub Pages ou outros clientes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos Pydantic
class RagRequest(BaseModel):
    question: str
    top_k: Optional[int] = 3

@app.post("/api/process-audio")
async def process_audio(
    file: UploadFile = File(...),
    department: str = Form("Operações e Manufatura")
):
    """
    Endpoint que recebe um arquivo de áudio/vídeo, executa o pipeline multimodal,
    sanitização de governança (PULSE), indexação no BigQuery e gera os diagramas em Mermaid.
    """
    os.makedirs("data/raw_audio", exist_ok=True)
    os.makedirs("reports", exist_ok=True)

    timestamp = int(time.time())
    ext = os.path.splitext(file.filename)[1]
    if not ext:
        ext = ".m4a"
    
    saved_filename = f"upload_{timestamp}_{file.filename}"
    saved_path = os.path.join("data", "raw_audio", saved_filename)

    try:
        # 1. Salva o arquivo de áudio
        with open(saved_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        meeting_id = f"WP-PORTAL-{timestamp}"
        
        # 2. Agente Multimodal (Gemini 2.5 Flash)
        multi_agent = MultimodalMeetingAgent()
        audio_analysis = multi_agent.process_audio_file(
            audio_path=saved_path,
            meeting_id=meeting_id,
            department=department
        )

        title = audio_analysis.get("meeting_title", "Alinhamento Operacional Whirlpool")
        raw_transcript = audio_analysis.get("raw_transcription") or audio_analysis.get("summary", "")

        # 3. Agente de Governança (Compliance PULSE/PIA)
        gov_agent = GovernanceAgent()
        gov_result = gov_agent.sanitize_transcript(raw_transcript)
        sanitized_text = gov_result["sanitized_text"]

        # 4. Ingestão e Vetorização no BigQuery
        chunks = audio_analysis.get("chunks", [])
        if not chunks:
            chunks = [{
                "chunk_id": f"{meeting_id}-CHK-01",
                "speaker": audio_analysis.get("participants", ["Colaborador"])[0] if audio_analysis.get("participants") else "Colaborador",
                "topic": "Demanda Operacional",
                "content": sanitized_text,
                "action_items": audio_analysis.get("action_items", [])
            }]

        bq_rows = []
        for i, chk in enumerate(chunks, 1):
            if isinstance(chk, dict):
                content = chk.get("content") or chk.get("text") or sanitized_text
                speaker = chk.get("speaker", "Colaborador")
                topic = chk.get("topic", department)
                raw_actions = chk.get("action_items") or audio_analysis.get("action_items", [])
                chunk_id = chk.get("chunk_id", f"{meeting_id}-CHK-{i:02d}")
            else:
                content = str(chk)
                speaker = "Colaborador"
                topic = department
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

            bq_rows.append({
                "chunk_id": chunk_id,
                "meeting_id": meeting_id,
                "meeting_title": title,
                "meeting_date": time.strftime("%Y-%m-%d"),
                "department": department,
                "speaker": speaker,
                "content_sanitized": content,
                "action_items": clean_actions,
                "embedding": emb
            })

        # Insere no BigQuery
        insert_meeting_chunks(bq_rows)

        # 5. Agente de Diagramas & RACI
        diagram_agent = ProcessDiagramAgent()
        mermaid_code = diagram_agent.generate_operational_diagram(audio_analysis)
        raci_markdown = diagram_agent.generate_raci_matrix(audio_analysis)

        # Limpa blocos de código markdown do mermaid se vierem com ```mermaid
        clean_mermaid = mermaid_code.replace("```mermaid", "").replace("```", "").strip()

        # Salva o relatório no disco
        report_filename = f"relatorio_{meeting_id}.md"
        report_path = os.path.join("reports", report_filename)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"# Relatório Operacional Whirlpool - {title}\n\n")
            f.write(f"**Departamento:** {department} | **ID:** {meeting_id}\n\n")
            f.write(f"## Resumo Executivo\n{audio_analysis.get('summary')}\n\n")
            f.write(f"## Transcrição Sanitizada (PULSE/LGPD)\n{sanitized_text}\n\n")
            f.write(f"## Fluxograma Operacional (Mermaid)\n```mermaid\n{clean_mermaid}\n```\n\n")
            f.write(f"## Matriz RACI\n{raci_markdown}\n")

        # Texto para WhatsApp
        summary_short = audio_analysis.get('summary', 'Resumo indisponível.')
        wa_text = (
            f"🚨 *WHIRLPOOL - ALINHAMENTO OPERACIONAL*\n\n"
            f"📌 *{title}*\n"
            f"🏭 *Departamento:* {department}\n\n"
            f"📝 *Resumo Executivo:*\n{summary_short}\n\n"
            f"📊 *Relatório e Matriz RACI gerados pelo Whirlpool AI Operations Hub.*\n"
            f"ID da Reunião: {meeting_id}"
        )

        return {
            "success": True,
            "meeting_id": meeting_id,
            "title": title,
            "department": department,
            "participants": audio_analysis.get("participants", []),
            "summary": summary_short,
            "key_decisions": audio_analysis.get("key_decisions", []),
            "sanitized_transcription": sanitized_text,
            "governance_metrics": gov_result["metrics"],
            "mermaid_code": clean_mermaid,
            "raci_markdown": raci_markdown,
            "report_file": report_filename,
            "whatsapp_text": wa_text,
            "email_subject": f"[Whirlpool AI Hub] Relatório Operacional: {title}",
            "email_body": f"Prezados,\n\nSegue o resumo da reunião '{title}' ({department}):\n\n{summary_short}\n\nO plano de ação e matriz RACI foram registrados na base corporativa.\n\nAtenciosamente,\nWhirlpool AI Operations Hub"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar áudio: {str(e)}")

@app.post("/api/rag-query")
async def rag_query(payload: RagRequest):
    """
    Endpoint para perguntas e respostas RAG baseadas nas reuniões e áudios salvos no BigQuery.
    """
    try:
        rag = RagConsultantAgent()
        result = rag.answer_query(payload.question, top_k=payload.top_k)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na consulta RAG: {str(e)}")

@app.get("/api/history")
async def get_history():
    """
    Retorna a lista dos registros mais recentes armazenados na base do BigQuery.
    """
    try:
        bq = get_bigquery_client()
        query = f"""
        SELECT DISTINCT
            meeting_id,
            meeting_title,
            meeting_date,
            department
        FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
        ORDER BY meeting_date DESC
        LIMIT 10
        """
        rows = bq.query(query).result()
        history = [
            {
                "meeting_id": r.meeting_id,
                "title": r.meeting_title,
                "date": r.meeting_date,
                "department": r.department
            }
            for r in rows
        ]
        return {"history": history}
    except Exception as e:
        return {"history": [], "error": str(e)}

# Serve arquivos estáticos do frontend
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    print("[+] Inicializando Whirlpool AI Operations Hub Web Server...")
    uvicorn.run(app, host="127.0.0.1", port=8000)
