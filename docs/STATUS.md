# Status de implementação

## Concluído

- frontend React/TypeScript integrado à API;
- dashboard sem dados fictícios;
- analytics Gold por UF e ocupação;

- arquitetura Bronze/Silver/Gold;
- descoberta automática de arquivos no FTP oficial;
- download de MOV/FOR/EXC;
- extração de `.7z`;
- manifesto SHA-256;
- detecção de mudança de layout;
- normalização de cabeçalhos com acentos;
- regras iniciais de qualidade;
- separação de registros rejeitados;
- recorte CBO versionado;
- Silver Parquet;
- Gold agregado;
- overview JSON consumível pela API;
- referência oficial de julho/2026;
- testes de schema e integridade da referência;
- gate de publicação vinculado ao SHA-256;
- camada PostgreSQL de serving;
- carga Gold → PostgreSQL transacional e idempotente;
- Alembic configurado;
- API com backend selecionável entre arquivos e PostgreSQL.

## Próximos gates

1. executar contra o arquivo oficial de julho/2026;
2. revisar rejeições reais;
3. confirmar parse de salário no layout atual;
4. validar códigos municipais;
5. implementar semântica testada de FOR/EXC;
6. reconciliar totais nacionais ajustados;
7. validar o build completo do frontend com as dependências instaladas;
8. carregar a primeira competência oficial aprovada no PostgreSQL;
9. conectar o dashboard aos primeiros dados oficiais validados;
10. preparar deploy público após a reconciliação metodológica.
