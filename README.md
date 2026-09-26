# Mercado Tech Brasil

[![CI](https://github.com/peedrovinicius/mercado-tech-brasil/actions/workflows/ci.yml/badge.svg)](https://github.com/peedrovinicius/mercado-tech-brasil/actions/workflows/ci.yml)
[![Frontend](https://github.com/peedrovinicius/mercado-tech-brasil/actions/workflows/frontend.yml/badge.svg)](https://github.com/peedrovinicius/mercado-tech-brasil/actions/workflows/frontend.yml)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Production](https://img.shields.io/badge/production-live-2ea44f)](https://mercado-tech-brasil.onrender.com)

Plataforma open source para análise do mercado formal de trabalho em tecnologia no Brasil a partir de fontes públicas oficiais.

**Produção:** https://mercado-tech-brasil.onrender.com  
**API:** https://mercado-tech-brasil.onrender.com/docs  
**Health:** https://mercado-tech-brasil.onrender.com/api/v1/system/health

## Visão geral

O projeto transforma dados públicos do trabalho formal em uma cadeia auditável de ingestão, validação, transformação, serving e visualização.

O desenho prioriza três propriedades:

- **rastreabilidade** — cada arquivo ingerido recebe manifesto e SHA-256;
- **reprodutibilidade** — regras de transformação, recorte CBO e metodologia são versionadas;
- **publicação controlada** — uma competência só pode alimentar o serving após passar pelos checks automáticos e pelo gate metodológico.

A aplicação pública já apresenta o contexto oficial de julho de 2026 publicado pelo MTE. Os indicadores específicos de tecnologia permanecem bloqueados até a primeira competência de microdados passar integralmente pelo pipeline e pelo gate de publicação.

## Arquitetura

~~~mermaid
flowchart LR
    A["Fontes oficiais<br/>MTE · CBO · IBGE"] --> B["Bronze<br/>arquivo original + SHA-256"]
    B --> C["Silver<br/>normalização + qualidade"]
    C --> D["Gold<br/>agregados reproduzíveis"]
    D --> E["PostgreSQL<br/>serving"]
    D --> F["DuckDB<br/>validação local"]
    E --> G["FastAPI<br/>/api/v1 + OpenAPI"]
    G --> H["React + TypeScript<br/>dashboard"]
~~~

### Fluxo de publicação

~~~mermaid
flowchart LR
    A["Microdado oficial"] --> B["Ingestão"]
    B --> C["Validação de schema"]
    C --> D["Rejeições auditáveis"]
    D --> E["Agregações Gold"]
    E --> F["Gate automático"]
    F --> G["Revisão metodológica<br/>vinculada ao SHA-256"]
    G --> H["PostgreSQL / API"]
~~~

## Fontes

| Fonte | Uso |
|---|---|
| Novo CAGED — MTE | admissões, desligamentos, saldo e remuneração de admissão |
| CBO — MTE | definição versionada das ocupações de tecnologia |
| IBGE | base territorial e indicadores normalizados planejados |

A referência oficial de julho de 2026 está versionada em **config/official_reference_202607.json**.

## Recorte de tecnologia

O recorte atual é ocupacional e está versionado em **config/cbo_tech.yml**.

| Família CBO | Denominação |
|---|---|
| 2122 | Engenheiros em computação |
| 2123 | Administradores de tecnologia da informação |
| 2124 | Analistas de tecnologia da informação |
| 3171 | Técnicos de desenvolvimento de sistemas e aplicações |
| 3172 | Técnicos em operação e monitoração de computadores |

A justificativa e as regras de governança do recorte estão em [docs/CBO_SCOPE.md](docs/CBO_SCOPE.md).

## Stack

| Camada | Tecnologias |
|---|---|
| Dados | Python, Polars, DuckDB, Parquet, Pandera |
| Banco | PostgreSQL, SQLAlchemy, Alembic |
| API | FastAPI, Pydantic, OpenAPI |
| Frontend | React, TypeScript, Vite, TanStack Query, ECharts |
| Qualidade | Pytest, Ruff |
| Infraestrutura | Docker, GitHub Actions, Render |

## Qualidade e governança

O pipeline implementa:

- Bronze imutável com manifesto e SHA-256;
- detecção de mudança de layout;
- normalização e tipagem antes das agregações;
- registros rejeitados preservados para auditoria;
- recorte CBO versionado;
- metodologia salarial alinhada às regras publicadas pelo MTE;
- referência externa para reconciliação;
- gate de publicação vinculado ao hash do arquivo de origem;
- carga PostgreSQL transacional e idempotente;
- API que não serve uma competência não aprovada.

Detalhes em [Metodologia](docs/METHODOLOGY.md), [Data lineage](docs/DATA_LINEAGE.md) e [Pipeline](docs/PIPELINE_REAL.md).

## Estado atual

| Componente | Estado |
|---|---|
| Aplicação pública | Operacional |
| API / OpenAPI | Operacional |
| Frontend de produção | Operacional |
| Bronze / Silver / Gold | Implementado |
| Gate de publicação | Implementado |
| PostgreSQL serving | Implementado |
| Reconciliação oficial de julho/2026 | Implementada |
| Primeira competência tech real publicada | Em andamento |
| Histórico multi-mês | Planejado após a primeira competência validada |

A aplicação pública usa, neste momento, a referência oficial agregada do MTE para demonstrar o produto sem substituir os microdados ainda não processados.

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

O Vite encaminha /api/* para o backend local em localhost:8000.

### Testes

~~~bash
ruff check src tests
pytest -q
cd frontend && npm run build
~~~

## Pipeline

Execução automática a partir da estrutura oficial:

~~~bash
python -m src.cli pipeline 202607
~~~

Para um arquivo oficial já disponível localmente:

~~~bash
python -m src.cli local-pipeline 202607 "/caminho/CAGEDMOV202607.7z" --kind MOV
~~~

Validação e aprovação de uma competência:

~~~bash
python -m src.cli validate-release 202607

python -m src.cli approve-release 202607 \
  --reviewer "responsavel" \
  --notes "Layout, rejeições e metodologia revisados." \
  --acknowledge-methodology-reviewed
~~~

Carga da competência aprovada no serving:

~~~bash
alembic upgrade head
python -m src.cli load-postgres 202607
~~~

## Estrutura

~~~text
config/      regras, fontes e referências versionadas
data/        camadas Bronze, Silver e Gold
docs/        arquitetura, metodologia, lineage e operação
frontend/    aplicação React/TypeScript
src/         ingestão, transformação, qualidade, banco e API
tests/       testes automatizados
alembic/     migrations do serving PostgreSQL
docker/      imagens de execução
~~~

## Documentação

- [Arquitetura](docs/ARCHITECTURE.md)
- [Visão técnica](docs/PROJECT_OVERVIEW.md)
- [Contrato de dados](docs/DATA_CONTRACT.md)
- [Metodologia](docs/METHODOLOGY.md)
- [Recorte CBO](docs/CBO_SCOPE.md)
- [Data lineage](docs/DATA_LINEAGE.md)
- [Pipeline real](docs/PIPELINE_REAL.md)
- [Deploy](docs/DEPLOY.md)
- [Roadmap](docs/ROADMAP.md)
- [Changelog](CHANGELOG.md)

## Limitações atuais

- Novo CAGED mede **fluxos** de emprego formal, não estoque de trabalhadores.
- Trabalho informal, prestação PJ e trabalho independente não são cobertos por esse indicador.
- FOR/EXC são preservados na ingestão, mas sua semântica de ajuste ainda não é incorporada aos indicadores publicados.
- Indicadores municipais e séries históricas entram após a validação da primeira competência real.
