# Relatório Operacional Whirlpool - Acidente de Caminhão - Brastemp (Geladeiras e Lavadoras)

**Departamento:** Inovação e Automação de Processos | **ID:** WP-PORTAL-1788431457

## Resumo Executivo
José relata um acidente envolvendo um caminhão que transportava geladeiras e lavadoras Brastemp, resultando em avaria de parte da carga. A entrega para o cliente Casas Bahia não poderá ser feita no prazo. São solicitadas ações para informar o cliente e encontrar um fornecedor alternativo da Whirlpool para 50 lavadoras e 130 geladeiras.

## Transcrição Sanitizada (PULSE/LGPD)
[speaker_0]: Boa tarde, tudo bem? Aqui é o José. Eu queria entrar em contato com a Ana do RH para informar sobre a logística de um dos nossos caminhões que estava transportando geladeiras e lavadoras da Brastemp. O respectivo caminhão, ele sofreu um acidente e parte da carga sofreu avaria. Então a gente não vai conseguir entregar a tempo para o nosso cliente essas... eh... essa carga. Então, por favor, entrem em contato com as Casas Bahia, que é o nosso cliente, para informar sobre essa questão e, por favor, verifique se há alguma outra fornecedora, eh, da Whirlpool que possa estar, ah, fornecendo esses, eh, essas lavadoras e, eh, geladeiras. Foram no total 50 lavadoras e 130 geladeiras. Tá bom?

## Fluxograma Operacional (Mermaid)
```mermaid
flowchart TD
    A[Gatilho: Acidente Caminhão Brastemp] --> B[Problema: Carga Avariada e Atraso na Entrega para Casas Bahia]

    B --> C{"Decisões da Reunião - Dpto. Inovação e Automação"}
    B --> F[Ação: Informar Ana (RH) sobre Logística]

    C --> D{"Decisão: Informar Cliente Casas Bahia sobre Atraso"}
    C --> E{"Decisão: Buscar Fornecedor Alternativo Whirlpool"}

    D --> G[Execução: Entrar em Contato com Casas Bahia]
    E --> H[Execução: Verificar Fornecedores para 50 Lavadoras e 130 Geladeiras]

    F --> I[Resultado: Ana (RH) Notificada]
    G --> J[Resultado: Cliente Casas Bahia Informado]
    H --> K[Resultado: Demanda Suprida com Fornecedor Alternativo]

    I & J & K --> L[Processo de Contingência Concluído]
```

## Matriz RACI
Com certeza! Como Gerente de Projetos Sênior da Whirlpool, entendo a urgência e a necessidade de clareza na gestão de incidentes como este. A Matriz RACI é fundamental para garantir que todos saibam suas responsabilidades.

Aqui está a Matriz RACI para as ações listadas, considerando as funções corporativas típicas da Whirlpool e o contexto do incidente:

**Matriz RACI - Acidente de Caminhão - Brastemp (Geladeiras e Lavadoras)**

| Ação / Entregável | Responsável (R) | Aprovador (A) | Consultado (C) | Informado (I) | Prazo |
|---|---|---|---|---|---|
| Informar Ana (RH) sobre a questão logística. | **José (Gerente de Projetos - Incidente)** | Gerente de Projetos Sênior (Eu) | Logística (Detalhes do incidente), Jurídico (Se houver implicações de pessoal) | Ana (RH), Diretoria de Logística, Gerência de Operações | D+1 (24 horas) |
| Entrar em contato com as Casas Bahia para informar sobre o acidente e o atraso na entrega da carga. | **Gerente de Contas (Vendas/Comercial)** | José (Gerente de Projetos - Incidente) | Logística (Novo prazo estimado), Jurídico (Termos contratuais) | Diretoria de Vendas, Diretoria de Logística, Financeiro, Diretoria Geral | D+0 (Até o fim do dia) |
| Verificar a existência de outros fornecedores da Whirlpool que possam suprir 50 lavadoras e 130 geladeiras. | **Analista/Gerente de Compras (Suprimentos)** | José (Gerente de Projetos - Incidente) | Manufatura (Capacidade/Disponibilidade), Logística (Capacidade de transporte dos novos fornecedores), Engenharia (Homologação, se aplicável) | Diretoria de Compras, Diretoria de Manufatura, Diretoria de Logística, Financeiro, Diretoria Geral | D+3 (3 dias úteis para opções iniciais) |
