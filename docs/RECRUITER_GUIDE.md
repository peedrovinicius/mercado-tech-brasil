# Visão rápida para avaliação técnica

Este documento existe para permitir que uma pessoa avaliadora entenda o projeto em poucos minutos.

## O problema

Dados públicos de emprego formal são volumosos e pouco amigáveis para comparação direta. O projeto transforma esses microdados em indicadores auditáveis sobre ocupações de tecnologia.

## O que este projeto demonstra

### Engenharia de dados
- ingestão reprodutível;
- camadas Bronze/Silver/Gold;
- Parquet;
- validação de qualidade;
- rastreabilidade SHA-256;
- processamento incremental planejado.

### Backend
- API REST com FastAPI;
- OpenAPI/Swagger;
- versionamento `/api/v1`;
- health/readiness endpoints;
- separação por routers e configuração.

### Banco de dados
- PostgreSQL;
- modelo dimensional;
- constraints e índices;
- serving de tabelas agregadas.

### Engenharia de software
- testes unitários;
- lint;
- CI leve;
- Docker;
- documentação de arquitetura;
- ADRs para decisões técnicas.

## Como verificar rapidamente

1. `pip install -e ".[dev]"`
2. `pip install httpx`
3. `pytest -q`
4. `uvicorn src.api.main:app --reload`
5. abrir `/docs`
6. consultar `/api/v1/metadata/sources`
7. consultar `/api/v1/system/readiness`

O endpoint de indicadores retorna 503 enquanto não houver dados oficiais processados. Isso é intencional: o projeto nunca usa valores fictícios para parecer completo.

## Decisões técnicas que valem discussão em entrevista

- Por que DuckDB/Polars antes de Spark?
- Por que PostgreSQL recebe agregados Gold em vez de todos os microdados?
- Como garantir que uma atualização do layout oficial não corrompa indicadores silenciosamente?
- Como versionar o recorte CBO de tecnologia?
- Como separar fluxo de emprego de estoque de vínculos?
- Como tornar comparações municipais mais justas usando população?
