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

## Competência publicada

Julho de 2026 é a primeira competência tech real validada pelo pipeline.

- MOV: 4.467.208 registros, 100% válidos;
- FOR: 78.129 registros, 100% válidos;
- EXC: 9.733 registros, 100% válidos;
- recorte tech: 19.253 admissões, 18.347 desligamentos e saldo +906;
- salário mediano de admissão: R$ 3.990,06;
- municípios no recorte: 1.274;
- reconciliação nacional com a referência oficial: aprovada;
- proveniência MOV vinculada ao SHA-256 07b580d8d6da65ed9b87f693262981027e417ab56a111301494ee5532983475f.

Os arquivos brutos permanecem fora do Git. O repositório versiona somente artefatos derivados e manifests necessários para rastreabilidade.
