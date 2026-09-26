# Operação de dados

## Objetivo

A operação mensal usa dois workflows manuais e reutilizáveis. O primeiro processa e audita. O segundo publica apenas um artefato já auditado e cuja aprovação metodológica está registrada no repositório.

Isso evita reprocessar microdados durante a publicação.

## Auditoria

Workflow: `Audit data competence`

Entradas:

- `competence`: competência no formato AAAAMM;
- `ipca_base`: competência base para valores reais. A série de 2026 usa 202607.

O workflow:

1. sincroniza referências do IBGE;
2. tenta baixar MOV, FOR e EXC;
3. usa FTP do MTE como transporte primário e HTTPS como fallback;
4. gera manifests e SHA-256;
5. transforma os dados;
6. produz Gold por UF, ocupação e município;
7. reconstrói ajustes;
8. executa os checks automáticos;
9. remove arquivos brutos antes de gerar o artefato;
10. publica um artefato temporário de auditoria por três dias.

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

- não publicar competência sem referência oficial;
- não publicar quando qualquer check bloqueante falhar;
- não reutilizar aprovação após mudança do SHA-256;
- manter a competência base do IPCA explícita;
- evitar reprocessamento quando um artefato auditado ainda estiver disponível;
- manter CI e build do frontend separados da operação de microdados.
