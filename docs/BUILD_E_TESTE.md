# Build e teste do protótipo

## Fonte do jogo

Esta branch usa `rh-hideout/pokeemerald-expansion`, e não o código-fonte de Pokémon Quetzal Alpha 9. O workflow fixa a revisão `f4dc700a130330fd2f9325a17bbb1e2d91dbf091` e confere esse SHA antes de aplicar os patches. Alterar essa revisão deve ser uma decisão explícita.

## Executar a compilação

Acesse [Build female-default boat-arrival prototype](https://github.com/Jin27012007/Pokemon-coodinator-rpg/actions/workflows/build-boat-arrival.yml), abra uma execução e consulte o artefato `female-default-boat-arrival-build). O artefato é temporário e expira após 7 dias.

A compilação de validação atual terminou com sucesso na execução [#39633590306](https://github.com/Jin27012007/Pokemon-coodinator-rpg/actions/runs/39633590306). A ROM foi extraída do artefato; seu tamanho é 32 MiB e o checksum do cabeçalho GBA confere. Isso comprova que o build produziu uma imagem GBA estruturalmente consistente, mas não substitui o teste visual no emulador.

## Teste manual obrigatório

Antes de considerar este protótipo validado, testar num emulador e anotar a versão usada:
- [ ] May aparece na apresentação inicial.
- [ ] Feminino começa selecionado, mas o masculino continua selecionável.
- [ ] Um jogo novo inicia no porto de Lilycove.
- [ ] O barco se desloca e termina o evento sem bloquear o movimento.
- [ ] É possível caminhar no porto, entrar em mapas ligados e retornar.
- [ ] Save/load funciona depois de concluir a chegada.
- [ ] A chegada inicial não se repete ao carregar o save.
- [ ] A viagem normal do S.S. Tidal continua funcionando no progresso comum.

A animação implementada por enquanto é uma aproximação curta do barco ao cais no mapa, não uma cena cinematográfica em mar aberto. Caso o movimento fique artificial ou cause problema de colisão, ajustar o ponto inicial, a direção e o caminho usando o mapa real no emulador.

Não enviar arquivos ROM ao GitHub. A ROM é apenas um artefato temporário de teste.
