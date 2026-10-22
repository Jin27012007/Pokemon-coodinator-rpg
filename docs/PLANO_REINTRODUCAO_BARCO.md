# Plano de reintrodução segura da chegada do SS Tidal

Branch: `experimental/pokeemerald-reference`  
Base: `rh-hideout/pokeemerald-expansion@f4dc700a130330fd2f9325a17bbb1e2d91dbf091`

## Status
**Não colocar ainda na pilha ativa de patches.** A ROM sem a animação é a baseline funcional confirmada pelo teste manual. O patch 0004 ativo continua desativando a cena; isto é intencional enquanto a nova implementação é desenvolvida isoladamente.

## Achados relevantes
- `LilycoveCity_Harbor_OnTransition` é um callback `MAP_SCRIPT_ON_TRANSITION`; o original configura apenas o escapewarp e termina.
- O `map.json` possui o objeto SS Tidal, normalmente oculto por `FLAG_HIDE_LILYCOVE_HARBOR_SSTIDAL`, com posição declarada (8,9); o script da embarcação é `0x0`.
- A versão que congelou adicionou `clearflag`, `setobjectxyperm`, `addobject`, `applymovement` e `waitmovement 0` ao callback de transição imediato, usando posição inicial (15,9) e sete passos à esquerda.
- `MAP_SCRIPT_ON_FRAME_TABLE` executa depois do fade-in, antes da entrada do jogador ser processada. Ainda assim, um script de frame só pode usar um movimento/espera depois que a visibilidade, a posição e o estado global estiverem corretos.
- `VAR_TEMP_D/E/F` são variáveis compartilhadas entre muitos sistemas (por exemplo, Frontier/Pyramid). Não podem ser assumidas livres no início do jogo sem conferir o fluxo de cada passagem.

## Experimento sugerido — ainda sem patch pronto
1. Definir um sinal de execução dedicado ou uma condição persistente adequada (não usar VAR_TEMP_* genericamente se o evento puder sobreviver a um save/load ou colidir com outros callbacks).
2. Preparar/apresentar o barco durante o estágio apropriado de carregamento do mapa, sem uma espera por movimento no callback imediato.
3. Disparar a cena a partir de um contexto que processe atualizações por frame e só depois que o mapa e o objeto estiverem carregados.
4. Garantir caminhos seguros para a cena ser executada uma única vez; retornar/entrar de novo no porto, salvar/carregar e viajar pelo ferry normal não devem ocultar ou recriar o barco indevidamente.
5. Usar uma primeira versão reduzida (apenas aparição/reposicionamento, sem movimento), compilar e testar. Depois adicionar o movimento numa mudança separada.
6. Nunca colocar o patch experimental na lista ativa até passar por compilação e teste manual.

## Por que não apliquei uma versão especulativa automaticamente
Uma proposta simples baseada em `VAR_TEMP_E/F/D` e `FLAG_HIDE...` parece curta, mas pode falhar após save/load, colidir com o fluxo do Battle Frontier/Pyramid ou deixar o objeto em posição errada. Isso repetiria exatamente o tipo de conflito que esta auditoria pretende evitar. É necessário confirmar como a primeira entrada é distinguida das reentradas e qual estado o código usa para esconder/mostrar o SS Tidal antes de escrever o patch.
