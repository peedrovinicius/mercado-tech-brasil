# Status de implementação

## Produção

- aplicação: https://mercado-tech-brasil.onrender.com
- API: https://mercado-tech-brasil.onrender.com/api/v1
- OpenAPI: https://mercado-tech-brasil.onrender.com/docs
- runtime: Python 3.11
- serving ativo: arquivos Gold publicados
- PostgreSQL: suporte implementado e disponível por configuração

## Série publicada

O produto cobre oito competências oficiais de 2026, de janeiro a agosto.

| Período | Admissões tech | Desligamentos tech | Saldo |
|---|---:|---:|---:|
| Jan-ago/2026 | 153.733 | 145.836 | +7.897 |

Em todas as competências processadas:

- o MOV nacional foi reconciliado com a referência oficial do MTE;
- MOV, FOR e EXC apresentaram taxa válida de 100%;
- os agregados por UF, ocupação e município fecham com o overview;
- o recorte ocupacional permaneceu restrito às cinco famílias CBO versionadas;
- cada aprovação está vinculada ao SHA-256 do MOV e ao fingerprint da referência oficial correspondente;
- FOR e EXC são aplicados às competências de origem;
- alterações retroativas do Gold são auditadas por hash antes de serem publicadas;
- remuneração real usa julho de 2026 como base do IPCA.

## Dados

- Bronze, Silver e Gold com manifestos, SHA-256 e proveniência;
- MOV, FOR e EXC tratados por competência de origem;
- agregados por UF, ocupação e município;
- série histórica e série por família CBO;
- RAIS 2025 e comparação descritiva com os fluxos CAGED;
- referências do MTE e IBGE, incluindo IPCA, municípios e população 2026;
- recorte CBO versionado e intake do QBQ preparado para arquivo oficial.

## Qualidade e publicação

- reconciliação nacional por competência e validação territorial;
- gates mensal e anual com aprovação metodológica vinculada às entradas;
- regressão dos artefatos históricos e controle de revisões FOR/EXC;
- validação de proveniência e cobertura populacional;
- política de cobertura mensal e detecção de revisão oficial;
- política de deploy para impedir promoção de artefatos não publicáveis;
- serviço Render ainda difere do Blueprint em `autoDeployTrigger` e health check.

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
- análise visual da evolução mensal das cinco famílias CBO tech;
- comparação visual RAIS x CAGED com participação e escala por estoque anterior;
- ranking municipal normalizado por 100 mil habitantes ativo para Ago/2026;
- frontend responsivo;
- deploy público no Render.

Os arquivos brutos permanecem fora do Git. O repositório versiona somente artefatos derivados e manifests necessários para rastreabilidade.
