# TopVistos EUA — Classificação de resultados de vistos

[English](README.md) | **Português**

Estudo reproduzível de classificação desenvolvido a partir do projeto da competição Kaggle **ML Olympiad for Students — TopVistos EUA**, de 2023. A implementação atual separa treino, validação e teste final reservado, ajusta o pré-processamento dentro de cada fold de treino e compara baselines fixos.

## Resultados até aqui

Em **3.567 casos de validação**, a regressão logística alcança **0,681 de F1 macro** e **0,769 de ROC-AUC**, contra 0,401 e 0,500 do baseline baseado na frequência das classes. São resultados de desenvolvimento; o teste final ainda não foi avaliado.

| Métrica de validação | Baseline de frequência | Regressão logística |
|---|---:|---:|
| F1 macro | 0,401 | 0,681 |
| F1 — classe aprovada | 0,802 | 0,824 |
| ROC-AUC | 0,500 | 0,769 |
| Recall — classe negada | 0,000 | 0,448 |

O baseline prevê aprovação para todos os casos. Seu F1 de 0,802 para a classe aprovada mostra por que essa métrica isolada oferece uma visão incompleta. A regressão logística ainda deixa de identificar 651 dos 1.180 casos negados, com limiar fixo de 0,5.

![Comparação dos baselines na validação](docs/baseline/validation-baselines.png)

O [relatório do experimento](docs/BASELINE.pt-BR.md) apresenta protocolo, validação cruzada, matriz de confusão e limitações. Os [resultados em JSON](docs/baseline/metrics.json) incluem hashes dos dados, código e partições.

## Reproduzir o experimento

Use uma versão **estável do Python 3.11**. A execução registrada usou Python 3.11.14 no Windows. As dependências estão fixadas em [requirements-lock.txt](requirements-lock.txt). Execute os comandos na raiz do repositório.

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-lock.txt
.venv/Scripts/python.exe -m unittest discover -s tests -v
.venv/Scripts/python.exe -m topvistos.baseline
```

Linux/macOS:

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m topvistos.baseline
```

Obtenha os [dados necessários](data/README.pt-BR.md) e coloque-os em `data/raw/` antes de executar o experimento. O baseline exige o hash registrado do `train.csv`. Os testes usam dados sintéticos e dispensam os arquivos da competição. A integração contínua instala as dependências fixadas e executa os testes no Linux.

As saídas ficam em `reports/generated/baseline/`: métricas, gráfico, identificadores das partições e pipelines treinados. Essa pasta é ignorada pelo Git; somente resultados agregados e o gráfico são selecionados para a documentação. Carregue modelos serializados apenas de uma fonte confiável.

## Decisões de implementação

- Divisão determinística e estratificada 60/20/20; a validação cruzada em cinco folds usa somente a partição de treino.
- Imputação, escala e codificação de categorias ajustadas dentro do pipeline; inferência aceita valores ausentes e categorias desconhecidas.
- IDs e alvo ficam fora das variáveis. Quantidades negativas de empregados viram valores ausentes com um indicador.
- Precisão e recall usam a ordem correta dos argumentos; ROC-AUC usa probabilidades.
- Testes cobrem integridade dos dados, separação das partições, isolamento do pré-processamento, métricas, serialização e execução sem variáveis ou rótulos do teste final.

## Escopo e próximos passos

O estudo modela o rótulo histórico `status_do_caso`: `Aprovado=1`, `Negado=0`. Não foi validado para determinar elegibilidade a vistos ou automatizar decisões de imigração. F1 macro é um critério interno de desenvolvimento; a variante oficial de F1 e o resultado no ranking da competição permanecem sem verificação.

Próximo passo: comparar poucos modelos candidatos, selecionar eventual limiar nos dados de desenvolvimento e então avaliar o teste reservado e os erros por segmentos relevantes. A base original já foi explorada no notebook histórico; a partição reservada não representa nova evidência externa. Os resultados atuais não são diretamente comparáveis aos do notebook, que usa outra divisão.

## Trabalho histórico e fonte dos dados

- [Notebook original (português)](ml-olympiad_top-vistos-eua_solucao.ipynb), preservado intacto.
- [Auditoria de reprodução](docs/REPRODUCIBILITY.pt-BR.md).
- [Manifesto agregado dos dados](docs/data-manifest.json).
- [Descrição original da competição (português)](docs/competition-description.pt-BR.md).

André Lopes. *ML Olympiad for Students — TopVistos EUA* (2023), [Kaggle](https://www.kaggle.com/competitions/ml-olympiad-for-students-topvistos-eua). O autor forneceu arquivos locais com as contagens históricas de linhas; a origem do download não foi verificada independentemente. Os dados brutos não são redistribuídos.