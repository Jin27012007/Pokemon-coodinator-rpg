# Auditoria ampliada de todos os eventos scriptados

**Projeto:** Pokemon-coodinator-rpg  
**Branch:** `experimental/pokeemerald-reference`  
**Revisão-base fixada pelo build:** `rh-hideout/pokeemerald-expansion@f4dc700a130330fd2f9325a17bbb1e2d91dbf091`  
**Estado:** inventário estrutural consultado; auditoria semântica de todos os eventos ainda em andamento.

## Escopo quantificado

A árvore Git da revisão upstream contém 34.155 entradas e não está truncada. A busca estrutural encontrou:

- 887 arquivos de scripts de mapa em `data/maps/*/scripts.inc`;
- 939 arquivos `data/maps/*/map.json`;
- 86 scripts compartilhados em `data/scripts/*.inc`;
- um agregador global `data/event_scripts.s`, que inclui os scripts dos mapas;
- definição de comandos em `asm/macros/event.inc` e `data/script_cmd_table.inc`;
- motor de execução em `src/script.c`;
- tipos de gatilho documentados em `include/constants/map_scripts.h`;
- IDs/flags/variáveis declarados em cabeçalhos de `include/constants/`.

A contagem é um inventário de arquivos, não 100% de análise semântica. O build experimental aplica a pilha canônica listada em `patches/ACTIVE_PATCHES.txt` antes de executar o scanner e compilar, para que os scripts alterados pelo projeto também entrem na análise. A engine também contém scripts nativos em C, scripts de batalha e macros/recursos gerados que não podem ser validados apenas procurando labels em arquivos `.inc`.

## Ordem de execução dos gatilhos de mapa

A revisão de `include/constants/map_scripts.h` documenta categorias diferentes:

- `ON_DIVE_WARP`: lógica especial de saída/entrada de mergulho;
- `ON_TRANSITION`: durante a transição, para definir flags/variáveis e estado de objetos;
- `ON_LOAD`: após carregar layout, antes de desenhar;
- `ON_WARP_INTO_MAP_TABLE`: após carregar objetos, frequentemente para ajustar objetos ou jogador;
- `ON_RESUME`: ao terminar o carregamento e também ao retornar ao campo, por exemplo após menus/batalhas;
- `ON_FRAME_TABLE`: a cada quadro depois do fade-in e antes de processar entrada; executa o primeiro script cuja condição é satisfeita;
- `ON_RETURN_TO_FIELD`: caminho específico ao retorno ao campo.

No motor `src/script.c`, os scripts de `ON_LOAD`, `ON_TRANSITION`, `ON_RESUME`, `ON_RETURN_TO_FIELD` e `ON_DIVE_WARP` passam por `RunScriptImmediately`, que executa o bytecode num contexto imediato até ele parar/terminar. Já as tabelas `ON_FRAME_TABLE` e `ON_WARP_INTO_MAP_TABLE` são consultadas por `MapHeaderCheckScriptTable`; a tabela de frame ativa o contexto global e a tabela de warp executa o script retornado no contexto imediato. Isso explica por que uma sequência com movimento e espera pode se comportar diferente conforme o tipo de gatilho e o momento do carregamento.

Esses momentos **não são intercambiáveis**. A animação de Lilycove foi colocada em `ON_TRANSITION`, que ocorre durante a transição, e passou a fazer alterações ao barco, iniciar movimento e aguardar. Como o usuário confirmou que a ROM funciona depois da remoção desse bloco, devemos manter essa separação de responsabilidades em qualquer reconstrução.

## Motor de scripts: riscos relevantes

Em `src/script.c`, o motor separa execução de bytecode, scripts nativos e estados parado/em execução/aguardando. `StopScript` tem uma asserção para evitar sair de um script enquanto há um warp em andamento sem `waitstate`; chamadas, retornos e saltos dependem de ponteiros/stack válidos. Os comandos são despachados pelo índice de `gScriptCmdTable`.

Na revisão fixada, `asm/macros/event.inc` define 401 macros. Entre as operações relevantes para segurança de eventos estão `call`, `goto`, os ramos condicionais, `setvar`/`copyvar`, `special`, `waitstate`, `warp`, `applymovement`, `waitmovement`, `lock`/`release`, `hideplayer`/`showplayer`, `hideobjectat`/`showobjectat`, `addobject`/`removeobject` e comandos de porta/fade. A lista completa deve ser catalogada por semântica, não só por nome: alguns `special` já geram `waitstate` implicitamente, conforme a tabela de especiais, e adicionar um `waitstate` explícito logo depois pode ser redundante ou ignorado.

