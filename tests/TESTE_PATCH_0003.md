# Teste local do patch 0003

## Ambiente

- Fonte de referência: arquivo `src/new_game.c` extraído de `pokeemerald-expansion-master.zip`.
- Patch testado: `patches/0003-lilycove-female-prototype.patch`.
- Testes executados: `git apply --check`, aplicação do patch e `git diff --check`.

## Resultado

Os três comandos terminaram sem erro. O diff altera somente `src/new_game.c`:
1. troca o destino inicial de Emerald para `MAP_LILYCOVE_CITY_HARBOR`, nas coordenadas provisórias (11, 13);
2. define `gSaveBlock2Ptr->playerGender = FEMALE` durante a inicialização de novo jogo.

## O que isso prova — e o que não prova

Isso prova que o patch é sintaticamente aplicável ao arquivo de referência e que o diff não contém erros básicos de whitespace. Não prova que as coordenadas sejam transitáveis, que o script de transição funcione, que todos os eventos estejam no estado certo, que o projeto compile ou que o resultado seja compatível com Pokémon Quetzal Alpha 9.

## Próximos testes necessários

1. Revalidar o patch numa extração limpa completa.
2. Instalar/usar a toolchain ARM e executar a compilação do projeto de referência.
3. Corrigir erros de compilação, se houver.
4. Testar em emulador: nova partida, personagem feminina, chegada ao porto, movimento, entrada/saída do porto, salvar/recarregar e retorno após desmaio.
5. Só então empacotar uma ROM de protótipo, sem distribuir ROM original nem assets sem autorização.

**Status: teste de aplicação do diff aprovado; build e teste de jogo pendentes.**
