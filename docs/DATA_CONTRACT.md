# Contrato de Dados

## Movimentações Silver

Campos mínimos esperados após normalização:

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---:|---|
| competencia | date | sim | competência mensal |
| cbo_codigo | string | sim | código CBO normalizado |
| cbo_familia | string | sim | quatro primeiros dígitos |
| municipio_codigo | string | sim | código do município |
| uf | string | sim | UF |
| tipo_movimentacao | string | sim | admissão/desligamento |
| salario_mensal | decimal | não | salário mensalizado validado |
| fonte | string | sim | fonte de origem |

## Regras

- CBO deve conter somente dígitos após normalização.
- UF deve pertencer ao conjunto oficial.
- competência não pode ser futura em relação ao arquivo.
- salário negativo é inválido.
- registros sem campos essenciais devem ser contabilizados no relatório de qualidade.
- o pipeline não pode descartar registros silenciosamente.

## Relatório de qualidade

Cada execução deve produzir:

- total lido;
- total válido;
- total rejeitado;
- rejeições por regra;
- famílias CBO encontradas;
- UFs encontradas;
- período detectado.


## RAIS vínculos

A RAIS usa contrato próprio e separado do Novo CAGED.

### Conceitos mínimos para Silver

| Conceito | Obrigatório | Uso |
|---|---:|---|
| ano-base | sim | referência anual |
| CBO ocupação 2002 | sim | recorte ocupacional tech |
| município | sim | dimensão territorial |
| UF | sim | dimensão territorial |
| vínculo ativo em 31/12 | sim | definição do estoque anual |
| remuneração de dezembro | não | análise salarial futura |
| remuneração média | não | análise salarial futura |

Os nomes físicos podem mudar entre layouts. A resolução é feita por aliases versionados em `config/rais_semantic_contract.yml`.

O relatório estrutural não autoriza o Silver. Antes da transformação, `rais-validate-layout` exige uma correspondência única para cada conceito obrigatório em todos os layouts observados.

O estoque anual será calculado somente sobre vínculos classificados como ativos em 31/12. O código CBO completo será preservado e a família tech será derivada pelos quatro primeiros dígitos, usando o mesmo recorte versionado do projeto.
