# Patches experimentais

Esta pasta contém patches pequenos para revisar contra a cópia de referência de `pokeemerald-expansion`. Eles não são uma ROM pronta e ainda não foram compilados.

## 0001 — protagonista feminina

Arquivo: [0001-force-female-player.patch](0001-force-female-player.patch)

- Define `gSaveBlock2Ptr->playerGender = FEMALE` durante a inicialização de uma nova partida.
- Verificação realizada: `git apply --check` passou contra `src/new_game.c` extraído da cópia de referência.
- Não verificado: compilação, funcionamento no emulador, sprite/arte da protagonista na abertura, diálogos e eventos que dependem do gênero.

## Próxima etapa — chegada ao porto de Lilycove

Não alterar somente o destino de `WarpToTruck()` às cegas. A chegada precisa configurar o respawn/escape warp e o estado inicial dos eventos; o script atual do caminhão também define flags, variáveis e um dynamic warp para Littleroot. O próximo patch deve criar um início específico para o RPG de Coordenadora e revisar os scripts de transição do porto.

## Limites atuais

A cópia de referência é `pokeemerald-expansion`, não uma fonte confirmada do Pokémon Quetzal Alpha 9. Portanto, os patches são experimentais e precisam ser adaptados e testados numa árvore de código compatível antes de gerar uma ROM jogável. Não enviar ROMs ao repositório.
