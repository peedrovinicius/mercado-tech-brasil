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

## Extração e inspeção de layout

A partir da RAIS 2024, o MTE informou mudança estrutural nos microdados públicos. Os arquivos compactados continuam em `.7z`, mas os arquivos de dados podem usar a extensão `.comt`, formato textual estruturado equivalente a CSV. O MTE também informou mudanças na nomenclatura e formatação de variáveis.

Por isso, o pipeline não assume que o layout histórico continua válido.

Extrair o Bronze anual:

```bash
python -m src.cli rais-extract 2025
```

Inspecionar os cabeçalhos realmente extraídos:

```bash
python -m src.cli rais-inspect 2025
```

A inspeção aceita `.comt`, `.txt` e `.csv`, detecta a codificação, identifica o delimitador, normaliza apenas os nomes para comparação e calcula uma assinatura SHA-256 do cabeçalho.

O resultado é salvo em:

```text
data/bronze/rais/2025/layout-report.json
```

O relatório registra, por arquivo:

- extensão;
- codificação detectada;
- delimitador;
- colunas originais;
- colunas normalizadas;
- quantidade de colunas;
- assinatura SHA-256 do layout.

`silver_ready` e `publication_ready` permanecem falsos. A inspeção estrutural não substitui a validação semântica com o dicionário oficial do ano.

## Contrato semântico

O contrato versionado fica em:

```text
config/rais_semantic_contract.yml
```

Ele define conceitos de negócio em vez de depender de um único nome literal de coluna. São obrigatórios:

- ano-base;
- ocupação CBO 2002;
- município;
- UF;
- indicador de vínculo ativo em 31/12.

Remuneração de dezembro e remuneração média são opcionais nesta etapa.

Executar a validação:

```bash
python -m src.cli rais-validate-layout 2025
```

A validação lê `layout-report.json` e gera:

```text
data/bronze/rais/2025/semantic-layout-report.json
```

Cada conceito obrigatório precisa produzir exatamente uma correspondência em cada layout. Ausência ou múltiplos aliases encontrados bloqueiam o Silver.

`silver_ready=true` significa apenas que o layout possui os conceitos mínimos sem ambiguidade. `publication_ready` continua falso até transformação, qualidade, reconciliação anual e gate específico.

## Perfil de valores

Depois de validar o layout semanticamente, o pipeline pode examinar uma amostra controlada dos conceitos obrigatórios:

```bash
python -m src.cli rais-profile-values 2025
```

O limite padrão é de 10.000 linhas por arquivo. Para alterar:

```bash
python -m src.cli rais-profile-values 2025 --max-rows-per-file 50000
```

O relatório é salvo em:

```text
data/bronze/rais/2025/value-profile.json
```

O perfil registra somente os conceitos necessários ao futuro Silver: ano, CBO, município, UF e vínculo ativo em 31/12. Para cada conceito ele informa valores mais frequentes, nulos, quantidade de valores distintos, comprimentos observados e quantos valores são compostos apenas por dígitos.

A amostra serve para confirmar a codificação real dos microdados 2025, principalmente o indicador de vínculo ativo e o formato da CBO. O perfil não escolhe automaticamente qual valor significa ativo.

`silver_transform_ready` e `publication_ready` continuam falsos até revisão explícita dessa semântica.

## Validação dos valores

A documentação oficial do MTE define a variável de situação em 31/12 por categorias:

- `SIM`: vínculo ativo ao final do ano;
- `NÃO`: vínculo inativo ao final do ano.

O projeto registra essa semântica em:

```text
config/rais_value_semantics.yml
```

Depois de gerar o perfil real:

```bash
python -m src.cli rais-validate-values 2025
```

O comando gera:

```text
data/bronze/rais/2025/value-semantics-report.json
```

A validação normaliza caixa e acentuação apenas para comparação. Valores diferentes de `SIM` e `NÃO`, nulos no indicador ativo ou ano-base divergente bloqueiam o Silver.

Se o microdado real usar outra codificação, como `1/0`, o pipeline não converte automaticamente. O contrato precisa ser revisado de forma explícita antes de qualquer transformação.

Quando a quantidade de valores distintos de um conceito é pequena, `value-profile.json` registra o conjunto completo observado para que códigos raros não fiquem escondidos pelo ranking de frequência.

`silver_transform_ready=true` libera apenas a construção técnica do Silver. A publicação continua bloqueada.

## Transformação Silver

Quando layout e valores estiverem aprovados, a transformação anual pode ser executada:

```bash
python -m src.cli rais-transform 2025
```

A transformação lê os arquivos extraídos em streaming e escreve Parquet em lotes, evitando carregar a RAIS anual inteira em memória.

São produzidos:

```text
data/silver/rais_tech_2025.parquet
data/silver/rais_rejected_2025.parquet
data/silver/rais_quality_2025.json
```

O Silver tech contém somente:

- ano-base;
- CBO completo;
- família CBO;
- código municipal observado;
- UF;
- confirmação de vínculo ativo em 31/12;
- arquivo de origem.

Somente vínculos ativos em 31/12 entram no estoque. Depois disso, o recorte CBO tech v2 é aplicado pelas famílias 2122, 2123, 2124, 3171 e 3172.

Registros com ano divergente, situação do vínculo desconhecida, CBO inválida, município ausente ou UF inválida são preservados no Parquet de rejeições com a razão correspondente.

O relatório de qualidade registra totais lidos, válidos, rejeitados, ativos, inativos e tech. Mesmo com Silver gerada, `gold_ready` e `publication_ready` permanecem falsos.

## Reconciliação anual

Antes de qualquer Gold, o estoque nacional bruto de vínculos ativos é comparado com a referência oficial do MTE.

Para 2025, o Sumário Executivo da RAIS informa:

`59.970.945 vínculos ativos`

A referência versionada fica em:

```text
config/rais_reference_totals.json
```

Executar:

```bash
python -m src.cli rais-reconcile 2025
```

A transformação Silver registra uma partição da fonte antes do recorte CBO:

- vínculos ativos do ano solicitado;
- vínculos inativos;
- status desconhecido;
- registros com ano divergente.

Essas categorias precisam fechar exatamente o total de linhas lidas. O gate exige também zero status desconhecido e zero ano divergente.

O total comparado com o MTE é `rows_active_source`, calculado antes das validações de CBO, município e UF. Assim, registros territoriais rejeitados não reduzem artificialmente o estoque nacional usado na reconciliação.

A diferença precisa ser exatamente zero. Qualquer divergência mantém `gold_ready=false`.

Quando a reconciliação passa, `gold_ready=true`, mas `publication_ready` continua falso.

O relatório é salvo em:

```text
data/silver/rais_reconciliation_2025.json
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
