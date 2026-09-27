# Avaliação do Quadro Brasileiro de Qualificações

## Decisão

O QBQ foi aprovado como fonte potencial de enriquecimento ocupacional do Mercado Tech Brasil.

A integração é exclusivamente descritiva. O QBQ pode acrescentar contexto sobre uma ocupação CBO, mas não altera admissões, desligamentos, saldo, remuneração ou estoque de vínculos.

Nenhum atributo QBQ é publicado enquanto o arquivo oficial não passar pelo intake auditável do projeto.

## Fonte oficial

Órgão responsável: Ministério do Trabalho e Emprego.

Serviço oficial:

https://www.gov.br/pt-br/servicos/consultar-quadro-brasileiro-de-qualificacoes

Sistema oficial:

https://qbq.trabalho.gov.br/

A base consolidada é disponibilizada pelo sistema QBQ em Excel. O acesso ao download exige cadastro e autenticação no portal.

Base normativa: Portaria Consolidada MTE nº 1, de 17 de dezembro de 2025, especialmente arts. 68 a 71.

## Adequação metodológica

O QBQ é compatível com o recorte ocupacional do projeto porque sua unidade de referência também é a ocupação da CBO.

Os atributos potencialmente úteis são:

- nível de qualificação;
- perfil ocupacional;
- conhecimentos;
- habilidades;
- atitudes.

Esses atributos não devem ser interpretados como características observadas de cada trabalhador registrado no Novo CAGED ou na RAIS. Eles descrevem requisitos e referências associados à ocupação.

## Regra de integração

O join será feito exclusivamente pelo código CBO de seis dígitos.

Antes de qualquer enriquecimento, o arquivo oficial precisa passar por:

1. validação de formato XLSX;
2. cálculo de SHA-256;
3. inspeção das planilhas e colunas;
4. detecção de uma coluna que contenha os códigos CBO tech já publicados;
5. verificação explícita da cobertura desses códigos;
6. revisão do schema real antes da definição do parser definitivo.

O projeto não usa scraping da interface HTML do QBQ como fonte de produção.

## Comando de intake

~~~bash
python -m src.cli qbq-inspect "/caminho/arquivo-oficial-qbq.xlsx" \
  --report "/caminho/qbq-inspection.json" \
  --strict
~~~

O modo `--strict` retorna erro quando algum código CBO tech presente nas competências publicadas não é encontrado no workbook.

## Estado atual

Concluído:

- avaliação metodológica;
- fonte oficial identificada;
- política de publicação definida;
- contrato de proveniência configurado;
- leitor XLSX;
- fingerprint SHA-256;
- detecção do join por conteúdo;
- validação contra os CBOs tech publicados;
- testes automatizados de intake.

Pendente de arquivo oficial:

- confirmar o schema real do Excel disponibilizado pelo QBQ;
- mapear os nomes reais das tabelas e colunas;
- definir o Silver QBQ;
- publicar atributos ocupacionais na API;
- integrar os atributos aprovados ao dashboard.

A ausência do arquivo autenticado não é substituída por dados inferidos, cópias não oficiais ou scraping.
