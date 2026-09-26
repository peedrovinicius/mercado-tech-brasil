# Changelog

## 0.33.0

- primeira validação operacional sobre microdados oficiais reais da RAIS 2025;
- amostra regional oficial confirmou arquivo COMT com 62 colunas, latin-1 e delimitador vírgula;
- contrato semântico RAIS evolui para versão 2 com aliases dos nomes reais observados;
- ano-base passa a ser derivado do contexto anual em vez de exigir coluna inexistente;
- UF passa a ser derivada do prefixo do código municipal;
- Município - Código é adotado como dimensão territorial principal e Município Trab - Código permanece opcional;
- amostra de 10.000 registros confirmou códigos 1 e 0 para situação do vínculo em 31/12, sem nulos ou terceiro valor;
- contrato de valores RAIS evolui para versão 2 com 1 como ativo e 0 como inativo;
- município foi observado com seis dígitos em todos os registros da amostra;
- CBO 2002 é normalizada para seis dígitos, preservando zero à esquerda quando o arquivo fornece cinco dígitos;
- downloader FTP da RAIS ganha retomada por offset, novas tentativas e validação pelo tamanho remoto;
- workflow de amostra volta a ser exclusivamente manual após a validação;
- publicação RAIS continua bloqueada até processamento integral, reconciliação, Gold e gate anual;
- cobertura mensal publicada do Novo CAGED permanece de janeiro a julho de 2026.

## 0.32.0

- gate anual de publicação RAIS implementado e separado do gate mensal do Novo CAGED;
- checks automáticos validam proveniência, reconciliação e fechamento dos agregados Gold;
- fingerprint da release combina hashes dos arquivos de origem, reconciliação e quatro artefatos Gold;
- qualquer alteração em entrada ou saída invalida a aprovação metodológica anterior;
- aprovação manual só pode ser registrada quando todos os checks automáticos passam;
- arquivo de aprovações RAIS é separado das aprovações mensais do CAGED;
- CLI ganha rais-validate-release e rais-approve-release;
- helpers de publicação retornam apenas anos RAIS com publishable=true;
- Gold anual não aprovado continua invisível para uma futura camada de serving;
- cobertura mensal publicada do Novo CAGED permanece de janeiro a julho de 2026.

## 0.31.0

- Gold anual RAIS implementado e separado do Gold mensal do Novo CAGED;
- geração exige reconciliação anual com reconciled=true e gold_ready=true;
- novo overview anual registra estoque tech, estoque nacional reconciliado e participação relativa;
- agregado por UF registra estoque ativo e participação no estoque tech;
- agregado por família CBO registra estoque, denominação e participação no estoque tech;
- Parquet anual agrega UF, família CBO, CBO completa e estoque ativo;
- município permanece fora do Gold RAIS até validação do sistema territorial observado em 2025;
- todos os artefatos Gold RAIS permanecem com publication_ready=false;
- CLI ganha comando rais-gold;
- cobertura mensal publicada do Novo CAGED permanece de janeiro a julho de 2026.

## 0.30.0

- referência oficial da RAIS 2025 versionada com 59.970.945 vínculos ativos;
- Silver passa a preservar contagens nacionais da fonte antes do recorte CBO e das validações territoriais;
- fonte é particionada em ativos, inativos, status desconhecido e ano divergente;
- a partição precisa fechar exatamente o total de linhas lidas;
- reconciliação usa o estoque bruto ativo, não o subconjunto tech;
- qualquer diferença em relação ao total oficial mantém Gold bloqueado;
- status desconhecido ou ano divergente também bloqueiam a reconciliação;
- CLI ganha comando rais-reconcile;
- reconciliação aprovada libera gold_ready, mas publication_ready permanece falso;
- cobertura mensal publicada do Novo CAGED permanece de janeiro a julho de 2026.

## 0.29.0

