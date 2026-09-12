# Avaliação final dos modelos congelados

[English](EVALUATION.md) | **Português**

O boosting selecionado alcançou **F1 macro de 0,701** nos **3.568 casos do teste final**, com intervalo bootstrap de 95% de **0,686–0,717**. O baseline logístico alcançou 0,672. O modelo selecionado e seu limiar de aprovação de 0,60 foram definidos antes da avaliação.

A melhoria na métrica geral convive com grandes diferenças nos erros entre grupos de escolaridade. É uma evidência para um estudo delimitado de classificação histórica, sem validação para decisões individuais de visto.

## Desenho da avaliação

O [protocolo](EVALUATION-PROTOCOL.pt-BR.md) e a [configuração](../configs/evaluation.json) foram registrados no commit `096312f` antes das métricas finais. Os 10.701 casos de treino e os 3.567 de validação não foram adicionados à avaliação final. O teste contém 1.180 casos negados e 2.388 aprovados.

As verificações dos artefatos, fontes de treinamento, dependências e dados passaram. Os três pipelines foram carregados dos artefatos já treinados. Não houve treinamento, busca de limiar ou ajuste de calibração. Os relatórios anteriores de [baseline](BASELINE.pt-BR.md) e [seleção](SELECTION.pt-BR.md) permanecem intactos como etapas históricas.

## Resultados finais

| Métrica no teste | Frequência / 0,50 | Logística / 0,50 | Boosting selecionado / 0,60 |
|---|---:|---:|---:|
| F1 macro | 0,400940 | 0,671587 | 0,701240 |
| F1 de aprovados | 0,801880 | 0,817016 | 0,808335 |
| Acurácia | 0,669283 | 0,735987 | 0,739630 |
| Acurácia balanceada | 0,500000 | 0,661937 | 0,698311 |
| ROC-AUC | 0,500000 | 0,761702 | 0,772532 |
| Brier score, menor é melhor | 0,221343 | 0,180478 | 0,174730 |
| Recall de negados | 0,000000 | 0,443220 | 0,576271 |
| Precisão de negados | 0,000000 | 0,647277 | 0,613165 |
| Recall de aprovados | 1,000000 | 0,880653 | 0,820352 |

Matriz de confusão do modelo selecionado:

| Observado / previsto | Negado | Aprovado |
|---|---:|---:|
| Negado | 680 | 500 |
| Aprovado | 429 | 1.959 |

Em relação à regressão logística, o selecionado identifica **157 negativas adicionais** e prevê **144 casos aprovados adicionais como negados**. Seu F1 de aprovados é menor. O resultado atende ao objetivo declarado de F1 macro, sem representar melhoria em todas as métricas.

A diferença pareada de F1 macro é **+0,02965**, com intervalo percentil de 95% de **+0,01675 a +0,04142**. Esse intervalo fica acima de zero sob as premissas de reamostragem registradas. O ROC-AUC do selecionado tem intervalo 0,755–0,789; o Brier score, 0,169–0,181.

As 1.000 amostras bootstrap usam os mesmos casos reamostrados nos três modelos e preservam as contagens das classes. Os intervalos são condicionados aos modelos ajustados e às contagens; não abrangem incerteza de treinamento/seleção ou mudança de distribuição. O intervalo do F1 macro do baseline constante se reduz a um ponto porque suas previsões e as contagens reamostradas são fixas.

![Comparação final e calibração](evaluation/evaluation.png)

## Calibração

O ECE com dez faixas é **0,01476**. É uma medida descritiva, dependente das faixas; não certifica calibração de probabilidades individuais. Brier combina aspectos de calibração e discriminação.

Na faixa [0,8; 0,9), os 660 casos têm probabilidade média prevista de aprovação de **85,1%**, contra **81,5%** de aprovações observadas (Wilson 95%: 78,4–84,3%). A faixa de menor probabilidade tem somente dois casos e intervalo muito amplo. Nenhum calibrador foi ajustado após essas observações.

## Erros escondidos pela métrica geral

Todos os grupos predefinidos e seus suportes estão no [apêndice de segmentos](evaluation/SEGMENTS.pt-BR.md), com intervalos dos dois recalls e motivos de supressão.

- Em `Doutorado`, o modelo identifica somente **4 dos 45 casos negados**: recall de negativas de **8,9%** (Wilson 95%: 3,5–20,7%).
- Em `Ensino Médio`, identifica **301 dos 310 casos negados**, mas somente **16 dos 170 aprovados**: recall de aprovados de **9,4%**.
- Para salários por hora (`Hora`), o recall de aprovados é **21,9%**, contra **84,9%** nos salários anuais (`Ano`).
- Cinco categorias não atendem ao suporte mínimo: África, Oceania, região de emprego Ilha, salários mensais e semanais. As contagens são publicadas; as estimativas de desempenho são omitidas.

Essas associações se referem a esta base histórica e ao modelo ajustado. Os grupos diferem na proporção das classes e em outras características, se sobrepõem entre dimensões e não tiveram correção para comparações múltiplas. A análise não identifica causas nem estabelece equidade ou discriminação como conclusão jurídica ou causal.

## Artefatos e reprodução

O [relatório JSON](evaluation/metrics.json) registra métricas, intervalos, faixas de calibração, segmentos, ambiente e hashes. Os testes usam dados sintéticos; **34 testes passaram localmente**. A validação pelo GitHub Actions depende da publicação.

Siga as [instruções do ambiente](../README.pt-BR.md). Com os artefatos congelados registrados nas pastas de saída padrão:

```text
python -m topvistos.evaluation
```

Use o Python do ambiente virtual. Os caminhos podem ser informados por `--selection-dir`, `--baseline-dir`, `--data-dir` e `--output-dir`. A avaliação exige os hashes dos binários registrados e as versões das dependências; falha deliberadamente quando artefatos reconstruídos diferem. Binários e dados brutos não são redistribuídos. Os comandos de treinamento permitem reconstruir modelos, mas binários idênticos não são garantidos entre ambientes.

O comando salva métricas agregadas, gráfico e cache privado de previsões em `reports/generated/evaluation/`, ignorada pelo Git. Ele recusa uma pasta de saída existente. Consulte os resultados salvos em vez de repetir avaliações para orientar ajustes.

**O teste final agora foi consumido.** Desenvolvimento posterior do modelo exige novo desenho de avaliação. A divisão aleatória por caso e a exposição histórica limitam a conclusão; não demonstram desempenho para futuros solicitantes, novos empregadores ou outra população. Métrica oficial e posição no ranking da competição seguem sem verificação.

Próxima entrega: finalizar exemplo de inferência, documentação e execução em um checkout limpo. Modelo e limiar continuam fixos.

Referências metodológicas: [calibração de probabilidades](https://scikit-learn.org/stable/modules/calibration.html), [intervalos por bootstrap](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html).