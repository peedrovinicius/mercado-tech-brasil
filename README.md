# Mercado Tech Brasil

Produto de dados open source para analisar o mercado formal de trabalho em tecnologia no Brasil usando fontes públicas oficiais.

> Objetivo: transformar microdados públicos em informação auditável sobre contratação, desligamento, remuneração, distribuição geográfica e evolução das ocupações de tecnologia.

## Por que este projeto existe

Muitos dashboards apenas exibem números. O Mercado Tech Brasil é desenhado como um **produto de dados completo**:

**fonte oficial → ingestão reproduzível → validação → transformação → banco analítico → API → aplicação web**

Nenhum indicador final é digitado manualmente.

## Fontes

### Novo CAGED — MTE
Fluxos mensais do emprego formal: admissões, desligamentos, salários e características das movimentações.

### CBO — MTE
Classificação oficial das ocupações usadas no recorte de tecnologia.

### IBGE
Território, códigos municipais e dados demográficos para indicadores normalizados.

### Expansão planejada
- RAIS: estoque anual de vínculos e análises estruturais;
- IPCA/IBGE: salários corrigidos pela inflação;
- QBQ/MTE: conhecimentos, habilidades e atitudes associados às ocupações.

## Perguntas que a aplicação deverá responder

- Onde o emprego formal em TI está crescendo?
- Quais ocupações apresentam maior volume de admissões e saldo?
- Como a remuneração de admissão varia entre regiões e ocupações?
- Quais municípios concentram mais movimentações de profissionais de TI?
- Qual a participação de ocupações de TI no mercado formal local?
- Como os resultados mudam ao longo do tempo?
- Como salários nominais diferem de salários reais quando ajustados pela inflação?

## Arquitetura

```text
Fontes oficiais
     |
     v
[ BRONZE ] arquivos originais + metadados + SHA-256
     |
     v
[ SILVER ] dados normalizados e validados em Parquet
     |
     v
[ GOLD ] indicadores analíticos reproduzíveis
     |
     +--------------------+
     |                    |
     v                    v
 PostgreSQL             DuckDB
 serving/API       validação/análise local
     |
     v
 FastAPI / OpenAPI
     |
     v
 React + TypeScript
```

## Stack

**Dados**
- Python
- Polars
- DuckDB
- Parquet
- Pandera
- PostgreSQL

**Backend**
- FastAPI
- SQLAlchemy
- Alembic
- Pydantic
- Pytest

**Frontend**
- React
- TypeScript
- Vite
- TanStack Query
- ECharts

**Infraestrutura**
- Docker Compose
- variáveis de ambiente
- logs estruturados
- testes automatizados
- CI leve apenas para lint/testes

## Camadas de dados

### Bronze
Cópia imutável do arquivo oficial. Cada ingestão registra fonte, competência, data de obtenção, tamanho e SHA-256.

### Silver
Tipos corrigidos, nomes normalizados, códigos territoriais/CBO tratados e registros inválidos identificados.

### Gold
Tabelas agregadas usadas diretamente pela API e pelo dashboard.

## Indicadores principais

- admissões;
- desligamentos;
- saldo;
- salário médio e mediano de admissão;
- salário real de admissão;
- participação das ocupações de TI nas admissões locais;
- admissões de TI por 100 mil habitantes;
- evolução mensal;
- distribuição por CBO, UF e município;
- variação mês contra mês e ano contra ano.

## Requisitos de qualidade

Todo indicador publicado deve ter:

1. fonte;
2. competência/período;
3. fórmula;
4. regra de filtragem;
5. teste automatizado;
6. data de atualização.

## Estrutura

