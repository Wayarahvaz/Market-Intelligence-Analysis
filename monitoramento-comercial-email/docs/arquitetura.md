# Monitoramento e Análise de Solicitações Comerciais via E-mail

Pipeline de captura, tratamento e análise de pedidos de cotação recebidos por e-mail

## 1. Contexto e Objetivo

A caixa de e-mail comercial recebe, entre outras mensagens, solicitações de cotação, orçamento e propostas de clientes. O acompanhamento manual desse fluxo é inviável frente ao volume de tarefas concorrentes do dia a dia, e não existia histórico estruturado para análise de funil.

Este projeto resolve dois problemas complementares:

- **Monitoramento contínuo**: capturar automaticamente, todos os dias, e-mails que representem novas solicitações comerciais, organizando-os para cadastro em massa no CRM.
- **Reconstrução de histórico**: extrair o histórico completo de e-mails da mesma caixa para dimensionar o volume de solicitações e alimentar uma análise macro de funil comercial.

## 2. Arquitetura da Solução

A solução foi construída inteiramente sobre a plataforma Microsoft Power Platform, evitando dependência de aprovações administrativas adicionais (Entra ID / Azure AD) que se mostraram bloqueadas no ambiente corporativo durante a fase de prototipagem com Microsoft Graph API.

| Camada | Ferramenta | Função |
| Captura | Power Automate | Monitoramento contínuo da caixa de e-mail e captura pontual do histórico |
| Armazenamento | Excel Online (OneDrive) | Tabela estruturada como camada bruta (raw) dos dados capturados |
| Transformação | Power Query + Python (pandas) | Limpeza, extração de cliente, categorização e agregação de threads |
| Análise | Power BI / Tabela Dinâmica | Consolidação de métricas de funil (volume, categoria, cliente) |

## 3. Fluxo 1 — Monitoramento Diário

Fluxo automatizado ("Monitorar cotações - Comercial"), ativo continuamente, responsável por capturar novas solicitações no momento em que chegam.

| Etapa | Ação | Detalhe técnico |
| 1. Gatilho | When a new email arrives (V3) | Monitora a pasta "Commercial" da caixa pessoal; dispara a cada novo item detectado |
| 2. Limpeza | Html to text | Converte o corpo do e-mail (HTML) em texto plano, removendo marcação e estilos |
| 3. Filtro | Condition (OR) | Verifica se Assunto ou Corpo contêm palavras-chave: cotação, orçamento, proposta, preço |
| 4. Persistência | Add a row into a table | Grava Data, Remetente, Assunto, Corpo, Origem e ConversationId numa tabela Excel no OneDrive |

Observação: o gatilho aponta para uma pasta pessoal ("Commercial"), alimentada por uma regra do Outlook que move automaticamente as mensagens da lista comercial. Essa escolha evitou a necessidade de acesso a uma caixa compartilhada, simplificando a configuração de permissões.

## 4. Fluxo 2 — Reconstrução de Histórico

Fluxo de execução manual e pontual ("Histórico - Comercial"), utilizado para popular a base com dados retroativos, permitindo iniciar a análise sem esperar meses de captura orgânica pelo Fluxo 1.

| Etapa | Ação | Detalhe técnico |
|---|---|---|
| 1. Gatilho | Manually trigger a flow | Execução única e sob demanda, sem recorrência automática |
| 2. Extração | Get emails (V3) | Busca a pasta inteira, sem filtro de data, limite de 1000 itens por execução |
| 3. Iteração | Apply to each | Processa cada e-mail retornado individualmente, evitando duplicidade de contexto |
| 4. Limpeza + Filtro | Html to text + Condition | Mesma lógica do Fluxo 1, com proteção `coalesce()` contra e-mails sem corpo (convites de calendário, notificações automáticas) |
| 5. Persistência | Add a row into a table | Grava na mesma tabela usada pelo monitoramento diário, unificando histórico e captura contínua |

## 5. Camada de Transformação (ETL)

Os dados brutos gravados pelos dois fluxos passam por um processo de ETL, disponível em duas implementações equivalentes: **Power Query** (dentro do Excel, para exploração rápida) e **Python/pandas** (script versionado, para reprodutibilidade e portfólio).

| Etapa | Transformação aplicada |
|---|---|
| Deduplicação | Remoção de linhas idênticas (mesmo remetente + assunto + data), que podem surgir da sobreposição entre o monitoramento diário e a extração histórica |
| Extração de cliente | Divisão do e-mail do remetente pelo delimitador `@`, isolando o domínio como identificador do cliente (`Dominio_Cliente`) |
| Identificação de thread | Agrupamento por `ConversationId` (identificador nativo do Outlook), método mais confiável que comparação textual de assunto |
| Classificação de tipo | Dentro de cada thread, a primeira mensagem cronológica é marcada como "Solicitação Nova"; as seguintes como "Atualização" |
| Categorização | Classificação por correspondência textual em Cotação, Proposta Técnica ou Outros |
| Agregação | Consolidação por thread, com data de solicitação, data da última atualização, duração da negociação e quantidade de interações |

## 6. Decisões Técnicas e Trade-offs

- **Power Automate em vez de Microsoft Graph API**: a abordagem inicial via Python + MSAL + Graph API exigia aprovação de administrador do Entra ID para conceder consentimento (Mail.Read), o que gerou bloqueio de dependência externa. A migração para Power Automate contornou o bloqueio, pois os conectores do Office 365 Outlook já possuíam consentimento pré-aprovado no tenant.
- **Classificação por palavra-chave em vez de IA (AI Builder)**: avaliou-se o uso de AI Builder (Prompts com GPT) para classificação semântica dos e-mails. A ação demonstrou instabilidade de configuração e dependência de créditos de capacidade do Power Platform. Optou-se por manter o filtro por palavras-chave nesta fase, com a evolução para classificação por IA registrada como melhoria futura.
- **Agrupamento por ConversationId em vez de texto de assunto**: a normalização textual do assunto (remoção de prefixos RE:/RES:/FW:) é frágil a variações de idioma e formatação. O ConversationId nativo do Outlook resolve isso de forma determinística.
- **Paginação manual em vez de paginação automática**: a ação "Get emails (V3)" não expõe paginação nativa na interface do Power Automate para volumes acima de ~1000 itens. Optou-se por limitar a extração a 1000 itens (cobrindo ~99,8% da caixa no momento da implementação) em vez de construir um loop de paginação manual via variáveis de controle, priorizando simplicidade de manutenção.

## 7. Melhorias Futuras

- Classificação semântica via AI Builder (Prompts) ou modelo de linguagem, substituindo o filtro por palavra-chave.
- Extração automática do nome do solicitante e da empresa a partir da assinatura do e-mail.
- Migração da camada de análise para Power BI, com relacionamento ao CRM e cálculo de tempo médio entre solicitação recebida e proposta enviada.
- ETL em SQL para consolidar e consultar as solicitações de forma mais escalável.
- Modelo de Machine Learning para classificação de intenção do e-mail (solicitação vs. atualização vs. ruído), substituindo a heurística baseada em thread.
