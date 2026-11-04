# Não Caia Nessa: Oficina de Prevenção a Golpes Digitais

Projeto da **Atividade Extensionista II: Tecnologia Aplicada à Inclusão Digital (Projeto)**, do CST em Ciência de Dados da UNINTER.

O projeto é uma oficina presencial sobre golpes digitais (Pix, WhatsApp, links falsos, falso suporte, lojas falsas), aplicada a um grupo familiar da comunidade local em 03/11/2026. O aprendizado é medido com um questionário respondido logo depois da oficina, com uma pergunta retrospectiva de autoconfiança (antes x depois), e analisado em **Python** (pandas e matplotlib).

- **Setor de aplicação:** grupo familiar, Vila Nastri, Itapetininga/SP
- **ODS:** 4 (Educação de qualidade), 10 (Redução das desigualdades), 16 (Paz, justiça e instituições eficazes)
- **Vídeo da aplicação:** https://youtu.be/C9xRmHuESKM

## Objetivos

1. Desenvolver uma oficina sobre prevenção a golpes digitais, com material de apoio em HTML.
2. Aplicar a oficina a um grupo familiar da comunidade local.
3. Medir o conhecimento dos participantes com um questionário de 10 questões e a autoconfiança antes e depois (pergunta retrospectiva).
4. Analisar os resultados com Python (pandas e matplotlib) e publicar o código no GitHub.

## Estrutura

```
material/apresentacao.html      slides da oficina (abre no navegador, setas ← → para navegar)
material/atividade_pratica.md   dinâmica "REAL ou GOLPE?"
questionario/questionario.md    questionário e gabarito
questionario/whatsapp_pos.txt   o mesmo questionário em formato de mensagem
dados/respostas.csv             respostas digitadas depois da oficina (anônimas)
analise.py                      correção, gráficos e resumo
resultados/                     saída da análise (gerada pelo script)
```

## Como rodar a análise

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python analise.py
```

### Formato do CSV

Uma linha por participante:

```
participante,q01,q02,q03,q04,q05,q06,q07,q08,q09,q10,confianca_antes,confianca_depois
P01,c,a,d,b,c,a,b,b,b,c,2,4
```

- `q01` a `q10`: a letra marcada (`a`, `b`, `c` ou `d`); deixe vazio se a pessoa não respondeu
- `confianca_depois`: nota de 1 a 5 da questão 11
- `confianca_antes`: nota de 1 a 5 da questão 12 (retrospectiva)

O script gera `resultados/confianca_antes_depois.png`, `resultados/acertos_por_questao.png` e `resultados/resumo.md` (com um parágrafo pronto para o relatório).

## Engenharia de requisitos (resumo)

**Partes interessadas:** participantes do grupo familiar (de 6 a 31 anos) e o aluno extensionista.

**Requisitos funcionais**
- RF01: Apresentar o conteúdo da oficina em slides navegáveis offline.
- RF02: Coletar as respostas de forma anônima, por código.
- RF03: Corrigir os questionários automaticamente a partir do gabarito.
- RF04: Gerar gráficos de autoconfiança antes x depois e de acerto por questão.
- RF05: Gerar um resumo textual dos resultados.

**Requisitos não funcionais**
- RNF01: Privacidade: não coletar nome, CPF ou telefone dos participantes (LGPD).
- RNF02: Acessibilidade: fonte grande, alto contraste e linguagem simples nos slides.
- RNF03: Funcionar sem internet durante a oficina.
- RNF04: Rodar em Python 3.9 ou superior com dependências mínimas.

## Gestão

Kanban simples (A fazer → Fazendo → Feito), com as etapas descritas na metodologia do relatório.

| Risco | Prob. | Impacto | Resposta |
|---|---|---|---|
| Data da oficina remarcada | Média | Alto | Reorganizar o cronograma e aplicar o questionário ao final, com pergunta retrospectiva |
| Participantes com pouca familiaridade com o celular | Alta | Médio | Linguagem simples, leitura do questionário em voz alta, ajuda nas duplas |
| Sem projetor | Média | Médio | Usar notebook ou celular e o material impresso |
| Questionários incompletos | Média | Baixo | Conferir no recolhimento; o script ignora campos vazios |
| Exposição de menores no vídeo | Alta | Alto | Filmar sem rostos ou com autorização assinada |
