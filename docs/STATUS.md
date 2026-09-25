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
- testes de schema e integridade da referência.

## Próximos gates

1. executar contra o arquivo oficial de julho/2026;
2. revisar rejeições reais;
3. confirmar parse de salário no layout atual;
4. validar códigos municipais;
5. implementar semântica testada de FOR/EXC;
6. reconciliar totais nacionais ajustados;
7. iniciar frontend somente depois desses gates.
