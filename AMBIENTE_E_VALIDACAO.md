# Relatório de ambiente e limites da auditoria

## Ambiente disponível nesta análise

- O ZIP de referência foi extraído e a árvore foi pesquisada localmente.
- O sistema tem `make`, mas a consulta aos executáveis não encontrou `arm-none-eabi-gcc`, `arm-none-eabi-as` ou `agbcc` no PATH.
- Por isso, **não foi possível testar uma compilação local neste ambiente** com as ferramentas encontradas. Isso não significa que a base não compile em ambiente adequado.
- O repositório GitHub do projeto contém documentação de análise, não contém a árvore completa do jogo e não deve receber a ROM.

## Implicação

Até existir um ambiente de build com o toolchain configurado (ou uma compilação remota confiável), a primeira alteração só poderá ser revisada estaticamente. Não devemos chamar um patch de funcional/jogável sem gerar a ROM e testar o início e o save num emulador.

## Próxima sequência

1. Determinar se existe código-fonte de Quetzal correspondente à Alpha 9 em algum repositório público ou pacote oficial.
2. Caso contrário, decidir conscientemente se o mod será construído em cima da expansão de referência enviada, aceitando que isso é uma nova base e não um patch compatível com a ROM Alpha 9.
3. Mapear o fluxo completo de escolha/inicialização do jogador, scripts de introdução e respawn.
4. Implementar início feminino em Lilycove numa branch ou conjunto pequeno de commits, sem tocar ainda no sistema de fitas.
5. Configurar build, produzir ROM de teste localmente/remotamente e verificar uma nova partida, save/load, respawn, saída do porto e ferry normal.
