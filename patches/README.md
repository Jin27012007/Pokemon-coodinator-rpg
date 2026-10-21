# Patches experimentais

Esta pasta contém diffs revisáveis contra a cópia de referência de `pokeemerald-expansion`. Um protótipo compilado já foi gerado, mas ainda precisa de teste dentro de um emulador.

## 0001 — protagonista feminina

Arquivo: [0001-force-female-player.patch](0001-force-female-player.patch)

Propõe definir `gSaveBlock2Ptr->playerGender = FEMALE` durante a inicialização. A ROM foi compilada com essa alteração, mas ainda não foi testada em emulador para confirmar o visual da abertura, sprites, diálogos e eventos dependentes do gênero.

## 0002 — destino no porto

Arquivo: [0002-start-at-lilycove-harbor.patch](0002-start-at-lilycove-harbor.patch)

Propõe substituir o destino inicial de Emerald pelo mapa do porto de Lilycove, usando coordenadas provisórias. Não configura por si só todos os estados de eventos, retorno ou respawn.

## 0003 — patch consolidado

Arquivo: [0003-lilycove-female-prototype.patch](0003-lilycove-female-prototype.patch)

Reúne as duas alterações. O patch passou na etapa de aplicação do workflow e a ROM foi compilada com sucesso pelo GitHub Actions. O workflow também aplica uma correção estreita de compatibilidade para duas declarações após labels no arquivo `src/battle_gfx_sfx_util.c` da fonte de referência.

## Resultado do build

Workflow: [Build experimental — execução 39627288019](https://github.com/Jin27012007/Pokemon-coodinator-rpg/actions/runs/39627288019)

Artefato temporário: `lilycove-prototype-build`. O resultado compilado tem 32 MiB e cabeçalho GBA válido. SHA-256 do arquivo entregue localmente: `fbaba088cdc317cb914e09fbd8ad4b112e946d092a8d02c7a312f3ef8d115c5e`.

## Limites

A fonte usada é `rh-hideout/pokeemerald-expansion`, não uma fonte confirmada do Pokémon Quetzal Alpha 9. A compilação passou, mas a chegada, as coordenadas, o fluxo de introdução e o estado de retorno ainda não foram testados em emulador. Não enviar ROMs ao repositório.
