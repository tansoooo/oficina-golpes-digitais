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
