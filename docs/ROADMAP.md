# Roadmap

## Estado atual

O núcleo do Mercado Tech Brasil está operacional e publicado.

Entregas concluídas:

- pipeline Bronze, Silver e Gold do Novo CAGED, com MOV, FOR e EXC;
- série mensal auditada de jan/2026 a ago/2026, com reconciliação oficial e salário real por IPCA;
- dimensões territoriais do IBGE, população 2026 e taxas municipais por 100 mil;
- recorte CBO versionado, série por família e comparação Brasil, Nordeste e Ceará;
- RAIS 2025 processada, reconciliada, validada por município e publicada;
- FastAPI, OpenAPI, frontend React/TypeScript e aplicação pública;
- serving por arquivos Gold e suporte PostgreSQL;
- gates de publicação, regressão histórica e política de deploy;
- intake do QBQ preparado para o arquivo oficial.

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

A correção depende de atualizar a configuração do serviço existente no Render para refletir o Blueprint versionado.

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

A cobertura permanece explicitamente limitada a **ago/2026** por `config/monthly_coverage_policy.json`.

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

Comparações anuais adicionais só entram quando houver cobertura temporal suficiente e metodologia defensável. Não serão extrapoladas a partir de oito competências mensais.

## Critério de inclusão

Uma nova métrica entra no produto somente quando possui:

1. fonte identificada;
2. regra de transformação documentada;
3. teste;
4. período de referência;
5. comportamento definido para ausência e inconsistência;
6. contrato de API compatível com a governança de publicação.
