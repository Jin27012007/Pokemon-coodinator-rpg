# Auditoria de eventos — Pokemon Coordinator RPG

Data da auditoria: 2026-10-22  
Branch analisada: `experimental/pokeemerald-reference`  
Commit analisado: `a9ccc47d56bce8f64f9ef8aae41b05e553bafe18`  
Base de compilação: `rh-hideout/pokeemerald-expansion` em `f4dc700a130330fd2f9325a17bbb1e2d91dbf091`

## Resultado do reconhecimento

A árvore do repositório experimental contém workflows de build, documentação técnica e quatro patches numerados. O código-fonte completo da engine não está guardado nesta branch: o workflow baixa uma revisão fixa do repositório `rh-hideout/pokeemerald-expansion` durante a compilação e aplica os patches sobre ela. Portanto, alterações de eventos precisam ser avaliadas contra essa revisão exata.

## Constatações confirmadas

- A versão de diagnóstico foi compilada no workflow [39688172012](https://github.com/Jin27012007/Pokemon-coodinator-rpg/actions/runs/39688172012); o usuário confirmou no teste manual que chegou a Lilycove e conseguiu jogar sem congelamento quando a animação do barco foi removida.
- O patch 0004 altera `src/main_menu.c` (fluxo que salta a escolha de gênero e segue para o nome), `src/new_game.c` (retira uma atribuição de gênero feita no início do save) e `src/overworld.c` (troca `ExecuteTruckSequence` por `FieldCB_WarpExitFadeFromBlack`).
- O histórico técnico informa que o evento de chegada havia sido integrado a `LilycoveCity_Harbor_OnTransition`, junto a visibilidade/posicionamento do barco e um movimento com espera. Isso acopla a cena cinematográfica à transição do mapa.
- O patch 0003 redireciona o warp de `WarpToTruck()` para `MAP_LILYCOVE_CITY_HARBOR` nas coordenadas (11, 13) e define a protagonista feminina no save.
- A revisão upstream é fixa no workflow atual, que ajuda a tornar as builds reprodutíveis.

## Hipótese prioritária sobre o congelamento

A animação do barco/alterações ao callback de transição é a principal suspeita porque removê-la resultou numa ROM que o usuário testou com sucesso. Isso ainda não determina qual comando exato era responsável. A causa pode estar no momento em que o evento roda, no estado/visibilidade do objeto, numa espera de movimento, ou na interação com a inicialização do mapa.

## Procedimento seguro para eventos

1. Preservar a compilação sem animação como baseline de regressão; não sobrescrevê-la.
2. Inspecionar o script original completo da revisão upstream fixa: `data/maps/LilycoveCity_Harbor/scripts.inc`, mais `events.inc` e `map.json`.
3. Diferenciar os gatilhos e pontos de execução: `OnTransition`, `OnLoad`, `OnFrame`, scripts de gatilho e scripts de objeto/NPC. Não colocar uma cena com esperas bloqueantes num callback que deve apenas inicializar o mapa.
4. Mapear cada comando da cena, referências a object events, flags/vars, condições de primeira execução e caminho de saída de todos os ramos.
5. Reintroduzir uma única alteração por build, com flag persistente para garantir execução única e um fallback que nunca deixe o jogador bloqueado.
6. Validar aplicação do patch, diff, compilação e então teste manual com save novo e save/load. Testar também a viagem normal do S.S. Tidal.
7. Documentar o resultado observado separadamente da inferência técnica.

## Limites desta auditoria

Esta etapa reconheceu a arquitetura do repositório, os patches e os workflows. Ainda não foi feita uma análise linha por linha do script original da engine porque os arquivos da base upstream são baixados dentro do job e não constam na árvore do projeto; o próximo passo é buscar o arquivo da revisão fixa diretamente e construir o mapa de fluxo. Também não foi identificada uma revisão de código-fonte oficial que corresponda exatamente ao Pokémon Quetzal Alpha 9, então não se deve afirmar compatibilidade com essa ROM.

## Referências do repositório

- [Branch experimental](https://github.com/Jin27012007/Pokemon-coodinator-rpg/tree/experimental/pokeemerald-reference)
- [Patch 0004](https://github.com/Jin27012007/Pokemon-coodinator-rpg/blob/experimental/pokeemerald-reference/patches/0004-female-default-and-boat-arrival.patch)
- [Workflow de compilação](https://github.com/Jin27012007/Pokemon-coodinator-rpg/blob/experimental/pokeemerald-reference/.github/workflows/build-boat-arrival.yml)
- [Documentação de build e teste](https://github.com/Jin27012007/Pokemon-coodinator-rpg/blob/experimental/pokeemerald-reference/docs/BUILD_E_TESTE.md)
