# Executar inferência

[English](INFERENCE.md) | **Português**

O comando de previsão carrega um pipeline confiável, valida a decisão correspondente e aplica o limiar de aprovação **0,60**. Ele não ajusta modelos nem avalia o teste final.

## Experimentar a entrada pública sem modelo

Instale o ambiente fixado do [README](../README.pt-BR.md) e execute na raiz do repositório com o Python desse ambiente:

```text
python -m topvistos.predict --input examples/synthetic_cases.csv --check-input
```

O comando verifica três casos inteiramente fictícios e retorna `input_valid: true`, sem precisar dos arquivos da competição ou de um modelo serializado. Não faz previsões.

O [CSV de entrada](../examples/synthetic_cases.csv) e o [CSV ilustrativo de previsões](../examples/synthetic_predictions.csv) são públicos. Contêm identificadores e variáveis inventados, sem copiar casos da competição. O terceiro caso exercita intencionalmente uma categoria desconhecida, quantidade negativa de empregados e salário ausente. Não há rótulos verdadeiros e esses exemplos não demonstram desempenho preditivo.

## Prever com o artefato registrado

Com seu artefato local confiável disponível no caminho exemplificado:

```text
python -m topvistos.predict --input examples/synthetic_cases.csv --model reports/generated/selection-verified/selected_pipeline.joblib --output reports/generated/inference/example.csv
```

A decisão padrão é [a decisão registrada](selection/decision.json). O comando verifica hashes das fontes de treinamento, versões das dependências, hash do artefato, classe do modelo, parâmetros selecionados e ordem das colunas de probabilidade antes das previsões. O artefato usado no estudo publicado não é distribuído pelo Git.

Colunas de saída:

| Coluna | Significado |
|---|---|
| `id_do_caso` | Identificador de entrada, preservando a ordem |
| `approval_probability` | Probabilidade do modelo para o rótulo histórico aprovado |
| `predicted_status` | Aprovado se probabilidade >= 0,60; caso contrário Negado |
| `decision_threshold` | Limiar aplicado |
| `artifact_origin` | recorded se os bytes correspondem ao artefato histórico; rebuilt nos demais casos |

O comando exige IDs de texto únicos e não vazios, seguidos exatamente pelas dez variáveis documentadas, na ordem do exemplo. Coluna de alvo, cabeçalhos duplicados, linhas malformadas e números inválidos são rejeitados. Células vazias nas variáveis representam ausências; categorias desconhecidas seguem o comportamento do pipeline existente. Arquivos de saída existentes nunca são sobrescritos.

## Artefatos reconstruídos e artefato histórico

Leitores com acesso autorizado aos dados podem reproduzir o desenvolvimento usando os comandos documentados de baseline/seleção. Um pipeline recém-serializado pode ter bytes diferentes entre ambientes. Para inferência com um pipeline reconstruído localmente, informe sua decisão correspondente:

```text
python -m topvistos.predict --input examples/synthetic_cases.csv --model reports/generated/selection/selected_pipeline.joblib --decision reports/generated/selection/decision.json --output reports/generated/inference/rebuilt-example.csv
```

Somente o hash dos bytes do artefato pode diferir da decisão registrada: configuração escolhida, limiar, hashes das fontes de treinamento, hash dos dados e identidade das partições devem corresponder. A saída identifica explicitamente bytes diferentes como `rebuilt`. Isso verifica compatibilidade para inferência, sem provar previsões idênticas ou produzir nova avaliação. As verificações da [avaliação final](EVALUATION.pt-BR.md) continuam estritas e intactas.

Carregue modelos e arquivos de decisão apenas de fonte confiável. Um hash correspondente verifica a associação entre arquivos; não torna seguro um artefato baseado em pickle. Veja as [orientações de persistência do scikit-learn](https://scikit-learn.org/stable/model_persistence.html).

## Escopo da verificação

A suíte usa dados artificiais, sem a base da competição. Cobre igualdade no limiar, ordem dos IDs, ausências/categorias desconhecidas, erros de esquema, divergência de artefatos e preservação da saída. A validação de entrada pela CLI está incluída na suíte automatizada.

Um checkout separado e um ambiente Python novo são usados para verificar a entrada pública e a previsão com o artefato congelado existente. Isso não repete treinamento, seleção de candidatos ou avaliação final na base original.

As previsões modelam rótulos históricos, sem validação para determinar elegibilidade a vistos ou decisões individuais de imigração. Consulte o [relatório final](EVALUATION.pt-BR.md) para erros, calibração e limitações por segmentos.