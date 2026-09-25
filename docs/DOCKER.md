# Execução com Docker

## Subir aplicação completa

```bash
docker compose up --build
```

Serviços:

- Frontend: http://localhost:8080
- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- PostgreSQL: localhost:5432

## Dados

`./data` é montado no container da API. Assim, Bronze/Silver/Gold permanecem no projeto local e não desaparecem ao recriar o container.

## Observação

A imagem do frontend precisa de acesso ao registro npm durante o primeiro build.
A imagem da API precisa de acesso ao PyPI durante o primeiro build.
