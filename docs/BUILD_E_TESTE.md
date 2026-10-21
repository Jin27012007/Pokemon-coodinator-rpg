# Build e teste do protótipo

## Fonte do jogo

Esta branch usa `rh-hideout/pokeemerald-expansion`, não o código de Quetzal. O workflow fixa a revisão `f4dc700a130330fd2f9325a17bbb1e2d91dbf091`.

## Executar a compilação

Acesse [Build female-default boat-arrival prototype](https://github.com/Jin27012007/Pokemon-coodinator-rpg/actions/workflows/build-boat-arrival.yml), abra a execução mais recente e baixe `female-default-boat-arrival-build`. O artefato expira após 7 dias.

## Histórico do congelamento

O teste manual identificou tela preta com silhueta branca ao confirmar o nome, antes do primeiro mapa. A primeira hipótese foi a sequência `ExecuteTruckSequence` continuar ativa após mudar o destino inicial para Lilycove. A substituição desse callback por `FieldCB_WarpExitFadeFromBlack` compilou, mas o usuário confirmou que o congelamento continuou no mesmo frame. Portanto, essa hipótese não explica sozinha o defeito e o problema ainda está aberto.

## Auditoria do evento do barco

O evento inicial foi colocado em `LilycoveCity_Harbor_OnTransition`. No código-base, esse callback já é chamado durante a transição do mapa e termina imediatamente depois de `setescapewarp`. O protótipo acrescentava nele a aparição do SS Tidal, a alteração da posição permanente, a liberação da flag de ocultação e uma sequência de movimento com `waitmovement 0`. Isso mistura a chegada cenográfica ao carregamento inicial do mapa. Como o congelamento acontece antes de o mapa ficar utilizável e começou quando essa animação foi introduzida, esse acoplamento é uma hipótese concreta a isolar. Ainda não há evidência suficiente para afirmar que `waitmovement` é definitivamente a causa.

A nova revisão remove a animação e todas as alterações ao evento do porto do patch. O início no porto e o callback genérico continuam como teste mínimo, para separar o carregamento do mapa da animação do barco. Só depois de o início passar sem congelar deve-se recolocar a chegada como evento acionado depois de o mapa estar estável, de preferência num evento controlado por uma flag de progresso e sem bloquear o callback de transição.

## Teste manual obrigatório

Use um jogo novo:
- [ ] A introdução termina após confirmar o nome.
- [ ] O jogo entra no porto de Lilycove com controles funcionais.
- [ ] Só depois desse teste será recolocada a animação do SS Tidal.
- [ ] Na versão com chegada, o barco aparece e se move sem travar o mapa.
- [ ] A chegada não se repete ao carregar um save.
- [ ] A viagem normal do SS Tidal continua funcionando.

Uma compilação verde confirma apenas que o código compila, não que o fluxo funciona em emulador. Não enviar ROMs ao GitHub; ROMs são apenas artefatos temporários de teste.
