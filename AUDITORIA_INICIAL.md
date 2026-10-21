# Auditoria inicial — Pokémon Coordinator RPG

## Arquivos recebidos

- `pokeemerald-expansion-master.zip`: código-fonte de `pokeemerald-expansion`.
- `Pokémon Quetzal Creditos.txt`: créditos fornecidos com o Quetzal.
- `PokemonQuetzalPtBrAlpha9v0.gba`: ROM Quetzal Alpha 9 em português.
- `Pokemon - Emerald Version (USA, Europe) (1).zip`: arquivo do Pokémon Emerald original.

**Importante:** ROMs comerciais e arquivos protegidos não serão enviados ao GitHub. Este repositório deve guardar nosso código-fonte próprio, documentação e alterações permitidas.

## O que os créditos confirmam

O arquivo de créditos informa que o jogo Quetzal usa como jogo base `pret/pokeemerald` e menciona `rh-hideout/pokeemerald-expansion` como origem do motor de batalha, expansão de Pokémon e itens. Os créditos também alertam que muitos sprites não são de uso público e não devem ser reutilizados sem autorização.

## O que foi encontrado no código-fonte fornecido

A cópia de `pokeemerald-expansion` contém:

- `src/new_game.c`, com a função `WarpToTruck()` relacionada ao início de um jogo novo.
- `data/maps/InsideOfTruck/scripts.inc`, com scripts de introdução e destinos para Littleroot Town.
- `data/maps/LilycoveCity_Harbor/scripts.inc` e `map.json`, com o mapa do porto de Lilycove e seus eventos de ferry.

Isso indica pontos úteis para investigar a mudança do início da aventura, mas **não prova que este código seja exatamente o código-fonte do Quetzal Alpha 9**. Não devemos aplicar alterações diretamente sem comparar a versão.

## Plano seguro

1. Identificar e confirmar a versão exata da base Quetzal que será modificada.
2. Preparar uma cópia de trabalho do código-fonte em um ambiente que consiga compilar o projeto.
3. Fazer uma única alteração inicial: começar em Lilycove e chegar ao porto por um evento coerente.
4. Compilar e testar antes de mexer nos concursos.
5. Depois, estudar como transformar fitas em progressão da carreira de Coordenadora sem remover insígnias ou sistemas antes de entender suas dependências.

## Estado atual

- [x] Arquivos recebidos e inventariados.
- [x] Pontos iniciais relevantes localizados na base de referência.
- [ ] Base Quetzal Alpha 9 comparada com o código-fonte disponível.
- [ ] Ambiente de compilação preparado.
- [ ] Primeiro início jogável em Lilycove implementado e testado.
- [ ] Progressão por fitas projetada e implementada.

Nenhuma modificação jogável foi aplicada ainda.