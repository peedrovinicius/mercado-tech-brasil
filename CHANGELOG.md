# Changelog

## 0.12.0

- imagem de produção unificada para FastAPI + React;
- FastAPI serve o frontend compilado quando `frontend/dist` está presente;
- frontend usa `/api/v1` por padrão;
- proxy Vite mantém desenvolvimento local sem CORS;
- Docker multi-stage reduz a topologia pública a um único serviço;
- `render.yaml` com plano free e health check;
- documentação de deploy;
- testes garantindo root/API docs no modo de desenvolvimento.

## 0.11.0

- dashboard visual responsivo para análise pública;
- hero com pipeline auditável;
- contexto oficial Brasil/Ceará disponível mesmo sem Gold tech;
- gráfico regional com dados publicados pelo MTE;
- endpoint de referência oficial para o frontend;
- separação visual explícita entre mercado formal total e recorte tech;
- pipeline visual com estado aguardando/publicado;
- layout responsivo aprimorado;
- versão de backend alinhada à versão do pacote;
- workflow visual separado e acionado somente quando `frontend/**` muda.

## 0.10.0

- recorte CBO de tecnologia elevado para versão 2;
- inclusão de 2122 — Engenheiros em computação;
- manutenção de 2123, 2124, 3171 e 3172;
- fontes oficiais da CBO registradas no arquivo de configuração;
- justificativa metodológica do recorte ocupacional;
- teste de regressão garantindo o conjunto exato de famílias;
- documentação dedicada em `docs/CBO_SCOPE.md`.

## 0.9.0

- referência oficial de julho/2026 versionada por Brasil, região e UF;
- testes de fechamento Brasil = 27 UFs + não identificados;
- testes de fechamento de cada região pela soma das respectivas UFs;
- metodologia salarial alinhada ao Sumário Executivo do MTE;
- salário mínimo de 2026 configurado em R$ 1.621,00;
- exclusão de salários abaixo de 0,3 salário mínimo e acima de 150 salários mínimos;
- exclusão de vínculos intermitentes das métricas salariais;
- fail-safe quando o indicador de trabalho intermitente não existe;
- contagem explícita de admissões elegíveis e excluídas das métricas salariais.

## 0.8.0

- camada PostgreSQL alinhada ao Gold real por competência, UF e CBO;
- carga transacional e idempotente;
- bloqueio da carga quando o gate de publicação não está aprovado;
- consultas da API diretamente no PostgreSQL via `DATA_BACKEND=postgres`;
- migrations Alembic;
- schema SQL atualizado;
- testes de serving com SQLite para manter o CI leve;
- Docker preparado para API usando PostgreSQL.

## 0.7.0

- gate de publicação por competência;
- validação de artefatos Bronze/Gold, proveniência e aritmética;
- limiar configurável de qualidade;
- aprovação metodológica manual vinculada ao SHA-256 do MOV;
- invalidação automática da aprovação quando o arquivo de origem muda;
- comandos `validate-release` e `approve-release`;
- endpoint `/api/v1/quality/publication-gate/latest`;
- testes do ciclo completo de bloqueio e aprovação.

## 0.6.0

- ingestão local auditável de TXT/.7z oficial;
- CLI `ingest-local` e `local-pipeline`;
- manifests descobertos recursivamente pela API;
- readiness exige overview + Gold analítico;
- endpoint de proveniência com SHA-256;
- card de proveniência no frontend;
- Dockerfiles para API e frontend;
- Docker Compose com PostgreSQL + API + web;
- testes de ingestão local, cobertura recursiva e readiness;
- documentação de execução local e Docker.

## 0.5.0

- frontend React + TypeScript com Vite;
- React Query para consumo da API;
- gráficos ECharts alimentados por Gold;
- estados loading, sem dados e API indisponível;
- painel de metodologia/rastreabilidade;
- endpoint analítico por UF;
- endpoint analítico por ocupação;
- Gold adicional por UF e CBO;
- CORS local para integração frontend/backend;
- novos testes para impedir publicação de analytics inexistentes.

## 0.4.0

- downloader FTP oficial do Novo CAGED;
- descoberta automática de MOV/FOR/EXC;
- extração 7z;
- Bronze com manifesto SHA-256;
- contrato de layout do MOV;
- detecção de schema drift;
- transformação Silver;
- rejeições auditáveis;
- Gold agregado;
- referência oficial de julho/2026 para futura reconciliação;
- CLI end-to-end;
- documentação do pipeline real;
- parsing defensivo de salário com vírgula ou ponto decimal;
- gate explícito que impede publicação automática no primeiro processamento;
- documentação de data lineage.

## 0.3.0

- API versionada em `/api/v1`;
- endpoints de health, readiness, fontes e cobertura;
- endpoint de indicadores que recusa publicar números sem dados oficiais;
- relatório estruturado de qualidade;
- testes de API e qualidade;
- CI leve para lint e testes;
- scripts locais;
- ADR documentando a escolha de DuckDB/Polars.
