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
8. verifica se alguma referência de competência já publicada mudou em relação ao fingerprint aprovado;
9. prioriza a reauditoria dessa competência quando existe uma revisão oficial;
10. lê a base IPCA já versionada;
11. aciona `Audit data competence` somente quando o candidato é elegível.

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

A aprovação fica em `config/publication_approvals.json` e contém dois vínculos criptográficos: o SHA-256 do MOV auditado e o fingerprint da referência oficial usada na reconciliação.

O gate invalida a aprovação se a origem ou a referência oficial mudar. Uma revisão de referência já publicada volta para reauditoria antes de qualquer nova publicação.

## Publicação

Workflow: `Publish audited data`

Entradas:

- `competence`;
- `audit_run_id`: ID da execução de auditoria que gerou o artefato.

O workflow baixa o artefato derivado, aplica apenas revisões históricas que passaram pela auditoria, confere se o baseline publicado continua igual ao observado durante a auditoria, refaz o gate em modo estrito e só então versiona Gold, auditoria e manifests.

Antes do processamento, a auditoria registra hashes dos artefatos já publicados. Se FOR ou EXC alterarem uma competência anterior, é gerado um manifesto de impacto com hashes antes/depois e métricas do overview. Alterações históricas sem uma competência efetiva correspondente em FOR/EXC são bloqueadas. O pacote de revisão só é aplicado se o histórico de produção ainda corresponder ao baseline auditado.

O cache de IPCA é incremental: novas sincronizações preservam índices de competências anteriores para que reconstruções históricas mantenham o cálculo de salário real.

Antes do commit de publicação, o mesmo workflow executa `python scripts/generate_readme_dashboard.py`. O SVG do dashboard é regenerado a partir da camada Gold e entra no mesmo commit da competência, evitando que o visual do README fique defasado.

Os microdados brutos não entram no Git.

## Regras operacionais

- não iniciar auditoria incremental sem referência oficial versionada e efetiva;
- não saltar competências na série mensal;
- não publicar competência sem referência oficial;
- não publicar quando qualquer check bloqueante falhar;
- não reutilizar aprovação após mudança do SHA-256 do MOV ou do fingerprint da referência;
- bloquear alteração histórica sem justificativa em FOR/EXC;
- bloquear ajuste com competência efetiva posterior à competência de ingestão;
- não aplicar pacote histórico se o baseline de produção mudou depois da auditoria;
- preservar índices IPCA anteriores durante sincronizações incrementais;
- manter a competência base do IPCA explícita;
- evitar reprocessamento quando um artefato auditado ainda estiver disponível;
- manter CI e build do frontend separados da operação de microdados.


## Enriquecimento populacional pós-publicação

Workflow: `Enrich published population`

Esse fluxo existe para competências já publicadas cujo Gold municipal foi gerado antes da disponibilidade da estimativa populacional oficial do mesmo ano.

Os alvos ficam em `config/population_release_targets.json`. Para cada alvo habilitado, o workflow:

1. valida a competência e a data oficial de referência;
2. consulta a tabela 6579, variável 9324, do SIDRA/IBGE;
3. grava o cache populacional versionado;
4. enriquece somente o Gold municipal já publicado;
5. preserva exatamente admissões, desligamentos e saldo;
6. exige população para todos os municípios identificados;
7. mantém o residual `999999` sem denominador;
8. calcula admissões, desligamentos e saldo por 100 mil habitantes;
9. gera relatório com SHA-256 antes/depois;
10. refaz o gate em modo estrito;
11. executa testes específicos e atualiza o visual do README;
12. versiona apenas os artefatos derivados.

O fluxo não baixa nem reprocessa MOV, FOR ou EXC.