```text
mercado-tech-brasil/
├── config/
│   ├── cbo_tech.yml
│   └── sources.json
├── data/
│   ├── bronze/
│   ├── silver/
│   └── gold/
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DATA_CONTRACT.md
│   ├── METHODOLOGY.md
│   └── ROADMAP.md
├── frontend/
├── sql/
│   └── schema.sql
├── src/
│   ├── api/
│   ├── core/
│   ├── ingestion/
│   ├── quality/
│   └── transform/
├── tests/
├── .env.example
├── .gitignore
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

## Status

**v0.7 — governança de publicação em validação**

- [x] arquitetura Bronze / Silver / Gold;
- [x] contrato de dados e recorte CBO versionado;
- [x] ingestão FTP + ingestão local auditável;
- [x] SHA-256 e proveniência;
- [x] validações e registros rejeitados;
- [x] transformação Silver e agregações Gold implementadas;
- [x] API FastAPI versionada com Swagger;
- [x] frontend React + TypeScript integrado à API;
- [x] Docker Compose para PostgreSQL + API + frontend;
- [x] testes automatizados;
- [ ] processar a primeira competência oficial real;
- [ ] revisar rejeições e reconciliar metodologia MOV/FOR/EXC;
- [ ] carregar os agregados validados no PostgreSQL;
- [ ] validar build completo do frontend;
- [ ] publicar a aplicação em ambiente acessível.

## Princípios

- dados reais, nunca números fictícios;
- fonte oficial visível na interface;
- metodologia reproduzível;
- código simples antes de tecnologia desnecessária;
- sem scraping frágil quando existe fonte pública oficial;
- sem subir microdados brutos grandes para o Git;
- sem workflow caro de CI para processar bases inteiras.


## Avaliação técnica em 5 minutos

Para quem está avaliando o repositório:

```bash
pip install -e ".[dev]"
pytest -q
uvicorn src.api.main:app --reload
```

Depois:

- Swagger: `/docs`
- Health: `/api/v1/system/health`
- Readiness: `/api/v1/system/readiness`
- Fontes: `/api/v1/metadata/sources`
- Cobertura dos dados: `/api/v1/metadata/coverage`
- Qualidade: `/api/v1/quality/latest`
- Indicadores: `/api/v1/indicators/overview`

A API **não inventa dados**. Enquanto nenhuma competência oficial tiver passado pelo pipeline, o endpoint de indicadores retorna `503` com uma explicação explícita.

### O que diferencia este repositório

- decisões arquiteturais justificadas em ADR;
- qualidade e proveniência tratadas como parte do produto;
- fonte pública exposta pela API;
- recorte CBO versionado;
- testes automatizados;
- modelo dimensional;
- CI propositalmente leve;
- arquitetura preparada para atualização incremental;
- separação clara entre dados brutos e dados servidos.

Veja também: [`docs/RECRUITER_GUIDE.md`](docs/RECRUITER_GUIDE.md).


## Pipeline oficial implementado

A versão 0.4 já possui ingestão por competência diretamente da estrutura pública do Novo CAGED.

```bash
python -m src.cli pipeline 202607
```

O pipeline:

1. descobre MOV/FOR/EXC no diretório oficial;
2. baixa os `.7z`;
3. preserva os arquivos na Bronze;
4. gera SHA-256;
5. valida o layout;
6. separa rejeições;
7. filtra o recorte CBO de tecnologia;
8. grava Silver em Parquet;
9. produz Gold agregado;
10. gera JSON de overview consumido pela API.

**Importante:** FOR/EXC já são ingeridos, mas ainda não são combinados aos indicadores publicados enquanto a lógica de ajustes não estiver validada. Isso evita resultados tecnicamente convincentes, porém metodologicamente errados.

Detalhes: [`docs/PIPELINE_REAL.md`](docs/PIPELINE_REAL.md)


### Rastreabilidade

Veja [`docs/DATA_LINEAGE.md`](docs/DATA_LINEAGE.md) para acompanhar o caminho de cada dado da fonte oficial até a API.


## Frontend profissional

A interface React + TypeScript está em `frontend/` e consome somente endpoints da API.

```bash
# terminal 1
uvicorn src.api.main:app --reload

# terminal 2
cd frontend
npm install
npm run dev
```

A primeira tela já possui estados de carregamento, API indisponível, ausência de dados publicados e dashboard real. Quando a camada Gold existir, a aplicação exibe automaticamente indicadores, ranking por UF, saldo por CBO e métricas de qualidade.

Nenhum número de demonstração é embutido no frontend.


## v0.6 — execução resiliente

A aplicação agora aceita duas rotas de ingestão do mesmo dado oficial:

### FTP automático

```bash
python -m src.cli pipeline 202607
```

### Arquivo oficial já baixado

```bash
python -m src.cli local-pipeline 202607 "C:\Downloads\CAGEDMOV202607.7z" --kind MOV
```

O caminho local existe para ambientes em que o FTP do PDET é bloqueado. O arquivo continua sendo preservado na Bronze, recebe SHA-256 e segue exatamente pelas mesmas camadas Silver/Gold.

Também foi adicionado `/api/v1/provenance/latest`, permitindo que o dashboard mostre qual arquivo e hash originaram os dados exibidos.

Veja [`docs/LOCAL_INGESTION.md`](docs/LOCAL_INGESTION.md) e [`docs/DOCKER.md`](docs/DOCKER.md).


### Gate de publicação

Uma competência só é considerada publicável quando passa pelos checks automáticos e por uma revisão metodológica vinculada ao SHA-256 do arquivo MOV:

```bash
python -m src.cli validate-release 202607
python -m src.cli approve-release 202607 \
  --reviewer "Nome do revisor" \
  --notes "Layout, rejeições e metodologia revisados." \
  --acknowledge-methodology-reviewed
```

Trocar o arquivo de origem invalida automaticamente a aprovação anterior. O status também fica disponível em `/api/v1/quality/publication-gate/latest`.
