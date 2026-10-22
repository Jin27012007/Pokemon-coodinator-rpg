# Playbook de scripts de evento — referência pokeemerald-expansion

Este documento descreve os comandos e padrões confirmados na revisão upstream fixada pelo workflow: `rh-hideout/pokeemerald-expansion`, commit `f4dc700a130330fd2f9325a17bbb1e2d91dbf091`.

## Arquivo e ponto de entrada do porto

Fonte: [data/maps/LilycoveCity_Harbor/scripts.inc](https://github.com/rh-hideout/pokeemerald-expansion/blob/f4dc700a130330fd2f9325a17bbb1e2d91dbf091/data/maps/LilycoveCity_Harbor/scripts.inc)

A estrutura existente no início do arquivo é:

```asm
LilycoveCity_Harbor_MapScripts::
    map_script MAP_SCRIPT_ON_TRANSITION, LilycoveCity_Harbor_OnTransition
    .byte 0

LilycoveCity_Harbor_OnTransition:
    setescapewarp MAP_LILYCOVE_CITY, 12, 33
    end
```

Interpretação: `MAP_SCRIPT_ON_TRANSITION` chama o script durante a transição para o mapa. O script atualmente configura o escapewarp e termina. O ferries/tickets são scripts de interação separados mais abaixo no mesmo arquivo. A cena do início não deve alterar nem substituir esses scripts do ferry.

## O que a tentativa de animação acrescentou

O commit [37d90bc](https://github.com/Jin27012007/Pokemon-coodinator-rpg/commit/37d90bc06ef23b921db0e68b682ca349bd13be04) introduziu no patch do porto a seguinte sequência:

- conferir `FLAG_HIDE_LILYCOVE_HARBOR_SSTIDAL`;
- limpar a flag de ocultação;
- definir a posição permanente do objeto SS Tidal;
- adicionar o objeto ao mapa;
- executar `applymovement` no barco;
- aguardar com `waitmovement 0`.

O movimento adicionava sete passos para a esquerda e `step_end`. O callback de transição, portanto, passou a executar uma cena e a esperar o movimento durante o carregamento. O commit [7338547](https://github.com/Jin27012007/Pokemon-coodinator-rpg/commit/7338547862f68dc955846b14c3c724d06c3e896f) removeu precisamente esse bloco, e o usuário relatou que a ROM resultante funciona em Lilycove. Isto confirma uma correlação reproduzível entre a remoção do bloco e a resolução do congelamento, mas não identifica isoladamente se o causador era a espera, a flag, a posição/objeto ou o momento de execução.

## Procedimento recomendado para editar eventos

1. **Não editar no escuro.** Abrir `scripts.inc`, `events.inc` e `map.json` do mesmo commit upstream fixado; conferir os nomes reais dos objetos e suas posições.
2. **Preservar a assinatura do mapa.** Não renomear ou remover labels existentes sem verificar suas referências em `map.json`, outros scripts e includes.
3. **Manter responsabilidades separadas.** `OnTransition` deve fazer configuração curta de mapa/estado. Cenas com vários movimentos, diálogo ou espera devem ser disparadas por um gatilho/flag depois de o mapa estar pronto, ou por outro fluxo explicitamente controlado.
4. **Fazer evento idempotente.** Usar uma flag persistente dedicada à conclusão/execução, e definir claramente quando ela é setada. Reentrar no mapa e carregar um save não deve repetir a cena, a menos que seja intencional.
5. **Garantir todos os caminhos de saída.** Todo ramo precisa terminar ou retornar corretamente, liberar controles quando houver `lock`, evitar waits sem movimento válido e não deixar o jogador invisível/travado em caso de estado inesperado.
6. **Alterar uma coisa por vez.** Um diff curto por tentativa. Confirmar `git apply --check`, compilação, artefato com tamanho plausível e teste manual.
7. **Testes mínimos de regressão.** Jogo novo; movimentos após entrada; sair e voltar ao mapa; save/load; repetição ou não da cena; ferry normal de Lilycove.

## Criação, alteração e remoção

- **Criar:** adicionar uma label única, definir como ela é alcançada, e confirmar que o script não ficou órfão.
- **Alterar:** examinar todas as chamadas para a label/flag/object local ID antes de mudar a lógica.
- **Remover:** procurar referências ao script, movimento, flag, variável, object local ID e constantes associadas. Remover só o corpo pode deixar referências inválidas ou recursos ocultos permanentemente.
- **Não reutilizar flags/vars por conveniência:** primeiro verificar se já estão usadas noutros mapas/fluxos e qual o ciclo de vida. Preferir uma flag nova devidamente declarada quando o estado persistente novo for necessário.

## Limites

Este playbook é uma primeira referência operacional baseada no arquivo do porto e no histórico do patch. Não é uma afirmação de que todos os comandos da engine já foram catalogados. Antes de reconstruir a animação, é necessário examinar os arquivos de objetos/posições do mapa e identificar a melhor forma de disparar a cena após a entrada estar estável.
