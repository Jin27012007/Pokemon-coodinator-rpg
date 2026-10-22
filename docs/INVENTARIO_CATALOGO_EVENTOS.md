# Inventário do catálogo de eventos — referência fixa

## Escopo confirmado

A árvore da revisão `rh-hideout/pokeemerald-expansion@f4dc700a130330fd2f9325a17bbb1e2d91dbf091` foi consultada por meio da árvore Git completa (sem truncamento). Contagens de arquivos relevantes:

- `data/maps/*/scripts.inc`: 887 arquivos de scripts de mapa.
- `data/maps/*/map.json`: 939 definições de mapa.
- `data/scripts/*.inc`: 86 arquivos de scripts compartilhados.
- `src/*script*.c`: 7 arquivos do motor/integrações de scripts.
- `asm/macros/event.inc`: catálogo das macros de comandos.
- `data/script_cmd_table.inc`: tabela que associa opcodes a implementações.
- `data/event_scripts.s`: agregador que inclui scripts de mapas e scripts comuns.
- Cabeçalhos de flags e variáveis: `include/constants/flags*.h` e `include/constants/vars*.h`.

A extensão não usa `events.inc` por mapa nesta revisão; cada mapa declara `map.json` e `scripts.inc`. O JSON contém warps, coordinate/background events e objetos; scripts referenciados por objetos normalmente apontam para labels existentes em scripts locais ou compartilhados.

## Famílias de conteúdo para o plano de revisão

1. Scripts de mapa: callbacks, objetos, coordinate/background events, movimentos e diálogos.
2. Scripts compartilhados: funções chamadas por vários mapas, prêmios, lojas, sistemas de transporte e fluxos comuns.
3. Motor/commands: interpretação do bytecode, stack, estados de espera, transições, movimento e chamadas nativas.
4. Estado persistente: flags, vars, flags temporárias, special vars e flags de ocultação.
5. Dados declarativos: IDs de mapa, warps, posições/elevation, object local IDs, scripts ligados a objetos e tabelas de gatilhos.
6. Scripts especiais: scripts nativos C, scripts de batalha, Mystery Gift/Event e script de movimento.
7. Testes: analisador estático, compilação com a revisão fixa, execução em emulador e regressões manuais.

## Lacuna importante

O scanner atual do repositório é uma primeira heurística e ainda precisa ser validado contra a árvore completa. Ele não substitui o pré-processador/assembler do próprio jogo, não entende todas as macros e não pode concluir que um label “não usado” está morto sem consultar includes, objetos, C e dados gerados. Qualquer alerta deverá ser revisado manualmente antes de alterar ou remover código.
