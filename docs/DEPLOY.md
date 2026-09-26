# Deploy

## Produção

A aplicação está disponível em:

https://mercado-tech-brasil.onrender.com

Frontend e API usam o mesmo domínio:

~~~text
Browser
   |
   v
FastAPI
  ├── /api/v1/*  API
  ├── /docs      OpenAPI
  └── /           React compilado
~~~

O serviço atual roda em Python 3.11 no Render. O build instala o backend, compila o frontend com Vite e inicia o Uvicorn.

## Configuração atual

Build:

~~~bash
pip install -e . && cd frontend && npm install --no-audit --no-fund && npm run build
~~~

Start:

~~~bash
uvicorn src.api.main:app --host 0.0.0.0 --port $PORT
~~~

Variáveis principais:

~~~text
APP_ENV=production
DATA_BACKEND=files
PYTHON_VERSION=3.11.11
~~~

DATA_BACKEND=files permanece ativo até a primeira competência tech ser aprovada e carregada no PostgreSQL.

## Docker

O repositório também mantém uma imagem multi-stage reproduzível:

~~~bash
docker build -f docker/app/Dockerfile -t mercado-tech-brasil .
docker run --rm -p 8000:8000 mercado-tech-brasil
~~~

O primeiro estágio compila o frontend. O segundo instala o backend Python e serve a aplicação inteira pelo FastAPI.

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

Durante o desenvolvimento, o Vite encaminha /api/* para http://localhost:8000.