- transformação Silver anual da RAIS implementada após as travas de schema e valores;
- leitura ocorre em streaming para evitar carregar os microdados anuais completos em memória;
- escrita Parquet usa lotes configuráveis e compressão Zstandard;
- somente vínculos ativos em 31/12 entram no estoque anual;
- recorte CBO tech v2 é aplicado após validação do registro;
- vínculos inativos são contabilizados, mas não entram no Silver tech;
- registros inválidos são preservados em Parquet de rejeições com motivo;
- relatório anual de qualidade registra lidas, válidas, rejeitadas, ativas, inativas e tech;
- CLI ganha comando rais-transform;
- Gold e publicação continuam bloqueados até reconciliação anual e gate específico;
- cobertura mensal publicada do Novo CAGED permanece de janeiro a julho de 2026.

## 0.28.0

- semântica oficial de situação do vínculo em 31/12 registrada em contrato versionado;
- SIM é tratado como ativo e NÃO como inativo, conforme documentação do MTE;
- perfil de valores passa a registrar o conjunto completo observado quando há até 50 categorias;
- códigos desconhecidos no indicador de vínculo bloqueiam o Silver;
- valores nulos no indicador de vínculo bloqueiam o Silver;
- ano-base observado precisa coincidir com o ano solicitado;
- codificações alternativas, como 1/0, não são inferidas automaticamente;
- CLI ganha comando rais-validate-values;
- silver_transform_ready só é liberado após validação explícita dos valores;
- publication_ready permanece falso até qualidade, reconciliação e gate anual;
- cobertura mensal publicada do Novo CAGED permanece de janeiro a julho de 2026.

## 0.27.0

- RAIS ganha perfil amostral de valores antes da transformação Silver;
- o perfil usa somente conceitos já resolvidos pelo contrato semântico;
- ano, CBO, município, UF e vínculo ativo em 31/12 recebem frequências, nulos e padrões de formato;
- limite de amostragem é configurável e protegido para evitar processamento acidental excessivo;
- value-profile.json não replica linhas individuais nem campos fora do contrato mínimo;
- a codificação de vínculo ativo não é inferida automaticamente;
- silver_transform_ready e publication_ready permanecem falsos até revisão explícita;
- CLI ganha comando rais-profile-values;
- cobertura mensal publicada do Novo CAGED permanece de janeiro a julho de 2026.

## 0.26.0

- contrato semântico RAIS versionado separadamente do layout físico;
- conceitos obrigatórios passam a incluir ano-base, CBO 2002, município, UF e vínculo ativo em 31/12;
- remuneração permanece opcional até a etapa salarial anual;
- aliases permitem absorver mudanças de nomenclatura sem esconder mudança de schema;
- ausência de conceito obrigatório bloqueia o Silver;
- mais de um alias do mesmo conceito no mesmo layout é tratado como ambiguidade e também bloqueia;
- semantic-layout-report.json registra correspondências, ausências e ambiguidades por arquivo;
- CLI ganha comando rais-validate-layout;
- silver_ready pode ser liberado pela validação semântica, mas publication_ready permanece falso;
- cobertura mensal publicada do Novo CAGED permanece de janeiro a julho de 2026.

## 0.25.0

- RAIS anual ganha etapa explícita de extração separada do download;
- arquivos extraídos recebem manifests com SHA-256 e metadados de origem;
- nova inspeção de layout aceita .comt, .txt e .csv;
- codificação e delimitador são detectados antes da leitura do cabeçalho;
- nomes de colunas são normalizados apenas para comparação de schema;
- cada layout observado recebe assinatura SHA-256 do cabeçalho normalizado;
- layout-report.json registra os layouts encontrados sem liberar transformação ou publicação;
- CLI ganha comandos rais-extract e rais-inspect;
- documentação passa a considerar formalmente a mudança de estrutura dos microdados RAIS recentes;
- cobertura mensal publicada do Novo CAGED permanece de janeiro a julho de 2026.

## 0.24.0

