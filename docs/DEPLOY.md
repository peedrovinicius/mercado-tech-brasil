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

A configuração versionada de produção em `render.yaml` representa o estado desejado: runtime Python 3.11, build do backend e do frontend no mesmo serviço, Uvicorn como processo web e health check em `/api/v1/system/health`.

O build executa a instalação do pacote Python e, em seguida, compila o frontend React + TypeScript com Vite. O frontend de produção utiliza `/api/v1` como base da API, mantendo tudo no mesmo domínio.

O Blueprint usa `autoDeployTrigger: checksPass`. Alterações de produção somente devem ser promovidas depois dos checks do GitHub. O `buildFilter` restringe builds automáticos a código de runtime, frontend, artefatos Gold, `pyproject.toml` e ao próprio `render.yaml`, evitando rebuild por alterações apenas documentais.

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


## Política de promoção para produção

O workflow `Deployment policy` valida alterações relevantes antes da promoção.

Para qualquer artefato mensal alterado em `data/gold`, a competência correspondente precisa possuir:

- `automatic_checks_passed=true`;
- `manual_approval_valid=true`;
- `publishable=true`;
- todos os checks bloqueantes aprovados.

A mesma regra é aplicada às releases anuais da RAIS.

Commits de publicação de Gold não usam `[skip ci]`, pois a política depende da execução dos checks antes do deploy.

A validação pode ser executada localmente com:

~~~bash
git diff --name-only HEAD^ HEAD > changed-files.txt
python -m src.validation.deployment_policy --changed-files changed-files.txt
~~~

A configuração operacional do serviço no Render deve permanecer equivalente ao Blueprint versionado. Em especial, o Auto-Deploy deve usar **After CI Checks Pass**.

### Drift operacional conhecido

Na última verificação do serviço existente, o Render ainda reportou:

- `autoDeployTrigger=commit`;
- health check vazio.

Portanto, o Blueprint está correto, mas o serviço existente ainda não está sincronizado com ele. Essa divergência deve ser tratada como drift de infraestrutura até a configuração operacional do serviço ser atualizada.
