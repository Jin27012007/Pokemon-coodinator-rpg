# Catálogo inicial: gatilhos de mapa e movimentos

Base: `rh-hideout/pokeemerald-expansion` em `f4dc700a130330fd2f9325a17bbb1e2d91dbf091`.

## Estrutura declarativa de mapa

O arquivo `data/maps/LilycoveCity_Harbor/map.json` define o mapa e objetos de evento. Constatações diretas do arquivo:

- ID: `MAP_LILYCOVE_CITY_HARBOR`, layout `LAYOUT_HARBOR`.
- O objeto do SS Tidal usa `LOCALID_LILYCOVE_HARBOR_SS_TIDAL`, gráfico `OBJ_EVENT_GFX_SS_TIDAL`, coordenadas (8, 9), movimento `MOVEMENT_TYPE_FACE_RIGHT`, script `0x0`, e flag `FLAG_HIDE_LILYCOVE_HARBOR_SSTIDAL`.
- O atendente do ferry usa a própria flag de ocultação e um script distinto.
- Existem dois warps na saída do mapa em (11,14) e (12,14), ambos com destino à cidade de Lilycove.

Isso confirma que o barco já existe como objeto estático e normalmente começa oculto por uma flag. Uma animação de chegada inicial precisa tratar de forma coerente a flag de visibilidade e a posição persistente; não deve assumir que adicionar o objeto é suficiente em todos os estados de save/load.

## Gatilho existente

O cabeçalho de `data/maps/LilycoveCity_Harbor/scripts.inc` usa `MAP_SCRIPT_ON_TRANSITION`. O callback original define apenas o escapewarp e termina. A tentativa experimental adicionou o controle de flag, posicionamento do SS Tidal, `addobject`, `applymovement` e `waitmovement 0` ao mesmo callback. O congelamento não deve ser atribuído definitivamente a um único comando até isolar cada variável; o momento de execução é igualmente suspeito.

## Próximas etapas técnicas

Antes de fazer outro patch:
- confirmar em `include/constants/flags.h` a semântica e os comentários da flag do SS Tidal e procurar todos os usos da flag;
- verificar se o movimento precisa ocorrer em tile/elevation que aceite o objeto e se as sete etapas terminam em uma posição válida;
- revisar macros de eventos em `asm/macros/event.inc` e as definições de `map_script`, `applymovement`, `waitmovement`, `setobjectxyperm`, `addobject` e `clearflag`;
- escolher um disparador seguro após o mapa estar estável e garantir execução única com estado persistente;
- compilar cada variação e manter a ROM que o usuário testou como baseline.

## Links para a revisão usada

- [map.json](https://github.com/rh-hideout/pokeemerald-expansion/blob/f4dc700a130330fd2f9325a17bbb1e2d91dbf091/data/maps/LilycoveCity_Harbor/map.json)
- [scripts.inc](https://github.com/rh-hideout/pokeemerald-expansion/blob/f4dc700a130330fd2f9325a17bbb1e2d91dbf091/data/maps/LilycoveCity_Harbor/scripts.inc)
- [flags.h](https://github.com/rh-hideout/pokeemerald-expansion/blob/f4dc700a130330fd2f9325a17bbb1e2d91dbf091/include/constants/flags.h)
- [event_scripts.s](https://github.com/rh-hideout/pokeemerald-expansion/blob/f4dc700a130330fd2f9325a17bbb1e2d91dbf091/data/event_scripts.s)
