# Biblioteca Digital de José Correia da Serra

Aplicação web para explorar o catálogo da Biblioteca de José Correia da Serra,
com o Excel como fonte de dados. Implementada em Python/Flask, pandas,
HTML/Jinja, CSS e JavaScript, sem uma base de dados SQL.

## Duas Aplicações

- **Publicar:** a aplicação pública na raiz deste repositório.
- **Editar:** a aplicação editorial em [`editar/`](editar/), com instruções
  próprias e credenciais configuradas apenas no ambiente privado.

As duas aplicações incluem o mesmo Excel de referência. Durante a utilização,
as alterações editoriais não são automaticamente publicadas: é necessário
validar e transferir o Excel atualizado para a aplicação pública.

- [Site público](https://iris.sysresearch.org/acl-novo/)
- [Dados no Zenodo](https://zenodo.org/records/19338055)

## Funcionalidades

- Catálogo paginado e fichas individuais das obras.
- Pesquisa livre e índices com pesquisa interna e seleção múltipla.
- Filtros combinados com contagens relativas/absolutas e opções incompatíveis desativadas.
- Filtragem por período e ordenação por data, título ou autor.
- Interface em português e inglês, adaptada a telemóveis.
- Imagens das obras e dos registos do catálogo manuscrito.
- Páginas Sobre, Equipa, Publicações e Contactos.
- Scripts para atualizar imagens a partir de uma folha de cálculo ou de thumbnails.

## Executar Localmente

Requer Python 3.11 ou 3.12. A imagem Docker utiliza Python 3.11.

```bash
git clone https://github.com/joaopgcoelho15/acl-biblioteca-correia-da-serra.git
cd acl-biblioteca-correia-da-serra
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m flask --app server.app run --port 5056
```

Abrir [http://127.0.0.1:5056](http://127.0.0.1:5056).
Este servidor destina-se apenas ao desenvolvimento; em produção utiliza-se Gunicorn.

## Executar Com Docker

```bash
docker compose up -d --build
```

O Compose configura o prefixo `/acl-novo` e publica a porta `5057`:
[http://127.0.0.1:5057/acl-novo/](http://127.0.0.1:5057/acl-novo/).
Num servidor público deve existir um reverse proxy com HTTPS, preservando o prefixo.

```bash
docker compose logs --tail=100
docker compose down
```

## Atualizar Dados E Imagens

`database.xlsx` é a fonte do catálogo (primeira folha, atualmente `Sheet1`). A aplicação lê o Excel
com pandas e constrói os filtros a partir dos seus campos. Deve manter-se a
estrutura de colunas e os identificadores dos registos.

A coluna Q chama-se `Impressor`. Por compatibilidade, as duas aplicações
também aceitam os cabeçalhos antigos `editor` e `Editor`. O nome interno
`editor` mantém-se na API e nas hiperligações; a app editorial grava o
cabeçalho `Impressor` no Excel.

A publicação não depende das outras folhas. A app editorial também tolera
a sua ausência, mas pode recriar `Chat` quando se escreve um comentário.
Para o Zenodo, pode usar-se uma cópia apenas com a primeira folha; guardar
antes um backup das folhas editoriais, que podem conter comentários.

`Url de obras.xlsx` associa o identificador da coluna A ao URL da imagem da
coluna C. Para atualizar as imagens:

```bash
python scripts/atualizar_imagens_obras.py
```

O script ignora células sem URL, guarda as imagens pelo identificador em
`website/static/obras/` e atualiza `manifest.json`. Pode ser executado novamente
para incorporar alterações. Consultar `--help` para opções como `--force`.

Para importar imagens locais da pasta `Thumbnails/`:

```bash
python scripts/importar_thumbnails.py
```

Essa pasta de importação não é versionada; as imagens utilizadas pelo site estão
em `website/static/`. No Docker, os dados e imagens são copiados para a imagem;
depois de atualizar ficheiros, reconstruir o contentor:

```bash
docker compose up -d --build
```

## Testes

```bash
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
```

Os testes incluem os filtros, intervalos de datas, o Excel incluído, a estrutura
da interface móvel e os conteúdos da página Publicações.

## Estrutura

```text
server/app.py                  Aplicação Flask e tratamento dos dados
server/catalogo.pdf            Catálogo manuscrito
templates/                     Páginas HTML/Jinja
website/style.css              Estilos e adaptação móvel
website/filters.js             Índices e interações do catálogo
website/navigation.js          Navegação móvel
website/static/                Imagens e manifesto das obras
scripts/                       Atualização e importação de imagens
tests/                         Testes automatizados
database.xlsx                  Dados do catálogo
Url de obras.xlsx              URLs das imagens
Dockerfile                     Imagem de produção com Gunicorn
docker-compose.yml             Execução do contentor
editar/                        Aplicação editorial e respetivos recursos
```

## Dados E Créditos

O catálogo é disponibilizado também no Zenodo com o DOI
[10.5281/zenodo.19338055](https://doi.org/10.5281/zenodo.19338055).
Consultar esse registo para autoria, versão e licença dos dados ali publicados;
o Excel deste repositório pode corresponder a uma atualização diferente.

As imagens e logótipos mantêm os direitos dos respetivos titulares. A presença
de um ficheiro neste repositório público não constitui uma licença de reutilização
de todos os conteúdos nem aplica a licença do dataset ao código ou às imagens.

Credenciais, ambientes locais, relatórios temporários e backups históricos não
são incluídos no repositório. A branch `backup-inicial` identifica a versão
completa de 18 de outubro de 2026 e, como o repositório, é pública.
O histórico do depósito original foi preservado.

As instruções complementares estão em [docs/installation.md](docs/installation.md).
O ficheiro [docs/deposit-sha256.txt](docs/deposit-sha256.txt) é um manifesto
histórico do depósito inicial, não uma verificação dos ficheiros atuais.
