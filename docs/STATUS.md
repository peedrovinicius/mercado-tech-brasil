# Status de implementação

## Produção

- aplicação: https://mercado-tech-brasil.onrender.com
- API: https://mercado-tech-brasil.onrender.com/api/v1
- OpenAPI: https://mercado-tech-brasil.onrender.com/docs
- runtime: Python 3.11
- serving ativo: arquivos Gold publicados
- PostgreSQL: suporte implementado e disponível por configuração

## Série publicada

O produto cobre sete competências oficiais de 2026, de janeiro a julho.

| Período | Admissões tech | Desligamentos tech | Saldo |
|---|---:|---:|---:|
| Jan-jul/2026 | 134.209 | 127.865 | +6.344 |

Em todas as competências processadas:

- o MOV nacional foi reconciliado com a referência oficial do MTE;
- MOV, FOR e EXC apresentaram taxa válida de 100%;
- os agregados por UF, ocupação e município fecham com o overview;
- o recorte ocupacional permaneceu restrito às cinco famílias CBO versionadas;
- cada aprovação está vinculada ao SHA-256 do MOV correspondente;
- FOR e EXC são aplicados às competências de origem;
- remuneração real usa julho de 2026 como base do IPCA.

## Dados

- Bronze, Silver e Gold;
- ingestão FTP oficial com fallback HTTPS;
- extração de arquivos .7z;
- manifestos SHA-256;
- proveniência de transporte;
- detecção de mudança de layout;
- normalização e tipagem;
- rejeições auditáveis;
- MOV, FOR e EXC;
- Gold por UF;
- Gold por ocupação;
- Gold por município;
- série histórica;
- referências oficiais nacionais por competência;
- recorte CBO v2;
- metodologia salarial MTE;
- salário real por IPCA;
- referência municipal IBGE;
- categoria residual municipal Não identificado.

## Qualidade e publicação

- checks automáticos;
- reconciliação nacional por competência;
- qualidade da dimensão municipal;
- gate de publicação por competência;
- aprovação metodológica vinculada ao SHA-256;
- invalidação da aprovação quando a origem muda;
- registro de releases publicado pela API;
- regra editorial automatizada para pontuação.

## Serving e aplicação

- arquivos Gold publicados como backend ativo de produção;
- PostgreSQL opcional para serving;
- SQLAlchemy;
- Alembic;
- carga PostgreSQL transacional e idempotente;
- API FastAPI;
- OpenAPI;
- React e TypeScript;
- gráficos ECharts modulares;
- frontend responsivo;
- deploy público no Render.

Os arquivos brutos permanecem fora do Git. O repositório versiona somente artefatos derivados e manifests necessários para rastreabilidade.
