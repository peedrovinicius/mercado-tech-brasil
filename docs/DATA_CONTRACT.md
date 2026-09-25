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
