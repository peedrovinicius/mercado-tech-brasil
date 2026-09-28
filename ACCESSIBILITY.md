# Acessibilidade

O Mercado Tech Brasil busca manter a interface utilizável por teclado, leitores de tela e pessoas com sensibilidade a movimento ou diferentes necessidades visuais.

## Implementado

A interface atual possui:

- estrutura semântica com `header`, `nav`, `main` e `footer`;
- rótulos ARIA nos controles que precisam de nome acessível;
- região `aria-live` para estados dinâmicos relevantes;
- estilos de `:focus-visible` para navegação por teclado;
- respeito a `prefers-reduced-motion`;
- informação textual acompanhando indicadores visuais;
- layout responsivo para diferentes larguras de tela.

## Princípios

Novas funcionalidades devem:

1. permanecer operáveis sem mouse;
2. não depender apenas de cor para transmitir significado;
3. manter foco visível;
4. usar HTML semântico antes de ARIA customizada;
5. fornecer nomes acessíveis para controles;
6. respeitar redução de movimento;
7. preservar legibilidade em zoom e telas menores.

## Relatar uma barreira

Use o formulário de problema do GitHub e descreva:

- página ou controle afetado;
- barreira encontrada;
- tecnologia assistiva e navegador, quando relevante;
- comportamento esperado.

Não inclua informações pessoais desnecessárias no relato.

## Escopo

Esta declaração descreve os controles implementados no código atual. Ela não representa certificação formal de conformidade com WCAG. Barreiras identificadas devem ser tratadas como defeitos de produto e cobertas por teste quando tecnicamente viável.