- camada anual RAIS iniciada de forma separada do fluxo mensal do Novo CAGED;
- descoberta de arquivos RAIS por ano diretamente no FTP oficial do MTE;
- download padrão seleciona somente arquivos de vínculos e exclui estabelecimentos;
- dataset de estabelecimentos pode ser solicitado explicitamente;
- Bronze RAIS usa diretório anual próprio e gera SHA-256, URL oficial e manifests;
- CLI ganha comandos rais-discover e rais-download;
- fonte RAIS 2025 registrada no catálogo de fontes oficiais;
- documentação explicita estoque anual em 31/12 e impede mistura conceitual com admissões e desligamentos;
- microdados RAIS não entram em workflow automático nesta etapa para preservar custo operacional;
- nenhuma métrica RAIS é publicada antes de layout, Silver, reconciliação e gate próprios;
- cobertura mensal publicada do Novo CAGED permanece de janeiro a julho de 2026.

## 0.23.0

- endpoint municipal passa a aceitar ranking por admissões absolutas ou admissões por 100 mil habitantes;
- rankings absoluto e normalizado são calculados separadamente para preservar comparabilidade;
- municípios sem denominador populacional são excluídos apenas do ranking normalizado;
- resposta municipal informa disponibilidade da normalização e referência populacional;
- PostgreSQL e arquivos Gold mantêm o mesmo contrato de ranking;
- frontend ganha seletor Volume e Por 100 mil, exibido somente quando a normalização está disponível;
- gráfico municipal adapta eixo, tooltip e cor ao modo normalizado;
- testes cobrem ranking normalizado, ausência de denominador e rejeição de métricas inválidas;
- cobertura publicada de emprego permanece de janeiro a julho de 2026.

## 0.22.0

- integração com Estimativas da População do IBGE pela tabela SIDRA 6579, variável 9324;
- nova sincronização populacional por ano com cache auditável e data de referência;
- Gold municipal passa a derivar admissões, desligamentos e saldo por 100 mil habitantes quando há denominador válido;
- categoria municipal residual permanece sem taxa populacional, sem imputação artificial;
- auditoria mensal sincroniza população do mesmo ano da competência antes da geração Gold;
- serving PostgreSQL recebe população, ano de referência e taxas por 100 mil;
- migration adiciona os novos campos à tabela municipal;
- contrato TypeScript já aceita os novos indicadores para a próxima etapa visual;
- testes cobrem parsing SIDRA, cache populacional e cálculo das taxas;
- cobertura publicada de emprego permanece de janeiro a julho de 2026.

## 0.21.0

- novo endpoint de consolidação temporal derivado exclusivamente da série publicada;
- competências são agrupadas automaticamente por trimestre;
- períodos incompletos são identificados explicitamente como parciais;
- API expõe acumulado publicado, totais trimestrais e média mensal do saldo;
- frontend ganha bloco visual de leitura trimestral;
- testes cobrem acumulado, primeiro e segundo trimestres completos e período parcial mais recente;
- roadmap passa a tratar consolidação trimestral como funcionalidade concluída;
- cobertura de dados permanece de janeiro a julho de 2026.

## 0.20.0

- pipeline real documentado novamente a partir da implementação atual;
- FOR e EXC documentados como ajustes aplicados à competência efetiva antes da reconstrução dos agregados;
- Gold municipal, série histórica e remuneração real deixam de aparecer como etapas futuras na documentação;
- publicação mensal passa a regenerar o dashboard do README dentro do workflow já existente;
- SVG visual entra no mesmo commit dos derivados publicados;
- Makefile ganha alvo `readme-dashboard` para regeneração local;
- nenhuma nova execução automática de workflow foi criada;
- cobertura de dados permanece de janeiro a julho de 2026.

## 0.19.6

- dashboard do README passa a ter gerador reproduzível em Python;
- gerador lê série histórica, overview e agregados por UF diretamente da camada Gold;
- acumulados, competência mais recente e participações territoriais são recalculados na geração;
- teste executa o gerador em arquivo temporário e confere os indicadores derivados;
- README documenta o comando de regeneração do painel;
- geração permanece manual para não consumir minutos de GitHub Actions;
- cobertura de dados permanece de janeiro a julho de 2026.

