# Protocolo de seleção de modelos

[English](SELECTION-PROTOCOL.md) | **Português**

Registrado antes do experimento de candidatos da etapa 2.3, após a análise dos baselines fixos. A [configuração](../configs/selection.json) define o orçamento completo da busca.

1. Reutilizar a composição registrada de treino/validação/teste e o hash dos dados. Não calcular métricas nem explorar variáveis do teste final.
2. Comparar sete configurações: regressão logística com C = 0,1, 1, 10; florestas aleatórias com 200 árvores, mínimo de 5 casos por folha e profundidade máxima 10 ou ilimitada; gradient boosting por histogramas com 200 iterações, taxa de aprendizado 0,05, mínimo de 20 casos por folha, L2 = 1 e 15 ou 31 folhas. Desativar parada antecipada do boosting. Semente 42, uma thread numérica.
3. Reutilizar regras de domínio, imputação, escala e codificação one-hot do baseline, ajustadas dentro dos folds. Pipelines de árvores usam saída one-hot densa; sem novas variáveis ou normalização salarial.
4. Usar os mesmos cinco folds estratificados de treino nas sete configurações (35 ajustes). Selecionar a maior média de F1 macro na validação cruzada, com limiar 0,5. Empates dentro de 1e-12 usam a ordem das configurações. Publicar todos os candidatos e resultados por fold; desvios padrão são descritivos, não intervalos de confiança. A seleção torna otimista o escore de validação cruzada do vencedor.
5. Ajustar somente a configuração selecionada nos 10.701 casos de treino. Usar os 3.567 casos de validação para escolher entre 25 limiares de 0,20 a 0,80, passo 0,025. Maximizar F1 macro; empates dentro de 1e-12 favorecem o limiar mais próximo de 0,5 e depois o menor limiar. Prever aprovação quando sua probabilidade for maior ou igual ao limiar.
6. Apresentar o modelo selecionado com limiar 0,5 e com o escolhido, incluindo matrizes de confusão e recall/precisão das duas classes. Métricas da validação usada na escolha do limiar são estimativas de desenvolvimento com viés de seleção, não estimativas finais de generalização. F1 macro é objetivo interno, não métrica confirmada da competição ou custo de negócio.
7. Congelar o pipeline selecionado, treinado somente no treino, e o limiar para a etapa 2.4. Não reajustar na validação antes da avaliação final, pois isso pode alterar as probabilidades. Preservar intacto o relatório dos baselines fixos. Não ampliar a busca em resposta aos resultados.

Testes usam dados sintéticos. Publicar resultados agregados, configuração, hashes das fontes e gráficos; manter dados brutos, identificadores e pipelines serializados somente no ambiente local.

Referências: [ajuste do limiar](https://scikit-learn.org/stable/modules/classification_threshold.html), [floresta aleatória](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html), [gradient boosting por histogramas](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html).