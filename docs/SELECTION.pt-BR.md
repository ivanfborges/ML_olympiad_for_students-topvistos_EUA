# Seleção de modelo e limiar

[English](SELECTION.md) | **Português**

**Configuração selecionada:** gradient boosting por histogramas com 15 folhas, 200 iterações, taxa de aprendizado 0,05 e regularização L2 igual a 1. O limiar de aprovação escolhido é **0,60**. O pipeline treinado usa somente a partição de treino; o teste final não foi avaliado.

O [protocolo](SELECTION-PROTOCOL.pt-BR.md) e a [configuração completa](../configs/selection.json) foram registrados no commit `afe309f` antes da execução dos candidatos. A busca de sete configurações não foi ampliada após observar os resultados.

## Comparação de candidatos

Todos os candidatos usaram os mesmos 10.701 casos de treino e cinco folds estratificados. A seleção maximizou a média de F1 macro com limiar 0,5. São resultados de validação cruzada no treino, não da partição de validação ou do teste final.

| Configuração | Média de F1 macro | Desvio entre folds | Média de ROC-AUC |
|---|---:|---:|---:|
| Logística, C = 0,1 | 0,674898 | 0,009782 | 0,773049 |
| Logística, C = 1 | 0,676288 | 0,009712 | 0,772985 |
| Logística, C = 10 | 0,676502 | 0,009598 | 0,772905 |
| Floresta, profundidade 10 | 0,690604 | 0,011511 | 0,784493 |
| Floresta, profundidade ilimitada | 0,691249 | 0,012600 | 0,782031 |
| **Boosting, 15 folhas** | **0,694191** | **0,010330** | **0,781803** |
| Boosting, 31 folhas | 0,686624 | 0,012289 | 0,777433 |

A floresta de profundidade 10 teve a maior média de ROC-AUC, mas o boosting venceu pelo critério declarado de F1 macro. Os desvios entre folds são descritivos; essas diferenças não comprovam significância estatística. O escore de validação cruzada do vencedor é otimista porque ele foi escolhido entre sete candidatos.

## Limiar e erros

Somente a configuração vencedora foi ajustada em todo o treino. Foram avaliados 25 limiares nos 3.567 casos de validação. Probabilidade maior ou igual ao limiar prevê aprovação. O maior F1 macro da grade ocorreu em 0,60.

| Medida de validação | Baseline logístico, 0,50 | Boosting escolhido, 0,50 | Boosting escolhido, 0,60 |
|---|---:|---:|---:|
| F1 macro | 0,680725 | 0,694407 | 0,709709 |
| F1 de aprovados | 0,823848 | 0,823344 | 0,813146 |
| ROC-AUC | 0,768863 | 0,776458 | 0,776458 |
| Acurácia | 0,744884 | 0,748809 | 0,746566 |
| Recall de negados | 0,448305 | 0,494068 | 0,589831 |
| Precisão de negados | 0,671320 | 0,660998 | 0,623656 |
| Recall de aprovados | 0,891496 | 0,874738 | 0,824047 |

Elevar o limiar do boosting identificou **113 negativas a mais**, enquanto **121 casos aprovados a mais foram previstos como negados**. F1 de aprovados e acurácia caíram, enquanto F1 macro subiu. A seleção do limiar altera as classes previstas, não a ordenação ou a calibração das probabilidades; ROC-AUC e Brier score permanecem iguais.

Matriz de confusão no limiar selecionado:

| Observado / previsto | Negado | Aprovado |
|---|---:|---:|
| Negado | 696 | 484 |
| Aprovado | 420 | 1.967 |

![Comparação de candidatos e efeito do limiar](selection/selection.png)

O [relatório JSON](selection/metrics.json) contém os escores de cada fold e toda a curva de limiares, incluindo os erros das duas classes. A [decisão congelada](selection/decision.json) registra especificação do modelo, limiar, identidade das partições e checksum do modelo local. Não são publicadas previsões individuais.

## Reprodução e próxima avaliação

Instale o ambiente fixado seguindo o [README](../README.pt-BR.md) e execute:

```text
python -m topvistos.selection
python -m unittest discover -s tests -v
```

Use o executável Python do ambiente virtual. As saídas ficam em `reports/generated/selection/`, ignorada pelo Git. Pipeline, JSON de decisão, métricas e gráfico são gerados juntos. Mantenha o pipeline e seu arquivo de decisão correspondente juntos: `pipeline.predict()` isoladamente usa a regra padrão do estimador, não o limiar selecionado de 0,60.

Os 25 testes cobrem alteração de partições, escolha de modelo somente por validação cruzada, comportamento na probabilidade exata do limiar, desempates, entradas ausentes/desconhecidas e execução completa sem variáveis ou rótulos do teste final. Recarregar o modelo preservou exatamente todas as probabilidades de validação. Ambiente: Python 3.11.14, Windows, mesmo arquivo de dependências fixadas, uma thread numérica.

Os 3.568 casos do teste final continuam reservados para a etapa 2.4. Avaliar o pipeline congelado, ajustado somente no treino, e seu limiar antes de qualquer novo ajuste. As métricas de validação usadas para escolher o limiar têm viés de seleção; não são evidência independente de generalização. F1 macro segue como objetivo interno, sem pressupor custo de negócio ou alegar confirmação da métrica da competição. Avaliação de calibração, análise por segmentos e avaliação final continuam pendentes. A exposição histórica aos dados e as limitações da divisão aleatória descritas no [relatório dos baselines](BASELINE.pt-BR.md) continuam aplicáveis.