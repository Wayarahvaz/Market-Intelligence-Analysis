"""
ETL de solicitações comerciais recebidas por e-mail.

Lê a planilha alimentada pelos fluxos do Power Automate (monitoramento
diário + extração histórica), limpa, identifica threads de conversa reais
via ConversationId, classifica cada e-mail como "Solicitação Nova" ou
"Atualização" dentro da própria thread, e categoriza por tipo de pedido.

Uso:
    python etl_solicitacoes.py --entrada Pedidos_Cotacao_Comercial.xlsx --saida solicitacoes_tratadas.xlsx
"""

import argparse
import re
import pandas as pd


PALAVRAS_COTACAO = [
    "cotação", "cotacao", "rfp", "rfi", "rfq", "orçamento", "orcamento",
    "proposta", "convite", "aquisição", "aquisicao", "solicitação", "solicitacao",
]

PREFIXOS_THREAD = re.compile(r"^(RES:|RE:|FW:|ENC:)\s*", flags=re.IGNORECASE)


def carregar_dados(caminho_excel: str, aba: str = "historico_email") -> pd.DataFrame:
    """Lê a planilha bruta exportada pelo Power Automate."""
    df = pd.read_excel(caminho_excel, sheet_name=aba)
    df["Date_Recieved"] = pd.to_datetime(df["Date_Recieved"], errors="coerce", utc=True)
    # Excel não aceita datetime com fuso horário embutido — converte para "naive"
    df["Date_Recieved"] = df["Date_Recieved"].dt.tz_localize(None)
    return df


def remover_duplicatas_exatas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove linhas idênticas que podem ter sido gravadas duas vezes
    (ex: mesmo e-mail capturado pelo fluxo diário E pela extração histórica).
    Usa Email_Remetente + Assunto + Data como chave de identidade do e-mail.
    """
    antes = len(df)
    df = df.drop_duplicates(subset=["Email_Remetente", "Assunto", "Date_Recieved"])
    removidas = antes - len(df)
    if removidas:
        print(f"[info] {removidas} linha(s) duplicada(s) removida(s).")
    return df


def extrair_dominio_cliente(df: pd.DataFrame) -> pd.DataFrame:
    """Extrai o domínio do e-mail do remetente como identificador do cliente."""
    df["Dominio_Cliente"] = (
        df["Email_Remetente"]
        .astype(str)
        .str.extract(r"@([^\s>]+)", expand=False)
        .str.lower()
        .str.strip()
    )
    return df


def normalizar_assunto(df: pd.DataFrame) -> pd.DataFrame:
    """Remove prefixos de resposta/encaminhamento para fins de leitura humana."""
    df["Assunto_Normalizado"] = (
        df["Assunto"].astype(str).str.replace(PREFIXOS_THREAD, "", regex=True).str.strip()
    )
    return df


def categorizar(row: pd.Series) -> str:
    """Classifica o tipo de solicitação por correspondência textual."""
    texto = f"{row.get('Assunto_Normalizado', '')} {row.get('Trecho_Corpo', '')}".lower()
    if "proposta tecnica" in texto or "proposta técnica" in texto:
        return "Proposta Tecnica"
    if any(p in texto for p in PALAVRAS_COTACAO):
        return "Cotação"
    return "Outros"


def classificar_por_thread(df: pd.DataFrame) -> pd.DataFrame:
    """
    Usa o ConversationId (thread real do Outlook) para identificar, dentro de
    cada conversa, qual e-mail foi a solicitação original e quais foram
    atualizações/respostas subsequentes.

    Se a coluna ID_Conversa não existir (planilhas antigas, sem esse campo),
    cai de volta para o agrupamento por Dominio_Cliente + Assunto_Normalizado.
    """
    chave_thread = "ID_Conversa" if "ID_Conversa" in df.columns else None
    if chave_thread is None:
        print("[aviso] Coluna 'ID_Conversa' não encontrada — agrupando por cliente + assunto normalizado.")
        df["_chave_thread"] = df["Dominio_Cliente"] + "|" + df["Assunto_Normalizado"].str.lower()
        chave_thread = "_chave_thread"

    df = df.sort_values([chave_thread, "Date_Recieved"])
    df["Ordem_na_Thread"] = df.groupby(chave_thread).cumcount()
    df["Tipo_Solicitacao"] = df["Ordem_na_Thread"].apply(
        lambda i: "Solicitação Nova" if i == 0 else "Atualização"
    )
    return df, chave_thread


def montar_resumo_por_thread(df: pd.DataFrame, chave_thread: str) -> pd.DataFrame:
    """Uma linha por negociação real, com métricas de duração e volume de troca."""
    resumo = (
        df.groupby(chave_thread)
        .agg(
            Dominio_Cliente=("Dominio_Cliente", "first"),
            Assunto=("Assunto_Normalizado", "first"),
            Categoria=("Categoria", "first"),
            Data_Solicitacao=("Date_Recieved", "min"),
            Data_Ultima_Atualizacao=("Date_Recieved", "max"),
            Qtd_Interacoes=("Ordem_na_Thread", "max"),
        )
        .reset_index(drop=True)
    )
    resumo["Qtd_Interacoes"] = resumo["Qtd_Interacoes"] + 1  # inclui a mensagem original
    resumo["Duracao_Negociacao_Dias"] = (
        resumo["Data_Ultima_Atualizacao"] - resumo["Data_Solicitacao"]
    ).dt.days
    return resumo.sort_values("Data_Solicitacao", ascending=False)


def executar_etl(caminho_entrada: str, caminho_saida: str, aba: str = "historico_email") -> None:
    df = carregar_dados(caminho_entrada, aba=aba)
    df = remover_duplicatas_exatas(df)
    df = extrair_dominio_cliente(df)
    df = normalizar_assunto(df)
    df["Categoria"] = df.apply(categorizar, axis=1)
    df, chave_thread = classificar_por_thread(df)
    resumo = montar_resumo_por_thread(df, chave_thread)

    with pd.ExcelWriter(caminho_saida, engine="openpyxl") as writer:
        df.drop(columns=["_chave_thread"], errors="ignore").to_excel(
            writer, sheet_name="detalhe_por_email", index=False
        )
        resumo.to_excel(writer, sheet_name="resumo_por_solicitacao", index=False)

    total_emails = len(df)
    total_solicitacoes = len(resumo)
    print(f"[ok] {total_emails} e-mails processados -> {total_solicitacoes} solicitações únicas.")
    print(f"[ok] Arquivo salvo em: {caminho_saida}")


def main():
    parser = argparse.ArgumentParser(description="ETL de solicitações comerciais por e-mail.")
    parser.add_argument("--entrada", required=True, help="Caminho da planilha bruta (.xlsx)")
    parser.add_argument("--saida", required=True, help="Caminho de saída da planilha tratada (.xlsx)")
    parser.add_argument("--aba", default="historico_email", help="Nome da aba de origem")
    args = parser.parse_args()
    executar_etl(args.entrada, args.saida, aba=args.aba)


if __name__ == "__main__":
    main()
