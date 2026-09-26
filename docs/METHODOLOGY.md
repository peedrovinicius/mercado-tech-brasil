# Metodologia

## Unidade básica

O Novo CAGED representa movimentações do emprego formal. Portanto, admissões e desligamentos são **fluxos**, e não o estoque total de pessoas empregadas.

Essa diferença permanece explícita na interface e na documentação.

## Saldo

`saldo = admissões - desligamentos`

## Salário médio e mediano de admissão

A partir da v0.9, o projeto reproduz a regra de elegibilidade publicada pelo MTE no Sumário Executivo do Novo Caged.

Para julho de 2026, o MTE informa que o cálculo do salário médio de admissão:

- não inclui valores menores que 0,3 salário mínimo;
- não inclui valores maiores que 150 salários mínimos;
- não inclui vínculos da modalidade intermitente.

O salário mínimo nacional vigente em 2026 é de R$ 1.621,00. Portanto, para competências de 2026, os limites implementados são:

- mínimo incluído: R$ 486,30;
- máximo incluído: R$ 243.150,00.

Os limites são inclusivos porque a documentação oficial exclui valores **menores que** 0,3 salário mínimo e **maiores que** 150 salários mínimos.

A média e a mediana de tecnologia usam exatamente o mesmo critério de elegibilidade, mas continuam sendo métricas do **recorte CBO de tecnologia**. Elas não devem ser comparadas como se fossem a média de todo o mercado formal.

Se a coluna necessária para identificar trabalho intermitente estiver ausente, o pipeline falha explicitamente e não publica a métrica salarial.

Fonte metodológica:
`config/official_reference_202607.json`

## Referência oficial de julho/2026

O projeto versiona uma referência externa extraída do Sumário Executivo oficial do MTE para permitir testes de reconciliação.

Para julho de 2026:

- Brasil: 2.262.888 admissões, 2.204.320 desligamentos e saldo +58.568;
- Ceará: 61.739 admissões, 57.558 desligamentos e saldo +4.181;
- salário médio nominal de admissão no Brasil: R$ 2.419,23;
- salário médio nominal de admissão no Ceará: R$ 2.173,94.

A referência contém todas as 27 UFs, as cinco regiões e os registros não identificados. Testes garantem que:

1. admissões - desligamentos = saldo;
2. cada região é exatamente a soma de suas UFs;
3. Brasil = 27 UFs + registros não identificados.

Essa referência é um **benchmark de reconciliação**. Ela não transforma o recorte de tecnologia em total do mercado, nem autoriza comparar diretamente um MOV isolado com números publicados que incluam ajustes.

## Salário real

Será criado posteriormente a partir de índice oficial do IBGE, com mês-base documentado.

## Indicadores relativos

Para comparar municípios de tamanhos muito diferentes, a aplicação deverá incluir métricas normalizadas, como admissões de TI por 100 mil habitantes.

## Recorte de tecnologia

O recorte CBO é versionado em `config/cbo_tech.yml`.

A versão 2 inclui as famílias 2122, 2123, 2124, 3171 e 3172. A inclusão de 2122 corrige uma omissão da versão inicial: o MTE classifica 2122 — Engenheiros em computação junto a 2123 e 2124 no grupo 212 — Profissionais da Informática. As famílias 3171 e 3172 pertencem ao grupo 317 — Técnicos em Informática.

O recorte é ocupacional, não setorial. A atividade econômica do empregador não determina, por si só, se o vínculo entra no indicador.

Nenhuma ocupação entra ou sai silenciosamente. Toda mudança exige:

- alteração do arquivo;
- nova versão;
- justificativa;
- fonte oficial;
- teste de regressão dos indicadores.

Detalhes: `docs/CBO_SCOPE.md`.

## Limitações

O projeto analisa emprego formal captado pelas fontes utilizadas. Não deve ser apresentado como representação completa de todo o trabalho em tecnologia, especialmente trabalho informal, prestação PJ, trabalho independente e outras relações não observadas pelo indicador.
