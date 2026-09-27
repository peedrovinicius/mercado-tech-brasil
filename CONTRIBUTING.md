# Contribuindo

Contribuições são bem-vindas quando preservam a rastreabilidade, a metodologia e a reprodutibilidade do projeto.

## Antes de começar

1. Procure uma issue aberta relacionada ao tema.
2. Se a mudança não estiver registrada, abra uma issue descrevendo problema, motivação e escopo.
3. Para alterações metodológicas, informe explicitamente qual indicador, fonte, recorte ou regra de publicação será afetado.

## Fluxo recomendado

1. Crie uma branch curta e específica a partir de `main`.
2. Faça uma alteração por tema.
3. Inclua ou atualize testes quando houver mudança de comportamento.
4. Execute as validações locais aplicáveis.
5. Abra um Pull Request com contexto suficiente para revisão.

Backend e dados:

```bash
ruff check src tests
pytest -q
```

Frontend:

```bash
cd frontend
npm install --no-audit --no-fund
npm run build
```

## Regras de qualidade

- não alterar resultados publicados sem evidência e reconciliação;
- não misturar mudança metodológica com refatoração sem necessidade;
- preservar hashes, manifests e gates de publicação quando aplicáveis;
- não versionar microdados brutos;
- documentar mudanças em contratos de API, fontes, indicadores ou recorte CBO;
- manter commits e Pull Requests com escopo claro.

## Pull Requests

Inclua no PR:

- problema resolvido;
- arquivos ou componentes afetados;
- testes ou validações executados;
- impacto metodológico, quando houver;
- evidência visual apenas quando a mudança for de interface.

Mudanças pequenas e bem delimitadas são preferíveis a PRs muito amplos.
