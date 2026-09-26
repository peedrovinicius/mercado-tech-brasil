# Roadmap

## Atual

### Primeira competência tech publicada
- processar o CAGEDMOV oficial;
- revisar schema, rejeições e salários;
- validar FOR/EXC;
- executar reconciliação;
- aprovar a competência pelo gate;
- carregar PostgreSQL;
- liberar indicadores no dashboard.

## Próxima etapa

### Histórico incremental
- processar competências anteriores e posteriores;
- séries mensais;
- variação mês contra mês;
- variação ano contra ano;
- atualização incremental.

### Geografia
- códigos municipais oficiais;
- indicadores por município;
- integração territorial do IBGE;
- métricas por 100 mil habitantes.

### Remuneração real
- integração IPCA/IBGE;
- salário de admissão corrigido pela inflação;
- comparação temporal em valores reais.

## Expansões

### RAIS
Adicionar estoque anual de vínculos para complementar os fluxos mensais do Novo CAGED.

### QBQ
Associar ocupações a conhecimentos, habilidades e atitudes quando a fonte oficial for incorporada ao modelo.

## Critério de inclusão

Novas métricas entram no produto somente quando possuem:

1. fonte identificada;
2. regra de transformação documentada;
3. teste;
4. período de referência;
5. comportamento definido para dados ausentes ou inconsistentes.
