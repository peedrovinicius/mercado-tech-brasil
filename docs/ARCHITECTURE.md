# Arquitetura

## Decisão principal

O projeto adota uma arquitetura de dados em três camadas.

### Bronze

Armazena o arquivo original exatamente como obtido da fonte pública.

Cada arquivo deve ter um manifesto contendo:

- origem;
- competência;
- URL de referência;
- timestamp de ingestão;
- tamanho;
- SHA-256;
- nome original.

A Bronze é imutável.

### Silver

Converte o dado para formato colunar Parquet e aplica:

- padronização de nomes;
- tipagem;
- normalização de CBO;
- normalização territorial;
- tratamento de ausências;
- validação das categorias;
- flags de qualidade.

### Gold

Agregados prontos para consumo:

- indicadores nacionais;
- indicadores por UF;
- indicadores por município;
- indicadores por ocupação;
- séries temporais;
- remuneração;
- métricas normalizadas por população.

## Por que Parquet + DuckDB

Os microdados são grandes. Parquet reduz armazenamento e leitura desnecessária; DuckDB permite consultar arquivos colunares localmente sem exigir que todos os registros sejam carregados no PostgreSQL.

O PostgreSQL funciona como serving database para as tabelas Gold consumidas pela API.

## Não usar Spark inicialmente

Spark acrescentaria complexidade operacional sem necessidade comprovada. O projeto só deverá migrar para processamento distribuído se benchmarks demonstrarem que Polars/DuckDB deixaram de atender.

Essa decisão é intencional e deve ser apresentada como trade-off técnico.
