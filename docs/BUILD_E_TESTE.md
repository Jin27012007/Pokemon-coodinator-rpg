# Build e teste do protótipo

## Fonte do jogo

Esta branch usa `rh-hideout/pokeemerald-expansion`, e não o código-fonte de Pokémon Quetzal Alpha 9. O workflow fixa a revisão `f4dc700a130330fd2f9325a17bbb1e2d91dbf091` e confere esse SHA antes de aplicar os patches. Alterar essa revisão deve ser uma decisão explícita.

## Executar a compilação

Acesse [Build female-default boat-arrival prototype](https://github.com/Jin27012007/Pokemon-coodinator-rpg/actions/workflows/build-boat-arrival.yml), abra a execução mais recente e baixe o artefato `female-default-boat-arrival-build`. O artefato é temporário e expira após 7 dias.

Uma compilação anterior foi concluída com sucesso na execução [#39633590306](https://github.com/Jin27012007/Pokemon-coodinator-rpg/actions/runs/39633590306). Essa versão não passou no teste manual: o jogador relatou congelamento no fim da introdução. Uma compilação verde confirma apenas que o código compila, não que o fluxo de jogo funciona.

## Causa identificada do congelamento

A função `CB2_NewGame()` em `src/overworld.c` selecionava `ExecuteTruckSequence` para Emerald sempre que um jogo novo iniciava. A sequência do caminhão assume que o mapa atual é `InsideOfTruck`. O protótipo alterou o primeiro mapa para `LilycoveCity_Harbor`, mas mantinha o callback exclusivo do caminhão; a sequência ficava operando no mapa errado durante a transição final, consistente com a tela preta com a silhueta branca relatada no teste.

O patch atualizado troca esse callback por `FieldCB_WarpExitFadeFromBlack`, que realiza a entrada genérica no mapa depois do warp. Essa é a correção direcionada à causa identificada; ainda precisa ser validada em emulador.

## Teste manual obrigatório

Usar um jogo novo, em vez de um save anterior, e anotar o emulador e a versão:
- [ ] May aparece na introdução.
- [ ] A seleção de gênero é pulada e a personagem é definida como feminina.
- [ ] A tela de inserção do nome aparece.
- [ ] Confirmar o nome leva ao primeiro mapa sem ficar preso na tela preta com a silhueta.
- [ ] O jogo inicia no porto de Lilycove e os controles voltam a funcionar.
- [ ] O S.S. Tidal chega ao cais sem bloquear o mapa.
- [ ] É possível caminhar no porto, entrar em mapas conectados e retornar.
- [ ] Save/load funciona depois de concluir a chegada.
- [ ] A chegada inicial não se repete ao carregar o save.
- [ ] A viagem normal do S.S. Tidal continua funcionando no progresso comum.

A animação do barco implementada é uma aproximação curta ao cais dentro do mapa, não uma cena cinematográfica em mar aberto. Não enviar ROMs ao GitHub; a ROM é apenas um artefato temporário de teste.
