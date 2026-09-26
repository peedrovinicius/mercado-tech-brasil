# PostgreSQL serving

A camada PostgreSQL recebe apenas competências que já passaram pelo pipeline e pelo gate de publicação.

## Modelo

### dataset_release

Uma linha por competência publicada, incluindo:

- fonte;
- SHA-256 do MOV;
- admissões;
- desligamentos;
- saldo;
- salários médio e mediano;
- taxa de registros válidos;
- timestamp da carga.

### fact_market_uf

Indicadores por competência e UF.

### fact_market_occupation

Indicadores por competência, família CBO e ocupação.

## Migração

```bash
alembic upgrade head
```

A URL vem de `DATABASE_URL`.

## Carga

```bash
python -m src.cli load-postgres 202607
```

A carga reavalia o gate. Se a competência não estiver aprovada ou se o SHA-256 atual não corresponder à aprovação, o comando termina sem alterar o banco.

## Idempotência e transação

Para a competência solicitada, o loader:

1. abre uma transação;
2. remove somente as linhas daquele mês;
3. grava a release;
4. grava UF e CBO;
5. confere as contagens;
6. faz commit somente se tudo estiver coerente.

Qualquer exceção provoca rollback.

## API

Por padrão, o desenvolvimento local ainda pode ler os JSONs Gold:

```bash
DATA_BACKEND=files uvicorn src.api.main:app --reload
```

Para servir do PostgreSQL:

```bash
DATA_BACKEND=postgres uvicorn src.api.main:app --reload
```

No Docker Compose, o backend PostgreSQL é o padrão.

## Testes

O CI usa SQLite para validar:

- criação do schema;
- carga;
- substituição idempotente;
- consultas;
- bloqueio sem aprovação;
- aceite com aprovação vinculada ao SHA.

Isso evita iniciar um container PostgreSQL em todo commit e reduz o consumo de GitHub Actions.
