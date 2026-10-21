# Ambiente, compilação e validação do protótipo

## Base e escopo

O protótipo é construído a partir de `rh-hideout/pokeemerald-expansion`, não da ROM Pokémon Quetzal Alpha 9. O fluxo trabalhado nesta etapa é o início em Lilycove, a seleção inicial de gênero com a personagem feminina pré-selecionada e a chegada do S.S. Tidal ao porto.

As alterações experimentais são aplicadas na ordem:
1. `patches/0003-lilycove-female-prototype.patch`
2. `patches/0004-female-default-and-boat-arrival.patch`

A ROM compilada é um artefato de teste, não uma distribuição oficial. Não enviar arquivos ROM ou assets de terceiros ao repositório.

## Compilação reproduzível

O workflow `.github/workflows/build-boat-arrival.yml` compila em GitHub Actions e publica um artefato temporário. A execução registrada em 21/10/2026 foi concluída com sucesso:
- Execução: [GitHub Actions #39633590306](https://github.com/Jin27012007/Pokemon-coodinator-rpg/actions/runs/39633590306)
- Artefato: `female-default-boat-arrival-build`
- Revisão de `pokeemerald-expansion` usada nessa execução: `f4dc700a130330fd2f9325a17bbb1e2d91dbf091`
- O artefato expira após 7 dias, conforme retenção definida no workflow.

Para manter builds reproduzíveis, a melhoria recomendada antes de distribuir builds é fixar o repositório de origem numa revisão conhecida, em vez de clonar sempre o HEAD atual. A execução citada registra a revisão usada, mas o workflow atual ainda busca o HEAD do upstream a cada execução.

## Checagens feitas

- O job de compilação e o passo de upload do artefato terminaram com sucesso.
- A ROM extraída tem 33.554.432 bytes (32 MiB), tamanho esperado para esta base.
- O cabeçalho identifica a ROM como `POKEMON EMER` / `BPEE`.
- O checksum do cabeçalho GBA confere (`0x72`).

Essas verificações confirmam que a compilação produziu um arquivo GBA estruturalmente consistente. Não comprovam, por si só, que a cena de chegada se comporta como desejado em emulador ou hardware.

## Testes manuais ainda necessários

Ao abrir a ROM, criar um save novo e testar:
1. Na apresentação do Professor Birch, May deve aparecer como protagonista e a opção feminina deve vir selecionada. A opção masculina continua disponível.
2. Ao iniciar, observar se o navio aparece e se desloca até o cais, sem ficar preso ou sobrepor o personagem.
3. Depois da chegada, caminhar pelo porto, entrar e sair das áreas conectadas e verificar se não há bloqueio de movimento.
4. Salvar, fechar o emulador, carregar o jogo e confirmar que a chegada inicial não se repete.
5. Testar a movimentação normal do S.S. Tidal depois de avançar o jogo, para detectar interferência no ferry comum.

Se algum teste falhar, registrar o emulador usado, se foi save novo ou save antigo e o ponto exato em que falhou. O protótipo deve ser tratado como experimental até esses testes visuais e de jogo serem concluídos.

## Próximo refinamento técnico

Antes de acrescentar mecânicas de concursos/coordenadora, revisar a lógica do evento para que seja idempotente e segura com save/load, fixar a revisão upstream do build e testar os estados de mapa e do objeto do S.S. Tidal. Só depois expandir para sistemas maiores.
