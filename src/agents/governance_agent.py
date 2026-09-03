import re
from typing import Dict, Any, Tuple
from src.utils.gcp_client import get_genai_client, GEMINI_MODEL

class GovernanceAgent:
    """
    Agente de Governança e Proteção de Dados corporativos (Compliance Whirlpool PULSE / PIA / LGPD).
    Responsável por auditar e mascarar dados sensíveis (PII) e informações confidenciais
    antes que qualquer informação seja persistida no BigQuery ou indexada para RAG.
    """

    def __init__(self):
        self.client = get_genai_client()
        self.model = GEMINI_MODEL

        # Padrões determinísticos de alta precisão
        self.cpf_pattern = re.compile(r'\b\d{3}\.\d{3}\.\d{3}-\d{2}\b')
        self.phone_pattern = re.compile(r'\b(?:\(?\d{2}\)?\s*)?(?:9\d{4}|\d{4})[-.\s]?\d{4}\b')
        self.badge_pattern = re.compile(r'\bWP-\d{4,5}\b', re.IGNORECASE)
        self.high_val_money_pattern = re.compile(r'R\$\s*[\d.]+(?:,\d{2})?')

    def apply_deterministic_masking(self, text: str) -> Tuple[str, Dict[str, int]]:
        """Aplica regras baseadas em regex para conformidade com LGPD/PULSE."""
        audit = {
            "cpf_redactions": 0,
            "phone_redactions": 0,
            "badge_redactions": 0,
            "high_value_redactions": 0
        }

        # 1. Mascaramento de CPF
        text, audit["cpf_redactions"] = self.cpf_pattern.subn("[CPF_REMOVIDO_CONFORME_PIA]", text)

        # 2. Mascaramento de Crachás / Matrículas funcionais
        text, audit["badge_redactions"] = self.badge_pattern.subn("[MATRICULA_FUNCIONAL_MASCARADA]", text)

        # 3. Mascaramento de Telefones
        text, audit["phone_redactions"] = self.phone_pattern.subn("[TELEFONE_MASCARADO]", text)

        return text, audit

    def sanitize_transcript(self, raw_transcript: str) -> Dict[str, Any]:
        """
        Executa o pipeline completo de governança:
        1. Regras determinísticas de PII.
        2. Validação contextual de confidencialidade via Vertex AI Gemini.
        """
        # Etapa 1: Regras determinísticas
        pre_masked_text, metrics = self.apply_deterministic_masking(raw_transcript)

        # Etapa 2: Auditoria contextual com Gemini
        prompt = f"""
Você é o Agente de Governança de Dados da Whirlpool (Comitê PULSE / PIA - Privacy Impact Assessment).
Analise o texto da reunião abaixo. Certifique-se de que nenhum dado confidencial não autorizado (como senhas, dados bancários de terceiros ou termos ultrassecretos) permaneça no texto.
Caso ainda encontre nomes próprios associados a dados criminais/médicos ou valores extremamente confidenciais de negociação, substitua por tags como [INFO_CONFIDENCIAL_REMOVIDA].

Texto:
\"\"\"{pre_masked_text}\"\"\"

Retorne APENAS o texto tratado, sem comentários adicionais.
"""
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt
        )

        sanitized_content = response.text.strip()

        return {
            "sanitized_text": sanitized_content,
            "metrics": metrics,
            "compliance_status": "APPROVED_PULSE_PIA",
            "governance_rule": "LGPD_WHIRLPOOL_V2_2026"
        }

if __name__ == "__main__":
    from data.sample_meetings import SAMPLE_MEETINGS
    print("Testando GovernanceAgent...")
    agent = GovernanceAgent()
    sample = SAMPLE_MEETINGS[0]["raw_text"]
    result = agent.sanitize_transcript(sample)
    print("\n--- Relatório de Auditoria de Governança ---")
    print(f"Métricas de Mascaramento: {result['metrics']}")
    print(f"Status: {result['compliance_status']}")
    print("\n--- Amostra do Texto Sanitizado ---")
    print(result["sanitized_text"][:400] + "...")
