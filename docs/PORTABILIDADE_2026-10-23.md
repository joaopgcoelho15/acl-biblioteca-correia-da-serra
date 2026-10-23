# Verificação de portabilidade — 23 de outubro de 2026

## Versão e método

- Código e dados clonados do GitHub: `84a3ddb79d3c6ca1f48a2f75048199517fe87bbf`.
- Ambiente novo: Python 3.11.17, dependências de `requirements-dev.txt`.
- Não foram usados dados da pasta OneDrive nem credenciais de produção.

## Resultado

**42 testes passaram**, incluindo os testes das duas aplicações para compatibilidade
do Excel, cabeçalho `Impressor`, folhas auxiliares, comentários e edição, além
de pesquisa, filtros, datas, rotas em português/inglês e estrutura móvel.

Os testes confirmaram os 1 869 IDs únicos do catálogo e a associação do manifesto
a IDs existentes. Os Excel público e editorial depositados são idênticos nesta
versão; isto não demonstra igualdade com uma cópia em edição no servidor.

Foram observados avisos de ficheiros não fechados em openpyxl e um aviso de
compatibilidade futura de tipos em pandas. Não houve falhas de testes.

SHA-256 dos principais ficheiros recuperados:

```text
ea976d59af29a008a45e13a1cf1f6252253d97a9a12337e88b914010559e9fd8  database.xlsx
ea976d59af29a008a45e13a1cf1f6252253d97a9a12337e88b914010559e9fd8  editar/database.xlsx
4d87087f6cabfc7d7cbdb3dc19740a5dc546734e5ae0ea18f531ab03c6954721  Url de obras.xlsx
fb0d4fa5b1229f66ba541a15d0b9b56138a97bab76e041c64c9885512a8d9901  server/catalogo.pdf
fb0d4fa5b1229f66ba541a15d0b9b56138a97bab76e041c64c9885512a8d9901  editar/server/catalogo.pdf
03bb45bfd20598ec04075b6083dbb74507306e5cafae8e34c02fd2487874382d  website/static/obras/manifest.json
```

## Limites

As rotas foram exercitadas pelo cliente de teste Flask. Não foi verificada a
renderização visual num browser nem uma implantação Docker/proxy completa.
Não foi comparado o estado vivo do servidor com os ficheiros depositados.
Credenciais, comentários privados ainda não enviados e configuração do proxy
precisam dos acessos e cópias autorizados descritos no guia de continuidade.
