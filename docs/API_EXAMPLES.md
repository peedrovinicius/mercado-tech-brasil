# Exemplos de consumo da API pública

Guia curto com exemplos reproduzíveis para consumir os endpoints públicos da API.
Todos os comandos abaixo funcionam contra a aplicação em produção:

```
https://mercado-tech-brasil.onrender.com
```

Os exemplos usam apenas `curl` — nenhum dado fictício é apresentado como
resultado oficial. As respostas reais variam conforme a competência (mês)
publicada no momento.

## Convenções

- O prefixo `/api/v1` é obrigatório em todos os endpoints de dados.
- `GET` é o único método aceito pelos routers públicos.
- Cada resposta 200 tem o cabeçalho `X-Request-ID` (identificador do pedido).
- Quando um endpoint ainda não tem dados publicados, a resposta é `503` com um
  `detail` em português que explica o motivo.

## 1. Health check

Confirma que a API está no ar e qual backend de dados está em uso.

```bash
curl -sS https://mercado-tech-brasil.onrender.com/api/v1/system/health
```

Exemplo de resposta:

```json
{
  "status": "ok",
  "project": "Mercado Tech Brasil",
  "version": "0.40.0",
  "environment": "production",
  "data_backend": "files"
}
```

## 2. Overview da competência publicada

Retorna o resumo agregado da competência (mês) mais recente aprovada pelo
gate de publicação.

```bash
curl -sS https://mercado-tech-brasil.onrender.com/api/v1/indicators/overview
```

Se ainda não houver competência aprovada, a API responde `503`:

```json
{
  "detail": "Indicadores ainda não disponíveis. O projeto não publica números antes da ingestão e validação dos dados oficiais."
}
```

Tratamento sugerido em clientes:

```bash
resp="$(curl -sS -w '%{http_code}' -o /tmp/overview.json \
  https://mercado-tech-brasil.onrender.com/api/v1/indicators/overview)"
if [ "$resp" = "503" ]; then
  echo "Ainda não há competência publicada — ler /tmp/overview.json para o motivo."
  cat /tmp/overview.json
fi
```

## 3. Endpoint analítico: ocupações

Retorna as ocupações de tecnologia com maior volume de admissões no mês
publicado, limitada ao parâmetro `limit` (1 a 50, padrão 10).

```bash
curl -sS "https://mercado-tech-brasil.onrender.com/api/v1/analytics/by-occupation?limit=5"
```

Outros recortes analíticos existentes (mesma base de parâmetros `limit`):

- `GET /api/v1/analytics/by-uf?limit=27` — ranking por UF (1 a 27).
- `GET /api/v1/analytics/by-municipality?limit=20&metric=admissions` — ranking
  municipal (`metric` aceita `admissions` ou `admissions_per_100k`).
- `GET /api/v1/analytics/trend` — série histórica de competências publicadas.
- `GET /api/v1/analytics/temporal-summary` — agregação trimestral.

## 4. Tratamento de erro

Quando o dado solicitado ainda não foi aprovado pelo gate de publicação, a API
retorna `503` com um `detail` em português que descreve o motivo. Isso é
esperado durante o período de construção do projeto — não é um defeito.

Regras para clientes:

- Não fazer *retry* agressivo: o status só muda quando a competência seguinte
  é publicada pelo pipeline mensal.
- Preservar o corpo da resposta (o campo `detail`) para exibir ao usuário.
- Para o health check (`/api/v1/system/health`), a resposta é sempre `200`
  quando o processo está vivo; `503` nos endpoints de dados indica dado
  ausente, não API fora do ar.

## Onde encontrar a documentação interativa

A especificação OpenAPI completa está disponível em:

- Swagger UI: `https://mercado-tech-brasil.onrender.com/docs`
- JSON da API: `docs/openapi.json` neste repositório

## Notas de segurança

- Não inclua tokens, senhas ou credenciais nestes exemplos: a API pública
  não exige autenticação.
- Use apenas os endpoints listados acima; endpoints internos de ingestão
  (`/api/v1/internal/*`, scripts de pipeline) não fazem parte da superfície
  pública.
