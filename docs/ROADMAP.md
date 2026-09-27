# Roadmap

## Estado atual

O núcleo do Mercado Tech Brasil está operacional e publicado.

Entregas concluídas:

- pipeline Bronze, Silver e Gold para Novo CAGED;
- ingestão e ajustes MOV, FOR e EXC;
- manifestos e SHA-256 da origem;
- detecção de mudança de layout;
- recorte CBO versionado;
- reconciliação nacional por competência;
- gates automáticos e aprovação metodológica;
- série mensal publicada de jan/2026 a jul/2026;
- política versionada que bloqueia competências posteriores a jul/2026;
- regressão histórica e pacotes auditáveis para revisões FOR/EXC;
- salário real por IPCA;
- dimensão municipal IBGE;
- população municipal 2026 e taxas por 100 mil em jul/2026;
- série temporal por família CBO;
- comparação Ceará, Nordeste e Brasil;
- comparação descritiva RAIS x CAGED;
- pipeline anual RAIS 2025 completo;
- 91.710.262 registros RAIS processados;
- estoque qualificado RAIS reconciliado em 59.970.945 vínculos;
- 786.296 vínculos tech RAIS publicados;
- dimensão municipal RAIS validada contra DTB 2025;
- API FastAPI e OpenAPI;
- frontend React + TypeScript;
- serving por arquivos Gold;
- serving PostgreSQL disponível por configuração;
- aplicação pública no Render;
- política de deploy que bloqueia Gold mensal ou RAIS sem gate publicável;
- enriquecimento populacional pós-publicação idempotente;
- intake auditável do QBQ preparado para workbook oficial.

## Pendências reais

### 1. Sincronizar o serviço Render com o Blueprint versionado

O `render.yaml` define a política desejada:

- runtime Python;
- health check em `/api/v1/system/health`;
- `autoDeployTrigger: checksPass`;
- build filter para evitar builds causados somente por documentação.

O serviço existente no Render ainda apresenta drift operacional:

- `autoDeployTrigger=commit`;
- health check não configurado.

A correção depende de alteração da configuração do serviço no Render. O conector usado pelo projeto permite leitura e deploy, mas não expõe mutação dessas propriedades.

### 2. QBQ: obter o workbook oficial autenticado

A avaliação metodológica e o intake estão prontos.

Falta somente o arquivo oficial XLSX disponibilizado pelo sistema QBQ autenticado para:

1. confirmar nomes reais de planilhas e colunas;
2. registrar o SHA-256 do workbook;
3. validar a cobertura dos CBOs tech publicados;
4. definir o contrato Silver;
5. construir API e visualização apenas para atributos efetivamente presentes.

Nenhum schema será inferido ou reconstruído a partir de cópias não oficiais.

## Expansões futuras condicionadas

### Cobertura mensal

A cobertura permanece explicitamente limitada a **jul/2026** por `config/monthly_coverage_policy.json`.

Uma nova competência só poderá entrar depois de revisão explícita dessa política. Quando isso ocorrer, o fluxo já está preparado para:

1. exigir referência oficial versionada e efetiva;
2. impedir saltos mensais;
3. baixar MOV, FOR e EXC;
4. gerar manifests e SHA-256;
5. executar Bronze, Silver e Gold;
6. validar regressões históricas;
7. gerar gate inicialmente não publicável;
8. exigir aprovação metodológica;
9. executar CI e política de deploy antes da promoção.

### Comparações anuais

Comparações anuais adicionais só entram quando houver cobertura temporal suficiente e metodologia defensável. Não serão extrapoladas a partir de sete competências mensais.

## Critério de inclusão

Uma nova métrica entra no produto somente quando possui:

1. fonte identificada;
2. regra de transformação documentada;
3. teste;
4. período de referência;
5. comportamento definido para ausência e inconsistência;
6. contrato de API compatível com a governança de publicação.
