"""Análise do questionário PÓS da oficina de prevenção a golpes digitais.

O questionário foi aplicado logo depois da oficina, com uma pergunta retrospectiva
("antes da oficina, de 1 a 5, quanto você se sentia capaz de reconhecer um golpe?").
A comparação antes x depois é feita só na autoconfiança; os acertos são do PÓS.

Uso:
    python analise.py                      # lê dados/respostas.csv
    python analise.py caminho/arquivo.csv  # lê outro arquivo

Saídas:
    resultados/confianca_antes_depois.png  autoconfiança antes (retrospectiva) x depois
    resultados/acertos_por_questao.png     % de acerto por questão no PÓS
    resultados/resumo.md                   números e texto prontos para o relatório
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

BASE = Path(__file__).resolve().parent
SAIDA = BASE / "resultados"

GABARITO = {
    "q01": "c", "q02": "a", "q03": "d", "q04": "b", "q05": "c",
    "q06": "a", "q07": "b", "q08": "b", "q09": "b", "q10": "c",
}
TEMAS = {
    "q01": "SMS falso", "q02": "Pix p/ parente", "q03": "Senha forte",
    "q04": "2FA", "q05": "Falso suporte", "q06": "Loja falsa",
    "q07": "Link falso", "q08": "Código WhatsApp", "q09": "Wi-Fi público",
    "q10": "O que fazer",
}
QUESTOES = list(GABARITO)
CONFIANCA = ["confianca_antes", "confianca_depois"]


def carregar(caminho):
    df = pd.read_csv(caminho, dtype=str).fillna("")
    faltando = {"participante", *QUESTOES, *CONFIANCA} - set(df.columns)
    if faltando:
        sys.exit(f"Colunas faltando no CSV: {sorted(faltando)}")
    if df.empty:
        sys.exit("O CSV não tem respostas. Preencha dados/respostas.csv depois da oficina.")

    df["participante"] = df["participante"].str.strip().str.upper()
    repetidos = df[df["participante"].duplicated()]["participante"].tolist()
    if repetidos:
        sys.exit(f"Código repetido no CSV: {repetidos}")
    for q in QUESTOES:
        df[q] = df[q].str.strip().str.lower()
    for c in CONFIANCA:
        df[c] = pd.to_numeric(df[c], errors="coerce")
        fora = df[~df[c].between(1, 5)]
        if not fora.empty:
            sys.exit(f"{c} precisa ser de 1 a 5 (linhas {list(fora.index + 2)})")
    return df


def corrigir(df):
    acertos = pd.DataFrame({q: df[q] == GABARITO[q] for q in QUESTOES})
    return df.assign(acertos=acertos.sum(axis=1)), acertos


def resumir(df, acertos):
    por_questao = acertos.mean() * 100
    por_questao.index = [TEMAS[q] for q in por_questao.index]
    return {
        "n": len(df),
        "media_acertos": df["acertos"].mean(),
        "min_acertos": int(df["acertos"].min()),
        "max_acertos": int(df["acertos"].max()),
        "conf_antes": df["confianca_antes"].mean(),
        "conf_depois": df["confianca_depois"].mean(),
        "aumentaram": int((df["confianca_depois"] > df["confianca_antes"]).sum()),
        "por_questao": por_questao.sort_values(ascending=False),
    }


def graficos(r):
    SAIDA.mkdir(exist_ok=True)

    fig, ax = plt.subplots(figsize=(5, 4))
    barras = ax.bar(["Antes (retrospectivo)", "Depois"], [r["conf_antes"], r["conf_depois"]],
                    color=["#9aa5b1", "#2b6cb0"])
    ax.bar_label(barras, fmt="%.1f")
    ax.set_ylim(0, 5)
    ax.set_ylabel("Autoconfiança média (1 a 5)")
    ax.set_title("Capacidade de reconhecer golpes")
    fig.tight_layout()
    fig.savefig(SAIDA / "confianca_antes_depois.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4))
    barras = ax.bar(r["por_questao"].index, r["por_questao"].values, color="#2b6cb0")
    ax.bar_label(barras, fmt="%.0f%%")
    ax.set_ylim(0, 110)
    ax.set_ylabel("% de acerto")
    ax.set_title("Acerto por questão no questionário PÓS")
    plt.xticks(rotation=35, ha="right")
    fig.tight_layout()
    fig.savefig(SAIDA / "acertos_por_questao.png", dpi=150)
    plt.close(fig)


def br(x):
    return f"{x:.1f}".replace(".", ",")


def escrever_resumo(r):
    pq = r["por_questao"]
    linhas = [
        "# Resumo da análise",
        "",
        f"- Participantes que responderam: {r['n']}",
        f"- Média de acertos no PÓS: {br(r['media_acertos'])}/10 (mínimo {r['min_acertos']}, máximo {r['max_acertos']})",
        f"- Autoconfiança (1 a 5): antes {br(r['conf_antes'])} → depois {br(r['conf_depois'])}",
        f"- Participantes cuja autoconfiança aumentou: {r['aumentaram']} de {r['n']}",
        f"- Tema com mais acertos: {pq.index[0]} ({pq.iloc[0]:.0f}%) | com menos: {pq.index[-1]} ({pq.iloc[-1]:.0f}%)",
        "",
        "## Acerto por questão no PÓS (%)",
        "",
        "| Questão | % de acerto |",
        "|---|---|",
        *[f"| {q} | {v:.0f} |" for q, v in pq.items()],
        "",
        "## Texto sugerido para o relatório",
        "",
        (f"O questionário foi respondido por {r['n']} participantes logo depois da oficina. "
         f"A média de acertos foi de {br(r['media_acertos'])} em 10 questões. Na pergunta retrospectiva, "
         f"a autoconfiança média para reconhecer golpes passou de {br(r['conf_antes'])} (antes da oficina) "
         f"para {br(r['conf_depois'])} (depois), numa escala de 1 a 5, e aumentou para {r['aumentaram']} "
         f"dos {r['n']} participantes. O tema com mais acertos foi \"{pq.index[0]}\" e o com menos foi "
         f"\"{pq.index[-1]}\", que deve ser reforçado em próximas aplicações. Por não ter sido aplicado "
         f"um questionário antes da oficina, a comparação antes x depois se limita à autoconfiança "
         f"declarada pelos participantes."),
    ]
    (SAIDA / "resumo.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return "\n".join(linhas)


def main():
    caminho = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE / "dados" / "respostas.csv"
    df, acertos = corrigir(carregar(caminho))
    r = resumir(df, acertos)
    graficos(r)
    print(escrever_resumo(r))
    print(f"\nArquivos gerados em: {SAIDA}")


if __name__ == "__main__":
    main()
