# Pipeline real do Novo CAGED

## 1. Descoberta

O downloader acessa o diretório oficial:

`ftp.mtps.gov.br/pdet/microdados/NOVO CAGED/<ANO>/<AAAAMM>/`

e descobre os arquivos `.7z` disponíveis.

Não há nome de arquivo inventado no código.

## 2. Três tipos de arquivo

O pipeline reconhece:

- `MOV`: movimentações;
- `FOR`: informações fora do prazo;
- `EXC`: exclusões.

Na primeira entrega analítica, somente `MOV` gera Silver/Gold. `FOR` e `EXC` já são ingeridos na Bronze, mas **não entram no indicador ajustado até sua semântica ser validada e testada**.

Isso é intencional: é melhor publicar menos do que combinar ajustes de modo incorreto.

## 3. Bronze

O arquivo oficial extraído é mantido imutável e recebe manifesto com:

- origem;
- competência;
- nome;
- tamanho;
- SHA-256;
- timestamp de ingestão.

## 4. Validação de layout

Antes de qualquer métrica, o pipeline exige campos centrais do layout:

- competência;
- UF;
- município;
- saldo da movimentação;
- CBO;
- tipo de movimentação;
- salário.

Se o MTE alterar o layout, o pipeline falha explicitamente.

## 5. Silver

O arquivo MOV é:

- normalizado;
- tipado;
- validado;
- separado entre registros válidos e rejeitados;
- filtrado pelo recorte CBO versionado de tecnologia;
- persistido em Parquet com Zstandard.

O código municipal do CAGED é preservado como `municipio_codigo_caged`; a conversão para código IBGE completo ficará em uma dimensão oficial própria.

## 6. Gold

A primeira tabela Gold contém:

- admissões;
- desligamentos;
- saldo;
- salário médio de admissão;
- salário mediano de admissão;

por UF, família CBO e CBO.

## 7. Reconciliação oficial

Em julho de 2026, o MTE publicou:

- 2.262.888 admissões;
- 2.204.320 desligamentos;
- saldo de 58.568.

Esses valores estão registrados em `config/reference_totals.json`.

Eles são uma referência de reconciliação, **não um teste de MOV isolado**, porque o resultado oficial publicado considera ajustes. A reconciliação completa será ativada somente após a lógica MOV/FOR/EXC ser validada.

## 8. Execução

```bash
python -m src.cli pipeline 202607
```

Ou por etapas:

```bash
python -m src.cli download 202607
python -m src.cli extract 202607
python -m src.cli transform 202607
python -m src.cli gold 202607
```


## 9. Gate de publicação

Depois de gerar Silver e Gold, o projeto executa um gate de liberação:

```bash
python -m src.cli validate-release 202607
```

O gate verifica:

- presença dos artefatos esperados;
- manifesto MOV e SHA-256;
- coerência da competência;
- contagens do relatório de qualidade;
- taxa mínima de registros válidos;
- identidade `admissões - desligamentos = saldo`;
- integridade da referência oficial cadastrada;
- revisão metodológica manual vinculada ao SHA-256 atual.

O mês permanece bloqueado até a revisão explícita:

```bash
python -m src.cli approve-release 202607 \
  --reviewer "Nome do revisor" \
  --notes "Layout, rejeições e metodologia revisados." \
  --acknowledge-methodology-reviewed
```

Se o arquivo MOV for substituído, o SHA-256 muda e a aprovação anterior deixa de ser válida automaticamente.