## 0.19.5

- README ganha dashboard visual em SVG com dados reais da série publicada;
- painel visual resume acumulado, competência mais recente e comparação territorial;
- o SVG é versionado no repositório e não depende de screenshot;
- tabela textual do dashboard permanece como fallback acessível e verificável;
- testes editoriais passam a incluir arquivos SVG;
- cobertura de dados permanece de janeiro a julho de 2026.

## 0.19.4

- README ganha dashboard executivo com indicadores reais da série publicada e estado operacional;
- arquitetura do README passa a refletir o serving ativo por arquivos Gold e o PostgreSQL como backend opcional;
- documentação de arquitetura atualizada para município, comparação territorial e série histórica já implementados;
- status de produção alinhado ao render.yaml e ao Dockerfile atuais;
- teste de versões deixa de exigir atualização manual do número a cada release;
- novo guardrail verifica coerência entre documentação de produção e DATA_BACKEND=files;
- cobertura de dados permanece de janeiro a julho de 2026.

## 0.19.3

- documentação do frontend atualizada para refletir a experiência publicada;
- documentação de deploy alinhada ao Dockerfile e ao render.yaml atuais;
- removida a descrição antiga que tratava o serving por arquivos como estado temporário anterior à primeira publicação;
- teste automatizado passa a exigir alinhamento entre versões do backend, frontend e settings;
- teste automatizado protege o escopo publicado contra reintrodução do período excluído;
- regra contra travessões longos foi consolidada no mesmo conjunto de guardrails;
- cobertura de dados permanece de janeiro a julho de 2026.

## 0.19.2

- gráficos com tooltips confinados à área visível para melhor uso em telas pequenas;
- eixos passam a formatar números no padrão pt-BR;
- recuos e rótulos recebem configuração responsiva para celular;
- acessibilidade nativa do ECharts ativada com descrições ARIA;
- foco de série adicionado à evolução mensal para facilitar leitura interativa;
- tamanhos de legenda e barras refinados para reduzir poluição visual;
- cobertura de dados permanece de janeiro a julho de 2026.

## 0.19.1

- refinamento visual e responsivo do frontend público;
- competência mais recente passa a aparecer no conjunto de badges do hero;
- serving exibido no hero respeita o backend informado pela readiness;
- mensagem de erro pública deixa de sugerir localhost;
- terminologia de qualidade padronizada em português;
- valores ausentes de moeda passam a exibir N/D;
- modal de metodologia fecha com Escape, bloqueia o scroll de fundo e recebe foco inicial;
- rodapé passa a expor API, código-fonte e metodologia;
- metadados de descrição, indexação e compartilhamento aprimorados;
- foco visível, redução de movimento e ajustes para telas pequenas adicionados;
- cobertura de dados permanece de janeiro a julho de 2026.

## 0.19.0

- documentação técnica sincronizada com o estado real da série publicada;
- removida a indicação antiga de que julho ainda aguardava publicação;
- roadmap reestruturado para separar base concluída e próximas entregas;
- metodologia passa a documentar explicitamente a comparação Brasil, Nordeste e Ceará;
- README ganha snapshot territorial de julho de 2026 com participações derivadas dos agregados publicados;
- versão do backend alinhada para 0.19.0;
- cobertura permanece de janeiro a julho de 2026.

## 0.18.0

- comparação territorial da competência mais recente entre Brasil, Nordeste e Ceará;
- participação nas admissões tech nacionais calculada diretamente dos agregados publicados;
- participação do Ceará nas admissões tech do Nordeste;
- novo endpoint territorial na API;
- novo bloco visual responsivo no dashboard;
- cobertura histórica permanece de janeiro a julho de 2026.

## 0.17.0

