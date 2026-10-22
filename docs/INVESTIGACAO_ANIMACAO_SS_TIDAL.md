# Caderno de investigação da animação inicial do SS Tidal

Base inspecionada: `rh-hideout/pokeemerald-expansion@f4dc700a130330fd2f9325a17bbb1e2d91dbf091`.

## Evidência estabelecida
- A ROM diagnostic build sem a cena foi testada manualmente pelo usuário: jogo novo chegou a Lilycove e foi jogável.
- A versão anterior colocou `clearflag FLAG_HIDE_LILYCOVE_HARBOR_SSTIDAL`, `setobjectxyperm LOCALID_LILYCOVE_HARBOR_SS_TIDAL, 15, 9`, `addobject`, `applymovement ...` e `waitmovement 0` dentro de `LilycoveCity_Harbor_OnTransition`.
- `MAP_SCRIPT_ON_TRANSITION` roda durante a transição. A definição oficial em `include/constants/map_scripts.h` indica que é tipicamente para flags/vars, posições de objetos, tipos de movimento e estado do mapa.
- `MAP_SCRIPT_ON_FRAME_TABLE` roda a cada frame depois do fade-in, antes da entrada do jogador; `MAP_SCRIPT_ON_WARP_INTO_MAP_TABLE` corre depois de carregar os object events e serve normalmente para adicionar objetos/ajustar estado da entrada.
- `map.json` define o SS Tidal no porto na posição (8,9), com script `0x0` e flag de ocultação `FLAG_HIDE_LILYCOVE_HARBOR_SSTIDAL`.
- `VAR_TEMP_D/E/F` não são exclusivas: a revisão usa-as em sistemas como Battle Frontier/Pyramid. Não usar essas variáveis para o estado da cena sem analisar o fluxo global.

## Conclusão até aqui
A combinação “spawn/posicionamento do objeto + movimento + espera” durante a transição síncrona é um risco de bloqueio real. O teste confirmou que remover esse bloco elimina o travamento observado, mas ainda não isola qual comando ou interação é responsável.

## Próxima implementação — ordem de experimentação
1. **Teste A (sem movimento):** estado de primeira chegada, exibição/reposicionamento do objeto e retorno imediato. Confirmar visualmente se a posição inicial é correta e que o jogo fica livre.
2. **Teste B (movimento sem espera bloqueante no callback):** disparar após entrada estável, em um contexto que processe updates por frame, usando um sinal que não colida com outros sistemas.
3. **Teste C (conclusão idempotente):** garantir que a cena não reinicia em reentrada, save/load, retorno de batalha/menu, nem interfere na viagem normal do ferry.
4. **Teste D (animação completa):** depois de A-C, restaurar os sete passos e testar saída/reentrada e save/load.

Cada teste deve ser um patch/build separado. A ROM sem cena é a baseline e não será substituída. O patch experimental não deve entrar em `patches/ACTIVE_PATCHES.txt` até compilar e passar no teste manual.

## Estado
A auditoria está suficientemente avançada para definir esta matriz, mas não para declarar todos os eventos do jogo revisados linha a linha. O scanner global é heurístico e há ainda uma revisão manual pendente de flags/vars, comandos de espera, callbacks síncronos, scripts nativos em C e cenários de regressão.
