# Exemplos de consumo da API

A API pública está disponível em `https://mercado-tech-brasil.onrender.com`. Estes exemplos usam
apenas requisições `GET` a endpoints já publicados. O conteúdo dos indicadores acompanha a última
competência aprovada e pode mudar após uma nova publicação.

## Verificar a disponibilidade

```sh
curl --fail --show-error --silent \
  https://mercado-tech-brasil.onrender.com/api/v1/system/health
```

## Consultar o overview publicado

```sh
curl --fail --show-error --silent \
  https://mercado-tech-brasil.onrender.com/api/v1/indicators/overview
```

A resposta apresenta o resumo da competência mais recente publicada, incluindo admissões,
desligamentos e saldo.

## Consultar admissões por UF

```sh
curl --fail --show-error --silent \
  'https://mercado-tech-brasil.onrender.com/api/v1/analytics/by-uf?limit=2'
```

O parâmetro `limit` aceita valores de 1 a 27. A resposta contém a competência, a fonte e os itens
retornados.

## Ver uma resposta de validação

```sh
curl --include --silent --show-error \
  'https://mercado-tech-brasil.onrender.com/api/v1/analytics/by-uf?limit=0'
```

Esse exemplo envia um limite inválido de propósito. O endpoint responde com HTTP `422` e informa a
validação do parâmetro. Não use `--fail` nesse comando, para que o corpo da resposta de erro também
seja exibido.
