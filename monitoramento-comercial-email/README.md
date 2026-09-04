# Monitoramento Comercial via E-mail # Monitoramento e Análise de Solicitações Comerciais via E-mail

Pipeline de captura, tratamento e análise de pedidos de cotação recebidos por e-mail, construído sobre Power Automate, Power Query e Python.

## Problema

A caixa de e-mail comercial recebe solicitações de cotação, orçamento e propostas de clientes misturadas com o restante do fluxo diário de trabalho. O acompanhamento manual é inviável frente ao volume de tarefas concorrentes, e não existia histórico estruturado para análise de funil comercial.

## O que este projeto resolve

- **Monitoramento contínuo** — captura automática de novas solicitações comerciais, prontas para cadastro em massa no CRM.
- **Reconstrução de histórico** — extração completa da caixa de e-mail para dimensionar volume de solicitações e alimentar análise de funil.
- **ETL reprodutível** — transformação dos dados brutos em base analítica (identificação de cliente, thread, categoria) tanto em Power Query quanto em Python.

## Arquitetura
