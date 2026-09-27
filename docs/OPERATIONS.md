# Operação de dados

## Objetivo

A operação mensal separa preparação, auditoria e publicação. A próxima competência só pode entrar no fluxo quando existe uma referência oficial do MTE versionada, válida, efetiva e imediatamente posterior à última competência publicada.

O workflow de preparação resolve essa competência automaticamente e aciona a auditoria. A publicação continua separada e só aceita um artefato já auditado cuja aprovação metodológica esteja registrada no repositório.

Isso evita antecipar períodos ainda não publicados e evita reprocessar microdados durante a publicação.

## Preparação incremental

Workflow: `Prepare next CAGED competence`

O workflow é acionado quando `config/reference_totals.json` muda no `main` e também pode ser executado manualmente.

Antes de qualquer download ele:

1. identifica a última competência mensal com `publishable=true`;
2. calcula o mês imediatamente seguinte;
3. exige que esse mês exista em `config/reference_totals.json`;
4. valida `reference_kind=published_monthly_mov`;
5. valida fonte, URL, data de publicação e aritmética nacional;
6. impede referências com `published_at` no futuro;
7. bloqueia saltos de competência;
8. lê a base IPCA já versionada;
9. aciona `Audit data competence` somente quando o candidato é elegível.

Quando nenhuma nova referência oficial está registrada, o workflow termina sem baixar microdados.

Comandos equivalentes:

~~~bash
python -m src.cli next-competence
python -m src.cli next-competence --json
python -m src.cli validate-incremental-competence AAAAMM
~~~

Uma competência já publicada só pode ser reauditada com solicitação explícita:

~~~bash
python -m src.cli validate-incremental-competence AAAAMM --allow-published
~~~

## Auditoria

Workflow: `Audit data competence`

Entradas:

- `competence`: competência no formato AAAAMM;
- `ipca_base`: competência base para valores reais. A série de 2026 usa 202607.

O workflow:

1. valida se a competência é a próxima elegível pela referência oficial;
2. sincroniza referências do IBGE;
3. tenta baixar MOV, FOR e EXC;
4. usa FTP do MTE como transporte primário e HTTPS como fallback;
5. gera manifests e SHA-256;
6. transforma os dados;
7. produz Gold por UF, ocupação e município;
8. reconstrói ajustes;
9. executa os checks automáticos;
10. remove arquivos brutos antes de gerar o artefato;
11. publica um artefato temporário de auditoria por três dias.

O resultado da auditoria não é publicado automaticamente.

## Aprovação metodológica

A aprovação fica em `config/publication_approvals.json` e contém o SHA-256 do MOV auditado.

O gate invalida uma aprovação quando o hash da origem muda.

## Publicação

Workflow: `Publish audited data`

Entradas:

- `competence`;
- `audit_run_id`: ID da execução de auditoria que gerou o artefato.

O workflow baixa o artefato derivado, refaz o gate em modo estrito e só então versiona Gold, auditoria e manifests.

Antes do commit de publicação, o mesmo workflow executa `python scripts/generate_readme_dashboard.py`. O SVG do dashboard é regenerado a partir da camada Gold e entra no mesmo commit da competência, evitando que o visual do README fique defasado.

Os microdados brutos não entram no Git.

## Regras operacionais

- não iniciar auditoria incremental sem referência oficial versionada e efetiva;
- não saltar competências na série mensal;
- não publicar competência sem referência oficial;
- não publicar quando qualquer check bloqueante falhar;
- não reutilizar aprovação após mudança do SHA-256;
- manter a competência base do IPCA explícita;
- evitar reprocessamento quando um artefato auditado ainda estiver disponível;
- manter CI e build do frontend separados da operação de microdados.
