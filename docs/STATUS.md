# Status de implementação

## Produção

- aplicação: https://mercado-tech-brasil.onrender.com
- API: https://mercado-tech-brasil.onrender.com/api/v1
- OpenAPI: https://mercado-tech-brasil.onrender.com/docs
- runtime: Python 3.11
- PostgreSQL gerenciado: provisionado no Render

## Dados

- Bronze, Silver e Gold;
- ingestão FTP;
- fallback HTTPS;
- extração de arquivos .7z;
- manifesto SHA-256;
- proveniência de transporte;
- detecção de mudança de layout;
- normalização e tipagem;
- rejeições auditáveis;
- MOV, FOR e EXC;
- Gold por UF;
- Gold por ocupação;
- Gold por município;
- série histórica;
- referência oficial de julho/2026;
- recorte CBO v2;
- metodologia salarial MTE;
- salário real por IPCA;
- referência municipal IBGE.

## Qualidade e publicação

- checks automáticos;
- gate de publicação por competência;
- aprovação metodológica vinculada ao SHA-256;
- invalidação da aprovação quando a origem muda;
- testes de reconciliação;
- teste de regra editorial para travessões.

## Serving e aplicação

- PostgreSQL;
- SQLAlchemy;
- Alembic;
- carga transacional e idempotente;
- API FastAPI;
- OpenAPI;
- React e TypeScript;
- gráficos ECharts;
- frontend responsivo;
- deploy público no Render.

## Próxima carga de dados

O pipeline está preparado para baixar, transformar, reconciliar e publicar a primeira competência tech real. A publicação permanece condicionada ao gate metodológico e ao SHA-256 da origem.
