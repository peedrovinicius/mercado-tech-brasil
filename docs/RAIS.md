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

Ele define conceitos de negócio em vez de depender de um único nome literal de coluna.

A validação com uma amostra oficial real da RAIS 2025 confirmou o layout atual de vínculos. Os campos físicos obrigatórios são:

- `CBO 2002 Ocupação - Código`;
- `Município - Código`;
- `Ind Vínculo Ativo 31/12 - Código`.

O ano-base não existe como coluna no arquivo regional de vínculos e é derivado do contexto anual do pipeline. A UF também não existe como coluna física e é derivada do prefixo do código municipal.

`Município Trab - Código` é preservado como conceito opcional e não substitui `Município - Código` como dimensão territorial principal nesta etapa.

Remuneração de dezembro e remuneração média permanecem opcionais.

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

O perfil registra os conceitos físicos CBO, município e vínculo ativo, além do ano derivado do contexto anual. Para cada conceito ele informa valores mais frequentes, nulos, quantidade de valores distintos, comprimentos observados e quantos valores são compostos apenas por dígitos.

Na amostra oficial de 10.000 registros do arquivo `RAIS_VINC_PUB_NORTE.COMT`:

- o indicador de vínculo ativo apresentou apenas `1` e `0`;
- `1` apareceu em 7.227 registros;
- `0` apareceu em 2.773 registros;
- não houve valor nulo ou terceiro código;
- o município apareceu em seis dígitos em todos os 10.000 registros;
- a CBO foi numérica em todos os registros, com códigos de cinco e seis dígitos observados.

A CBO 2002 define ocupações em seis dígitos. Por isso, códigos numéricos de cinco dígitos são normalizados com zero à esquerda antes da derivação da família ocupacional.

`publication_ready` continua falso até o ciclo anual completo.

## Validação dos valores

A consulta oficial da RAIS apresenta a situação em 31/12 pelas categorias SIM e NÃO. Nos microdados, a amostra oficial de 2025 confirmou a codificação numérica usada no arquivo de vínculos:

- `1`: vínculo ativo em 31/12;
- `0`: vínculo inativo em 31/12.

Essa codificação também é consistente com documentação técnica que utiliza a variável de vínculo ativo igual a `1` para selecionar o estoque de 31 de dezembro.

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

Para a RAIS 2025, valores diferentes de `1` e `0`, valores nulos no indicador ativo ou ano-base contextual divergente bloqueiam o Silver.

A codificação não é inferida em tempo de execução. Ela está versionada em `config/rais_value_semantics.yml` e qualquer código novo ou desconhecido exige revisão explícita.

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

O ano é fixado pelo contexto anual validado, e a UF é derivada do prefixo municipal oficial. Registros com situação de vínculo desconhecida, CBO inválida, município inválido ou prefixo de UF desconhecido são preservados no Parquet de rejeições com a razão correspondente.

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

## Gold anual

Depois de uma reconciliação exata com `gold_ready=true`, os agregados anuais podem ser gerados:

```bash
python -m src.cli rais-gold 2025
```

O Gold anual é separado dos artefatos mensais do Novo CAGED e produz:

```text
data/gold/rais-overview-2025.json
data/gold/rais-by-uf-2025.json
data/gold/rais-by-cbo-family-2025.json
data/gold/rais-market-2025.parquet
```

O overview registra:

- estoque tech ativo em 31/12;
- estoque nacional ativo usado na reconciliação;
- participação do estoque tech no total nacional;
- versão do recorte CBO;
- quantidade de UFs;
- status da reconciliação.

O agregado por UF registra estoque ativo e participação no estoque tech. O agregado por família CBO registra estoque, denominação da família e participação no estoque tech.

O Parquet Gold agrega por UF, família CBO e CBO completa.

Município não entra nesta primeira camada Gold da RAIS. O sistema territorial observado nos microdados 2025 ainda precisa ser confirmado antes de qualquer enriquecimento municipal anual.

Todos os artefatos são gerados com `publication_ready=false`. A existência do Gold não autoriza serving ou dashboard.

## Gate anual de publicação

Depois do Gold, a release anual ainda permanece fora do serving até passar pelo gate específico da RAIS.

Executar os checks:

```bash
python -m src.cli rais-validate-release 2025
```

Para exigir código de saída 2 enquanto a release não estiver publicável:

```bash
python -m src.cli rais-validate-release 2025 --strict
```

O gate verifica:

- proveniência dos arquivos anuais de origem com SHA-256;
- presença da reconciliação e dos quatro artefatos Gold;
- reconciliação nacional exata;
- integridade dos totais do overview;
- fechamento do agregado por UF;
- fechamento do agregado por família CBO;
- fechamento do Parquet Gold;
- manutenção de `publication_ready=false` antes da aprovação;
- fingerprint completo da release.

O fingerprint combina os SHA-256 dos arquivos de origem com hashes da reconciliação e dos quatro artefatos Gold. Qualquer alteração em entrada ou saída muda o fingerprint e invalida automaticamente uma aprovação anterior.

A aprovação metodológica é separada da aprovação mensal do Novo CAGED:

```bash
python -m src.cli rais-approve-release 2025 \
  --reviewer "responsavel" \
  --notes "Origem, rejeições, reconciliação e Gold revisados." \
  --acknowledge-methodology-reviewed
```

A aprovação manual só pode ser registrada depois que todos os checks automáticos passam.

O gate final é salvo em:

```text
data/gold/rais-publication-gate-2025.json
```

Somente `publishable=true` autoriza uma camada futura de API a expor os agregados anuais. Os helpers de publicação ignoram anos sem gate aprovado, mesmo quando os arquivos Gold existem.

## Regra de publicação

A existência de Bronze, Silver ou Gold RAIS não autoriza a publicação de métricas. O serving deve considerar apenas anos com `rais-publication-gate-<ano>.json` e `publishable=true`.

Até uma release anual atingir esse estado, o dashboard público continua exibindo somente indicadores derivados das competências do Novo CAGED já aprovadas.

## Separação conceitual

A futura métrica de estoque tech será apresentada como:

`estoque anual de vínculos tech ativos em 31/12`

Ela não será chamada de admissão, saldo ou movimentação e não será usada para preencher meses ausentes do Novo CAGED.
