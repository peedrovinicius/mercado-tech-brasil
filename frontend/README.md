# Frontend: Mercado Tech Brasil

Interface React + TypeScript para a camada pública de análise do Mercado Tech Brasil.

## Estado atual

O frontend consome exclusivamente a API do projeto e apresenta a série publicada de janeiro a julho de 2026 sem manter indicadores fixos no código da interface.

A experiência atual inclui:

- hero com fonte, competência mais recente, cobertura e backend ativo;
- contexto oficial do mercado formal total separado do recorte de tecnologia;
- indicadores de admissões, desligamentos, saldo e remuneração;
- comparação Brasil, Nordeste e Ceará;
- gráficos por UF, município, ocupação e série histórica;
- painel de qualidade dos dados;
- proveniência com SHA-256;
- metodologia acessível na própria interface;
- estados de carregamento, ausência de dados e indisponibilidade da API;
- responsividade para desktop, tablet e celular;
- configuração responsiva e ARIA nos gráficos ECharts.

## Princípios

- nenhum indicador tech é fixado no frontend;
- o mercado formal total nunca é apresentado como recorte de tecnologia;
- a competência exibida depende do que foi efetivamente publicado pela API;
- dados ausentes usam estado explícito em vez de valores demonstrativos;
- metodologia, qualidade e proveniência permanecem visíveis ao usuário;
- a interface respeita foco visível e preferência por redução de movimento.

## Desenvolvimento local

Instale as dependências e inicie o Vite:

```bash
npm install
npm run dev
```

Durante o desenvolvimento, o Vite encaminha chamadas de `/api/*` para:

```text
http://localhost:8000
```

O backend pode ser iniciado na raiz do projeto com:

```bash
uvicorn src.api.main:app --reload
```

## API

Em produção, frontend e API usam o mesmo domínio e o frontend utiliza `/api/v1`.

Para apontar o frontend para outro backend no desenvolvimento, copie o arquivo de exemplo e defina `VITE_API_BASE_URL`:

```bash
cp .env.example .env
```

## Build

```bash
npm run build
```

O build executa TypeScript e Vite. Na imagem de produção, os arquivos gerados em `frontend/dist` são servidos pelo FastAPI.

## Fonte e escopo

A fonte principal é o Novo CAGED do Ministério do Trabalho e Emprego. O contexto oficial do mercado formal total é identificado separadamente para não ser confundido com o recorte ocupacional de tecnologia.
