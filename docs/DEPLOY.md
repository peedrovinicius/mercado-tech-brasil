# Deploy

## Produção

A aplicação pública está disponível em:

https://mercado-tech-brasil.onrender.com

Frontend e API usam o mesmo domínio:

~~~text
Browser
   |
   v
FastAPI
  +-- /api/v1/*  API
  +-- /docs      OpenAPI
  +-- /           React compilado
~~~

## Arquitetura de produção

O Render usa `render.yaml` com runtime Docker e health check em `/api/v1/system/health`.

A imagem `docker/app/Dockerfile` possui dois estágios:

1. Node 22 compila o frontend React + TypeScript com Vite;
2. Python 3.11 instala o backend e serve API e frontend pelo Uvicorn.

O frontend de produção utiliza `/api/v1` como base da API, mantendo tudo no mesmo domínio.

## Backend de dados atual

A configuração versionada de produção usa:

~~~text
APP_ENV=production
DATA_BACKEND=files
~~~

Nesse modo, a API serve apenas competências que passaram pelo gate de publicação e possuem os artefatos Gold necessários.

O suporte a PostgreSQL também está implementado. Para operar com serving PostgreSQL, o ambiente precisa definir `DATA_BACKEND=postgres`, disponibilizar `DATABASE_URL` e carregar previamente as competências aprovadas no banco.

## Build local da imagem de produção

~~~bash
docker build -f docker/app/Dockerfile -t mercado-tech-brasil .
docker run --rm -p 8000:8000 mercado-tech-brasil
~~~

A aplicação fica disponível em `http://localhost:8000`, com OpenAPI em `http://localhost:8000/docs`.

## Desenvolvimento local

Backend:

~~~bash
uvicorn src.api.main:app --reload
~~~

Frontend:

~~~bash
cd frontend
npm install
npm run dev
~~~

Durante o desenvolvimento, o Vite encaminha `/api/*` para `http://localhost:8000`.

## Verificações de publicação

Antes de tratar uma competência como publicada, o projeto exige os artefatos Gold correspondentes e um gate válido. O endpoint de readiness informa o backend ativo e se há dados publicados disponíveis para serving.
