# Catálogo de comandos que podem bloquear eventos

Base analisada: `rh-hideout/pokeemerald-expansion@f4dc700a130330fd2f9325a17bbb1e2d91dbf091`.

## Por que isto importa

Um evento pode compilar e ainda assim travar em tempo de execução se um comando aguardar algo que nunca termina ou se um script encerrar enquanto uma transição está ativa. Este catálogo destaca famílias que devem receber revisão especial antes de alterar cenas.

## Famílias a revisar

- Fluxo: `call`, `return`, `goto`, `end`, ramos condicionais e `switch`.
- Esperas: `waitstate`, `waitmovement`, `waitmovementall`, `waitse`, `waitfanfare`, `waitmessage`, `waitbuttonpress`, `waitdooranim`, `waitfieldeffect`.
- Warp/transição: `warp`, `warpsilent`, `warpdoor`, `warphole`, `warpteleport`, `setwarp`, `setdynamicwarp`, `setdivewarp`, `setholewarp`, `setescapewarp`, e comandos de fade/entrada.
- Movimento e visibilidade: `applymovement`, `waitmovement`, `addobject`, `removeobject`, `showobjectat`, `hideobjectat`, `showplayer`, `hideplayer`.
- Trava de controles: `lock`, `lockall`, `lockfortrainer`, `release`, `releaseall`.
- Efeitos indiretos: `special`, `specialvar`, `callnative`, `gotonative`.

## Esperas implícitas em special

A macro `special` consulta `SPECIAL_WAITSTATE_<nome>` na tabela gerada a partir de `data/specials.inc`. A tabela declara alguns specials com `waitstate=1`, por exemplo `DoCableClubWarp`, `ReturnFromLinkRoom`, `EnterNewlyCreatedSecretBase`, operações de link, `DoTrainerApproach`, `SaveGame` e `ShowPokemonStorageSystemPC`.

A macro acrescenta um `waitstate` automaticamente quando o special requer isso. Logo, não é seguro adicionar `waitstate` após todos os `special` por padrão; primeiro é necessário consultar a declaração do special. O comando/compilador ajuda a detectar alguns casos, mas a semântica precisa ser conferida.

## Revisão obrigatória ao modificar um script

1. Para cada comando de espera, registrar o evento que libera essa espera e garantir que existe em todos os ramos.
2. Para cada warp, garantir que o fluxo de script respeita a transição e as regras de `waitstate` documentadas no motor.
3. Para cada `lock`/ocultação, conferir que os ramos terminam com restauração/liberação coerente.
4. Para cada `applymovement`, verificar se o objeto existe, se o movimento termina em `step_end` e se a espera usa o identificador adequado.
5. Para cada `special`, conferir sua assinatura, efeitos colaterais, retorno e configuração de espera implícita.
6. Testar o caso normal e os ramos condicionais, incluindo save/load e retorno ao mapa.

## Exemplo que motivou a auditoria

A cena inicial do SS Tidal foi ligada a `LilycoveCity_Harbor_OnTransition`, um callback que originalmente apenas configurava escapewarp e encerrava. A cena acrescentou criação/posicionamento do objeto, `applymovement` e `waitmovement 0` durante a transição. O usuário confirmou que retirar a cena eliminou o congelamento na ROM de diagnóstico. Isso demonstra por que callbacks de mapa e scripts cinematográficos precisam ter responsabilidades separadas; não determina sozinho qual comando individual causava o bloqueio.
