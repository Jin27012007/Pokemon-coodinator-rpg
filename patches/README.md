# Patches experimentais

Esta pasta contém diffs pequenos para revisar contra a cópia de referência de `pokeemerald-expansion`. Eles não são uma ROM pronta e ainda não foram compilados.

## Patch consolidado — início feminino em Lilycove

Arquivo: [0003-lilycove-female-prototype.patch](0003-lilycove-female-prototype.patch)

- Define o gênero salvo como feminino durante a inicialização de uma nova partida.
- Altera o destino inicial do Emerald de Inside of Truck para Lilycove City Harbor, coordenadas provisórias (11, 13).
- O diff gerado localmente passou em `git apply --check` contra `src/new_game.c` da cópia de referência.
- Isso não valida coordenadas, scripts de evento, sprite/diálogos, respawn ou funcionamento no emulador.

## Patches anteriores

Os arquivos `0001-force-female-player.patch` e `0002-start-at-lilycove-harbor.patch` são etapas anteriores separadas. Prefira testar o patch consolidado 0003 numa cópia limpa para evitar aplicar duas vezes a mesma alteração.

## Limites e próximo marco

A cópia de referência é `pokeemerald-expansion`, não uma fonte confirmada do Pokémon Quetzal Alpha 9. O ambiente atual não tem `arm-none-eabi-gcc`/DevkitARM disponível, então a compilação ainda não foi executada. Antes de gerar uma ROM jogável, precisamos de uma árvore compatível, toolchain ARM, build bem-sucedido e teste em emulador. Não enviar ROMs ao repositório.
