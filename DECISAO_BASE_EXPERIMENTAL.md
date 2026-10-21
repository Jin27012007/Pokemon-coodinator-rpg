# Decisão de base experimental

## Decisão

Como não foi encontrada uma fonte confirmada do Pokémon Quetzal Alpha 9, o projeto seguirá provisoriamente usando a cópia de `pokeemerald-expansion` enviada pelo usuário. Isso é um experimento de base nova, **não uma garantia de compatibilidade com a ROM Quetzal Alpha 9**.

Branch de trabalho: `experimental/pokeemerald-reference`

## Regras de trabalho

1. Manter `main` como documentação e referência estável.
2. Fazer experimentos nesta branch.
3. Uma alteração por vez, com diff pequeno e explicado.
4. Não afirmar que algo funciona até compilar e testar uma ROM.
5. Não subir a ROM comercial nem assets cuja licença/permite não esteja confirmada.
6. Não confundir um patch de código-fonte com uma ROM pronta.

## Primeiro experimento planejado

Objetivo: substituir o destino inicial do caminhão por uma entrada controlada no porto de Lilycove, com a protagonista feminina e um ponto de retorno/respawn coerente.

Arquivos principais da base de referência:
- `src/new_game.c`: função `WarpToTruck()`, chamada no fluxo de inicialização do jogo novo.
- `data/maps/InsideOfTruck/scripts.inc`: configurações de introdução, flags e respawn específicas de Brendan/May em Littleroot.
- `src/intro.c`: cena introdutória e variável temporária de gênero visual.
- `data/maps/LilycoveCity_Harbor/map.json`: coordenadas e objetos do porto.
- `data/maps/LilycoveCity_Harbor/scripts.inc`: scripts de ferry e transição existentes.

## Decisões ainda necessárias no código

Não basta alterar uma única coordenada. Antes de fechar o patch inicial, precisamos definir:
- onde fixar o gênero persistente como feminino, sem confundir isso com o gênero visual temporário da cena de abertura;
- quais flags/variáveis de Littleroot deixam de ser necessárias e quais outras rotinas ainda dependem delas;
- qual ponto do porto é realmente caminhável e como o mapa inicial posiciona o jogador;
- como definir respawn em Lilycove para que desmaios e carregamentos não devolvam a protagonista a Littleroot;
- como garantir que a cena de chegada só execute uma vez e não interfira no ferry normal.

## Estado

- [x] Branch experimental criada.
- [x] Arquivos de referência e pontos de entrada identificados.
- [ ] Patch inicial preparado e revisado.
- [ ] Compilação executada.
- [ ] Teste em emulador: novo jogo, movimentação no porto, save/load e respawn.
- [ ] Só depois: desenho do sistema de carreira e fitas.
