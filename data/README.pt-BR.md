# Dados da competição

[English](README.md) | **Português**

Arquivos originais necessários:

| Arquivo | Função |
|---|---|
| `train.csv` | Variáveis, identificador e alvo observado |
| `test.csv` | Variáveis e identificadores para submissão; não é a futura partição rotulada de avaliação |
| `sample_submission.csv` | Exemplo de colunas e codificação; o arquivo fornecido não contém a lista completa de IDs |

Coloque os arquivos em `data/raw/`, após obtê-los na [competição](https://www.kaggle.com/competitions/ml-olympiad-for-students-topvistos-eua) por uma conta/fonte autorizada.

A pasta de dados brutos é ignorada pelo Git. Este repositório não redistribui os arquivos. Não adicione credenciais de conta ou tokens.

Se os arquivos originais estiverem indisponíveis, registre essa limitação antes de escolher outra base. Uma base semelhante não comprova reprodução do resultado da competição.

Próximo passo: validar origem, esquema, IDs, rótulos e hashes antes de instalar e executar o novo ambiente de treinamento.

## Arquivos fornecidos

Em 12/09/2026, o autor forneceu arquivos locais: 17.836 linhas de treino, 7.644 de teste da competição e dez de exemplo de submissão. Seis IDs do exemplo não ocorrem no test.csv. Use o test.csv como fonte dos identificadores para a saída de predição.

Veja o [manifesto agregado](../docs/data-manifest.json). Para regenerá-lo localmente:

```text
python scripts/inspect_data.py --output reports/generated/data-manifest.json
```

Não são publicados registros individuais nem caminhos locais de origem.