# Build e teste do protótipo

## Fonte do jogo

Esta branch usa `rh-hideout/pokeemerald-expansion`, não o código de Quetzal. O workflow fixa a revisão `f4dc700a130330fd2f9325a17bbb1e2d91dbf091`.

## Executar a compilação

Acesse [Build female-default boat-arrival prototype](https://github.com/Jin27012007/Pokemon-coodinator-rpg/actions/workflows/build-boat-arrival.yml), abra a execução mais recente e baixe `female-default-boat-arrival-build`. O artefato expira após 7 dias.

## Diagnóstico técnico do congelamento

O teste manual confirmou que o início em Lilycove funciona após remover a animação. A hipótese inicial de que `ExecuteTruckSequence` era a única causa foi descartada: substituir esse callback por `FieldCB_WarpExitFadeFromBlack` não resolveu o travamento.

A leitura do código da revisão-base agora aponta para uma causa específica e consistente com o sintoma: **a animação chamava `waitmovement 0` dentro de `LilycoveCity_Harbor_OnTransition`, um script executado sincronicamente durante a transição do mapa.**

A cadeia no código é:
1. `src/overworld.c` chama `RunOnTransitionMapScript()` durante a preparação do mapa.
2. `src/script.c` encaminha isso para `MapHeaderRunScriptType()`, que usa `RunScriptImmediately()`.
3. `RunScriptImmediately()` executa um laço apertado até o script acabar; ele não devolve o controle normal ao ciclo de quadros do jogo.
4. Em `src/scrcmd.c`, `ScrCmd_waitmovement()` muda o contexto para um script nativo `WaitForMovementFinish`, que continua retornando “ainda não terminou” até o motor de movimento atualizar o objeto.
5. Como esse wait ocorre dentro do laço síncrono de transição, o movimento não recebe os quadros normais necessários para terminar. O script fica preso antes de o mapa tornar-se jogável.

Referências diretas da revisão fixada:
- [Chamadas de transição e resume em overworld.c](https://github.com/rh-hideout/pokeemerald-expansion/blob/f4dc700a130330fd2f9325a17bbb1e2d91dbf091/src/overworld.c#L901-L913)
- [Laço síncrono RunScriptImmediately em script.c](https://github.com/rh-hideout/pokeemerald-expansion/blob/f4dc700a130330fd2f9325a17bbb1e2d91dbf091/src/script.c#L359-L366)
- [MapHeaderRunScriptType e gatilhos de mapa em script.c](https://github.com/rh-hideout/pokeemerald-expansion/blob/f4dc700a130330fd2f9325a17bbb1e2d91dbf091/src/script.c#L389-L394)
- [ScrCmd_waitmovement em scrcmd.c](https://github.com/rh-hideout/pokeemerald-expansion/blob/f4dc700a130330fd2f9325a17bbb1e2d91dbf091/src/scrcmd.c#L1334-L1346)
- [Script de chegada introduzido pelo patch histórico](https://github.com/Jin27012007/Pokemon-coodinator-rpg/commit/37d90bc06ef23b921db0e68b682ca349bd13be04)

A remoção da animação e o teste bem-sucedido corroboram esse diagnóstico. O mecanismo de bloqueio é sustentado pelo código; ainda assim, uma recompilação experimental que coloque a cena em um contexto assíncrono, seguida de teste manual, será a validação final da correção.

A próxima implementação não deve recolocar movimento com espera em `ON_TRANSITION`. A chegada deve ser disparada depois que o mapa estiver pronto — por exemplo, por um gatilho controlado após a entrada e condicionado por uma flag persistente — de forma que o motor de quadros continue processando os movimentos.

## Teste manual obrigatório

Use um jogo novo:
- [ ] A introdução termina após confirmar o nome.
- [ ] O jogo entra no porto de Lilycove com controles funcionais.
- [ ] Só depois desse teste será recolocada a animação do SS Tidal.
- [ ] Na versão com chegada, o barco aparece e se move sem travar o mapa.
- [ ] A chegada não se repete ao carregar um save.
- [ ] A viagem normal do SS Tidal continua funcionando.

Uma compilação verde confirma apenas que o código compila, não que o fluxo funciona em emulador. Não enviar ROMs ao GitHub; ROMs são apenas artefatos temporários de teste.
