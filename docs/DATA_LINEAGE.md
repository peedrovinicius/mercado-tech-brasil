# Data lineage

```text
MTE / FTP oficial
      |
      | .7z
      v
data/bronze/<AAAAMM>/archives
      |
      | extração imutável + SHA-256
      v
data/bronze/<AAAAMM>/extracted
      |
      | contrato de layout + regras de qualidade
      v
data/silver/caged_tech_<AAAAMM>.parquet
      |                     \
      |                      -> caged_rejected_<AAAAMM>.parquet
      v
data/gold/market-<AAAAMM>.parquet
      |
      +-> overview-<AAAAMM>.json -> FastAPI
      |
      +-> quality-<AAAAMM>.json  -> FastAPI
```

## Regra central

Não existe caminho direto `raw -> dashboard`.

Todo número visível deve atravessar:

1. fonte;
2. manifesto;
3. validação;
4. transformação;
5. camada Gold;
6. API.

Isso permite rastrear um indicador até o arquivo de origem e detectar alterações de layout antes da publicação.
