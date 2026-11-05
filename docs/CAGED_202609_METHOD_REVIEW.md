# Parecer técnico para revisão metodológica: Novo CAGED 202609

**Status: pronto para revisão humana; NÃO APROVADO PARA PUBLICAÇÃO.**

Issue: #87. Competência: setembro de 2026. Revisão independente elaborada sobre o artefato da auditoria da `main`, executada no GitHub Actions em 05/11/2026.

## Evidência primária e integridade

- Auditoria integrada aprovada: https://github.com/peedrovinicius/mercado-tech-brasil/actions/runs/42118600648
- Artefato `caged-202609-audit` dessa execução (ID 13457008812; retenção limitada do GitHub Actions).
- Fonte oficial Novo CAGED: https://www.gov.br/trabalho-e-emprego/pt-br/noticias-e-conteudo/2026/novembro/pais-gerou-1-248-mil-empregos-formais-ate-setembro-de-2026
- MOV nacional: **2.214.437 admissões**, **2.093.132 desligamentos**, **saldo +121.305**. Totais do microdado coincidem com a referência do MTE.
- FTP oficial MOV `CAGEDMOV202609.7z`: 49.478.375 bytes; SHA-256 `967a29800166b32ba4f9d786e95b53122eed6dbd78ca94da783290d67cd5d50d`.
- FTP oficial FOR `CAGEDFOR202609.7z`: 1.056.240 bytes; SHA-256 `2646a98e115577be8606fb0f3ba772a2e5dde7e749211a35065f2cce8f13c056`.
- FTP oficial EXC `CAGEDEXC202609.7z`: 53.017 bytes; SHA-256 `96cd1af3eac03ec65e0dd12693f9fa4669ca3c049bbc21b6fc1d45f862124ba8`.
- SHA-256 do arquivo MOV extraído, usado para vincular a aprovação: **`9a8b6bdb17e0097ae3d3e7cc8e9460f75888a5f58cb05d27d74f7728d9b3b567`**.
- SHA-256 da referência estatística no gate: **`8b4a4e177bc7fd47a5ae5fea991a200c0462c449d4ef6b07d5843f03f691226d`**.

## Qualidade e escopo tecnológico

| Indicador | Resultado auditado |
|---|---:|
| MOV nacional (linhas) | 4.307.569 |
| MOV rejeitado | 0 |
| MOV taxa de validade | 100% |
| MOV recorte tecnológico | 35.527 |
| FOR linhas / rejeitadas / tech | 91.861 / 0 / 682 |
| EXC linhas / rejeitadas / tech | 4.161 / 0 / 15 |
| Admissões tech no MOV | 18.346 |
| Desligamentos tech no MOV | 17.181 |
| Saldo tech no MOV | **+1.165** |
| Média salarial nominal admissão tech | R$ 6.134,61 |
| Mediana salarial nominal admissão tech | R$ 4.000,00 |

O recorte tecnológico é definido pela configuração CBO do projeto, **não** equivale à totalidade do mercado de tecnologia nem ao saldo nacional total.

Foi refeita uma conferência dos arquivos Gold derivados: os 27 agregados por UF, os 19 por CBO e os 1.265 por município somam exatamente **18.346 admissões, 17.181 desligamentos e +1.165**. Não há códigos municipais duplicados nos 1.265 itens, nem estimativas de população ausentes. São **1.265 municípios presentes no recorte**, não 5.571 municípios com movimentações tech.

## População, inflação e histórico

- Referência populacional: IBGE SIDRA, ano 2026, data 01/07/2026. Relatório de enriquecimento: 1.265 municípios identificados, 1.265 com população, zero faltantes; os totais do recorte não mudaram após enriquecer.
- Contingência territorial: DTB 2025 oficial IBGE, identificada por SHA-256 `d077a0e48c36cf18bcc96268b4a436200c014c6b8522c1a62d894acaf39dad27`; 5.571 municípios verificados.
- Série de IPCA: setembro de 2026 com variação oficial de **0,82%**, referência https://www.ibge.gov.br/indicadores/inflacao. Valores internos do índice estão documentados em `data/reference/ipca.json`; os salários reais utilizam base julho de 2026.
- Revisão histórica estrita executada: `passed=true`, `changed_published_competencies=[]`, `unexpected_changed_competencies=[]`, `packaged_files=[]`.
- **Ponto de atenção obrigatório:** FOR e EXC contêm registros de competências históricas. A ausência de revisões empacotadas deve ser confrontada com a metodologia de aplicação de ajustes e com a baseline vigente antes da autorização humana; não inferir que ajustes históricos inexistem.

## Resultado do gate

`automatic_checks_passed = true`, `manual_approval_valid = false`, `publishable = false`.

Todos os checks automáticos e de reconciliação passaram, após enriquecimento populacional. O gate bloqueante `manual_methodology_approval` permanece falso. A aprovação humana deve estar vinculada aos **hashes exatos** acima; não reutilizar aprovações antigas.

## Checklist para responsável metodológico

- [ ] Conferi a correspondência entre fonte MTE, competência, layout e hashes MOV/FOR/EXC.
- [ ] Conferi a identidade do saldo nacional e o recorte CBO versionado.
- [ ] Conferi médias e medianas salariais, exclusões e a base de deflação IPCA.
- [ ] Conferi a dimensão municipal, o residual e a referência populacional.
- [ ] Analisei FOR/EXC e eventuais revisões históricas, inclusive o relatório sem arquivos empacotados.
- [ ] Estou ciente do recorte metodológico e das limitações da divulgação.
- [ ] Revalidei que os hashes atuais são os mesmos desta revisão.

**Somente após essas verificações:** um responsável humano pode preencher `config/publication_approvals.json` para `202609` com o revisor real, data UTC de aprovação, justificativa, `source_sha256` e `reference_sha256`, seguindo o formato da configuração existente. Abrir PR exclusivo de aprovação; exigir os checks de CI; então usar os workflows governados para gerar PR de publicação dos derivados Gold e fazer deploy.

Esta documentação **não representa assinatura ou aprovação**. Nenhum dado Gold 202609 foi publicado por este parecer. A baseline de produção continua em 202608 até que o gate completo se torne `publishable=true`.
