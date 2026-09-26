# Roadmap

## Operação de dados

- executar a primeira competência completa com MOV, FOR e EXC;
- registrar o relatório de qualidade da execução real;
- concluir a reconciliação com a referência oficial publicada;
- aprovar a competência pelo gate;
- carregar a competência no PostgreSQL gerenciado;
- ativar o backend PostgreSQL na aplicação pública.

## Expansão temporal

- executar competências adicionais;
- consolidar comparação mensal;
- consolidar comparação anual;
- automatizar atualização incremental após publicação oficial.

## Expansão analítica

- incorporar população municipal para indicadores por 100 mil habitantes;
- adicionar RAIS para estoque anual de vínculos;
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
