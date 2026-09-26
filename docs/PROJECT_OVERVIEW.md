# Visão técnica

## Objetivo

Transformar fontes públicas de emprego formal em indicadores de tecnologia com rastreabilidade suficiente para reproduzir cada resultado a partir do arquivo de origem.

## Estado atual

A aplicação publica uma série auditada de janeiro a julho de 2026. Julho de 2026 é a competência mais recente disponível no produto.

| Indicador de Jul/2026 | Valor |
|---|---:|
| Admissões tech no Brasil | 19.253 |
| Desligamentos tech no Brasil | 18.347 |
| Saldo tech no Brasil | +906 |
| Admissões tech no Nordeste | 1.951 |
| Desligamentos tech no Nordeste | 1.796 |
| Saldo tech no Nordeste | +155 |
| Admissões tech no Ceará | 522 |
| Desligamentos tech no Ceará | 415 |
| Saldo tech no Ceará | +107 |

A comparação territorial Brasil, Nordeste e Ceará é calculada a partir dos agregados por UF da competência publicada. O Ceará responde por 26,76% das admissões tech do Nordeste em julho de 2026.

## Componentes

### Ingestão

Obtém ou recebe o arquivo oficial, preserva a origem na Bronze e gera o manifesto de proveniência.

### Transformação

Aplica normalização, tipagem, regras de qualidade e recorte CBO. Registros que falham nas regras são preservados separadamente.

### Agregação

Produz artefatos Gold por competência, UF, município e ocupação, além da série histórica publicada.

### Gate de publicação

Combina verificações automáticas e revisão metodológica. A aprovação é vinculada ao SHA-256 do arquivo MOV. Trocar a origem invalida a aprovação anterior.

### Serving

Competências aprovadas podem ser carregadas no PostgreSQL por uma operação transacional e idempotente. A aplicação também mantém suporte ao serving por arquivos publicados.

### API e frontend

FastAPI expõe contratos versionados. React + TypeScript consome a API e apresenta indicadores nacionais, territoriais, por UF, município, ocupação, série histórica, qualidade e proveniência.

## Decisões principais

- Parquet para armazenamento analítico;
- Polars para transformação;
- DuckDB para análise e validação local;
- PostgreSQL para agregados publicados;
- FastAPI para contratos HTTP e OpenAPI;
- React + TypeScript para a interface;
- microdados brutos fora do Git;
- CI sem processamento de bases completas;
- publicação condicionada à reconciliação e ao gate.

## Garantias de integridade

- SHA-256 da origem;
- detecção de schema drift;
- rejeições auditáveis;
- recorte CBO versionado;
- metodologia documentada;
- reconciliação com referências oficiais;
- gate antes do serving;
- constraints no banco;
- testes de aritmética, publicação e consistência territorial.

## Estado dos dados

As competências de janeiro a julho de 2026 estão publicadas no recorte de tecnologia. O MOV de cada mês é reconciliado com a referência nacional do MTE, enquanto FOR e EXC são aplicados às competências de origem antes da construção dos agregados finais.

A aplicação pública utiliza julho de 2026 como competência mais recente para os painéis de recorte territorial e detalhamento analítico.
