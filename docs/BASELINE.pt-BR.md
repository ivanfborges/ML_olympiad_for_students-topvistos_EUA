# Experimento com baselines fixos

[English](BASELINE.md) | **Português**

Esta entrega reconstrói o fluxo de avaliação do projeto histórico do Kaggle. Ela estabelece uma referência reproduzível de desenvolvimento antes da seleção de modelos e limiares. Não reproduz o resultado antigo no ranking.

## Dados e fronteira de avaliação

O autor forneceu 17.836 casos rotulados. O [manifesto dos dados](data-manifest.json) registra hashes dos arquivos e verificações estruturais; a data e a origem do download não foram verificadas independentemente.

Os casos são ordenados pelo identificador antes de duas divisões aleatórias estratificadas com semente 42. A primeira reserva 20%; a segunda destina 25% do restante à validação.

| Partição | Casos | Uso |
|---|---:|---|
| Treino | 10.701 | Validação cruzada estratificada em cinco folds e ajuste |
| Validação | 3.567 | Comparação dos baselines fixos; futura seleção de modelo/limiar |
| Teste final | 3.568 | Reservado; não avaliado nesta entrega |

O `test.csv` sem rótulos da competição é separado desse teste final. Ele e o exemplo de submissão não participam do treinamento do baseline. O exemplo fornecido tem dez linhas e não é um modelo completo de submissão.

A divisão aleatória pressupõe casos intercambiáveis. Não demonstra generalização para anos futuros, novos empregadores ou outra população. O notebook histórico já explorou a base de origem: o teste está reservado dentro desta reconstrução, mas não é uma nova base externa. Os rótulos são usados na estratificação; variáveis e rótulos do teste final não são enviados à função de treinamento ou cálculo das métricas.

## Protocolo fixo

A [configuração](../configs/baseline.json) define semente 42, cinco folds de treino, limiar 0,5, regularização logística `C=1.0` e F1 macro como métrica principal interna. Não houve busca de parâmetros ou ajuste do limiar.

O baseline de frequência retorna as proporções das classes no treino. A regressão logística usa `lbfgs` com até 2.000 iterações. Imputação, escala e codificação one-hot são ajustadas separadamente dentro de cada fold de treino. Os pipelines finais dos baselines são ajustados somente nos 10.701 casos de treino.

As variáveis numéricas são quantidade de empregados, ano de estabelecimento e salário prevalecente. Os outros sete preditores são categóricos. IDs e alvo nunca entram no pipeline de variáveis. Quantidades negativas de empregados viram valores ausentes e recebem um indicador explícito; a partição de treino contém 13 casos assim. A imputação numérica usa medianas do treino; a categórica usa modas do treino. Categorias desconhecidas são ignoradas pelo codificador one-hot já ajustado.

Os salários mantêm as unidades originais junto da categoria de unidade salarial; não se introduz anualização nem hipótese sobre horas trabalhadas. O baseline pode não capturar bem essas interações. Avisos de falta de convergência interrompem a execução.

## Resultados de validação

A classe 1 significa aprovado; a classe 0, negado. F1 macro dá o mesmo peso ao F1 de cada classe. ROC-AUC usa probabilidades de aprovação.

| Métrica | Baseline de frequência | Regressão logística |
|---|---:|---:|
| F1 macro | 0,400907 | 0,680725 |
| F1 de aprovados | 0,801814 | 0,823848 |
| Acurácia | 0,669190 | 0,744884 |
| Acurácia balanceada | 0,500000 | 0,669900 |
| ROC-AUC | 0,500000 | 0,768863 |
| Precisão média — aprovados | 0,669190 | 0,858658 |
| Brier score, menor é melhor | 0,221375 | 0,177887 |
| Precisão — negados | 0,000000 | 0,671320 |
| Recall — negados | 0,000000 | 0,448305 |

![Métricas de validação](baseline/validation-baselines.png)

Matriz de confusão da regressão logística; linhas representam classes observadas e colunas representam previsões:

| Observado / previsto | Negado | Aprovado |
|---|---:|---:|
| Negado | 529 | 651 |
| Aprovado | 259 | 2.128 |

O baseline de frequência aprova todos os casos e, portanto, não identifica nenhuma negativa. Seu F1 de aprovados já é 0,802. A regressão logística melhora a discriminação, mas ainda deixa de identificar 55,2% das negativas nesse limiar. Esses erros orientam o desenvolvimento; não demonstram adequação a um uso real.

## Validação cruzada no treino

Resultados da regressão logística em cinco folds, antes do ajuste na partição inteira de treino:

| Métrica | Média | Desvio padrão entre folds |
|---|---:|---:|
| F1 macro | 0,676288 | 0,009712 |
| F1 de aprovados | 0,818215 | 0,007362 |
| Acurácia balanceada | 0,666440 | 0,008580 |
| ROC-AUC | 0,772985 | 0,013118 |

Os desvios descrevem a variação entre esses folds; não são intervalos de confiança. Os resultados de cada fold, todas as métricas de validação, hashes de composição das partições, hashes do código e versões das dependências estão no [relatório JSON](baseline/metrics.json).

## Reprodução e limites

Siga os [comandos do README](../README.pt-BR.md). O ambiente registrado usa Python 3.11.14 no Windows, o arquivo de dependências fixadas e uma thread numérica. Os 17 testes automatizados usam entradas sintéticas, incluindo uma execução completa em que a partição reservada contém somente IDs. A serialização dos pipelines reproduziu probabilidades idênticas em três casos de validação por modelo. Pequenas diferenças numéricas podem ocorrer entre plataformas.

O notebook original permanece intacto. Seus resultados usam outro processo de avaliação e não demonstram melhoria por comparação direta com este relatório. A variante oficial de F1 e a posição no ranking da competição seguem sem verificação.

Próxima entrega: comparar poucos candidatos, selecionar eventual limiar nos dados de desenvolvimento e documentar a relação entre os tipos de erro. A avaliação do teste final acontece somente depois dessas escolhas. Avaliação de calibração, análise por segmentos e validação para uso em produção continuam pendentes. Este é um estudo de classificação histórica, sem validação para decisões de imigração.

Referências metodológicas: [orientações do scikit-learn sobre vazamento de dados](https://scikit-learn.org/stable/common_pitfalls.html), [métricas de classificação](https://scikit-learn.org/stable/modules/model_evaluation.html).