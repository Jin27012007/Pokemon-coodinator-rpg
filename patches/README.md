# Patches experimentais

Esta pasta contém patches pequenos para revisar contra a cópia de referência de `pokeemerald-expansion`. Eles não são uma ROM pronta e ainda não foram compilados.

## 0001 — protagonista feminina

Arquivo: [0001-force-female-player.patch](0001-force-female-player.patch)

- Propõe definir `gSaveBlock2Ptr->playerGender = FEMALE` durante a inicialização de uma nova partida.
- O patch ainda precisa de validação de contexto numa árvore de trabalho limpa antes de ser considerado pronto para aplicação.
- Não verificado: compilação, emulador, sprite/arte da protagonista, diálogos e eventos que dependem do gênero.

## 0002 — destino inicial no porto de Lilycove

Arquivo: [0002-start-at-lilycove-harbor.patch](0002-start-at-lilycove-harbor.patch)

- Propõe substituir o destino inicial de Emerald pelo mapa do porto de Lilycove, usando coordenadas provisórias.
- Verificação realizada localmente: `git apply --check` passou contra `src/new_game.c` extraído da cópia de referência.
- Isso só valida que o diff se aplica ao arquivo de referência. Não valida coordenadas em jogo, respawn, flags/eventos, compilação ou compatibilidade com Quetzal Alpha 9.
- Para uma chegada completa, ainda é necessário configurar respawn/escape warp e eventos iniciais sem depender do script do caminhão de Littleroot.

## Limites atuais

A cópia de referência é `pokeemerald-expansion`, não uma fonte confirmada do Pokémon Quetzal Alpha 9. Portanto, os patches são experimentais e precisam ser adaptados e testados numa árvore de código compatível antes de gerar uma ROM jogável. Não enviar ROMs ao repositório.
