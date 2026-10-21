# Patches experimentais

Esta pasta contém patches pequenos para revisar contra a cópia de referência de `pokeemerald-expansion`. Eles não são uma ROM pronta e ainda não foram compilados.

## 0001 — protagonista feminina

Arquivo: [0001-force-female-player.patch](0001-force-female-player.patch)

- Define `gSaveBlock2Ptr->playerGender = FEMALE` durante a inicialização de uma nova partida.
- A revisão anterior foi feita sobre o trecho de inicialização, mas ainda é necessário validar o contexto exato numa árvore de trabalho limpa antes de aplicar o patch final.
- Não verificado: compilação, emulador, sprite/arte da protagonista, diálogos e eventos que dependem do gênero.

## 0002 — destino inicial no porto de Lilycove

Arquivo: [0002-start-at-lilycove-harbor.patch](0002-start-at-lilycove-harbor.patch)

- Propõe substituir o destino do início de Emerald pelo mapa do porto de Lilycove, em coordenadas experimentais.
- É apenas uma primeira hipótese de destino. As coordenadas precisam ser testadas no mapa e podem exigir ajuste.
- Não é seguro considerar a chegada completa ainda: é preciso definir respawn/escape warp, revisar o gênero salvo e configurar os eventos iniciais sem depender do script do caminhão de Littleroot.

## Limites atuais

A cópia de referência é `pokeemerald-expansion`, não uma fonte confirmada do Pokémon Quetzal Alpha 9. Portanto, os patches são experimentais e precisam ser adaptados e testados numa árvore de código compatível antes de gerar uma ROM jogável. Não enviar ROMs ao repositório.
