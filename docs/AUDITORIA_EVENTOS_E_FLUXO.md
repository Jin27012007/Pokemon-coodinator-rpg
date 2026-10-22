# Auditoria de eventos — Pokemon Coordinator RPG

Data da auditoria: 2026-10-22  
Branch de trabalho: `experimental/pokeemerald-reference`  
Base de compilação: `rh-hideout/pokeemerald-expansion` em `f4dc700a130330fd2f9325a17bbb1e2d91dbf091`

## Resultado do reconhecimento

O repositório experimental mantém a lógica do projeto em patches e baixa uma revisão fixa do código-fonte de `pokeemerald-expansion` durante os workflows. Para mudanças de eventos, a referência obrigatória é essa revisão upstream exata, e não o binário de Pokémon Quetzal Alpha 9. Ainda não identificamos uma revisão oficial do código-fonte que corresponda exatamente a Quetzal Alpha 9.

## Constatações confirmadas

- O usuário testou a ROM de diagnóstico e confirmou que, removida a animação, o jogo entra em Lilycove e permanece jogável.
- O patch 0003 redireciona o warp inicial de `WarpToTruck()` para `MAP_LILYCOVE_CITY_HARBOR` nas coordenadas (11, 13).
- O patch 0004 altera o fluxo da apresentação feminina em `src/main_menu.c` e o callback inicial em `src/overworld.c`.
- A animação do barco foi adicionada ao `LilycoveCity_Harbor_OnTransition` e executava mudança da flag de ocultação, posicionamento do barco, `addobject`, `applymovement` e `waitmovement 0`.
- A revisão upstream fixa contém 887 arquivos `data/maps/*/scripts.inc`, 939 arquivos `data/maps/*/map.json`, 86 arquivos de scripts compartilhados em `data/scripts/`, além do motor em `src/script.c` / `src/scrcmd.c` e das macros em `asm/macros/event.inc`.

## Causa identificada para o congelamento do barco

A hipótese foi refinada pela leitura direta do motor: o bloqueio é consistente com a combinação de `waitmovement 0` dentro do script `MAP_SCRIPT_ON_TRANSITION`.

1. `src/overworld.c` chama `RunOnTransitionMapScript()` enquanto prepara a entrada do mapa.
2. `src/script.c` despacha esse tipo por `MapHeaderRunScriptType()`, que usa `RunScriptImmediately()`.
3. `RunScriptImmediately()` executa o script em um laço síncrono até ele terminar, sem devolver o controle normal ao ciclo de quadros.
4. `src/scrcmd.c::ScrCmd_waitmovement()` troca para o native `WaitForMovementFinish`, que continua aguardando o término do movimento do objeto.
5. O movimento depende de atualizações do jogo por quadro; aguardar seu término dentro do laço síncrono de transição pode prender o processo antes de o mapa ficar jogável.

O teste manual de sucesso após remover a animação corrobora fortemente esta explicação. A causa técnica está identificada, mas a correção final da cena ainda precisa ser provada por uma nova implementação em contexto assíncrono e por teste manual.

Referências do upstream:
- [Chamadas de transição e resume em `overworld.c`](https://github.com/rh-hideout/pokeemerald-expansion/blob/f4dc700a130330fd2f9325a17bbb1e2d91dbf091/src/overworld.c#L901-L913)
- [Execução síncrona em `RunScriptImmediately`](https://github.com/rh-hideout/pokeemerald-expansion/blob/f4dc700a130330fd2f9325a17bbb1e2d91dbf091/src/script.c#L359-L366)
- [Despacho de gatilhos em `script.c`](https://github.com/rh-hideout/pokeemerald-expansion/blob/f4dc700a130330fd2f9325a17bbb1e2d91dbf091/src/script.c#L389-L394)
- [Implementação de `waitmovement` em `scrcmd.c`](https://github.com/rh-hideout/pokeemerald-expansion/blob/f4dc700a130330fd2f9325a17bbb1e2d91dbf091/src/scrcmd.c#L1334-L1346)
- [Commit que introduziu a sequência de chegada](https://github.com/Jin27012007/Pokemon-coodinator-rpg/commit/37d90bc06ef23b921db0e68b682ca349bd13be04)

## Regras de segurança extraídas desta investigação

1. Preservar a ROM sem animação como baseline; não substituí-la durante os experimentos.
2. Separar callbacks de configuração de mapa de cenas com movimentos, mensagens e esperas.
3. Distinguir os contextos dos gatilhos: `ON_TRANSITION`, `ON_LOAD`, `ON_RESUME`, `ON_RETURN_TO_FIELD`, `ON_DIVE_WARP` e `ON_WARP_INTO_MAP_TABLE` executam scripts por caminho imediato; `ON_FRAME_TABLE` usa o contexto global e seleciona o primeiro script cuja condição passa.
4. Antes de remover ou renomear um evento, procurar referências nas labels, scripts compartilhados, objetos do `map.json`, flags/vars e código nativo.
5. Para cada alteração: validar aplicação do patch, revisar o diff, executar análise estática, compilar a revisão fixada e testar manualmente novo jogo, movimentação, save/load e fluxo normal do ferry.
6. Não tratar a compilação bem-sucedida como prova de ausência de congelamento; a execução dentro do jogo segue necessária.

## Estado da auditoria

- [x] Inventário estrutural da árvore de eventos.
- [x] Fluxo do motor de scripts e diferentes tipos de gatilhos mapeados.
- [x] Causa provável do congelamento de chegada ligada ao `waitmovement` síncrono, corroborada pelo teste manual.
- [x] Scanner inicial para referências cruzadas adicionado ao branch.
- [ ] Calibrar o scanner contra todos os casos condicionais e confirmar falsos positivos.
- [ ] Concluir a análise de referências de comandos de espera em callbacks síncronos.
- [ ] Compilar a base completa via workflow de auditoria.
- [ ] Projetar e testar a nova chegada após o mapa estar estável, com execução única e sem travar o ciclo de quadros.

## Referências do projeto

- [Branch experimental](https://github.com/Jin27012007/Pokemon-coodinator-rpg/tree/experimental/pokeemerald-reference)
- [Patch 0004](https://github.com/Jin27012007/Pokemon-coodinator-rpg/blob/experimental/pokeemerald-reference/patches/0004-female-default-and-boat-arrival.patch)
- [Workflow de compilação de diagnóstico](https://github.com/Jin27012007/Pokemon-coodinator-rpg/blob/experimental/pokeemerald-reference/.github/workflows/build-boat-arrival.yml)
- [Guia de build e teste](https://github.com/Jin27012007/Pokemon-coodinator-rpg/blob/experimental/pokeemerald-reference/docs/BUILD_E_TESTE.md)
