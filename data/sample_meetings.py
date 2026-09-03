"""
Dados sintéticos de reuniões operacionais e estratégicas da Whirlpool.
Cenários reais mapeando os departamentos mencionados na vaga:
Logística, Engenharia, Finanças, Qualidade e Operações das plantas de Rio Claro e Joinville.
"""

SAMPLE_MEETINGS = [
    {
        "meeting_id": "WP-OPS-2026-08-15",
        "meeting_title": "Alinhamento Operacional: Cadeia de Suprimentos e Compressores - Linha Brastemp",
        "meeting_date": "2026-08-15",
        "department": "Logística e Manufatura",
        "raw_text": """
Participantes: Carlos Silva (Gerente de Logística), Mariana Mendes (Supervisora de Suprimentos), Roberto Souza (Engenharia de Produção).

[00:01] Carlos Silva: Bom dia equipe. Convoquei este alinhamento de emergência devido ao atraso de 14 dias no lote de compressores inverter para a planta de Rio Claro. O fornecedor principal reportou parada técnica. Meu CPF para a ata é 284.918.472-09 e meu crachá funcional é WP-94821.
[00:03] Mariana Mendes: Carlos, nós mapeamos o impacto. Se os compressores não chegarem até sexta, teremos que paralisar a linha de montagem dos refrigerantes Frost Free Brastemp Duplex. O custo de frete aéreo emergencial com a transportadora parceira foi cotado em R$ 4.850.000,00. Contato do despachante João Santos: (11) 98765-4321.
[00:06] Roberto Souza: Da parte da Engenharia, temos 800 unidades de compressores de segunda geração no armazém de Joinville que podem ser transferidos via rodoviário expresso. Eles têm compatibilidade mecânica total e passam pelo protocolo de testes PULSE-ENG-402.
[00:08] Carlos Silva: Excelente saída, Roberto. Decisão tomada: 
1. Mariana aciona a transferência imediata de 800 compressores de Joinville para Rio Claro até amanhã às 18h.
2. Roberto prepara o laudo técnico da engenharia para o controle de qualidade.
3. Eu aprovo o frete rodoviário dedicado no valor contingenciado de R$ 68.000,00, cancelando a opção aérea de 4.8 milhões.
[00:11] Mariana Mendes: Combinado. Vou registrar o plano de ação no Jira corporativo sob o ticket LOG-2026-784.
""",
        "source_type": "transcript_simulated"
    },
    {
        "meeting_id": "WP-QUAL-2026-08-22",
        "meeting_title": "Comitê de Qualidade: Análise de Ruído em Centrifugação - Linha Lava e Seca",
        "meeting_date": "2026-08-22",
        "department": "Engenharia e Qualidade",
        "raw_text": """
Participantes: Fernanda Lima (Gerente de Qualidade), Lucas Prado (Engenheiro de Produto), Beatriz Ramos (Atendimento ao Consumidor / SAC).

[00:01] Fernanda Lima: Iniciando a revisão mensal de qualidade. Beatriz, você trouxe os dados do SAC sobre a nova linha de Lava e Seca 12kg?
[00:02] Beatriz Ramos: Sim, Fernanda. Registramos 34 chamados nas últimas duas semanas relacionados a vibração e ruído excessivo durante a centrifugação a 1400 RPM. A maioria dos clientes é da Grande São Paulo e Curitiba. A reclamação formal do cliente chave protocolo SAC-99482 incluiu dados do cliente como CPF 109.827.364-55 e fone (41) 99123-8877.
[00:05] Lucas Prado: O laboratório acústico de Joinville fez o desmonte de 4 unidades de campo. Identificamos que o coxim de amortecimento dianteiro do lote fornecido em julho estava com dureza Shore A abaixo da especificação técnica (55 vs 65 esperado).
[00:07] Fernanda Lima: Qual o plano corretivo?
[00:08] Lucas Prado: Ações prioritárias:
1. Bloquear o lote restante de amortecedores código WP-DAMPER-78 no almoxarifado de Joinville.
2. Homologar novo composto de borracha de alta densidade até dia 28/08.
3. Emitir boletim técnico para a rede de assistência autorizada para troca preventiva do coxim em visitas de garantia.
[00:10] Fernanda Lima: Aprovado. Prazo final de implementação em linha: 05 de setembro.
""",
        "source_type": "transcript_simulated"
    },
    {
        "meeting_id": "WP-FIN-2026-08-28",
        "meeting_title": "Revisão Orçamentária e Eficiência Operacional - Capex Automação",
        "meeting_date": "2026-08-28",
        "department": "Finanças e Controladoria",
        "raw_text": """
Participantes: André Castro (Diretor Financeiro), Juliana Rocha (Gerente de TI e Inovação), Carlos Silva (Logística).

[00:01] André Castro: Bom dia. Nosso objetivo hoje é avaliar o Capex para o projeto de agentes autônomos de IA no Google Cloud e automação dos Centros de Distribuição. Meu crachá corporativo é WP-1002.
[00:03] Juliana Rocha: André, conforme solicitado na diretriz de governança PULSE, o projeto de IA no Vertex AI e BigQuery tem ROI projetado de 18 meses. Estimamos uma redução de 35% no tempo de busca de documentação de engenharia e histórico de supply chain. O orçamento anual de computação em nuvem ficou projetado em R$ 120.000,00, plenamente coberto pela economia de horas de analistas.
[00:06] Carlos Silva: Na logística, o impacto do assistente de conhecimento já evitou paradas críticas de linha semana passada. Apoiamos integralmente.
[00:07] André Castro: Orçamento de Capex aprovado para a fase de piloto e rollout em escala das soluções de GenAI da Whirlpool no Google Cloud.
""",
        "source_type": "transcript_simulated"
    }
]
