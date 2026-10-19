# Editar — Biblioteca Correia da Serra

Aplicação editorial existente, com edição de metadados e comentários.
A aplicação de publicação encontra-se na raiz do repositório.

## Executar

Copiar `.env.example` para `.env` e preencher `EDIT_PASSWORD` e `SECRET_KEY`
com valores privados. Sem `EDIT_PASSWORD`, a verificação da password de edição
é recusada. O ficheiro `.env` não deve ser publicado.

```bash
docker compose up -d --build
```

Abrir `http://127.0.0.1:5055/`. Os URLs do frontend editorial estão preparados
para o reverse proxy institucional em `/acl/`. Para utilização completa com
esse prefixo, o proxy deve remover `/acl/` ao encaminhar para a aplicação,
tal como na instalação existente.

O Excel está montado como volume para preservar as edições. Utiliza-se um
único worker porque a escrita em Excel não suporta múltiplos escritores
concorrentes. Não executar várias instâncias sobre o mesmo ficheiro.

## Dados

- A primeira folha contém o catálogo e tem de manter os campos e IDs.
- A coluna Q chama-se `Impressor`; os antigos nomes `editor` e `Editor`
  continuam a ser aceites na leitura. Internamente a API mantém `editor`,
  enquanto as gravações no Excel mantêm o cabeçalho `Impressor`.
- É possível abrir e editar um ficheiro com apenas a primeira folha.
- `Chat`, quando existe, guarda comentários editoriais e não é uma folha de
  dados bibliográficos. Sem essa folha, as fichas mostram uma conversa vazia;
  a folha é recriada apenas quando se grava um comentário novo.
- A operação antiga de descrição usa `Sheet2` se existir; caso contrário,
  grava na coluna `description` da primeira folha.

Eliminar folhas auxiliares pode apagar comentários ou informação de trabalho,
mesmo que a aplicação continue a funcionar. Para o Zenodo, utilizar uma cópia
limpa com a primeira folha, preservando o ficheiro editorial completo em backup.

## Limites De Segurança

Esta publicação do código não é uma auditoria de segurança. A aplicação
editorial herdada tem rotas de escrita que exigem proteção adicional no proxy
ou na rede; a password do botão de edição não substitui controlo de acesso
a todas as rotas. Não disponibilizar uma instalação nova diretamente na
Internet sem essa proteção. Nenhuma password ou chave privada é incluída.
