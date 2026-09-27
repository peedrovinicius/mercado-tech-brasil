# Revisão da release RAIS 2025

## Estado

A release anual foi processada integralmente, passou por todos os checks automáticos e teve a aprovação metodológica manual registrada para o fingerprint atual.

- Ano-base: 2025
- Fonte metodológica: RAIS, Ministério do Trabalho e Emprego
- Dataset: vínculos
- Fingerprint da release: `4da07584f1fe5843133f8725a43b48c45f081e88c55c85cc36adc7573ad9ee1a`
- Checks automáticos: aprovados
- Aprovação metodológica manual: aprovada por `peedrovinicius`
- Aprovação registrada em: `2026-09-27T11:00:09+00:00`
- `publishable`: verdadeiro

## Proveniência

Os sete arquivos regionais de vínculos estão representados no manifesto nacional com nome, tamanho, SHA-256, URL oficial do MTE e transporte efetivo.

| Arquivo | Tamanho | SHA-256 |
|---|---:|---|
| RAIS_VINC_PUB_CENTRO_OESTE.7z | 354.015.896 | 0e4459ee90c0219d9b40b9d6129e494034b8d6cd4dbe86eeb1f49e54f964d724 |
| RAIS_VINC_PUB_MG_ES_RJ.7z | 766.814.132 | d9c4e359fa16c6a1f929f49c8aec0201a9fbfb801964dc2e27032914924f1f15 |
| RAIS_VINC_PUB_NI.7z | 209.311 | dfd32817429cb732963b538d987c1537b12e119e81f667c3f7ffeb279ec0c201 |
| RAIS_VINC_PUB_NORDESTE.7z | 639.823.548 | 4366dda32c86e5fdb16f62b09028c7c693852f9b44118cd5536d79613eced089 |
| RAIS_VINC_PUB_NORTE.7z | 211.992.734 | c7deb880bf43db4e0250c1cba20a84a61dcedc6d1888a0687a18b01483ce2e29 |
| RAIS_VINC_PUB_SP.7z | 1.107.305.918 | d19f924d71578c782408678888ee59d89b05688e3b31babc1f174d06270d29df |
| RAIS_VINC_PUB_SUL.7z | 704.888.712 | c537caaaa8318b04e6f4cbbc7e59b130988668b7ea58ce67a0ab2caebf2f5bd0 |

O transporte efetivo desta execução foi o espelho HTTPS pinado. O manifesto preserva a URL oficial do MTE como origem metodológica e registra separadamente a URL efetiva de transporte.

## Qualidade nacional

- Registros lidos: 91.710.262
- Registros válidos: 91.710.262
- Registros rejeitados: 0
- Taxa válida: 100%
- Vínculos ativos brutos: 60.691.770
- Vínculos ativos abandonados: 720.825
- Estoque oficial elegível: 59.970.945
- Vínculos inativos: 31.018.492
- Status ativo desconhecido: 0
- Status de abandono desconhecido: 0
- Vínculos tech após qualificação do estoque: 786.296

Regra do estoque anual:

```text
active_3112 = 1
and abandoned_link = 0
```

## Reconciliação nacional

A referência oficial do MTE para 2025 é de 59.970.945 vínculos formais ativos.

- Esperado: 59.970.945
- Observado após qualificação: 59.970.945
- Diferença: 0
- Reconciliação nacional: aprovada
- Gold liberado tecnicamente: sim

O total bruto de 60.691.770 não foi usado para substituir a referência oficial. A diferença de 720.825 vínculos foi explicada pela variável de vínculo abandonado e excluída antes da reconciliação.

## Reconciliação territorial

Todos os sete grupos de origem fecham exatamente com a referência oficial.

| Grupo | Esperado | Observado | Diferença |
|---|---:|---:|---:|
| Norte | 3.869.191 | 3.869.191 | 0 |
| Nordeste | 11.686.314 | 11.686.314 | 0 |
| MG + ES + RJ | 12.255.362 | 12.255.362 | 0 |
| São Paulo | 16.158.390 | 16.158.390 | 0 |
| Sul | 10.054.135 | 10.054.135 | 0 |
| Centro-Oeste | 5.944.488 | 5.944.488 | 0 |
| Não identificado | 3.065 | 3.065 | 0 |

