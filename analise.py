"""Análise dos questionários PRÉ e PÓS da oficina de prevenção a golpes digitais.

Uso:
    python analise.py                      # lê dados/respostas.csv
    python analise.py caminho/arquivo.csv  # lê outro arquivo

Saídas:
    resultados/acertos_pre_pos.png     gráfico da média de acertos antes e depois
    resultados/acertos_por_questao.png % de acerto por questão (PRÉ x PÓS)
    resultados/resumo.md               números e texto prontos para o relatório
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


def carregar(caminho):
    df = pd.read_csv(caminho, dtype=str).fillna("")
    faltando = {"participante", "momento", *QUESTOES} - set(df.columns)
    if faltando:
        sys.exit(f"Colunas faltando no CSV: {sorted(faltando)}")
    if df.empty:
        sys.exit("O CSV não tem respostas. Preencha dados/respostas.csv depois da oficina.")

    df["participante"] = df["participante"].str.strip().str.upper()
    df["momento"] = (
        df["momento"].str.strip().str.lower()
        .str.normalize("NFKD").str.encode("ascii", "ignore").str.decode("ascii")
    )
    invalidos = df[~df["momento"].isin(["pre", "pos"])]
    if not invalidos.empty:
        sys.exit(f"Momento inválido (use PRE ou POS) nas linhas: {list(invalidos.index + 2)}")
    for q in QUESTOES:
        df[q] = df[q].str.strip().str.lower()
    return df


def corrigir(df):
    acertos = pd.DataFrame({q: df[q] == GABARITO[q] for q in QUESTOES})
    df = df.assign(acertos=acertos.sum(axis=1))
    return df, acertos


def resumir(df, acertos):
    pre = df[df["momento"] == "pre"]
    pos = df[df["momento"] == "pos"]
    pares = pre.merge(pos, on="participante", suffixes=("_pre", "_pos"))

    por_questao = pd.DataFrame({
        "pre": acertos[df["momento"] == "pre"].mean() * 100,
        "pos": acertos[df["momento"] == "pos"].mean() * 100,
    })
    por_questao.index = [TEMAS[q] for q in por_questao.index]

    r = {
        "n_pre": len(pre),
        "n_pos": len(pos),
        "n_pares": len(pares),
        "media_pre": pre["acertos"].mean(),
        "media_pos": pos["acertos"].mean(),
        "melhoraram": int((pares["acertos_pos"] > pares["acertos_pre"]).sum()),
        "por_questao": por_questao,
    }
    if "confianca" in df.columns:
        conf = pd.to_numeric(df["confianca"], errors="coerce")
        r["conf_pre"] = conf[df["momento"] == "pre"].mean()
        r["conf_pos"] = conf[df["momento"] == "pos"].mean()
    return r


def graficos(r):
    SAIDA.mkdir(exist_ok=True)

    fig, ax = plt.subplots(figsize=(5, 4))
    barras = ax.bar(["Antes (PRÉ)", "Depois (PÓS)"], [r["media_pre"], r["media_pos"]],
                    color=["#9aa5b1", "#2b6cb0"])
    ax.bar_label(barras, labels=[br(v) for v in (r["media_pre"], r["media_pos"])])
    ax.set_ylim(0, 11)
    ax.set_yticks(range(0, 11, 2))
    ax.set_ylabel("Média de acertos (de 10)")
    ax.set_title("Acertos antes e depois da oficina")
    fig.tight_layout()
    fig.savefig(SAIDA / "acertos_pre_pos.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4))
    r["por_questao"].plot.bar(ax=ax, color=["#9aa5b1", "#2b6cb0"], width=0.8)
    ax.set_ylim(0, 125)
    ax.set_yticks(range(0, 101, 20))
    ax.set_ylabel("% de acerto")
    ax.set_title("Acerto por questão: PRÉ x PÓS")
    ax.legend(["PRÉ", "PÓS"], loc="upper left", ncol=2)
    plt.xticks(rotation=35, ha="right")
    fig.tight_layout()
    fig.savefig(SAIDA / "acertos_por_questao.png", dpi=150)
    plt.close(fig)


def br(x, casas=1):
    return f"{x:.{casas}f}".replace(".", ",")


def escrever_resumo(r):
    pq = r["por_questao"]
    ganho = (pq["pos"] - pq["pre"]).sort_values(ascending=False)
    maiores = list(ganho[ganho == ganho.iloc[0]].index)
    temas_ganho = ", ".join(f'"{t}"' for t in maiores)
    linhas = [
        "# Resumo da análise",
        "",
        f"- Questionários PRÉ: {r['n_pre']} | PÓS: {r['n_pos']} | participantes com os dois: {r['n_pares']}",
        f"- Média de acertos: PRÉ {br(r['media_pre'])}/10 → PÓS {br(r['media_pos'])}/10",
        f"- Participantes que melhoraram a nota: {r['melhoraram']} de {r['n_pares']}",
    ]
    if "conf_pre" in r:
        linhas.append(f"- Autoconfiança (1 a 5): PRÉ {br(r['conf_pre'], 2)} → PÓS {br(r['conf_pos'], 2)}")
    linhas += [
        f"- Maior ganho ({ganho.iloc[0]:.0f} pontos percentuais): {', '.join(maiores)}",
        "",
        "## Acerto por questão (%)",
        "",
        "| Questão | PRÉ | PÓS |",
        "|---|---|---|",
        *[f"| {q} | {v['pre']:.0f} | {v['pos']:.0f} |" for q, v in pq.iterrows()],
        "",
        "## Texto sugerido para o relatório",
        "",
        (f"A oficina foi aplicada com {r['n_pares']} participantes, que responderam ao questionário "
         f"antes e depois da atividade. A média de acertos passou de {br(r['media_pre'])} para "
         f"{br(r['media_pos'])} (de 10 questões), e "
         + (f"todos os {r['n_pares']}" if r['melhoraram'] == r['n_pares'] else f"{r['melhoraram']} dos {r['n_pares']}")
         + f" participantes melhoraram a pontuação. O maior ganho ({ganho.iloc[0]:.0f} pontos percentuais) ocorreu em "
         f"{'um tema' if len(maiores) == 1 else f'{len(maiores)} temas'}: {temas_ganho}."
         + (f" A autoconfiança média para reconhecer golpes foi de {br(r['conf_pre'], 2)} no PRÉ e de "
            f"{br(r['conf_pos'], 2)} no PÓS, numa escala de 1 a 5." if "conf_pre" in r else "")),
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
