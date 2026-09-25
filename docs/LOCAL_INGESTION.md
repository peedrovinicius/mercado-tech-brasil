# Ingestão local auditável

O PDET distribui os microdados por FTP. Alguns ambientes corporativos, navegadores e sandboxes não conseguem abrir FTP diretamente.

Por isso, o projeto oferece uma segunda entrada **sem alterar o pipeline analítico**.

## TXT já extraído

```bash
python -m src.cli local-pipeline 202607 "C:\Downloads\CAGEDMOV202607.txt" --kind MOV
```

## Arquivo .7z

```bash
python -m src.cli local-pipeline 202607 "C:\Downloads\CAGEDMOV202607.7z" --kind MOV
```

A ingestão:

1. copia o original para Bronze;
2. impede sobrescrever silenciosamente arquivo diferente;
3. extrai `.7z`, quando necessário;
4. calcula SHA-256;
5. cria manifesto;
6. para MOV, executa Silver e Gold;
7. para FOR/EXC, preserva a Bronze sem incorporá-los automaticamente aos indicadores.

## Por que isso é importante

A origem do arquivo muda (FTP automático ou download manual), mas:

- o formato oficial não é alterado;
- o SHA-256 é preservado;
- o pipeline seguinte é o mesmo;
- a API consegue expor a proveniência.

Isso torna a solução reproduzível mesmo quando o protocolo FTP não está disponível no ambiente de execução.
