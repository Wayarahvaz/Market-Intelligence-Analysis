 Monitoramento e Análise de Solicitações Comerciais via E-mail

Pipeline de captura, tratamento e análise de pedidos de cotação recebidos por e-mail, construído sobre Power Automate, Power Query e Python.

## Problema

A caixa de e-mail comercial recebe solicitações de cotação, orçamento e propostas de clientes misturadas com o restante do fluxo diário de trabalho. O acompanhamento manual é inviável frente ao volume de tarefas concorrentes, e não existia histórico estruturado para análise de funil comercial.

## O que este projeto resolve

- **Monitoramento contínuo** — captura automática de novas solicitações comerciais, prontas para cadastro em massa no CRM.
- **Reconstrução de histórico** — extração completa da caixa de e-mail para dimensionar volume de solicitações e alimentar análise de funil.
- **ETL reprodutível** — transformação dos dados brutos em base analítica (identificação de cliente, thread, categoria) tanto em Power Query quanto em Python.

## Arquitetura
E-mail (Outlook) → Power Automate → Excel (OneDrive) → ETL (Power Query / Python) → Análise (Power BI) 


Veja a documentação completa da arquitetura em [`docs/arquitetura.md`](docs/arquitetura.md).

## Stack

- **Power Automate** — captura e monitoramento (sem dependência de aprovação administrativa de Entra ID/Graph API)
- **Excel Online** — camada de armazenamento bruto
- **Power Query** — ETL exploratório
- **Python (pandas)** — ETL reprodutível e versionado, com classificação de thread via `ConversationId`
- **Power BI** *(planejado)* — camada de análise e storytelling

## Estrutura do repositório

monitoramento-comercial-email/
├── docs/
│ ├── arquitetura.md → decisões técnicas e desenho dos fluxos
│ └── layout-powerbi.md → plano de dashboard e modelo de dados
├── power-automate/ → fluxos exportados e documentados
├── etl/
│ ├── etl_solicitacoes.py → script de ETL em Python
│ └── requirements.txt
├── dados_exemplo/ → dados fictícios para reprodução
└── roadmap/
└── proximos-passos.md → próximas evoluções (SQL, Machine Learning)


## Resultados

A execução da extração histórica, após ETL e agrupamento por thread, identificou dezenas de solicitações comerciais distintas, categorizadas por tipo e associadas ao domínio de e-mail do cliente — base estruturada para responder volume, categoria e concentração por cliente de forma recorrente e sem esforço manual.

## Decisões técnicas de destaque

Este projeto documenta explicitamente os trade-offs de engenharia enfrentados num ambiente corporativo real — como a substituição de uma abordagem via Microsoft Graph API por Power Automate após bloqueio de aprovação administrativa, e o uso de `ConversationId` nativo do Outlook em vez de heurística textual para identificar threads de conversa. Detalhes completos em [`docs/arquitetura.md`](docs/arquitetura.md).

## Próximos passos

Ver [`roadmap/proximos-passos.md`](roadmap/proximos-passos.md).
