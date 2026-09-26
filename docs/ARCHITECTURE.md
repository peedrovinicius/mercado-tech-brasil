# Arquitetura

## Visão geral

~~~mermaid
flowchart LR
    A["Fontes oficiais"] --> B["Bronze"]
    B --> C["Silver"]
    C --> D["Gold"]
    D --> E["Arquivos publicados"]
    D --> P["PostgreSQL opcional"]
    D --> F["DuckDB"]
    E --> G["FastAPI"]
    P --> G
    G --> H["React"]
~~~

## Bronze

Preserva o arquivo recebido da fonte oficial.

Cada ingestão registra:

- origem;
- competência;
- nome original;
- timestamp;
- tamanho;
- SHA-256.

A camada Bronze não é usada diretamente pela interface.

## Silver

Normaliza o microdado para processamento analítico:

- nomes de colunas;
- tipos;
- CBO;
- território;
- salário;
- flags de qualidade;
- registros rejeitados.

O formato principal é Parquet.

## Gold

Contém somente agregados derivados da Silver e prontos para serving.

O escopo atual implementado inclui:

- overview da competência;
- indicadores por UF;
- indicadores por família e ocupação CBO;
- indicadores por município;
- comparação territorial Brasil, Nordeste e Ceará;
- série histórica por competência;
- métricas nominais e reais de remuneração de admissão.

## PostgreSQL

O PostgreSQL recebe somente competências aprovadas.

A carga é:

- transacional;
- idempotente por competência;
- protegida pelo gate de publicação;
- vinculada ao SHA-256 da origem.

## DuckDB e Polars

Polars executa as transformações colunares e DuckDB apoia consultas e validações locais.

Spark não faz parte da arquitetura atual porque a complexidade distribuída não é necessária para o volume e o modo de execução previstos. A adoção de processamento distribuído depende de benchmark.

## API

FastAPI expõe:

- health e readiness;
- metadados e fontes;
- qualidade;
- proveniência;
- indicadores;
- analytics por UF, município e ocupação;
- comparação territorial;
- série histórica.

A API pública é versionada em /api/v1.

## Frontend

React + TypeScript consome exclusivamente os contratos da API.

A interface distingue:

- contexto oficial agregado do mercado formal;
- indicadores do recorte tech;
- estado de dados não publicados;
- qualidade e proveniência.

## Produção

A aplicação pública usa um único serviço Docker no Render:

~~~text
Render
+-- FastAPI
    +-- /api/v1
    +-- /docs
    +-- / -> frontend/dist
    +-- data/gold -> serving ativo
~~~

A configuração versionada usa DATA_BACKEND=files em produção. O PostgreSQL permanece implementado como backend alternativo e pode ser ativado por configuração quando a operação exigir serving em banco.
