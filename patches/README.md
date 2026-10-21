# Patches experimentais

Esta pasta contém diffs pequenos para revisar contra a cópia de referência de `pokeemerald-expansion`. Eles não são uma ROM pronta e ainda não foram compilados.

## 0001 — protagonista feminina

Arquivo: [0001-force-female-player.patch](0001-force-female-player.patch)

- Propõe definir `gSaveBlock2Ptr->playerGender = FEMALE` durante a inicialização de uma nova partida.
- `git apply --check` passou localmente contra o `src/new_game.c` da cópia de referência.
- Ainda não foi compilado nem testado em emulador. Sprite da abertura, diálogos e eventos que dependem do gênero precisam de revisão.

## 0002 — destino inicial no porto de Lilycove

Arquivo: [0002-start-at-lilycove-harbor.patch](0002-start-at-lilycove-harbor.patch)

- Propõe substituir o destino inicial de Emerald pelo mapa do porto de Lilycove, usando coordenadas provisórias.
- O patch foi corrigido e `git apply --check` passou localmente contra o `src/new_game.c` de referência.
- Isso só confirma que o diff se aplica ao arquivo, não que as coordenadas sejam válidas em jogo ou que os eventos estejam configurados corretamente.
- A chegada ainda depende de uma revisão de respawn/escape warp e dos scripts iniciais do caminhão de Littleroot.

## Próxima etapa

Criar um fluxo de início próprio para o RPG de Coordenadora e revisar as dependências de eventos, gênero e retorno antes de tentar compilar.

## Limites atuais

A cópia de referência é `pokeemerald-expansion`, não uma fonte confirmada do Pokémon Quetzal Alpha 9. Os patches são experimentais e precisam ser adaptados e testados numa árvore compatível antes de gerar uma ROM jogável. Não enviar ROMs ao repositório.
