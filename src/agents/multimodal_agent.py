import os
import json
from typing import Dict, Any, List
from google.genai import types
from src.utils.gcp_client import get_genai_client, GEMINI_MODEL

class MultimodalMeetingAgent:
    """
    Agente Multimodal responsável pela ingestão e estruturação de reuniões.
    Suporta arquivos de áudio/vídeo (MP3, WAV, MP4) ou transcrições brutas.
    Utiliza o Gemini 2.5 Flash no Vertex AI para extrair participantes,
    tópicos operacionais, decisões e planos de ação.
    """

    def __init__(self):
        self.client = get_genai_client()
        self.model = GEMINI_MODEL

    def process_transcript_text(self, meeting_id: str, title: str, raw_text: str, department: str, date: str) -> Dict[str, Any]:
        """
        Segmenta e estrutura o texto da reunião em chunks semânticos para indexação vetorial.
        """
        prompt = f"""
Você é um especialista em análise de operações industriais e corporativas da Whirlpool.
Analise a transcrição abaixo da reunião '{title}' do departamento '{department}' datada de '{date}'.

Transcreva e estruture o conteúdo em formato JSON estrito contendo:
1. "summary": Resumo executivo da reunião (2-3 frases).
2. "participants": Lista de nomes e cargos identificados.
3. "key_decisions": Lista das principais decisões tomadas.
4. "action_items": Lista de ações definidas, cada uma contendo "action", "owner" e "deadline" (se mencionado).
5. "chunks": Lista de blocos semânticos do diálogo para busca vetorial. Cada chunk deve conter:
   - "chunk_id": ID único no formato "{meeting_id}-CHK-01", etc.
   - "speaker": Nome do participante que falou.
   - "topic": Tópico específico do trecho.
   - "content": O texto exato da fala/discussão.
   - "action_items": Lista de ações associadas a esse trecho específico.

Transcrição:
\"\"\"{raw_text}\"\"\"

Retorne EXCLUSIVAMENTE o JSON válido, sem tags de código adicionais como ```json.
"""
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )

        try:
            structured_data = json.loads(response.text.strip())
        except Exception:
            # Fallback para parsing simples se houver formatação
            clean_text = response.text.replace("```json", "").replace("```", "").strip()
            structured_data = json.loads(clean_text)

        structured_data["meeting_id"] = meeting_id
        structured_data["meeting_title"] = title
        structured_data["department"] = department
        structured_data["meeting_date"] = date

        return structured_data

    def process_audio_file(self, audio_path: str, meeting_id: str, department: str = "Operações") -> Dict[str, Any]:
        """
        Processa arquivo de áudio diretamente usando a capacidade nativa multimodal do Gemini.
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {audio_path}")

        print(f"[INFO] Lendo arquivo de áudio: {audio_path}")
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()

        # Determina o MIME type
        ext = os.path.splitext(audio_path)[1].lower()
        mime_map = {
            ".mp3": "audio/mp3",
            ".wav": "audio/wav",
            ".m4a": "audio/m4a",
            ".ogg": "audio/ogg"
        }
        mime_type = mime_map.get(ext, "audio/mp3")

        audio_part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)

        prompt = f"""
Você é o Agente de IA da Whirlpool.
Ouça o áudio da reunião corporativa anexado.
Transcreva todo o diálogo com precisão em português do Brasil e estruture a resposta no formato JSON com:
- "meeting_title": Título sugerido para a reunião.
- "raw_transcription": A transcrição completa com marcação de falantes.
- "summary": Resumo executivo.
- "participants": Lista de pessoas presentes.
- "key_decisions": Principais decisões.
- "action_items": Lista de tarefas.
- "chunks": Segmentos de diálogo para indexação vetorial no BigQuery.

Retorne EXCLUSIVAMENTE o JSON válido.
"""
        response = self.client.models.generate_content(
            model=self.model,
            contents=[audio_part, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )

        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_text)
        data["meeting_id"] = meeting_id
        data["department"] = department
        return data

if __name__ == "__main__":
    from data.sample_meetings import SAMPLE_MEETINGS
    print("Testando MultimodalMeetingAgent com transcrição...")
    agent = MultimodalMeetingAgent()
    sample = SAMPLE_MEETINGS[0]
    result = agent.process_transcript_text(
        meeting_id=sample["meeting_id"],
        title=sample["meeting_title"],
        raw_text=sample["raw_text"],
        department=sample["department"],
        date=sample["meeting_date"]
    )
    print(f"[OK] Reunião estruturada com sucesso!")
    print(f"Resumo: {result.get('summary')}")
    print(f"Chunks gerados: {len(result.get('chunks', []))}")
