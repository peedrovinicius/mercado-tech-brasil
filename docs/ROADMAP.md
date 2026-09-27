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
- fallback HTTPS pinado e auditável para instabilidade do FTP, sem trocar a fonte metodológica;
- processamento RAIS regional isolado e merge nacional em streaming;
- processamento integral dos sete arquivos RAIS 2025 concluído;
- 91.710.262 registros processados com zero rejeições;
- estoque bruto nacional observado em 60.691.770 vínculos ativos;
- 720.825 vínculos ativos abandonados identificados e excluídos do estoque oficial;
- estoque qualificado reconciliado exatamente em 59.970.945 vínculos;
- filtro de vínculo abandonado validado nacionalmente e por grupos regionais oficiais;
- transformação Silver RAIS em streaming com rejeições auditáveis;
- reconciliação nacional RAIS contra referência oficial do MTE;
- Gold anual RAIS por overview, UF, município e família CBO;
- dimensão municipal RAIS 2025 validada contra a DTB oficial do IBGE;
- 3.689 códigos municipais não residuais com correspondência e zero divergências de UF;
- gate anual RAIS com fingerprint integral e aprovação metodológica;
- helpers de serving que ignoram anos sem publicação aprovada;
- endpoints anuais RAIS protegidos por publishable=true;
- integração visual RAIS condicionada ao registry anual;
- relatório técnico de revisão da release RAIS 2025 consolidado;
- aprovação metodológica manual da RAIS 2025 vinculada ao fingerprint da release;
- RAIS 2025 publicada com publishable=true;
- API anual validada contra os artefatos reais publicados;
- frontend configurado para reconstruir quando o estado de publicação RAIS mudar;
- publicação pública no Render.

## Próximas entregas

### Atualização incremental

Este é o próximo bloco prioritário após o fechamento da RAIS 2025.

- preparação automática da próxima competência condicionada à referência oficial: implementada;
- detecção contínua da próxima competência sem antecipar período não publicado: implementada;
- bloqueio de saltos mensais e de data de publicação futura: implementado;
- auditoria automática disparada quando a referência oficial elegível entra no main: implementada;
- baixar e registrar a origem com manifesto e SHA-256 na próxima competência elegível;
- executar Bronze, Silver, Gold, ajustes FOR/EXC e enriquecimentos pelo fluxo existente;
- manter validação explícita da referência oficial do MTE antes da liberação;
- gerar o gate da nova competência inicialmente bloqueado;
- preservar a publicação somente após aprovação metodológica do gate;
- testes de regressão histórica com bloqueio de alterações não explicadas por FOR/EXC: implementados;
- manifesto e pacote auditável para revisões retroativas de competências publicadas: implementados;
- proteção contra pacote baseado em baseline histórico desatualizado: implementada;
- fingerprint da referência oficial vinculado à aprovação metodológica: implementado;
- detecção e reauditoria de republicações ou revisões oficiais do MTE: implementadas;
- cache IPCA incremental para preservar reconstruções históricas: implementado;
- política de deploy bloqueia Gold mensal ou RAIS sem gate publicável: implementada;
- Blueprint de produção configurado para deploy após checks e build filter: implementado;
- commits de publicação preservam CI antes da promoção: implementado;
- manter a configuração operacional do Render sincronizada com o Blueprint versionado.

### Expansão temporal

- incorporar novas competências sem alterar a metodologia já publicada;
- consolidar comparações anuais quando houver cobertura suficiente;
- documentar revisões oficiais que alterem competências anteriores.

### Expansão analítica

- enriquecimento pós-publicação de Gold municipal com população oficial do IBGE: implementado;
- gate populacional com cobertura completa, taxas por 100 mil e fingerprint: implementado;
- Jul/2026 enriquecida com Estimativas da População 2026: concluído;
- 1.274 municípios tech identificados cruzados com população, zero ausências;
- gate populacional de Jul/2026 aprovado sem alterar os totais de movimentação;
- série temporal por família CBO com agregação das cinco famílias versionadas: implementada;
- endpoint e visualização de evolução ocupacional por família: implementados;
- ampliar comparações territoriais e ocupacionais mantendo a mesma governança: primeira expansão ocupacional implementada;
- avaliação metodológica do QBQ como dimensão ocupacional: concluída;
- intake auditável de workbook QBQ com SHA-256 e cobertura dos CBOs tech: implementado;
- confirmar o schema real do Excel QBQ após obtenção do arquivo oficial autenticado;
- construir Silver e API QBQ somente depois da validação do schema real;
- comparação descritiva entre estoque RAIS e fluxos Novo CAGED no mesmo recorte CBO: implementada;
- escala de admissões, desligamentos e saldo por 100 vínculos do estoque anterior: implementada;
- comparação de participação no estoque versus participação nas admissões por família CBO: implementada;
- interpretação explicitamente bloqueada para turnover, probabilidade individual ou crescimento direto do estoque.

## Critério de inclusão

Uma nova métrica entra no produto quando possui:

1. fonte identificada;
2. regra de transformação documentada;
3. teste;
4. período de referência;
5. comportamento definido para ausência e inconsistência;
6. contrato de API compatível com a governança de publicação.
