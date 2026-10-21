# Auditoria técnica — mapa do código-fonte de referência

> Escopo: arquivo local `pokeemerald-expansion-master.zip` enviado nesta conversa. Esta auditoria descreve essa cópia, não afirma que ela seja idêntica ao código-fonte do Pokémon Quetzal Alpha 9.

## Identidade da base

O README incluído descreve `pokeemerald-expansion` como uma base de ROM hack construída sobre a descompilação de `pret/pokeemerald`, e declara que não é um jogo jogável pronto. O README identifica a linhagem como RHH `pokeemerald-expansion 1.17.1`.

O arquivo ZIP contém aproximadamente 30.215 arquivos. Diretórios relevantes incluem `src/`, `include/`, `constants/`, `data/`, `data/maps/`, `data/scripts/`, `graphics/`, `sound/`, `tools/`, `test/` e `docs/`.

Os créditos de Quetzal enviados separadamente citam `pret/pokeemerald` como jogo base e `rh-hideout/pokeemerald-expansion` para motor de batalha, expansão de Pokémon e itens. Isso é consistente com a linhagem, mas não identifica por si só um commit exato do Quetzal.

## Linguagens e formatos encontrados na arquitetura

- **C**: lógica do jogo em `src/*.c`, declarada via cabeçalhos em `include/*.h`.
- **Assembly ARM / GNU as**: partes de baixo nível em `asm/` e chamadas de sistema em `libagbsyscall/`.
- **Scripts de eventos próprios do pokeemerald**: comandos como `map_script`, `goto_if_unset`, `setvar`, `special`, `warp`, `setescapewarp`, em arquivos `data/maps/*/scripts.inc` e `data/scripts/*.inc`. Não são JavaScript nem Python.
- **Definições declarativas de dados**: cabeçalhos e arquivos de dados para constantes, movimentos, Pokémon, treinadores e concursos.
- **JSON**: metadados de mapas/eventos, por exemplo `data/maps/LilycoveCity_Harbor/map.json`.
- **Makefile e ferramentas de build**: o `Makefile`, scripts em `tools/` e documentação `INSTALL.md` descrevem a montagem da ROM.
- **Recursos binários/gráficos/áudio**: `graphics/` e `sound/`, que têm pipeline de conversão/inserção próprio.

## Início de jogo: pontos para acompanhar

Em `src/new_game.c`:
- Existe a função estática `WarpToTruck()`.
- Ela é invocada no fluxo de inicialização de jogo novo.
- Isso aponta para o início original em Littleroot/ caminhão como uma das entradas que precisam ser rastreadas.

Arquivos relacionados:
- `data/maps/InsideOfTruck/scripts.inc`: eventos da introdução e passagem para Littleroot.
- `src/intro.c`: inclui código da cena introdutória e tratamento de gênero/personagem do jogador (os nomes concretos de funções e variáveis devem ser seguidos na análise posterior).
- `data/maps/LilycoveCity_Harbor/scripts.inc`: contém os scripts atuais do porto, principalmente o sistema de ferry pós-jogo e eventos de tickets. Não devemos simplesmente substituir esse script complexo pelo evento inicial.

## Concursos e fitas: pontos para acompanhar

Arquivos/símbolos identificados:
- `src/contest.c`, `src/contest_ai.c`, `src/contest_effect.c`, `src/contest_util.c` e arquivos de dados de oponentes de Concurso.
- `data/scripts/contest_hall.inc`: fluxo de atendimento/entrada e entrega de fitas.
- `src/contest_util.c`: função `GiveMonContestRibbon()`, responsável pela fita do Pokémon vencedor/participante no sistema existente.
- `constants/` e dados de Pokémon definem os tipos de fitas/ranks.
- Há ranks de Concurso como Normal, Super, Hyper e Master na cópia auditada.

Implicação de design: fita de Pokémon e carreira persistente da protagonista são conceitos diferentes. A futura progressão da Coordenadora precisa de estado próprio salvo no jogo (ou uma estratégia explicitamente justificada de flags/variáveis já existentes), sem supor que receber uma fita no Pokémon automaticamente registra uma etapa da carreira do jogador.

