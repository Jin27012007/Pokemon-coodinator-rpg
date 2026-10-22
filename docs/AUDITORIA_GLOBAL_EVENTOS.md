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
