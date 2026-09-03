from typing import Dict, Any
from src.utils.gcp_client import get_genai_client, GEMINI_MODEL

class ProcessDiagramAgent:
    """
    Agente especialista em Modelagem e Otimização de Processos Operacionais da Whirlpool.
    Analisa as discussões e decisões de uma reunião e gera:
    1. Fluxogramas operacionais em sintaxe Mermaid.js (visualizáveis no GitHub, Notion e Markdown).
    2. Matriz RACI (Responsável, Aprovador, Consultado, Informado) para os planos de ação.
    """

    def __init__(self):
        self.client = get_genai_client()
        self.model = GEMINI_MODEL

    def generate_operational_diagram(self, meeting_data: Dict[str, Any]) -> str:
        """
        Gera o código Mermaid.js representando o fluxo operacional de decisões.
        """
        prompt = f"""
Você é um Engenheiro de Processos e Arquiteto de Soluções da Whirlpool.
Com base nas informações da reunião abaixo:
- Título: {meeting_data.get('meeting_title')}
- Departamento: {meeting_data.get('department')}
- Decisões: {meeting_data.get('key_decisions')}
- Ações: {meeting_data.get('action_items')}
- Resumo: {meeting_data.get('summary')}

Gere um fluxograma de processos elegante e claro em sintaxe Mermaid (flowchart TD ou flowchart LR).
O diagrama deve demonstrar a cadeia de eventos: o problema/gatilho inicial, as opções avaliadas, a decisão tomada e as etapas de execução com os responsáveis.

Regras importantes:
- Inicie com ```mermaid e termine com ```.
- Use nomes de nós claros (ex: A[Atraso no Fornecimento] --> B[Decisão de Contingência]).
- Destaque nós de decisão com losangos {{"Decisão"}}.
- Inclua apenas o bloco mermaid válido.
"""
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt
        )
        return response.text.strip()

    def generate_raci_matrix(self, meeting_data: Dict[str, Any]) -> str:
        """
        Gera uma Matriz RACI formatada em Markdown com as ações acordadas.
        """
        prompt = f"""
Você é um Gerente de Projetos Sênior da Whirlpool.
Para as tarefas e ações listadas na reunião '{meeting_data.get('meeting_title')}':
Ações: {meeting_data.get('action_items')}
Participantes: {meeting_data.get('participants')}

Gere uma tabela Markdown com a Matriz RACI:
Colunas: | Ação / Entregável | Responsável (R) | Aprovador (A) | Consultado (C) | Informado (I) | Prazo |

Certifique-se de ser realista conforme as funções corporativas tradicionais da Whirlpool (Logística, Engenharia, Manufatura, Finanças, Qualidade).
"""
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt
        )
        return response.text.strip()

if __name__ == "__main__":
    from data.sample_meetings import SAMPLE_MEETINGS
    from src.agents.multimodal_agent import MultimodalMeetingAgent

    print("Testando ProcessDiagramAgent...")
    multi_agent = MultimodalMeetingAgent()
    sample = SAMPLE_MEETINGS[0]
    structured = multi_agent.process_transcript_text(
        meeting_id=sample["meeting_id"],
        title=sample["meeting_title"],
        raw_text=sample["raw_text"],
        department=sample["department"],
        date=sample["meeting_date"]
    )

    diagram_agent = ProcessDiagramAgent()
    mermaid_chart = diagram_agent.generate_operational_diagram(structured)
    raci = diagram_agent.generate_raci_matrix(structured)

    print("\n--- Diagrama Mermaid Gerado ---")
    print(mermaid_chart)
    print("\n--- Matriz RACI ---")
    print(raci)