## Alertas técnicos

1. A ROM Quetzal Alpha 9 é um binário; não revela diretamente a árvore de código-fonte usada para construí-la.
2. O ZIP de referência não está confirmado como o exato source tag/commit de Quetzal Alpha 9.
3. O sistema de porto existente realiza viagens e depende de flags, variáveis e objetos de mapa. Um evento de chegada inicial deve ser separado da lógica normal de ferry sempre que possível.
4. A build do projeto requer toolchain compatível com GBA (incluindo compilador ARM e ferramentas do projeto). Ainda não houve tentativa de compilar esta cópia.
5. Sprites/arte de Quetzal podem ter restrições; os créditos enviados alertam expressamente que muitos sprites não são de uso público. Não copiar esses assets para o repositório sem autorização.
6. ROMs comerciais não devem ser carregadas no repositório.

## Próximas verificações

- Extrair a árvore e anotar os arquivos de boot, intro, saves, map scripts e concursos.
- Comparar indicadores da ROM Quetzal e a base de referência sem distribuir a ROM.
- Procurar um source oficial/versionado do Quetzal, caso disponível, ou manter a referência como base provisória e sinalizar incompatibilidades.
- Antes de implementar, mapear onde gênero/personagem se decide, onde o primeiro warp é definido, como salvamento/respawn funciona, quais flags a introdução espera, como a entrada de mapas e o ferry funcionam, e como as fitas de Pokémon são gravadas.
- Criar pequenas alterações isoladas, revisar os diffs e compilar/testar cada uma antes da próxima.

## Estado desta auditoria

- [x] Árvore do ZIP inventariada.
- [x] Principais linguagens e formatos identificados.
- [x] Primeiro ponto de entrada, scripts do porto e utilitário de fitas localizados.
- [ ] Versão exata do código-fonte Quetzal Alpha 9 identificada.
- [ ] Fluxo completo de inicialização/novo jogo mapeado.
- [ ] Persistência de progressão da Coordenadora projetada.
- [ ] Ferramenta de compilação executada e ROM de teste validada.


## Atualização de profundidade: observações confirmadas nos fontes

- `src/new_game.c::WarpToTruck()` define o destino de warp e chama `WarpIntoMap()`. `NewGameInitData()` chama essa função antes de executar `EventScript_ResetAllMapFlags` no caminho de Emerald.
- Em `data/maps/InsideOfTruck/scripts.inc`, `InsideOfTruck_EventScript_SetIntroFlags` verifica o gênero já salvo e separa duas rotas: cada uma define um respawn, um estado da introdução, flags para ocultar personagens/objetos e um warp dinâmico para Littleroot. Este é um motivo concreto para não apenas trocar o mapa de destino: precisamos substituir ou adaptar explicitamente essa inicialização.
- Em `src/intro.c::Task_Scene1_Load()`, `sIntroCharacterGender` é escolhido aleatoriamente para a cena visual (Brendan/May). Isso não deve ser confundido com `gSaveBlock2Ptr->playerGender`, o campo persistente usado por diversos sistemas do jogo.
- O fluxo atual de prêmios em `data/scripts/contest_hall.inc` chama `HasMonWonThisContestBefore`; se elegível, chama `GiveMonContestRibbon`, incrementa `GAME_STAT_RECEIVED_RIBBONS`, seta `FLAG_SYS_RIBBON_GET` e mostra diálogos de prêmio. É assim que o jogo vincula a fita ao prêmio do concurso.
- `src/contest_util.c::GiveMonContestRibbon()` retorna se o jogador não ficou em primeiro; do contrário, incrementa o dado da fita na estrutura do Pokémon dentro dos limites de rank configurados.
- `data/maps/LilycoveCity_Harbor/scripts.inc` inicia com uma transição que define escapewarp para a cidade. Os scripts próximos tratam ferry/tickets e têm condições de pós-jogo; esses scripts não são uma cena de chegada de barco para um jogo novo.
- O `Makefile` indica prefixo `arm-none-eabi-` e permite apontar para `DEVKITARM`; o `INSTALL.md` descreve a compilação usando `make`. Nenhuma compilação foi executada durante esta auditoria.
