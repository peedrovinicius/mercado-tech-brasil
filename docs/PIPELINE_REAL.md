# Pipeline real do Novo CAGED

## 1. Descoberta

O downloader acessa a estrutura oficial do Novo CAGED por competência e descobre os arquivos disponíveis sem depender de um nome de arquivo fixo inventado no código.

O transporte primário é FTP do MTE, com fallback HTTPS quando necessário.

## 2. Arquivos processados

O pipeline reconhece três tipos de arquivo:

- `MOV`: movimentações da competência;
- `FOR`: movimentações declaradas fora do prazo;
- `EXC`: exclusões de movimentações anteriormente informadas.

MOV forma a base da competência. FOR acrescenta movimentações à competência efetiva identificada no arquivo. EXC inverte o efeito da movimentação correspondente.

Os ajustes preservam `effective_competence`, permitindo aplicar seus deltas à competência de origem antes da reconstrução dos agregados publicados.

## 3. Bronze

Os arquivos recebidos da fonte oficial são preservados na camada Bronze durante o processamento.

Cada ingestão registra:

- origem;
- competência;
- tipo do arquivo;
- nome original;
- transporte;
- tamanho;
- SHA-256;
- timestamp de ingestão.

Os microdados brutos não são versionados no Git. Manifests necessários à rastreabilidade são preservados na publicação.

## 4. Validação de layout

Antes das métricas, o pipeline valida os campos centrais do layout, incluindo:

- competência;
- UF;
- município;
- saldo da movimentação;
- CBO;
- tipo de movimentação;
- salário.

Mudança incompatível de schema provoca falha explícita antes da publicação.

## 5. Silver

MOV, FOR e EXC passam por normalização e validação.

A camada Silver preserva:

- tipos normalizados;
- recorte CBO versionado;
- registros válidos;
- registros rejeitados;
- deltas de ajustes;
- competência efetiva dos ajustes;
- Parquet com compressão Zstandard.

Registros rejeitados permanecem auditáveis e não são descartados silenciosamente.

## 6. Gold

A camada Gold contém os artefatos derivados usados pelo produto:

- `overview-AAAAMM.json`;
- `by-uf-AAAAMM.json`;
- `by-occupation-AAAAMM.json`;
- `by-municipality-AAAAMM.json`;
- `market-AAAAMM.parquet`;
- `trend.json`;
- relatórios de qualidade;
- auditoria nacional do MOV;
- gate de publicação.

Os agregados incluem admissões, desligamentos, saldo e métricas de remuneração. A dimensão municipal utiliza referência oficial do IBGE e mantém tratamento explícito para a categoria residual Não identificado.

## 7. Remuneração real

A metodologia salarial aplica os limites documentados para admissões elegíveis e exclui vínculos intermitentes das métricas salariais.

Quando a referência IPCA está disponível, a camada Gold também registra média e mediana reais na competência base configurada.

## 8. Reconciliação oficial

Antes da publicação, o MOV nacional da competência é comparado com a referência oficial registrada em `config/reference_totals.json`.

O gate verifica:

- integridade aritmética da referência;
- igualdade entre MOV nacional e referência oficial;
- tratamento da categoria Não identificado quando presente;
- coerência entre overview e artefatos publicados.

A série publicada de janeiro a julho de 2026 foi reconciliada competência por competência.

## 9. Gate de publicação

Depois do processamento, o projeto executa:

```bash
python -m src.cli validate-release 202607
```

O gate verifica, entre outros pontos:

- presença dos artefatos obrigatórios;
- manifesto MOV e SHA-256;
- competência dos relatórios;
- contagens de qualidade;
- taxa mínima de registros válidos;
- identidade `admissões - desligamentos = saldo`;
- qualidade da dimensão municipal;
- reconciliação com referência oficial;
- revisão metodológica vinculada ao SHA-256 atual.

A aprovação explícita usa:

```bash
python -m src.cli approve-release 202607 \
  --reviewer "responsavel" \
  --notes "Layout, rejeições e metodologia revisados." \
  --acknowledge-methodology-reviewed
```

Se o MOV mudar, o SHA-256 muda e a aprovação anterior deixa de ser válida.

## 10. Auditoria e publicação

A operação mensal separa processamento pesado e publicação.

O workflow `Audit data competence`:

1. sincroniza referências;
2. baixa MOV e tenta obter FOR e EXC;
3. transforma e agrega;
4. executa o gate;
5. remove microdados brutos;
6. publica somente o artefato temporário de auditoria.

O workflow `Publish audited data`:

1. recebe o ID da auditoria aprovada;
2. baixa o artefato derivado;
3. refaz o gate em modo estrito;
4. verifica os arquivos obrigatórios;
5. regenera o dashboard visual do README a partir da camada Gold;
6. versiona os derivados e o dashboard no mesmo commit.

Essa separação evita reprocessar os microdados na etapa de publicação.

## 11. Dashboard do README

O painel visual é derivado dos próprios artefatos Gold:

```bash
python scripts/generate_readme_dashboard.py
```

Ele usa a série histórica, o overview da competência mais recente e os agregados por UF. Assim, acumulados e participações territoriais não precisam ser digitados manualmente no SVG.

## 12. Execução local

Pipeline completo de uma competência:

```bash
python -m src.cli pipeline 202607
```

Processamento de arquivo oficial local:

```bash
python -m src.cli local-pipeline 202607 "/caminho/CAGEDMOV202607.7z" --kind MOV
```

Validação:

```bash
python -m src.cli validate-release 202607
```
