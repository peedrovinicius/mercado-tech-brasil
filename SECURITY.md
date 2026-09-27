# Segurança

## Versões suportadas

| Versão | Suporte |
| --- | --- |
| 0.40.x | Sim |
| anteriores a 0.40 | Não |

A versão suportada corresponde ao baseline publicado mais recente do projeto.

## Escopo

Relatos de segurança são relevantes quando envolvem, por exemplo:

- API FastAPI e frontend público;
- execução de workflows e cadeia de suprimentos;
- exposição de segredos, tokens ou credenciais;
- alteração indevida de artefatos Gold ou gates de publicação;
- bypass de controles de publicação, cobertura ou integridade;
- vulnerabilidades que permitam execução de código, injeção, acesso indevido ou comprometimento da aplicação.

Discordâncias metodológicas, correções estatísticas e problemas de qualidade de dados sem impacto de segurança devem ser tratados como questões de dados, não como vulnerabilidades.

## Como relatar

Não abra uma issue pública para uma vulnerabilidade ainda não corrigida.

Prefira o mecanismo privado de reporte de vulnerabilidade do GitHub quando ele estiver disponível no repositório. Caso essa opção não esteja disponível, entre em contato de forma privada com o mantenedor pelo perfil do GitHub.

Inclua, sempre que possível:

- descrição objetiva do problema;
- componente e versão afetados;
- passos mínimos para reprodução;
- impacto observado ou plausível;
- evidências sem dados pessoais ou segredos;
- sugestão de mitigação, se houver.

## Tratamento responsável

O mantenedor deve confirmar o recebimento, reproduzir o problema quando possível, avaliar impacto e preparar uma correção antes de qualquer divulgação pública que aumente o risco de exploração.

Uma correção de segurança deve preservar os mesmos controles usados no restante do projeto: testes, CI, política de deploy e validação em produção.

## Dados e segredos

O projeto publica análises agregadas derivadas de fontes públicas e não versiona microdados brutos.

Nunca envie ao repositório:

- credenciais;
- arquivos `.env`;
- dumps privados;
- dados pessoais;
- tokens de API;
- chaves privadas;
- cookies ou sessões autenticadas;
- workbooks protegidos por autenticação contendo informação que não possa ser redistribuída.

## Dependências

Dependências Python, npm e GitHub Actions são acompanhadas pelo Dependabot. A análise estática de Python e JavaScript/TypeScript é executada pelo CodeQL.
