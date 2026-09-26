# Frontend: Mercado Tech Brasil

Interface React + TypeScript para consumir exclusivamente a API do projeto.

## Princípios

- nenhum indicador tech é fixado no frontend;
- sem microdados tech aprovados, a interface continua útil com contexto oficial separado;
- contexto do mercado formal total nunca é apresentado como recorte de tecnologia;
- erros de backend têm estado visual próprio;
- metodologia e rastreabilidade ficam acessíveis na própria experiência;
- responsividade para desktop, tablet e mobile.

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

## Experiência v0.11

- hero de produto;
- pipeline visual;
- contexto oficial Brasil/Ceará;
- gráfico de saldo por região;
- estado de espera elegante;
- indicadores tech quando publicados;
- admissões tech por UF;
- saldo por CBO;
- painel de qualidade;
- proveniência por SHA-256;
- modal de metodologia.

O contexto oficial vem da API e é claramente rotulado como **mercado formal total**, não como indicador de tecnologia.
