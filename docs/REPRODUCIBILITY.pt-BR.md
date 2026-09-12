# Auditoria de reprodução

[English](REPRODUCIBILITY.md) | **Português**

Revisão de 12/09/2026 sobre o commit `626ae2d4cf12379817d7443c0624ca4d5fd0fb2d`. Esta é uma auditoria estática, sem reexecução.

O notebook original tem 41 células, sendo 32 de código. Seus metadados registram Python 3.10.10; as versões de dependências não estão registradas em um lockfile. Os três CSVs da competição não estavam no repositório no momento da auditoria.

Os índices abaixo começam em zero e indicam a posição no JSON do notebook, independentemente dos contadores salvos de execução.

| Célula(s) | Achado | Correção necessária |
|---|---|---|
| 3, 33 | A leitura de `df_test` está comentada, mas a variável é usada depois. Os caminhos dependem do ambiente Kaggle. | Entradas explícitas e execução em um interpretador limpo. |
| 16, 38 | Codificadores são ajustados em toda a base rotulada e novamente na base de submissão. | Aprender o pré-processamento nos folds de treino e reutilizar os transformadores na avaliação/inferência; tratar categorias desconhecidas. |
| 19 | A divisão aleatória 70/30 não é estratificada. | Definir uma divisão adequada aos rótulos, entidades e uso pretendido; registrar premissas. |
| 21 | A comparação passa previsões antes da referência para precisão/recall; `model_test(x, y)` ignora seus argumentos e usa variáveis globais. | Corrigir a ordem das métricas e usar entradas explícitas. A inversão dos argumentos, isoladamente, não altera F1 binário ou acurácia. |
| 21–30 | A partição chamada `X_test` participa da comparação e da inspeção de parâmetros. | Separar desenvolvimento de teste final reservado. |
| 25 | ROC-AUC recebe classes previstas. | Avaliar ordenação com probabilidades ou escores de decisão. |
| 30 | A busca em grade otimiza acurácia, embora a descrição histórica cite F1. | Confirmar a variante oficial de F1 e alinhar seleção e objetivo. |

## Condições para dados e ambiente

Antes de treinar a nova versão:
- obter `train.csv`, `test.csv` e `sample_submission.csv` originais;
- registrar fonte, data de download, hashes, esquema, quantidade de linhas e unicidade dos IDs;
- conferir separação dos IDs de treino/submissão e correspondência com o modelo de submissão;
- distinguir rótulos originais da codificação para submissão;
- especificar e validar o ambiente a partir de uma instalação limpa.

As saídas históricas registram 17.836 linhas rotuladas e 7.644 linhas de submissão. Os arquivos locais fornecidos pelo autor em 12/09/2026 correspondem a essas contagens; isso não é uma verificação independente contra um novo download oficial.

## Andamento da reconstrução

A inspeção dos dados e a entrega dos baselines fixos estão concluídas. A nova implementação ajusta o pré-processamento dentro dos folds, corrige as entradas das métricas e separa treino, validação e teste final reservado. Veja os resultados medidos no [relatório do baseline](BASELINE.pt-BR.md). Seleção de candidatos e avaliação final continuam pendentes.

O notebook original permanece intacto para permitir distinguir o código histórico da versão reconstruída.

Referências: [boas práticas do scikit-learn](https://scikit-learn.org/stable/common_pitfalls.html), [ROC-AUC](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.roc_auc_score.html).

## Recebimento dos dados concluído

O [manifesto dos dados](data-manifest.json) registra os arquivos fornecidos e seus hashes. A validação estrutural e sete testes isolados passaram. O exemplo de submissão está incompleto e inclui IDs fora do teste; submissões futuras devem usar os identificadores do arquivo de teste.

Os dados continuam locais e excluídos do Git. O novo baseline foi executado em ambiente isolado com Python 3.11.14 e dependências fixadas. Os 17 testes passaram. A validação numérica e o tratamento de quantidades negativas de empregados estão implementados no pipeline. O teste final ainda não foi avaliado.