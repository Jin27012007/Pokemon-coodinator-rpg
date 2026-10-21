# Fluxos prioritários para entender antes de editar

Esta nota aprofunda os caminhos de execução observados na cópia de referência.

## A. Começo de um jogo novo

1. `src/new_game.c` declara a função privada `WarpToTruck()`.
2. Na cópia analisada, ela escolhe o mapa inicial (caminhão no Emerald; um mapa de casa em FRLG) com `SetWarpDestination(...)` e executa `WarpIntoMap()`.
3. O fluxo de `NewGameInitData()` chama `WarpToTruck()` e depois executa `EventScript_ResetAllMapFlags` no caminho de Emerald.
4. `data/maps/InsideOfTruck/scripts.inc` é a próxima área que controla scripts associados à introdução e às transições para Littleroot.
5. `src/intro.c` é importante para compreender o gênero/personagem; na cópia de referência existe `sIntroCharacterGender`, e a cena introdutória tem ramos de desenho/representação segundo esse gênero. O gênero salvo do jogador é armazenado no campo `playerGender` do save.

**Risco a evitar:** trocar apenas o destino inicial pode pular inicialização narrativa, flags, variáveis ou outros passos que a introdução espera. Precisamos ler o contexto completo da chamada e os scripts acionados na primeira entrada de mapa antes de implementar.

## B. Porto de Lilycove

O script `LilycoveCity_Harbor_OnTransition` define o escapewarp normal para `MAP_LILYCOVE_CITY` em coordenadas específicas. Isso é configuração de saída/retorno, não uma cena de chegada inicial.

O mapa tem scripts robustos para ferries e tickets de pós-jogo. Eles usam variáveis, flags, seleção de destino e movimento de personagens. A cena inicial deve ser um script separado, ativado somente na primeira chegada, em vez de alterar indiscriminadamente o atendente de ferry ou substituir as rotinas de viagem.

Antes do código, confirmar:
- quem aparece e em que coordenadas no porto;
- como a entrada de mapa inicial é definida;
- se há warp de água/porto que exige orientação específica do jogador;
- quais flags de evento já foram inicializadas;
- qual ponto salva/define respawn e para onde volta o jogador depois de desmaiar;
- se a cena precisa ter barco visual/animação ou se uma transição de tela e diálogo bastam para o primeiro protótipo.

## C. Concurso e fita

Na cópia de referência, `src/contest_util.c::GiveMonContestRibbon()` concede ao Pokémon uma fita conforme o rank/categoria, quando o Pokémon termina em primeiro. A informação fica no registro do Pokémon (`SetMonData`), não é por si só uma ficha persistente de carreira para a protagonista.

Separar dois conceitos:
- **Fitas do Pokémon:** são dados por criatura, associados às categorias/ranks atuais.
- **Carreira da Coordenadora:** é progressão da protagonista/save, que pode incluir total de vitórias, ranks desbloqueados, concursos concluídos e narrativa.

A implementação futura deve escolher explicitamente onde salvar a carreira. Flags/variáveis têm limite e significados existentes; idealmente, usar um campo de save ou estrutura compatível com a base exata, depois de avaliar migração e compatibilidade com saves existentes.

## D. Toolchain

O Makefile usa prefixo `arm-none-eabi-` e suporta a configuração `DEVKITARM`. A build também usa ferramentas/scripts do próprio projeto. Esta auditoria ainda não executou uma compilação; por isso não se declara que o build é funcional neste ambiente.

## E. Compatibilidade e procedência

A pasta extraída é a referência `pokeemerald-expansion` informada no arquivo ZIP. O Quetzal de créditos próprios usa essa família de base, mas a árvore exata do código-fonte Quetzal Alpha 9 ainda não foi localizada. Até encontrarmos uma fonte versionada correspondente ou confirmar correspondência de versão por artefatos confiáveis, mudanças nessa árvore são protótipos sobre a base de referência, não patches garantidos para Quetzal Alpha 9.
