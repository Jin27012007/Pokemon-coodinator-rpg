# Referência de arquivos e responsabilidades

Este índice resume onde investigar cada sistema na árvore de referência enviada. Ele é um mapa de navegação, não uma alegação de que já entendemos cada implementação até o último detalhe.

| Sistema | Arquivos/pontos iniciais | O que entender antes de modificar |
|---|---|---|
| Novo jogo e warp inicial | `src/new_game.c`, `data/maps/InsideOfTruck/scripts.inc`, `data/maps/InsideOfTruck/map.json` | ordem de inicialização, flags, respawn, warp dinâmico, estado da introdução |
| Gênero/protagonista | `src/intro.c`, `src/main_menu.c`, `src/oak_speech.c`, `include/global.h` | diferença entre gênero aleatório da cena promocional e gênero real salvo, seleção do jogador, gráficos e nomes |
| Porto de Lilycove | `data/maps/LilycoveCity_Harbor/scripts.inc`, `events.inc`, `map.json`, arquivos de movimento associados | warp de entrada, posições de NPCs, scripts de ferry, escapewarp, flags e variáveis |
| Scripts comuns | `data/scripts/*.inc`, `data/event_scripts.s` e includes relacionados | sintaxe de comandos, macros, labels, chamadas de specials e scripts reutilizados |
| Mapas/eventos | `data/maps/*/map.json`, `events.inc`, `scripts.inc`, `connections.inc` | IDs dos mapas, entradas, NPCs, objetos, coordenadas e transições |
| Fitas do Pokémon | `src/contest_util.c::GiveMonContestRibbon`, dados/headers de Pokémon e fitas | quais bits/valores representam ranks, como a fita é atribuída e vista |
| Sistema de Concursos | `src/contest.c`, `src/contest_ai.c`, `src/contest_effect.c`, `src/contest_util.c`, `data/scripts/contest_hall.inc`, `include/contest.h` | categoria, rank, ordem final, elegibilidade, prêmios, flags e estados de batalha |
| Saves e progressão | `include/global.h`, `include/save.h`, `src/new_game.c`, rotinas de load/save e `constants/flags.h` / `constants/vars.h` | espaço de save, valores reiniciados em jogo novo, migração de save e risco de colidir com flags existentes |
| Compilação | `Makefile`, `INSTALL.md`, `tools/`, `.github/workflows/build.yml` | toolchain ARM, ferramentas de dados/gráficos, dependências, comandos de build e verificação |
| Gráficos e som | `graphics/`, `sound/`, tabelas de sprites/mapas e scripts de inserção | formatos, compressão, paletas, nomes de recursos e regras de uso de assets |
| Constantes e dados | `constants/`, `include/constants/` quando presentes, tabelas em `src/data/` | IDs estáveis, relações entre enums, flags/vars e dados serializados |
| Testes e validação | `test/`, `dev_scripts/`, workflows em `.github/workflows/` | o que pode ser testado automaticamente e o que exige abrir a ROM em um emulador |

## Diferença importante sobre o gênero

Em `src/intro.c`, `sIntroCharacterGender` é inicializado com um valor aleatório para a sequência visual da introdução. Isso não é a seleção permanente da protagonista. O gênero real aparece no save como `gSaveBlock2Ptr->playerGender` e tem usos espalhados pelo jogo. Como nosso alvo é uma protagonista feminina, devemos ajustar corretamente a seleção/inicialização do jogador na base escolhida, e verificar retratos, sprites, pronomes/textos, rival e flags de casas; não basta alterar a cena de Flygon.

## Prioridade prática

A mudança inicial deve ser pequena e de baixo acoplamento: após entender como um novo save prepara o estado do jogador e o warp, selecionar explicitamente a protagonista feminina e inicializar o local/flags necessários para começar no porto. A cena do barco pode vir em seguida como evento limitado à primeira entrada. O sistema de fitas deve ser outra alteração independente, com testes separados.