Macros em `asm/macros/event.inc` definem operações como `call`, `goto`, `goto_if`, `setvar`, `copyvar`, `special` e `waitstate`. A macro de `setvar` inclusive emite alerta quando o segundo argumento parece ser um identificador de variável; o caso comum correto é `copyvar`. Isso mostra que comandos parecidos têm semânticas diferentes e precisam ser conferidos, não apenas copiados.

## O que precisa ser verificado em cada script antes de editar

1. Label e referências: toda chamada, salto, callback de mapa e referência de objeto precisam resolver para um alvo válido.
2. Encerramento e pilha: confirmar `end`, `return`, `goto` e `call` corretos em cada caminho; evitar recursão ou saltos sem saída.
3. Esperas: todo `waitmovement`, `waitstate`, `waitse`, `waitfanfare` ou equivalente deve ter um produtor/condição que possa efetivamente terminar.
4. Controle do jogador: todo caminho que bloqueia controles/usa `lock`, oculta jogador ou objeto deve liberar/restaurar o estado, inclusive caminhos alternativos.
5. Estado persistente: mapear flags/vars e garantir que a cena possa ou não se repetir intencionalmente após entrada, retorno, save/load e reinício.
6. Objetos: cada `LOCALID`, gráfico, flag de ocultação, coordenada/elevation e movimento precisa corresponder a um objeto existente.
7. Transições: validar destino de warp, escapewarp, respawn e flags esperadas pela introdução.
8. Alterações e remoções: procurar referências no conjunto de scripts, JSON, cabeçalhos, tabelas geradas e código C antes de renomear/remover labels, flags, vars, movimento ou objetos.
9. Build: compilar com a mesma revisão-base fixada e preservar o diff. Build verde não substitui teste dentro do emulador.
10. Teste de regressão: mapa local, transições vizinhas, save/load, retorno de batalha/menu, jogo novo e fluxo normal de ferry.

## Scanner estático adicionado

Foi incluído `tools/audit_event_script_refs.py`. O workflow aplica primeiro a pilha de patches ativa e roda o scanner nessa árvore. Ele cobre scripts de mapa, scripts compartilhados, labels no agregador global e referências declaradas em `map.json`; confere labels/chamadas, flags/vars (incluindo cabeçalhos de configuração), movimentos, specials, referências de scripts de eventos, conexões/warps e IDs locais/IDs de mapa. O analisador do grafo de gatilhos síncronos também percorre chamadas alcançáveis e identifica esperas que dependem de quadros, operações de contexto, warps/natives e macros de evento que se expandem para essas famílias de comandos. O comando `callstd` (usado por macros como mensagens) é classificado para revisão de contexto.

**Limitação explícita:** esse scanner é heurístico, não um parser completo da linguagem de eventos. Pode emitir falsos positivos por ramos condicionais, constantes geradas, includes compartilhados, macros complexas e scripts nativos em C. Não edita nem apaga eventos automaticamente. Alertas não bloqueiam a compilação por si só, mas falhas do próprio scanner interrompem o job para evitar relatórios vazios apresentados como sucesso.

## Estado da auditoria

- [x] Revisão upstream identificada e fixada no workflow.
- [x] Inventário estrutural dos diretórios de eventos contado.
- [x] Arquivos centrais da engine, macros, tabela de comandos e gatilhos identificados.
- [x] Primeiro caso real de conflito (chegada do barco no callback de transição) documentado.
- [x] Scanner heurístico inicial adicionado ao branch.
- [ ] Executar e calibrar o scanner sobre a checkout completa com a pilha de patches ativa; revisar manualmente os alertas de macros e contextos síncronos.
- [ ] Fazer verificação de fluxo mais robusta para todas as labels de eventos.
- [ ] Verificar sistematicamente referências de flags/variáveis/LOCALIDs e comandos de espera.
- [ ] Revisar todos os scripts nativos em C e pontos onde o motor chama scripts de mapa.
- [x] Adicionar o scanner à CI com relatório informativo e falha explícita se o programa de auditoria não executar corretamente.
- [ ] Criar suíte de testes de regressão para os eventos que forem alterados.
- [x] Usar a mesma lista de patches ativa no workflow de build e no workflow de auditoria.

## Conclusão provisória

O projeto agora tem um mapa de onde vivem os eventos e uma primeira ferramenta para encontrar inconsistências potenciais. Ainda não é correto afirmar que **todos os eventos foram revisados linha por linha** ou que não existem conflitos. O caminho seguro é concluir a análise estática, corrigir suas limitações, e então revisar os scripts conforme uma matriz de riscos, começando por inicialização, gatilhos de mapa, movimentos/esperas, warps e flags persistentes.
