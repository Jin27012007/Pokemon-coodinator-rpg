# Relatório da tentativa de animação do SS Tidal — 22/10/2026

Base: `rh-hideout/pokeemerald-expansion@f4dc700a130330fd2f9325a17bbb1e2d91dbf091`

## Baseline comprovada
O usuário testou a ROM sem animação e confirmou que o jogo novo chegou a Lilycove e a cidade ficou jogável. Essa continua sendo a única ROM com teste manual positivo nesta investigação.

## Análise direta da engine
- O barco já existe em `data/maps/LilycoveCity_Harbor/map.json` com `LOCALID_LILYCOVE_HARBOR_SS_TIDAL`, coordenadas (8,9), gráfico `OBJ_EVENT_GFX_SS_TIDAL` e flag `FLAG_HIDE_LILYCOVE_HARBOR_SSTIDAL`.
- O início de Emerald define essa flag como oculta em `EventScript_ResetAllMapFlags`. O fluxo personalizado deve apresentar o barco intencionalmente durante a primeira entrada.
- O callback original `LilycoveCity_Harbor_OnTransition` só define o escapewarp. A tentativa anterior colocou um movimento de sete passos e `waitmovement 0` dentro do callback de transição imediato e congelou.
- `src/script.c`: `RunScriptImmediately` executa até o script terminar. Já `TryRunOnFrameMapScript` consulta a tabela `MAP_SCRIPT_ON_FRAME_TABLE`, configura o contexto global e permite a execução em quadros. `MAP_SCRIPT_ON_FRAME_TABLE` deve ser declarado no cabeçalho do mapa explicitamente.
- Os macros confirmam que `addobject` não altera a flag de ocultação; `removeobject` altera a flag se existir. Os estados de visibilidade precisam ser consistentes com o ciclo normal do ferry.
- Não reutilizar `VAR_TEMP_D/E/F` indiscriminadamente: outros sistemas, como Battle Pyramid/Frontier, reutilizam esses slots.

## Patch experimental 0005
Foi criado `patches/0005-boat-arrival-frame-experiment.patch` e um workflow separado `.github/workflows/build-boat-experiment.yml`. A cena de movimento é disparada por uma nova entrada `MAP_SCRIPT_ON_FRAME_TABLE`, depois da transição, e não foi adicionada a `patches/ACTIVE_PATCHES.txt`. Assim, a build normal e a baseline funcional permanecem sem a cena.

O patch usa `VAR_TEMP_0` como sinal temporário apenas para sequenciar a primeira chegada. Isso evita a colisão óbvia com `VAR_TEMP_D/E/F`, mas ainda requer revisão/teste: a variável temporária é global no save e a cena deve ser avaliada em reentrada e save/load. A movimentação também depende da posição e do movimento real do objeto no mapa.

## Validação de build
A execução experimental #39765320045 está disponível em:
https://github.com/Jin27012007/Pokemon-coodinator-rpg/actions/runs/39765320045

Na última consulta de status o job ainda estava instalando a toolchain; nenhum artefato da cena animada estava disponível naquele momento. Não declarar que a ROM animada está pronta até a execução terminar, o artefato aparecer e o teste manual passar.

A execução anterior #39764067065 compilou com sucesso a baseline sem a animação e publicou:
- `event-script-validation-build` (37.016.394 bytes), válido para regressão de build, mas **sem a cena animada**.
- `event-script-audit-report`.

## Próximos passos
1. Confirmar status/resultado da execução #39765320045 e corrigir qualquer falha de aplicação/build.
2. Inspecionar o patch aplicado, garantir que a entrada de tabela não sobrescreve outra definição.
3. Baixar artefato apenas se houver conclusão de sucesso.
4. Testar ROM nova no emulador; observar congelamento, sete passos completos, liberdade de movimento, reentrada no porto, save/load e ferry normal.
5. Só depois dos testes decidir se o patch 0005 pode substituir a cena desativada no patch 0004.
