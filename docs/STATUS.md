# Status de implementação

## Produção

- aplicação: https://mercado-tech-brasil.onrender.com
- API: https://mercado-tech-brasil.onrender.com/api/v1
- OpenAPI: https://mercado-tech-brasil.onrender.com/docs
- runtime: Python 3.11
- backend atual: arquivos versionados e referência oficial agregada

## Implementado

### Dados
- arquitetura Bronze / Silver / Gold;
- ingestão FTP e ingestão local;
- extração de arquivos .7z;
- manifesto SHA-256;
- detecção de mudança de layout;
- normalização de cabeçalhos e tipos;
- rejeições auditáveis;
- Silver em Parquet;
- Gold por UF e ocupação;
- referência oficial de julho/2026;
- metodologia salarial alinhada ao MTE;
- recorte CBO v2.

### Qualidade e publicação
- checks automáticos de qualidade;
- gate de publicação por competência;
- aprovação metodológica vinculada ao SHA-256;
- invalidação da aprovação quando a origem muda;
- testes de reconciliação da referência oficial.

### Serving e aplicação
- PostgreSQL com migrations Alembic;
- carga Gold → PostgreSQL transacional e idempotente;
- backend selecionável entre arquivos e PostgreSQL;
- FastAPI / OpenAPI;
- frontend React / TypeScript;
- build Vite validado em CI;
- deploy público no Render.

## Em andamento

1. processar a primeira competência oficial de microdados;
2. revisar rejeições e layout reais;
3. validar a semântica de FOR/EXC;
4. reconciliar agregados do microdado com as referências publicadas;
5. liberar a primeira competência tech pelo gate;
6. carregar o Gold aprovado no PostgreSQL;
7. ativar os indicadores tech no dashboard público.
