# Metodologia

## Unidade básica

O Novo CAGED representa movimentações do emprego formal. Admissões e desligamentos são tratados como fluxos.

## Saldo

`saldo = admissões - desligamentos`

## MOV, FOR e EXC

O pipeline preserva cada tipo de arquivo separadamente na Bronze e na Silver.

Para os agregados, cada registro recebe deltas explícitos:

- MOV registra o efeito original da movimentação;
- FOR acrescenta o efeito da movimentação declarada fora do prazo;
- EXC inverte o efeito da movimentação original.

Uma exclusão de admissão reduz admissões. Uma exclusão de desligamento reduz desligamentos. O pipeline não converte exclusões em um tipo diferente de movimento.

Os ajustes são associados à competência da movimentação. Quando um arquivo FOR ou EXC afeta uma competência cuja Silver base já existe, o Gold dessa competência é reconstruído.

## Salário médio e mediano de admissão

O projeto reproduz a regra de elegibilidade publicada pelo MTE no Sumário Executivo do Novo Caged.

Para competências de 2026:

- não entram valores menores que 0,3 salário mínimo;
- não entram valores maiores que 150 salários mínimos;
- vínculos intermitentes não entram na métrica salarial.

Com salário mínimo nacional de R$ 1.621,00 em 2026, os limites implementados são R$ 486,30 e R$ 243.150,00.

FOR e EXC também participam da distribuição salarial por pesos. Uma exclusão retira a contribuição da admissão original quando os atributos correspondentes estão presentes no arquivo de ajuste.

## Salário real

O salário real usa o número índice do IPCA da tabela 1737 do SIDRA/IBGE.

A correção segue:

`valor_real = valor_nominal x indice_base / indice_observacao`

A competência base é registrada junto ao dado. Se o cache oficial do IPCA não estiver disponível para a competência, a métrica nominal continua válida e a métrica real permanece ausente.

## Referências oficiais

O projeto versiona os totais nacionais publicados pelo MTE para cada competência da série. O MOV de cada mês precisa reconciliar admissões, desligamentos e saldo antes da aprovação.

A referência detalhada de julho de 2026 também preserva dados por região, UF e remuneração para testes adicionais de fechamento.

Para julho de 2026:

- Brasil: 2.262.888 admissões, 2.204.320 desligamentos e saldo +58.568;
- Ceará: 61.739 admissões, 57.558 desligamentos e saldo +4.181;
- salário médio nominal de admissão no Brasil: R$ 2.419,23;
- salário médio nominal de admissão no Ceará: R$ 2.173,94.

Testes verificam a aritmética por UF, por região e o fechamento do total nacional.

## Comparação territorial

A comparação Brasil, Nordeste e Ceará utiliza os mesmos agregados por UF liberados para a competência mais recente publicada.

O Nordeste é formado por AL, BA, CE, MA, PB, PE, PI, RN e SE.

As métricas territoriais seguem as mesmas definições de admissões, desligamentos e saldo usadas no restante do produto.

A participação nas admissões tech nacionais é calculada por:

`participacao_nacional = admissoes_territorio / admissoes_brasil`

A participação do Ceará nas admissões tech do Nordeste é calculada por:

`participacao_ceara_nordeste = admissoes_ceara / admissoes_nordeste`

Os percentuais são derivados em tempo de consulta a partir dos agregados publicados, sem manter uma segunda base manual de valores territoriais.

## Recorte de tecnologia

O recorte CBO é versionado em `config/cbo_tech.yml`.

A versão atual inclui as famílias 2122, 2123, 2124, 3171 e 3172.

O recorte é ocupacional. A atividade econômica do empregador não determina, isoladamente, a entrada de um vínculo no indicador.

Toda mudança no recorte exige fonte, justificativa, nova versão e teste de regressão.

## Municípios

O microdado mantém o código municipal usado pelo CAGED. A camada de referência consulta a API oficial de Localidades do IBGE e acrescenta nome do município, UF e código IBGE de sete dígitos.

O mapeamento usa os seis primeiros dígitos do código IBGE como chave de correspondência do código municipal presente no CAGED.

Quando o CAGED informa o código residual `999999`, o produto registra o município como **Não identificado**, com UF `NI` e sem fabricar um código IBGE. O gate de publicação valida essa exceção explicitamente e exige identificação completa para os demais municípios.

### População municipal e taxas por 100 mil habitantes

A referência populacional usa a pesquisa Estimativas da População do IBGE, tabela 6579 do SIDRA, variável 9324. Para a série de 2026, a data de referência é 1º de julho de 2026.

A população é associada pelo código IBGE de sete dígitos já incorporado à dimensão municipal. Quando a referência está disponível, o Gold municipal deriva:

`admissoes_por_100_mil = admissoes / populacao_estimada x 100000`

`desligamentos_por_100_mil = desligamentos / populacao_estimada x 100000`

`saldo_por_100_mil = saldo / populacao_estimada x 100000`

Municípios sem código IBGE válido, população ausente ou categoria residual permanecem com essas taxas nulas. O pipeline não substitui denominadores ausentes por estimativas próprias.

A referência populacional é sincronizada antes da geração Gold e registra fonte, tabela, variável, ano e data de referência no cache de processamento.

## Série histórica

Cada overview Gold é incorporado em `trend.json`. No backend PostgreSQL, a série é construída diretamente a partir das competências publicadas em `dataset_release`.

A série contém apenas competências que passaram pelas mesmas regras de transformação e publicação aplicáveis ao período. De janeiro a julho de 2026, FOR e EXC são incorporados às competências de origem antes da reconstrução dos indicadores mensais.

## Escopo

O produto publica indicadores derivados das fontes declaradas e mantém período, origem, metodologia e proveniência junto dos artefatos e contratos de API.
