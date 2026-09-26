# ADR 0001: Usar DuckDB e Polars antes de Spark

**Status:** Aceito

## Contexto

O projeto processa microdados públicos de grande volume. A arquitetura deve permanecer simples enquanto o processamento local atender ao tempo e à memória definidos para a operação.

## Decisão

A arquitetura usa:

- Parquet para armazenamento colunar;
- Polars para transformação;
- DuckDB para consultas analíticas locais;
- PostgreSQL para servir agregados Gold.

## Efeitos

- menos infraestrutura;
- desenvolvimento local simples;
- menor custo;
- pipeline reproduzível;
- testes rápidos;
- adoção de processamento distribuído condicionada a benchmark reproduzível.

## Critério de evolução

Spark entra quando benchmark demonstrar ganho necessário de processamento distribuído para o volume operacional.
