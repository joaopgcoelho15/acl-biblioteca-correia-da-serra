# Biblioteca Correia da Serra — contexto duradouro

Documento preparado em 23 de outubro de 2026 para retomar o projeto sem o
histórico dos chats. Confirmar o commit e os dados atuais antes de qualquer mudança.

## Objetivo

Permitir estudar e consultar o catálogo da Biblioteca de José Correia da Serra,
relacionando descrições bibliográficas, transcrições e imagens do catálogo
manuscrito com os metadados e imagens das obras. A consulta pública deve permitir
pesquisar, combinar índices, filtrar por datas e abrir fichas em português e inglês.
Uma aplicação editorial separada permite corrigir metadados e guardar comentários.

Preservar os dados e a relação com as fontes históricas é parte do objetivo:
melhorar a interface não deve mudar silenciosamente identificadores,
transcrições, atribuições, datas ou ligações às imagens.

O projeto está em
[joaopgcoelho15/acl-biblioteca-correia-da-serra](https://github.com/joaopgcoelho15/acl-biblioteca-correia-da-serra).
É independente do ILLLP/Dicionário e Vocabulário, que usa XML/TEI, SQLite e
Meilisearch noutro repositório. Não aplicar essa arquitetura a esta app por analogia.

## Arquitetura e mapa do código

```text
editar/database.xlsx ← aplicação editorial Flask
          │ validação e transferência explícita
          ▼
database.xlsx → aplicação pública Flask/pandas → HTML/Jinja + CSS/JavaScript
                  ↑
          imagens + manifesto + PDF
```

| Caminho | Função |
| --- | --- |
| `server/app.py` | Rotas públicas, leitura/cache do Excel, pesquisa, filtros, datas e traduções |
| `templates/` | Páginas e fichas públicas |
| `website/style.css` | Estilos e adaptação móvel |
| `website/filters.js`, `website/navigation.js` | Interação dos filtros e navegação |
| `website/static/` | Recortes manuscritos, imagens e recursos gráficos |
| `website/static/obras/manifest.json` | Associação dos IDs às imagens das obras |
| `server/catalogo.pdf` | Download do catálogo manuscrito |
| `database.xlsx` | Catálogo da aplicação pública |
| `Url de obras.xlsx` | Fonte de URLs para atualização das imagens |
| `editar/server/app.py`, `editar/templates/`, `editar/website/` | Aplicação editorial e interface própria |
| `editar/database.xlsx` | Ficheiro de trabalho editorial; não sincroniza automaticamente com a raiz |
| `scripts/` | Importação e atualização das imagens |
| `tests/` | Testes públicos e de compatibilidade editorial |

## Contratos dos dados e decisões a preservar

- O catálogo é Excel, sem base SQL. Ambas as aplicações leem a primeira folha.
  Os ficheiros incluídos são uma referência versionada, não um canal de
  sincronização automática entre servidor e GitHub.
- `id` identifica a obra na aplicação. O número interpretado a partir do nome
  do recorte manuscrito pode ser diferente; não trocar um pelo outro.
- Preservar nomes das colunas e caminhos `path`, normalmente relativos a
  `website/`, como `static/…jpg`.
- A coluna Q é `Impressor`. A leitura aceita os nomes históricos `editor` e
  `Editor`; o campo interno e os parâmetros da API continuam a chamar-se `editor`.
- `Chat` contém comentários editoriais, não registos bibliográficos. A sua
  ausência é tolerada e a folha pode ser criada ao adicionar um comentário.
  `Sheet2`, quando existe, pode conservar descrições da operação antiga.
  Não apagar folhas auxiliares do original de trabalho.
- O dataset usado pelos testes atuais tem 1 869 IDs únicos. Esta é uma referência
  datada: uma atualização legítima do corpus exige rever os testes de contagens.
- Preservar datas incompletas e intervalos; não transformar tudo em anos exatos.
- Os filtros combinam seleções, apresentam contagens globais e relativas e
  desativam opções incompatíveis. Preservar o comportamento definido nos testes.
- O manifesto de capas é necessário para associar imagens às obras. Um ficheiro
  de imagem presente sem associação não implica que seja apresentado.
- Alterações editoriais só chegam à app pública depois de validação e
  transferência explícita do Excel. No Docker público, dados e imagens fazem
  parte da imagem: reconstruir o contentor após uma atualização.

## Executar e verificar

O README contém os comandos completos. Requer Python 3.11/3.12 e dependências
de `requirements.txt`; `requirements-dev.txt` inclui também as dependências
editoriais necessárias para testar ambas as apps.

- Desenvolvimento público: `python -m flask --app server.app run --port 5056`,
  na raiz, sem prefixo URL por omissão.
- Docker público: `docker compose up -d --build`, acesso na porta 5057 com
  prefixo `/acl-novo/`. O proxy preserva esse prefixo.
- Docker editorial: executar o Compose dentro de `editar/`, configurar `.env`
  a partir do exemplo e aceder pela porta local 5055. A interface usa também
  o prefixo institucional `/acl/`; o proxy editorial remove-o ao encaminhar.
- O editor usa um worker e uma thread para proteger a escrita no Excel. Não
  executar vários escritores sobre o mesmo ficheiro.

A password de edição não protege todas as rotas de escrita herdadas. O acesso
editorial precisa de proteção no proxy ou na rede, conforme `editar/README.md`.
Configurar `EDIT_PASSWORD` e `SECRET_KEY` no destino sem os publicar.

Verificar catálogo, pesquisa, filtros combinados, intervalos de datas, ficha,
imagens, downloads, português/inglês e navegação móvel. Para testar gravações e
comentários, usar uma cópia do Excel, nunca o ficheiro editorial de produção.

## Dados, proveniência e transferência

O repositório inclui código, Excel, PDF, recortes e imagens das obras nas duas
árvores. Não é necessário descarregar novamente as capas para iniciar a app.
Os scripts de imagens são ferramentas de atualização; dependem de fontes
externas que podem mudar e não devem ser executados sem necessidade.

O depósito Zenodo [10.5281/zenodo.19338055](https://doi.org/10.5281/zenodo.19338055)
é uma referência de dados e autoria. Pode não coincidir com o Excel atual do
GitHub. Consultar a licença desse depósito para os dados ali publicados; não
estender automaticamente a licença ao código, às capas ou aos logótipos.

`docs/deposit-sha256.txt` refere-se ao depósito original, não aos ficheiros
atuais. A branch `backup-inicial` preserva uma versão histórica; não a usar como
substituto da branch atual sem escolher explicitamente essa recuperação.

Seguir [docs/CONTINUIDADE_DADOS.md](docs/CONTINUIDADE_DADOS.md) para preservar
trabalho novo e restaurar noutra máquina. Este guia não declara que o Excel
atualmente no servidor seja igual à última versão no GitHub.

## Próximas intervenções

Não há neste documento uma alteração funcional futura pré-autorizada. Retomar
com o pedido concreto do utilizador, verificar o comportamento existente e
atualizar contexto e testes quando mudar dados, publicação ou contratos.
