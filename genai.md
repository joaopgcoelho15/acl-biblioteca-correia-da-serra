# Continuidade para qualquer sistema de IA

## Primeira leitura

Ler `README.md`, `CORREIA_DA_SERRA.md`, `docs/CONTINUIDADE_DADOS.md` e, quando
a tarefa envolver edição, `editar/README.md`. Confirmar branch, commit e
alterações locais. Não é necessário aceder às conversas que originaram a app.

O objetivo é tornar consultável e editável o catálogo histórico, preservando
os dados, a proveniência e a ligação entre obras e imagens. O Excel é a fonte
do catálogo; este projeto não usa o SQLite/Meilisearch da aplicação ILLLP.

## Escolher a área de intervenção

| Pedido | Ficheiros de entrada |
| --- | --- |
| Pesquisa, filtros, contagens e datas | `server/app.py`, `website/filters.js`, `tests/test_filters.py`, `tests/test_advanced_filters.py` |
| Interface e telemóvel | `templates/`, `website/style.css`, `website/navigation.js`, `tests/test_mobile_markup.py` |
| Conteúdos e publicações | `server/app.py`, `templates/`, `tests/test_publications.py` |
| Excel, Impressor e folhas auxiliares | As duas `server/app.py`, `tests/test_excel_schema.py`, `docs/installation.md` |
| Edição e comentários | `editar/server/app.py`, `editar/templates/`, `editar/website/` |
| Capas e associações | `scripts/`, `Url de obras.xlsx`, `website/static/obras/manifest.json` |
| Execução e implantação | Os dois `Dockerfile` e `docker-compose.yml`, `editar/.env.example` |

## Regras de intervenção

- Preservar IDs, nomes das colunas, transcrições, imagens e folhas de trabalho.
  Não confundir `editor` interno com o cabeçalho Excel `Impressor`.
- Não alterar o corpus para fazer passar um teste. Se a tarefa mudar os dados
  legitimamente, rever as referências de contagem e explicar a proveniência.
- Testar escritas em cópias temporárias. Não copiar automaticamente o Excel
  público sobre o editorial: podem existir correções ou comentários por publicar.
- Não descarregar de novo milhares de imagens para uma tarefa de CSS ou filtros.
- Não publicar comentários editoriais ou dados pessoais presentes em folhas
  auxiliares. Preservá-los em backup privado quando necessário.
- Criar branches a partir de `main`; procurar templates e criar ou atualizar a
  descrição do PR ao fazer commits. Não acrescentar autoria ou coautoria de IA.
  Usar `gh` para PRs e nunca invocar `/code-review`.
- Usar ferramentas nativas para ler e editar. Num worktree, copiar os `.env`
  locais em falta do checkout principal, preservar caminhos e permissões,
  mantê-los ignorados e nunca mostrar os valores.
- Não implantar alterações por consequência de um pedido apenas sobre código.
- Não enviar comentários no chat ou no PR depois de commits ou de tratar uma
  revisão, salvo pedido expresso do utilizador.

## Verificação

Instalar `requirements-dev.txt` e executar a suite do README:

```sh
python -m unittest discover -s tests -v
```

Verificar os casos relacionados com a alteração e usar o dataset incluído para
confirmar as ligações entre IDs e imagens. Para alterações visuais, verificar
as páginas em ecrã largo e móvel, em português e inglês. Para documentação,
verificar caminhos, referências e `git diff --check`.

Na descrição do PR, distinguir testes executados de verificações não realizadas.
Atualizar README e contexto se mudarem comandos, estrutura, publicação ou dados.
Não declarar que os dados de produção estão salvaguardados apenas porque existe
um Excel no repositório: confirmar qual versão foi efetivamente enviada.

## Pedido inicial reutilizável

> Estás no repositório acl-biblioteca-correia-da-serra. Lê README.md,
> CORREIA_DA_SERRA.md, genai.md e docs/CONTINUIDADE_DADOS.md. Identifica o
> objetivo, a separação entre edição e publicação e os contratos do Excel;
> depois executa este pedido: [descrever a alteração]. Preserva os dados e
> valida os testes adequados, atualizando a documentação quando necessário.
