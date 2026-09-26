<div align="center">

# Mercado Tech Brasil

Plataforma de dados para análise do mercado formal de trabalho em tecnologia no Brasil com fontes públicas oficiais, rastreabilidade e metodologia versionada.

[![CI](https://github.com/peedrovinicius/mercado-tech-brasil/actions/workflows/ci.yml/badge.svg)](https://github.com/peedrovinicius/mercado-tech-brasil/actions/workflows/ci.yml)
[![Frontend](https://github.com/peedrovinicius/mercado-tech-brasil/actions/workflows/frontend.yml/badge.svg)](https://github.com/peedrovinicius/mercado-tech-brasil/actions/workflows/frontend.yml)
[![Production](https://img.shields.io/badge/production-live-2ea44f)](https://mercado-tech-brasil.onrender.com)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)

[Aplicação](https://mercado-tech-brasil.onrender.com) · [Swagger](https://mercado-tech-brasil.onrender.com/docs) · [Health](https://mercado-tech-brasil.onrender.com/api/v1/system/health)

</div>

## Produto

O Mercado Tech Brasil transforma dados públicos do trabalho formal em uma cadeia auditável de ingestão, validação, transformação, serving e visualização.

<table>
<tr>
<td><strong>Rastreabilidade</strong><br/>Manifesto, competência, origem e SHA-256 por arquivo.</td>
<td><strong>Reprodutibilidade</strong><br/>Recorte CBO, metodologia e regras versionadas.</td>
<td><strong>Publicação controlada</strong><br/>Dados chegam ao serving somente após validação.</td>
</tr>
</table>

## Snapshot publicado

**Competência: julho de 2026**

<table>
<tr>
<td><strong>19.253</strong><br/>admissões tech</td>
<td><strong>18.347</strong><br/>desligamentos tech</td>
<td><strong>+906</strong><br/>saldo</td>
<td><strong>R$ 3.990,06</strong><br/>salário mediano de admissão</td>
</tr>
</table>

A primeira competência real foi processada a partir dos microdados oficiais do Novo CAGED. O MOV de julho contém 4.467.208 registros e reconciliou exatamente com os totais nacionais publicados pelo MTE. O recorte tech contém 37.600 movimentações e 1.274 municípios identificados pela referência do IBGE.

**SHA-256 do MOV:** `07b580d8d6da65ed9b87f693262981027e417ab56a111301494ee5532983475f`

## Arquitetura

~~~mermaid
flowchart LR
    A["Fontes oficiais<br/>MTE · CBO · IBGE"] --> B["Bronze<br/>arquivo original + SHA-256"]
    B --> C["Silver<br/>normalização + qualidade"]
    C --> D["Gold<br/>agregados reproduzíveis"]
    D --> E["PostgreSQL<br/>serving"]
    D --> F["DuckDB<br/>validação local"]
    E --> G["FastAPI<br/>API + OpenAPI"]
    G --> H["React + TypeScript<br/>dashboard"]

    classDef source fill:#f2f5ff,stroke:#8ea6ff,color:#15245c
    classDef data fill:#f7f7f8,stroke:#bfc1c8,color:#25262b
    classDef serving fill:#eef9f2,stroke:#75b98b,color:#184d2c
    class A source
    class B,C,D,F data
    class E,G,H serving
~~~

### Fluxo de publicação

~~~mermaid
flowchart LR
    A["Microdado oficial"] --> B["Ingestão"]
    B --> C["Validação de schema"]
    C --> D["Rejeições auditáveis"]
    D --> E["Agregações Gold"]
    E --> F["Gate automático"]
    F --> G["Revisão metodológica"]
    G --> H["PostgreSQL + API"]
~~~

## Stack

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![Polars](https://img.shields.io/badge/Polars-data-6B5BFF)
![DuckDB](https://img.shields.io/badge/DuckDB-analytics-FFF000?logo=duckdb&logoColor=000)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-serving-4169E1?logo=postgresql&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-frontend-61DAFB?logo=react&logoColor=000)
![TypeScript](https://img.shields.io/badge/TypeScript-frontend-3178C6?logo=typescript&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-runtime-2496ED?logo=docker&logoColor=white)

</div>

| Camada | Tecnologias |
|---|---|
| Dados | Python, Polars, DuckDB, Parquet, Pandera |
| Banco | PostgreSQL, SQLAlchemy, Alembic |
| API | FastAPI, Pydantic, OpenAPI |
| Frontend | React, TypeScript, Vite, TanStack Query, ECharts |
| Qualidade | Pytest, Ruff |
| Infraestrutura | Docker, GitHub Actions, Render |

## Fontes

| Fonte | Uso |
|---|---|
| Novo CAGED, MTE | admissões, desligamentos, saldo e remuneração de admissão |
| CBO, MTE | definição versionada das ocupações de tecnologia |
| IBGE | municípios, território e IPCA para valores reais |

A referência oficial de julho de 2026 está versionada em **config/official_reference_202607.json**.

## Recorte de tecnologia

O recorte é ocupacional e está versionado em **config/cbo_tech.yml**.

| Família CBO | Denominação |
|---|---|
| 2122 | Engenheiros em computação |
| 2123 | Administradores de tecnologia da informação |
| 2124 | Analistas de tecnologia da informação |
| 3171 | Técnicos de desenvolvimento de sistemas e aplicações |
| 3172 | Técnicos em operação e monitoração de computadores |

A justificativa e as regras de governança estão em [docs/CBO_SCOPE.md](docs/CBO_SCOPE.md).

## Qualidade e governança

O pipeline mantém:

- Bronze imutável com manifesto e SHA-256;
- detecção de mudança de layout;
- normalização e tipagem antes das agregações;
- registros rejeitados preservados para auditoria;
- recorte CBO versionado;
- metodologia salarial alinhada às regras publicadas pelo MTE;
- salário real com número índice do IPCA pelo SIDRA/IBGE;
- ajustes FOR e EXC incorporados como deltas auditáveis;
- referência externa para reconciliação;
- gate de publicação vinculado ao hash do arquivo de origem;
- carga PostgreSQL transacional e idempotente;
- contratos de API versionados.

## Estado do produto

~~~mermaid
flowchart LR
    A["Aplicação pública<br/>operacional"] --> B["API + OpenAPI<br/>operacional"]
    B --> C["Pipeline de dados<br/>implementado"]
    C --> D["Gate de publicação<br/>implementado"]
    D --> E["PostgreSQL serving<br/>implementado"]
~~~

| Componente | Estado |
|---|---|
| Aplicação pública | Operacional |
| API / OpenAPI | Operacional |
| Frontend de produção | Operacional |
| Bronze / Silver / Gold | Implementado |
| Gate de publicação | Implementado |
| PostgreSQL serving | Implementado |
| Reconciliação oficial de julho/2026 | Implementada |
| Transporte FTP com fallback HTTPS | Implementado |
| Tratamento de MOV, FOR e EXC | Implementado |
| Agregação municipal | Implementada |
| Série histórica incremental | Implementada |
| Salário real por IPCA | Implementado |
| PostgreSQL gerenciado | Provisionado |
| Primeira competência tech real | Julho/2026 validada e publicada |

## Execução local

### Backend

~~~bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn src.api.main:app --reload
~~~

No Windows PowerShell:

~~~powershell
.\.venv\Scripts\Activate.ps1
~~~

### Frontend

~~~bash
cd frontend
npm install
npm run dev
~~~

### Testes

~~~bash
ruff check src tests
pytest -q
cd frontend && npm run build
~~~

## Pipeline

Sincronização das referências oficiais:

~~~bash
python -m src.cli sync-municipalities
python -m src.cli sync-ipca 202607 --base 202607
~~~

Processamento por competência:

~~~bash
python -m src.cli pipeline 202607
~~~

Processamento de arquivo oficial local:

~~~bash
python -m src.cli local-pipeline 202607 "/caminho/CAGEDMOV202607.7z" --kind MOV
~~~

Validação e aprovação:

~~~bash
python -m src.cli validate-release 202607

python -m src.cli approve-release 202607 \
  --reviewer "responsavel" \
  --notes "Layout, rejeições e metodologia revisados." \
  --acknowledge-methodology-reviewed
~~~

Carga no serving:

~~~bash
alembic upgrade head
python -m src.cli load-postgres 202607
~~~

## Estrutura

~~~text
config/      regras, fontes e referências versionadas
data/        camadas Bronze, Silver e Gold
docs/        arquitetura, metodologia, lineage e operação
frontend/    aplicação React e TypeScript
src/         ingestão, transformação, qualidade, banco e API
tests/       testes automatizados
alembic/     migrations do PostgreSQL
docker/      imagens de execução
~~~

## Documentação

| Documento | Conteúdo |
|---|---|
| [Arquitetura](docs/ARCHITECTURE.md) | componentes e responsabilidades |
| [Visão técnica](docs/PROJECT_OVERVIEW.md) | desenho geral do produto |
| [Contrato de dados](docs/DATA_CONTRACT.md) | campos e expectativas de schema |
| [Metodologia](docs/METHODOLOGY.md) | regras de cálculo e reconciliação |
| [Recorte CBO](docs/CBO_SCOPE.md) | definição ocupacional de tecnologia |
| [Data lineage](docs/DATA_LINEAGE.md) | origem e transformação dos dados |
| [Pipeline](docs/PIPELINE_REAL.md) | execução do processamento |
| [Deploy](docs/DEPLOY.md) | produção e execução |
| [Roadmap](docs/ROADMAP.md) | próximos blocos técnicos |