- série histórica auditada de janeiro a julho de 2026;
- 134.209 admissões tech, 127.865 desligamentos e saldo acumulado +6.344;
- reconciliação nacional do MOV em cada uma das sete competências;
- FOR e EXC aplicados às competências de origem;
- remuneração real em valores de julho de 2026 pelo IPCA/IBGE;
- categoria municipal residual 999999 tratada como Não identificado sem inventar código IBGE;
- qualidade da dimensão municipal incorporada ao gate de publicação;
- endpoint de registro de releases com estado automático, aprovação e SHA-256;
- cobertura histórica publicada exposta no dashboard;
- publicação histórica reutiliza o artefato auditado e evita reprocessamento dos microdados.


## 0.16.0

- referências oficiais nacionais registradas para janeiro a julho de 2026;
- referência oficial passa a ser obrigatória no gate;
- backfill histórico de 2026 preparado para execução em lote;
- MOV de cada mês reconciliado separadamente da série ajustada;
- FOR e EXC permanecem aplicados às competências de origem;
- overview passa a registrar deltas de ajustes por tipo;
- processamento em um único runner para reduzir consumo de Actions.


## 0.15.0

- primeira competência tech real validada para julho/2026;
- 4.467.208 registros MOV reconciliados exatamente com a referência oficial;
- categoria Não identificado reconciliada separadamente;
- zero rejeições em MOV, FOR e EXC após tratamento do código residual oficial;
- 19.253 admissões tech, 18.347 desligamentos e saldo +906;
- salário mediano de admissão de R$ 3.990,06;
- 1.274 municípios enriquecidos com nome, UF e código IBGE;
- publicação vinculada ao SHA-256 do arquivo MOV;
- snapshot Gold e manifests de proveniência versionados sem microdados brutos.


## 0.14.1

- descompressão transparente de respostas gzip da API de Localidades do IBGE;
- sincronização de referências IBGE obrigatória na auditoria operacional;
- teste de resposta gzip com e sem cabeçalho Content-Encoding.


## 0.14.0

- categoria oficial Não identificado preservada como UF residual;
- auditoria nacional MOV gerada antes do recorte tech;
- reconciliação nacional exata com a referência oficial no gate;
- reconciliação específica de Não identificado;
- correção da classificação de 1.369 registros reais de julho/2026.


## 0.13.0

- transporte resiliente com FTP do MTE e fallback HTTPS;
- proveniência de transporte registrada nos manifests;
- processamento de FOR e EXC com deltas explícitos;
- reconstrução de competências afetadas por ajustes;
- Gold municipal;
- série histórica incremental;
- integração com municípios pela API oficial do IBGE;
- integração com IPCA pelo SIDRA;
- salário nominal e salário real no Gold e no serving;
- endpoints municipais e de série histórica;
- PostgreSQL municipal com migrations;
- PostgreSQL gerenciado provisionado no Render;
- visualizações de município e histórico no frontend;
- tipografia editorial justificada para textos corridos;
- regra automatizada que impede travessões no repositório.


## 0.12.0

- imagem de produção unificada para FastAPI + React;
- FastAPI serve o frontend compilado quando `frontend/dist` está presente;
- frontend usa `/api/v1` por padrão;
- proxy Vite mantém desenvolvimento local sem CORS;
- Docker multi-stage reduz a topologia pública a um único serviço;
- `render.yaml` com plano free e health check;
- documentação de deploy;
- testes garantindo root/API docs no modo de desenvolvimento.

## 0.11.0

- dashboard visual responsivo para análise pública;
- hero com pipeline auditável;
- contexto oficial Brasil/Ceará disponível mesmo sem Gold tech;
- gráfico regional com dados publicados pelo MTE;
- endpoint de referência oficial para o frontend;
- separação visual explícita entre mercado formal total e recorte tech;
- pipeline visual com estado aguardando/publicado;
- layout responsivo aprimorado;
- versão de backend alinhada à versão do pacote;
- workflow visual separado e acionado somente quando `frontend/**` muda.

