# Roadmap

## Base operacional concluída

A base necessária para publicar e auditar o produto está implementada:

- ingestão de MOV, FOR e EXC;
- Bronze, Silver e Gold;
- manifesto e SHA-256 da origem;
- detecção de mudança de layout;
- recorte CBO versionado;
- reconciliação nacional por competência;
- gate de publicação;
- ajustes FOR e EXC aplicados às competências de origem;
- enriquecimento municipal;
- salário real por IPCA;
- série histórica de janeiro a julho de 2026;
- serving por arquivos e PostgreSQL;
- API FastAPI e frontend React;
- comparação Brasil, Nordeste e Ceará;
- consolidação trimestral com identificação de períodos parciais;
- integração SIDRA para população municipal e cálculo por 100 mil no Gold;
- ranking municipal normalizado no frontend, ativado somente quando há denominador publicado;
- descoberta e ingestão Bronze auditável dos microdados anuais da RAIS;
- extração RAIS compatível com arquivos .comt, .txt e .csv;
- inspeção de schema anual com assinatura SHA-256 do cabeçalho;
- contrato semântico RAIS versionado com bloqueio por ausência ou ambiguidade;
- perfil amostral dos valores RAIS antes do Silver;
- contrato de valores RAIS para situação do vínculo em 31/12;
- amostra oficial RAIS 2025 validada em arquivo regional real;
- layout real 2025 confirmado com 62 colunas, latin-1 e delimitador vírgula;
- codificação real 1/0 do vínculo ativo confirmada em amostra de 10.000 registros;
- downloader RAIS com retomada FTP e verificação de tamanho;
- transformação Silver RAIS em streaming com rejeições auditáveis;
- reconciliação nacional RAIS contra referência oficial do MTE;
- Gold anual RAIS por overview, UF e família CBO;
- gate anual RAIS com fingerprint integral e aprovação metodológica;
- helpers de serving que ignoram anos sem publicação aprovada;
- publicação pública no Render.

## Próximas entregas

### Atualização incremental

- automatizar a preparação da próxima competência após a publicação oficial;
- manter validação explícita da referência do MTE antes da liberação;
- preservar a publicação somente após aprovação do gate;
- ampliar testes de regressão da série histórica.

### Expansão temporal

- incorporar novas competências sem alterar a metodologia já publicada;
- consolidar comparações anuais quando houver cobertura suficiente;
- documentar revisões oficiais que alterem competências anteriores.

### Expansão analítica

- acompanhar a primeira competência Gold enriquecida com população no fluxo de publicação;
- baixar o conjunto completo dos arquivos de vínculos RAIS 2025;
- executar inspeção e validação em todos os arquivos regionais, não apenas na amostra Norte;
- executar o Silver completo sobre os microdados reais de 2025;
- revisar rejeições reais, inclusive qualquer CBO ou município fora do padrão observado na amostra;
- executar a reconciliação exata com 59.970.945 vínculos ativos;
- executar rais-gold 2025 somente depois de gold_ready=true;
- executar o gate anual sobre os artefatos reais da RAIS 2025;
- expor endpoints RAIS somente depois de uma release real atingir publishable=true;
- validar sistema de códigos municipais da RAIS 2025 antes de agregação municipal;
- avaliar QBQ para atributos ocupacionais;
- ampliar comparações territoriais e ocupacionais mantendo a mesma governança.

## Critério de inclusão

Uma nova métrica entra no produto quando possui:

1. fonte identificada;
2. regra de transformação documentada;
3. teste;
4. período de referência;
5. comportamento definido para ausência e inconsistência;
6. contrato de API compatível com a governança de publicação.
