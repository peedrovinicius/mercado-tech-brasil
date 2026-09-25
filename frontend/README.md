# Frontend — Mercado Tech Brasil

Interface React + TypeScript para consumir exclusivamente a API do projeto.

## Princípios

- nenhum indicador é fixado no frontend;
- sem dados oficiais, a interface mostra um estado vazio explícito;
- erros de backend têm estado visual próprio;
- gráficos só aparecem quando endpoints Gold estão disponíveis;
- metodologia e rastreabilidade ficam acessíveis na própria experiência.

## Executar

```bash
npm install
npm run dev
```

Por padrão o frontend acessa:

```text
http://localhost:8000/api/v1
```

Para alterar:

```bash
cp .env.example .env
```

Defina `VITE_API_BASE_URL`.

## Build

```bash
npm run build
```

## Telas/estados implementados

- dashboard principal;
- loading/skeleton;
- API indisponível;
- pipeline sem dados publicados;
- indicadores reais;
- admissões por UF;
- saldo por CBO;
- painel de qualidade;
- modal “Como este número foi calculado?”.
