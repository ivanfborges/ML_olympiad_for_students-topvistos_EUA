# ML_olympiad_for_students-topvistos_EUA
Preveja a aprovação de vistos de trabalho dos EUA nessa competição de Machine Learning proposta pelo Kaggle. Será que você acerta?

Description
Contexto:
As comunidades empresariais nos Estados Unidos enfrentam uma alta demanda por recursos humanos, mas um dos desafios constantes é identificar e atrair o talento certo, que é talvez o elemento mais importante para se manter competitivo. Empresas nos Estados Unidos procuram indivíduos trabalhadores, talentosos e qualificados tanto localmente quanto no exterior.

A Lei de Imigração e Nacionalidade (INA) dos EUA permite que trabalhadores estrangeiros venham trabalhar nos Estados Unidos temporária ou permanentemente. A lei também protege os trabalhadores americanos contra impactos adversos em seus salários ou condições de trabalho, garantindo que os empregadores americanos cumpram os requisitos legais ao contratar trabalhadores estrangeiros para suprir a escassez de mão de obra. Os programas de imigração são administrados pelo Escritório de Certificação de Trabalho Estrangeiro (OFLC).

O OFLC processa pedidos de certificação de emprego para empregadores que buscam trazer trabalhadores estrangeiros para os Estados Unidos e concede certificações nos casos em que os empregadores podem demonstrar que não há trabalhadores americanos suficientes disponíveis para realizar o trabalho com salários que atendam ou excedam o salário pago para a ocupação na área de emprego pretendida.

Objetivo:
No ano fiscal de 2016, o OFLC processou 775.979 pedidos de empregadores para 1.699.957 posições de certificações de trabalho temporárias e permanentes. Isso representou um aumento de nove por cento no número total de pedidos processados em relação ao ano anterior. O processo de revisar cada caso está se tornando uma tarefa tediosa à medida que o número de candidatos aumenta a cada ano.

O aumento do número de candidatos a cada ano demanda uma solução baseada em Aprendizado de Máquina que possa ajudar na pré-seleção dos candidatos com maiores chances de aprovação de VISTO. O OFLC contratou sua empresa, TopVistos, para soluções baseadas em dados. Como Cientista de Dados, você deve analisar os dados fornecidos e, com a ajuda de um modelo de classificação:

Facilitar o processo de aprovação de vistos.

Recomendar um perfil adequado para os candidatos para os quais o visto deve ser certificado ou negado, com base nos fatores que influenciam significativamente o status do caso.

Avaliação
F1-Score
A métrica de avaliação para esta competição é a Média do F1-Score. O F1-Score, comumente usado em problemas de classificação, mede a taxa de acertos utilizando as estatísticas de Precisão (p) e Recall (r).

A precisão é a razão dos verdadeiros positivos, ouTrue Positives (tp),
para todos os positivos previstos (tp + fp).

O Recall é a razão dos verdadeiros positivos (tp) para todos os positivos reais (tp + fn).

O F1 score é dado por:


A métrica F1 pondera igualmente o Recall e a Precisão, e um bom algoritmo de classificação maximizará simultaneamente a precisão e o recall. Assim, um desempenho moderadamente bom em ambos será favorecido em relação a um desempenho extremamente bom em um e um desempenho ruim no outro.

Nota: Para maiores informações sobre métricas de performance em modelos de classificação, como o F1-Score, leia o seguinte artigo: https://brains.dev/2023/medidas-de-performance-modelos-de-classificacao/

Formato do Envio
Para cada observação, ou cada aplicação de visto analisada, o arquivo a ser enviado deve conter duas colunas: id_do_caso e status_do_caso.

status_do_caso é sua coluna alvo, a ser prevista pelo modelo. A plataforma irá analisar a sua taxa de acerto de acordo com as previsões do seu modelo nesta coluna.

id_do_caso é a chave primária, identificador único de cada observação. É importante manter essa coluna como primeira do seu arquivo a ser enviado, para que a plataforma saiba que cada predição corresponde a cada observação.

É muito importante manter esta estrutura do arquivo para que o seu modelo seja avaliado corretamente pela plataforma. Note que a coluna alvo (status_do_caso) precisa de um enconding para 0 e 1, onde 0 é um visto "Negado" e 1 um visto "Aprovado".

O arquivo deve manter o seu cabeçalho (header) e deve ter o seguinte formato:

id_do_caso,status_do_caso
EZYV0x,0
Citation
Andre Lopes. (2023). ML Olympiad for Students - TopVistos EUA. Kaggle. https://kaggle.com/competitions/ml-olympiad-for-students-topvistos-eua
