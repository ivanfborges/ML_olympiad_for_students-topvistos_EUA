# TopVistos EUA — Classificação de resultados de vistos

[English](README.md) | **Português**

Projeto de aprendizado da competição **ML Olympiad for Students — TopVistos EUA**, realizada no Kaggle em 2023. O notebook original explora dados tabulares de solicitações, compara classificadores, ajusta um modelo de gradient boosting e gera previsões para submissão.

## Situação atual

O notebook original está preservado como registro histórico. A revisão de reprodução e avaliação está em andamento; **nenhum novo modelo foi treinado ou avaliado de forma independente nesta revisão**.

O repositório contém o notebook, a documentação e o plano de reconstrução. Os CSVs da competição e um ambiente de treinamento verificado não estão incluídos. As saídas salvas no notebook são observações históricas, não um benchmark recém-reproduzido ou uma pontuação verificada no ranking.

## Por onde começar

- [Notebook original em português](ml-olympiad_top-vistos-eua_solucao.ipynb): exploração, pré-processamento, comparação de modelos, ajuste e submissão.
- [Auditoria de reprodução e próximos passos](docs/REPRODUCIBILITY.pt-BR.md): problemas identificados e critérios para a nova versão.
- [Preparação dos dados](data/README.pt-BR.md): arquivos necessários e organização local.
- [Descrição original da competição](docs/competition-description.pt-BR.md): texto anteriormente publicado neste repositório.

## Problema e escopo

A competição usa o alvo binário `status_do_caso` e o identificador `id_do_caso`. O notebook histórico mapeia `Aprovado` para 1 e `Negado` para 0 no treinamento.

Este é um estudo de classificação de dados históricos. Não é um sistema validado para determinar elegibilidade de vistos ou automatizar decisões de imigração. A avaliação deve considerar limitações dos dados e diferenças dos erros entre grupos relevantes.

## Reconstrução planejada

1. Identificar as bases originais, registrar sua origem e hashes e estabelecer um ambiente limpo.
2. Integrar o pré-processamento ao pipeline de treinamento e reservar uma partição final de teste.
3. Comparar referências simples com poucos modelos candidatos.
4. Selecionar hiperparâmetros e eventual limiar usando apenas dados de desenvolvimento.
5. Apresentar avaliação final, erros por segmento, limitações e inferência reproduzível.

São entregas planejadas, ainda não implementadas. A auditoria distingue o notebook atual da nova versão pretendida.

## Fonte e atribuição

André Lopes. *ML Olympiad for Students — TopVistos EUA* (2023), Kaggle.

[Competição](https://www.kaggle.com/competitions/ml-olympiad-for-students-topvistos-eua)

Obtenha os arquivos originais por uma fonte autorizada e observe as condições de acesso e reutilização da competição. O acesso aos dados e a configuração exata da métrica oficial precisam ser confirmados antes da nova avaliação.