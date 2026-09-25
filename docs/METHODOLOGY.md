# Metodologia

## Unidade básica

O Novo CAGED representa movimentações do emprego formal. Portanto, admissões e desligamentos são **fluxos**, e não o estoque total de pessoas empregadas.

Essa diferença deve permanecer explícita na interface e na documentação.

## Saldo

`saldo = admissões - desligamentos`

## Salário médio de admissão

Calculado somente sobre movimentações classificadas como admissão e com salário considerado válido após as regras de qualidade.

A aplicação deve exibir também mediana quando a amostra permitir, reduzindo a dependência de uma única medida sensível a extremos.

## Salário real

Será criado posteriormente a partir de índice oficial do IBGE, com mês-base documentado.

## Indicadores relativos

Para comparar municípios de tamanhos muito diferentes, a aplicação deverá incluir métricas normalizadas, como admissões de TI por 100 mil habitantes.

## Recorte de tecnologia

O recorte CBO é versionado em `config/cbo_tech.yml`.

Nenhuma ocupação deve entrar ou sair silenciosamente. Toda mudança exige:

- alteração do arquivo;
- nova versão;
- justificativa;
- teste de regressão dos indicadores.

## Limitações

O projeto analisa emprego formal captado pelas fontes utilizadas. Não deve ser apresentado como representação completa de todo o trabalho em tecnologia, especialmente trabalho informal, prestação PJ, trabalho independente e outras relações não observadas pelo indicador.
