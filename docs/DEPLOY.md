# Deploy público

## Arquitetura de produção

A demonstração pública usa um único serviço:

```text
Browser
   |
   v
FastAPI
  ├── /api/v1/*  -> API
  ├── /docs      -> OpenAPI
  └── /           -> React compilado
```

O frontend usa `/api/v1` como URL relativa. Isso significa que frontend e API compartilham o mesmo domínio em produção.

### Por que um único serviço

Enquanto a primeira competência tech ainda não foi carregada, separar frontend e backend aumentaria custo e complexidade sem benefício real. Um único container:

- elimina CORS em produção;
- exige apenas um health check;
- reduz cold starts e configuração;
- mantém a arquitetura fácil de demonstrar;
- pode ser separado no futuro sem mudar os contratos da API.

## Docker de produção

```bash
docker build -f docker/app/Dockerfile -t mercado-tech-brasil .
docker run --rm -p 8000:8000 mercado-tech-brasil
```

Abra:

- aplicação: http://localhost:8000
- health: http://localhost:8000/api/v1/system/health
- Swagger: http://localhost:8000/docs

## Render

O repositório inclui `render.yaml` com um único Web Service Docker e health check em:

```text
/api/v1/system/health
```

O blueprint usa `DATA_BACKEND=files` enquanto não há competência tech aprovada no banco. Assim a demo já apresenta o contexto oficial de julho/2026, mas continua recusando indicadores tech inexistentes.

Quando houver Gold aprovado, o deployment poderá migrar para `DATA_BACKEND=postgres` e um PostgreSQL gerenciado.

## Desenvolvimento local

O frontend também usa a URL relativa `/api/v1`. O Vite encaminha chamadas `/api/*` para `http://localhost:8000`, portanto o fluxo local continua funcionando com dois processos:

```bash
uvicorn src.api.main:app --reload
cd frontend && npm run dev
```
