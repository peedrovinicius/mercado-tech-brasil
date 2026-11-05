# Preparação do Novo CAGED — 202609

Status: **pré-auditoria; NÃO APROVADO PARA PUBLICAÇÃO**.

Issue de acompanhamento: #87.

## Fonte e divulgação
- Órgão: Ministério do Trabalho e Emprego (MTE/PDET).
- Competência: setembro de 2026 (`202609`).
- Divulgação anunciada para: 04/11/2026.
- Fonte oficial: https://www.gov.br/trabalho-e-emprego/pt-br/mte-divulga-dados-do-emprego-formal-de-setembro-nesta-quarta-feira-4
- Instruções oficiais de microdados: https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/estatisticas-trabalho/microdados-rais-e-caged

**Importante:** a divulgação dos resultados agregados não prova que os arquivos MOV, FOR e EXC estejam disponíveis, íntegros ou reconciliados. Não inferir nomes, hashes, contagens ou URLs de download.

## Bloqueios antes da auditoria
- [ ] Verificar a disponibilidade oficial de MOV, FOR e EXC para `202609`, anotando URL e data de acesso.
- [ ] Fazer download em ambiente controlado; registrar tamanho, SHA-256, origem, transporte e horário de ingestão em manifests.
- [ ] Validar layout e qualidade, incluindo registros rejeitados e ajustes históricos.
- [ ] Obter os totais nacionais exatos do MOV da referência oficial e conferir `admissoes - desligamentos = saldo`.
- [ ] Atualizar `config/reference_totals.json` apenas com números exatos e fonte oficial comprovada.
- [ ] Alterar `config/monthly_coverage_policy.json` para `202609` somente quando houver evidência suficiente de disponibilidade e elegibilidade.
- [ ] Executar auditoria incremental e revisão histórica estrita, mantendo a baseline `202608` intacta.
- [ ] Conferir Gold, metadados, cobertura populacional, testes, CI e segurança.
- [ ] Exigir aprovação metodológica humana vinculada aos hashes correntes e `publishable=true`.

## Publicação
Não fazer merge, deploy ou publicar dados enquanto qualquer gate obrigatório estiver pendente. Não marcar checks como aprovados por antecipação. RAIS 2025 não faz parte desta alteração.