## 0.10.0

- recorte CBO de tecnologia elevado para versão 2;
- inclusão de 2122: Engenheiros em computação;
- manutenção de 2123, 2124, 3171 e 3172;
- fontes oficiais da CBO registradas no arquivo de configuração;
- justificativa metodológica do recorte ocupacional;
- teste de regressão garantindo o conjunto exato de famílias;
- documentação dedicada em `docs/CBO_SCOPE.md`.

## 0.9.0

- referência oficial de julho/2026 versionada por Brasil, região e UF;
- testes de fechamento Brasil = 27 UFs + não identificados;
- testes de fechamento de cada região pela soma das respectivas UFs;
- metodologia salarial alinhada ao Sumário Executivo do MTE;
- salário mínimo de 2026 configurado em R$ 1.621,00;
- exclusão de salários abaixo de 0,3 salário mínimo e acima de 150 salários mínimos;
- exclusão de vínculos intermitentes das métricas salariais;
- fail-safe quando o indicador de trabalho intermitente não existe;
- contagem explícita de admissões elegíveis e excluídas das métricas salariais.

## 0.8.0

- camada PostgreSQL alinhada ao Gold real por competência, UF e CBO;
- carga transacional e idempotente;
- bloqueio da carga quando o gate de publicação não está aprovado;
- consultas da API diretamente no PostgreSQL via `DATA_BACKEND=postgres`;
- migrations Alembic;
- schema SQL atualizado;
- testes de serving com SQLite para manter o CI leve;
- Docker preparado para API usando PostgreSQL.

## 0.7.0

- gate de publicação por competência;
- validação de artefatos Bronze/Gold, proveniência e aritmética;
- limiar configurável de qualidade;
- aprovação metodológica manual vinculada ao SHA-256 do MOV;
- invalidação automática da aprovação quando o arquivo de origem muda;
- comandos `validate-release` e `approve-release`;
- endpoint `/api/v1/quality/publication-gate/latest`;
- testes do ciclo completo de bloqueio e aprovação.

## 0.6.0

- ingestão local auditável de TXT/.7z oficial;
- CLI `ingest-local` e `local-pipeline`;
- manifests descobertos recursivamente pela API;
- readiness exige overview + Gold analítico;
- endpoint de proveniência com SHA-256;
- card de proveniência no frontend;
- Dockerfiles para API e frontend;
- Docker Compose com PostgreSQL + API + web;
- testes de ingestão local, cobertura recursiva e readiness;
- documentação de execução local e Docker.

## 0.5.0

- frontend React + TypeScript com Vite;
- React Query para consumo da API;
- gráficos ECharts alimentados por Gold;
- estados loading, sem dados e API indisponível;
- painel de metodologia/rastreabilidade;
- endpoint analítico por UF;
- endpoint analítico por ocupação;
- Gold adicional por UF e CBO;
- CORS local para integração frontend/backend;
- novos testes para impedir publicação de analytics inexistentes.

## 0.4.0

- downloader FTP oficial do Novo CAGED;
- descoberta automática de MOV/FOR/EXC;
- extração 7z;
- Bronze com manifesto SHA-256;
- contrato de layout do MOV;
- detecção de schema drift;
- transformação Silver;
- rejeições auditáveis;
- Gold agregado;
- referência oficial de julho/2026 para futura reconciliação;
- CLI end-to-end;
- documentação do pipeline real;
- parsing defensivo de salário com vírgula ou ponto decimal;
- gate explícito que impede publicação automática no primeiro processamento;
- documentação de data lineage.

## 0.3.0

- API versionada em `/api/v1`;
- endpoints de health, readiness, fontes e cobertura;
- endpoint de indicadores que recusa publicar números sem dados oficiais;
- relatório estruturado de qualidade;
- testes de API e qualidade;
- CI leve para lint e testes;
- scripts locais;
- ADR documentando a escolha de DuckDB/Polars.
