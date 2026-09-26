# Roadmap

## Base operacional concluída

A base necessária para publicar e auditar o produto está implementada:

- ingestão de MOV, FOR e EXC;
- Bronze, Silver e Gold;
- manifesto e SHA-256 da origem;
- detecção de mudança de layout;
- recorte CBO versionado;
- reconciliação nacional por competência;
- gate de publicação;
- ajustes FOR e EXC aplicados às competências de origem;
- enriquecimento municipal;
- salário real por IPCA;
- série histórica de janeiro a julho de 2026;
- serving por arquivos e PostgreSQL;
- API FastAPI e frontend React;
- comparação Brasil, Nordeste e Ceará;
- consolidação trimestral com identificação de períodos parciais;
- integração SIDRA para população municipal e cálculo por 100 mil no Gold;
- ranking municipal normalizado no frontend, ativado somente quando há denominador publicado;
- descoberta e ingestão Bronze auditável dos microdados anuais da RAIS;
- extração RAIS compatível com arquivos .comt, .txt e .csv;
- inspeção de schema anual com assinatura SHA-256 do cabeçalho;
- publicação pública no Render.

## Próximas entregas

### Atualização incremental

- automatizar a preparação da próxima competência após a publicação oficial;
- manter validação explícita da referência do MTE antes da liberação;
- preservar a publicação somente após aprovação do gate;
- ampliar testes de regressão da série histórica.

### Expansão temporal

- incorporar novas competências sem alterar a metodologia já publicada;
- consolidar comparações anuais quando houver cobertura suficiente;
- documentar revisões oficiais que alterem competências anteriores.

### Expansão analítica

- acompanhar a primeira competência Gold enriquecida com população no fluxo de publicação;
- validar semanticamente o relatório de layout RAIS 2025 contra o dicionário oficial;
- construir Silver e Gold de estoque anual somente após essa validação;
- reconciliar o estoque RAIS com referências anuais oficiais antes da publicação;
- avaliar QBQ para atributos ocupacionais;
- ampliar comparações territoriais e ocupacionais mantendo a mesma governança.

## Critério de inclusão

Uma nova métrica entra no produto quando possui:

1. fonte identificada;
2. regra de transformação documentada;
3. teste;
4. período de referência;
5. comportamento definido para ausência e inconsistência;
6. contrato de API compatível com a governança de publicação.
