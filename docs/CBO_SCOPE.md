# Recorte CBO de tecnologia

## Objetivo

Definir de forma reproduzível quais famílias ocupacionais entram no indicador de tecnologia do Mercado Tech Brasil.

O recorte é **ocupacional**, não setorial. Isso significa que um analista de sistemas empregado em um banco, indústria ou órgão público continua pertencendo ao recorte, mesmo que o CNAE do empregador não seja de tecnologia.

## Versão 2

Famílias incluídas:

| Família | Denominação oficial |
|---|---|
| 2122 | Engenheiros em computação |
| 2123 | Administradores de tecnologia da informação |
| 2124 | Analistas de tecnologia da informação |
| 3171 | Técnicos de desenvolvimento de sistemas e aplicações |
| 3172 | Técnicos em operação e monitoração de computadores |

## Por que 2122 foi adicionada

A versão 1 continha 2123, 2124, 3171 e 3172. A revisão da documentação oficial da CBO mostrou que o MTE organiza o subgrupo 212 como **Profissionais da Informática**, incluindo:

- 2122 — Engenheiros em computação;
- 2123 — Administradores de tecnologia da informação;
- 2124 — Analistas de tecnologia da informação.

A família 2122 inclui ocupações como engenheiro de aplicativos em computação, engenheiro de equipamentos em computação e engenheiro de sistemas operacionais em computação. Por isso, sua exclusão reduziria artificialmente o universo ocupacional de tecnologia.

O grupo 317, por sua vez, é definido como **Técnicos em Informática** e contém 3171 e 3172.

## O que não entra automaticamente

O projeto não inclui famílias apenas porque podem usar tecnologia no trabalho. Ocupações adjacentes — por exemplo telecomunicações, eletrônica, estatística, design ou gestão — exigem justificativa própria antes de entrar.

## Governança

Qualquer alteração futura deve:

1. citar fonte oficial da CBO;
2. incrementar a versão do recorte;
3. explicar inclusão ou exclusão;
4. adicionar teste de regressão;
5. registrar impacto esperado sobre os indicadores.

Arquivo de configuração: `config/cbo_tech.yml`.
