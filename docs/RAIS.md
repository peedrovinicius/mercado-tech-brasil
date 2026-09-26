# RAIS anual

## Objetivo

A RAIS complementa o Novo CAGED com uma perspectiva diferente do mercado formal.

O Novo CAGED mede fluxo mensal de admissões e desligamentos. A RAIS é anual e o conceito de estoque corresponde aos vínculos formais ativos em 31 de dezembro do ano-base.

Essas duas medidas não são somadas nem tratadas como equivalentes no produto.

## Fonte

Fonte oficial:

- Ministério do Trabalho e Emprego;
- Programa de Disseminação das Estatísticas do Trabalho;
- microdados públicos da RAIS;
- diretório oficial: `ftp://ftp.mtps.gov.br/pdet/microdados/RAIS/<ano>/`.

A edição mais recente confirmada na documentação do projeto é a RAIS 2025.

## Camada Bronze

A ingestão anual é separada do Novo CAGED:

```text
data/bronze/rais/<ano>/
└── archives/
    ├── RAIS_VINC_*.7z
    ├── *.manifest.json
    └── download-manifest.json
```

O comando padrão seleciona apenas arquivos de vínculos. Arquivos de estabelecimentos exigem seleção explícita.

Cada arquivo baixado recebe:

- SHA-256;
- tamanho;
- ano-base;
- URL oficial;
- transporte;
- timestamp de ingestão;
- dataset RAIS correspondente.

## Descoberta

Listar os arquivos de vínculos disponíveis:

```bash
python -m src.cli rais-discover 2025
```

Baixar a camada Bronze:

```bash
python -m src.cli rais-download 2025
```

Arquivos de estabelecimentos não entram no download padrão:

```bash
python -m src.cli rais-download 2025 --dataset estabelecimentos
```

## Regra de publicação

A existência do Bronze RAIS não autoriza a publicação de métricas.

Antes de entrar no serving, a camada anual ainda precisa de:

1. contrato de layout validado;
2. transformação Silver;
3. recorte CBO v2 aplicado de forma documentada;
4. reconciliação com referência anual oficial;
5. Gold de estoque anual;
6. testes;
7. gate de publicação específico para RAIS.

Até esse ciclo ser concluído, o dashboard público continua exibindo somente indicadores derivados das competências do Novo CAGED já aprovadas.

## Separação conceitual

A futura métrica de estoque tech será apresentada como:

`estoque anual de vínculos tech ativos em 31/12`

Ela não será chamada de admissão, saldo ou movimentação e não será usada para preencher meses ausentes do Novo CAGED.
