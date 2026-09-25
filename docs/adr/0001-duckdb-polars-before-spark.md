# ADR 0001 — Usar DuckDB e Polars antes de Spark

**Status:** Aceito

## Contexto

O projeto processa microdados públicos que podem ser grandes, mas ainda não existe evidência de que o volume exija cluster distribuído.

## Decisão

A primeira arquitetura usa:

- Parquet para armazenamento colunar;
- Polars para transformação;
- DuckDB para consultas analíticas locais;
- PostgreSQL apenas para servir agregados Gold.

## Consequências

### Positivas
- menos infraestrutura;
- desenvolvimento local simples;
- menor custo;
- pipeline reproduzível;
- mais fácil de explicar e testar.

### Negativas
- se o volume ou tempo de processamento ultrapassar os limites aceitáveis, será necessário reavaliar.

## Critério para rever

Spark só entra quando benchmark reproduzível demonstrar necessidade de processamento distribuído.
