# Patches experimentais

Esta pasta contém diffs para revisão contra a cópia de referência de `pokeemerald-expansion`. Nenhum deles é uma ROM pronta.

## 0001 — protagonista feminina

Arquivo: [0001-force-female-player.patch](0001-force-female-player.patch)

Propõe definir `gSaveBlock2Ptr->playerGender = FEMALE` durante a inicialização. Ainda exige compilação e testes da abertura, sprites, diálogos e eventos.

## 0002 — destino no porto

Arquivo: [0002-start-at-lilycove-harbor.patch](0002-start-at-lilycove-harbor.patch)

Propõe substituir o destino inicial de Emerald pelo mapa do porto de Lilycove, usando coordenadas provisórias. Não configura por si só o estado de eventos, retorno ou respawn.

## 0003 — patch consolidado

Arquivo: [0003-lilycove-female-prototype.patch](0003-lilycove-female-prototype.patch)

Reúne as duas mudanças anteriores. Foi corrigido depois de uma revisão detectar que a versão anterior tinha cabeçalhos de hunk inválidos. A versão atual passou localmente em `git apply --check` contra `src/new_game.c` da cópia de referência.

Esse teste prova somente que o diff é aplicável ao arquivo. Não prova compilação nem funcionamento no emulador.

## Bloqueios e próximos testes

A toolchain `arm-none-eabi-gcc` não está instalada no ambiente de trabalho, então a compilação completa ainda não foi executada. Antes de gerar uma ROM, precisamos preparar a toolchain, compilar, corrigir erros, validar as coordenadas do porto e revisar flags/eventos de início, respawn e retorno.

A fonte de referência é `pokeemerald-expansion`, não uma fonte confirmada do Quetzal Alpha 9. Compatibilidade com a ROM Quetzal não está demonstrada. Não enviar ROMs ao repositório.
