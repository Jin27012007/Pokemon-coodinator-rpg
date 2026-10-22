# Triagem manual do scanner global de eventos

**Execução estática analisada:** [GitHub Actions #39763952106](https://github.com/Jin27012007/Pokemon-coodinator-rpg/actions/runs/39763952106)  
**Commit analisado:** aa6bf735ecd7077eb543b69c6034e6ff3318382f  
**Fonte upstream:** rh-hideout/pokeemerald-expansion@f4dc700a130330fd2f9325a17bbb1e2d91dbf091  
**Pilha experimental aplicada antes do scanner:** patches/ACTIVE_PATCHES.txt  
**Escopo:** scripts do jogo e dados de mapas, não somente o evento inicial.

## Resultado estrutural

O job estático concluiu com sucesso e publicou o artefato event-script-audit-report. O relatório detectou:

- 887 arquivos data/maps/*/scripts.inc, 939 map.json e 86 arquivos data/scripts/*.inc.
- 22.609 nomes de labels indexados em scripts de mapa/compartilhados.
- 0 referências de fluxo não resolvidas pelo scanner.
- 0 referências de movimento não resolvidas.
- 0 referências de specials não resolvidas.
- 0 referências de scripts de objetos ausentes em map.json.
- 0 arquivos JSON inválidos, IDs locais duplicados, mapas de conexão desconhecidos, warps desconhecidos ou IDs de mapa duplicados.
- 1 label duplicada candidata na mesma unidade: MtChimney_EventScript_BagIsFull. O scanner classifica-a como possível duplicação em ramos de montagem condicional; não deve ser removida sem conferir a diretiva condicional e a compilação.
- 0 movimentos com terminador suspeito na versão atual do scanner.

Esses resultados reduzem o risco de referências quebradas, mas só cobrem as relações que o scanner compreende. Macros, tabelas, código C, pré-processador e comportamento em execução exigem outras verificações.

## Candidato de espera: Battle Dome

O único alerta de espera em um gatilho síncrono é:

- Arquivo: data/maps/BattleFrontier_BattleDomeBattleRoom/scripts.inc
- Label: BattleFrontier_BattleDomeBattleRoom_EventScript_SetUpObjects
- Contexto: tabela MAP_SCRIPT_ON_WARP_INTO_MAP_TABLE
- Sequência relevante: removeobject do oponente, delay 1, addobject, applymovement.

No upstream fixado, src/script.c mostra que a tabela ON_WARP_INTO_MAP_TABLE chama RunScriptImmediately. Em src/scrcmd.c, ScrCmd_delay configura RunPauseTimer; esse timer decrementa um contador a cada chamada nativa, sem aguardar explicitamente a passagem de um quadro visual. Portanto, o alerta não comprova um deadlock. A preocupação mais precisa é que delay 1 usado nesse contexto pode não fornecer uma pausa real de quadro, embora pareça fazê-lo. A sequência pertence à fonte upstream, não foi adicionada pelo patch de Lilycove.

Regra de projeto: não copiar delay/waitmovement/esperas com animação para um callback imediato sem confirmar a semântica no motor. Se o projeto precisar de uma cena após o carregamento, deve usar um gatilho compatível com execução por quadros e estado persistente para controlar primeira execução.

## Alertas de contexto: triagem

### Battle Pyramid — ON_RESUME

Os scripts do andar e do topo consultam o estado do desafio. Em estados SAVING/LOST, seguem para o script comum de retorno ao lobby, que atualiza dados, cura a equipe, executa warpsilent e waitstate. Isso é uma transferência intencional, não evidência isolada de congelamento. A asserção em src/script.c avisa para não encerrar script com warp em andamento sem waitstate. Esses scripts continuam sendo contextuais e não são modelos para cenas de entrada genéricas.

### Contest Hall — ON_TRANSITION

O script de música faz TryWaitForLink; só entra no caminho de espera quando IsWirelessContest retorna verdadeiro. Nesse caminho, chama LinkContestWaitForConnection, declarado com waitstate=1 em data/specials.inc. Isso pertence ao fluxo de concurso sem fio. O scanner sinaliza corretamente que é uma operação que depende de estado externo; ainda assim, o resultado por si só não prova defeito. Não reutilizar essa lógica em um evento offline comum.

### Petalburg Gym — ON_LOAD

A abertura de portas chama PetalburgGymSlideOpenRoomDoors, também declarado com waitstate=1. É uma animação de estado do ginásio, disparada quando a progressão já desbloqueou portas. É uma exceção do conteúdo upstream que exige conhecimento da implementação do special; não deve ser tratada como um padrão genérico seguro para novos callbacks.

### Route 117 — ON_TRANSITION

A macro getdaycaregfx chama GetDaycareGraphics como native com requests_effects=1 para preparar dados/visuais dos Pokémon da creche. O scanner assinala o uso de native/contexto, não uma chamada desconhecida. A revisão deve conferir a semântica do native se esse mapa ou macro for alterado; não existe evidência aqui de que cause o congelamento de Lilycove.

## Como interpretar os contadores do scanner

O scanner procura padrões suspeitos; ele não prova por si só que uma sequência de comandos vai congelar, nem prova que um evento é seguro por não ter sido sinalizado. Um relatório sem referências não resolvidas significa apenas que as categorias de referências suportadas foram resolvidas no conjunto de fontes analisado.

Antes de editar qualquer evento, conferir:
1. o contexto em que o callback é executado (imediato, contexto global ou tabela por quadro);
2. a implementação C do comando/native/special, inclusive se produz espera implícita;
3. a flag/variável que decide quando executar e se o evento pode repetir em reentrada/save-load;
4. o alvo de warp, estado e coordenadas/elevation dos objetos;
5. todos os caminhos de call/goto/return/end e qualquer lock/ocultação;
6. o diff aplicado, a compilação limpa e os testes manuais correspondentes.

## Validação ainda necessária

- Revisar a label condicional duplicada de Mt Chimney contra o pré-processador/assembler.
- Tratar o caso Battle Dome como discrepância semântica a validar, sem alterar conteúdo upstream não relacionado ao Coordinator RPG.
- Confirmar o resultado final do job de compilação separado da auditoria estática.
- Manter a ROM de diagnóstico que o usuário testou como baseline até cada nova variante passar por compilação e teste manual.
- Ampliar a cobertura dos scripts nativos em C, ponteiros/tabelas e efeitos colaterais que não podem ser inferidos por regex.

**Conclusão:** o relatório atual não encontrou referências quebradas nas categorias verificadas, mas encontrou exceções de contexto que exigem leitura de código. A meta correta é resolver ou classificar cada alerta e testar todos os eventos alterados — não afirmar que o scanner garante risco zero.