## Validação municipal

A dimensão municipal da RAIS 2025 foi validada contra a Divisão Territorial Brasileira 2025 do IBGE antes de integrar o fingerprint da release.

- Linhas Silver tech: 786.296
- Códigos municipais distintos observados: 3.690
- Códigos não residuais correspondentes à DTB 2025: 3.689
- Códigos sem correspondência: 0
- Prefixos ambíguos: 0
- Divergências de UF: 0
- Códigos com comprimento inválido: 0
- Códigos não numéricos: 0
- Residual preservado: `999999`, com 1 vínculo tech, classificado como `NI`
- `municipality_ready`: verdadeiro

O agregado municipal fecha exatamente em 786.296 vínculos tech e faz parte do fingerprint atual da release.

## Gold tech

- Estoque tech ativo: 786.296
- Estoque formal nacional de referência: 59.970.945
- Participação tech: 1,311128%
- Famílias CBO: 2122, 2123, 2124, 3171 e 3172
- UFs no agregado: 28, incluindo a categoria residual NI
- Municípios/códigos territoriais no agregado: 3.690, incluindo o residual NI
- Soma do agregado municipal: 786.296

Distribuição por família CBO:

| Família | Estoque | Participação tech |
|---|---:|---:|
| 2124, Analistas de tecnologia da informação | 487.872 | 62,05% |
| 3172, Técnicos em operação e monitoração de computadores | 121.680 | 15,48% |
| 3171, Técnicos de desenvolvimento de sistemas e aplicações | 103.877 | 13,21% |
| 2123, Administradores de tecnologia da informação | 47.446 | 6,03% |
| 2122, Engenheiros em computação | 25.421 | 3,23% |

## Gate automático

Os seguintes controles estão aprovados:

- [x] proveniência completa com sete arquivos de origem;
- [x] reconciliação nacional presente;
- [x] reconciliação regional presente;
- [x] validação municipal presente;
- [x] overview Gold presente;
- [x] agregado por UF presente;
- [x] agregado por família CBO presente;
- [x] agregado por município presente;
- [x] Parquet Gold presente;
- [x] reconciliação nacional com diferença zero;
- [x] reconciliação regional com diferença zero em todos os grupos;
- [x] dimensão municipal validada contra a DTB 2025;
- [x] ano do overview correto;
- [x] integridade do estoque tech e nacional;
- [x] soma por UF fecha em 786.296;
- [x] soma por família CBO fecha em 786.296;
- [x] soma por município fecha em 786.296;
- [x] Parquet Gold fecha em 786.296;
- [x] fingerprint atual da release calculado: `4da07584f1fe5843133f8725a43b48c45f081e88c55c85cc36adc7573ad9ee1a`;
- [x] aprovação metodológica manual vinculada ao fingerprint atual.

## O que a aprovação manual confirma

A aprovação manual deve ser registrada somente depois de uma pessoa revisar conscientemente:

1. a fonte e a proveniência dos sete arquivos;
2. a regra de estoque ativo e não abandonado;
3. o fechamento nacional;
4. o fechamento dos sete grupos regionais;
5. o recorte CBO v2;
6. a validação municipal contra a DTB 2025 e o tratamento do residual `999999`;
7. os agregados Gold por UF, família CBO e município;
8. o fingerprint atual da release: `4da07584f1fe5843133f8725a43b48c45f081e88c55c85cc36adc7573ad9ee1a`.

A aprovação não altera os dados. Ela apenas registra que a release atual, identificada pelo fingerprint acima, foi revisada e pode ser exposta pelos endpoints e pelo frontend já protegidos pelo gate.

Registro utilizado para a aprovação humana:

```bash
python -m src.cli rais-approve-release 2025 \
  --reviewer "peedrovinicius" \
  --notes "Origem, estoque ativo e não abandonado, reconciliação nacional e regional, recorte CBO v2, dimensão municipal DTB 2025, agregados Gold e fingerprint atual revisados." \
  --acknowledge-methodology-reviewed
```

Qualquer alteração futura nos artefatos que compõem a release modifica o fingerprint e invalida automaticamente a aprovação anterior.
