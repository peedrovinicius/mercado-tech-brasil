# Visão técnica

## Objetivo

Transformar fontes públicas de emprego formal em indicadores de tecnologia com rastreabilidade suficiente para reproduzir cada resultado a partir do arquivo de origem.

## Componentes

### Ingestão
Obtém ou recebe o arquivo oficial, preserva a origem na Bronze e gera o manifesto de proveniência.

### Transformação
Aplica normalização, tipagem, regras de qualidade e recorte CBO. Registros que falham nas regras são preservados separadamente.

### Agregação
Produz artefatos Gold por competência, UF e ocupação.

### Gate de publicação
Combina checks automáticos e revisão metodológica. A aprovação é vinculada ao SHA-256 do arquivo MOV; trocar a origem invalida a aprovação anterior.

### Serving
Competências aprovadas podem ser carregadas no PostgreSQL por uma operação transacional e idempotente.

### API e frontend
FastAPI expõe contratos versionados. React consome apenas a API e mantém estados explícitos para dados ainda não publicados.

## Decisões principais

- Parquet para armazenamento analítico;
- Polars para transformação;
- DuckDB para análise e validação local;
- PostgreSQL somente para agregados publicados;
- FastAPI para contratos HTTP e OpenAPI;
- React + TypeScript para a interface;
- microdados brutos fora do Git;
- CI sem processamento de bases completas.

## Garantias de integridade

- SHA-256 da origem;
- detecção de schema drift;
- rejeições auditáveis;
- recorte CBO versionado;
- metodologia documentada;
- gate antes do serving;
- constraints no banco;
- testes de aritmética e reconciliação.

## Estado dos dados

A aplicação pública já contém referência oficial agregada de julho de 2026. O recorte tech da mesma competência ainda não é publicado porque o microdado bruto precisa passar pelo pipeline completo e pela validação metodológica.
