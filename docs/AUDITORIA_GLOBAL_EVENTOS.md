# Continuação da auditoria global de eventos

**Branch:** `experimental/pokeemerald-reference`  
**Base upstream fixada:** `rh-hideout/pokeemerald-expansion@f4dc700a130330fd2f9325a17bbb1e2d91dbf091`  
**Status:** scanner estático e compilação completa concluídos na execução #39764067065; revisão semântica e teste de runtime ainda em andamento.

## Resultado da validação mais recente
- Workflow: https://github.com/Jin27012007/Pokemon-coodinator-rpg/actions/runs/39764067065
- Job de auditoria estática: sucesso.
- Job de compilação da fonte com patches ativos: sucesso.
- ROM de validação: artefato `event-script-validation-build` (não contém a animação do barco).
- Relatório: artefato `event-script-audit-report`.

A compilação válida não confirma o comportamento em runtime. O artefato dessa execução ainda é a baseline sem animação, e não deve ser apresentado como uma build com o barco reintroduzido.

## Revisão adicional do caso SS Tidal
1. `MAP_SCRIPT_ON_TRANSITION` executa durante a transição. O script original do porto configura o escapewarp e termina.
2. `MAP_SCRIPT_ON_FRAME_TABLE` só é consultado após o fade-in e antes do processamento de input; o motor consulta a tabela em `src/script.c`. É mais apropriado investigar essa fase para uma cena animada, mas cada comando ainda precisa ser compatível com o estado global e o momento de carregamento.
3. O objeto do SS Tidal já está declarado no `map.json`, na posição (8,9), inicialmente escondido via `FLAG_HIDE_LILYCOVE_HARBOR_SSTIDAL`. A tentativa anterior o criou/reposicionou em (15,9) e tentou mover sete tiles à esquerda.
4. Não assumir que `VAR_TEMP_D`, `VAR_TEMP_E` ou `VAR_TEMP_F` são livres: a fonte as reutiliza em várias features. Uma flag persistente também não deve ser reaproveitada sem pesquisar todos os usos e estados de save.
5. O teste manual do usuário prova que a ROM sem o script não congela no início; não prova qual comando individual causou a falha.

## Próxima sequência segura
- **A.** Criar um patch isolado não ativo que apenas apresenta o barco numa primeira chegada, sem movimento nem espera.
- **B.** Compilar, conferir se o patch não mexe nos scripts de ferry comuns e testar início do jogo.
- **C.** Adicionar movimento só depois do teste A, disparado num contexto ativo por frame e com estado dedicado/sem colisões.
- **D.** Testar jogo novo, reentrada no porto, save/load, retorno de batalha/menu e ferry regular.
- **E.** Promover o patch à lista ativa apenas depois da compilação e do teste manual.

Não é seguro implementar ainda uma cena completa com base só numa hipótese. Um sinal temporário pode ser sobrescrito; um flag de barco pode alterar a lógica regular de ferry; e uma espera pode ficar presa se o objeto não estiver pronto para se mover. A próxima implementação deve ser uma mudança pequena e reversível.

## Limitações gerais da auditoria
O scanner acompanha chamadas de script e vários tipos de gatilho, referências a flags/vars, eventos de mapa, warps, objetos, movimentos, specials e macros de risco. Ainda pode gerar falsos positivos e omissões por montagem condicional, macros, tabelas, scripts nativos em C, estado de runtime e controle de fluxo indireto. Não é prova de ausência total de conflitos. Alertas relevantes precisam de triagem manual, e toda alteração precisa de teste no emulador.

## Checklist de conclusão
- [x] Fixar revisão upstream e mesma pilha de patches para build e scanner.
- [x] Executar o scanner na árvore de código após aplicar os patches ativos.
- [x] Compilar a fonte completa na mesma execução da auditoria.
- [x] Preservar a ROM funcional sem a animação como baseline.
- [ ] Revisar manualmente candidatos do relatório e todos os caminhos de flags/vars dos eventos modificados.
- [ ] Fazer testes dinâmicos dos fluxos de inicialização/mapa e ferry.
- [ ] Reintroduzir a animação gradualmente e obter confirmação manual do usuário.

## Triagem manual dos candidatos do scanner (22/10/2026)

Relatório gerado pelo artefato `event-script-audit-report` da execução [#39763952106](https://github.com/Jin27012007/Pokemon-coodinator-rpg/actions/runs/39763952106), usando a revisão upstream fixa `f4dc700a130330fd2f9325a17bbb1e2d91dbf091`.

- **Mt. Chimney duplicate label:** candidato de definição duplicada no mesmo arquivo, em ramos condicionais de montagem; não é confirmado como colisão de runtime.
- **Battle Dome / delay em setup de objetos:** o scanner aponta `delay 1` alcançável via `MAP_SCRIPT_ON_WARP_INTO_MAP_TABLE`. Deve ser revisto porque esse tipo de tabela é executado imediatamente pelo motor. O contexto indica que o atraso está no ramo de setup do oponente final; não foi alterado nesta auditoria.
- **Battle Pyramid floor/top:** os scripts de resume incluem fluxo de recuperação de desafio e `warpsilent`/`waitstate`. São fluxos específicos da Battle Frontier e exigem testes em contexto de desafio salvo; não são alterações desta branch.
- **Contest Hall:** `OnTransition` chama a preparação de música, que pode chamar `LinkContestWaitForConnection` quando o estado wireless pede conexão. É um fluxo de link, não um padrão para copiar em cenas locais. A condição de entrada precisa ser respeitada.
- **Petalburg Gym:** o callback de load restaura portas e chama um special de animação com espera. É um caso existente que depende da semântica específica desse special; não deve ser generalizado para scripts novos.
- **Route 117:** `getdaycaregfx` expande para native/special com efeitos e foi classificado como risco assíncrono. A rotina é uma inicialização específica de gráficos dos Pokémon da creche; não há indicação de que seja um conflito com o patch do barco.

Os candidatos acima são alertas para revisão, não defeitos confirmados. A auditoria não modificou nenhum desses eventos upstream. Qualquer correção neles deve ser um projeto separado, com teste de regressão próprio.

## Experimento do barco em duas fases

- Patch ativo `0005-safe-boat-arrival-frame-script.patch`: apenas sinaliza a primeira chegada durante a transição e agenda a aparição do barco em `MAP_SCRIPT_ON_FRAME_TABLE`. O callback de transição não contém movimento nem espera.
- Patch preparado, **não ativo**, `0006-boat-arrival-movement-stage.patch`: acrescenta `applymovement` e `waitmovement` dentro do script de frame, após a aparição. Só deve ser adicionado a `patches/ACTIVE_PATCHES.txt` depois que a build da fase 1 compilar e a ROM for testada manualmente.
- O estado `VAR_LILYCOVE_CITY_STATE` está documentado como variável não utilizada na revisão upstream fixada; o script o zera antes de alterar o objeto para evitar que a tabela de frame dispare repetidamente.
- O teste manual da fase 1 deve confirmar: sem congelamento na chegada; barco visível; possibilidade de andar e interagir; sair/voltar ao porto; salvar e recarregar; ferry regular ainda funcional.

A fase 1 é uma validação intermediária, não a animação final. Não substituir a ROM de referência sem teste manual.
