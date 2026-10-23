# Preservar e transferir código e dados

## Conteúdo recuperável de um clone

O GitHub contém `database.xlsx`, `editar/database.xlsx`, `Url de obras.xlsx`,
os PDFs em `server/` e `editar/server/`, as imagens das duas aplicações e o
manifesto de capas público. Estes ficheiros permitem executar a versão
depositada sem depender da pasta OneDrive original ou de uma conta de IA.

O histórico Git conserva versões enviadas. Não recupera alterações que tenham
ficado apenas no Excel montado no servidor editorial. Não existe neste projeto
um backup automático equivalente ao do ILLLP.

## Salvaguardar uma atualização editorial

1. Identificar a instância e a versão do Excel que se pretende preservar.
   Suspender as escritas enquanto se obtém uma cópia consistente do ficheiro
   editorial completo, incluindo `Chat` e outras folhas de trabalho.
2. Preservar essa cópia num destino privado autorizado, com data e checksum.
   Não colocar comentários internos ou dados pessoais num repositório público.
3. Preparar separadamente o Excel de publicação com os dados aprovados.
   Preservar IDs, cabeçalhos e caminhos; confirmar as imagens associadas.
4. Versionar o ficheiro apropriado no GitHub e registar no PR a origem, data,
   contagens, folhas incluídas e verificações. A raiz é a versão pública;
   `editar/database.xlsx` é a referência editorial partilhável, não um destino
   automático para comentários privados.
5. Validar catálogo, fichas, pesquisa, filtros e downloads antes de implantar.
   Reconstruir a imagem pública depois de transferir os dados aprovados.
6. Confirmar que o commit ficou no remoto e manter a cópia anterior até validar
   o resultado. As duas aplicações podem legitimamente ter versões diferentes.

Não há neste procedimento autorização implícita para descartar informação
editorial ou publicar folhas privadas. Se houver trabalho privado ainda não
salvaguardado, a transferência operacional exige também essa cópia autorizada.

## Retomar noutra máquina ou conta

1. Obter acesso ao repositório se a sua visibilidade o exigir e clonar `main`.
   Registar o commit usado. Para recuperar uma versão anterior, escolher o
   commit dos dados e do código compatível com o objetivo.
2. Instalar Python e as dependências ou Docker Compose, conforme o README.
3. Iniciar a aplicação pública com os dados incluídos e verificar catálogo,
   uma ficha com imagens e os downloads de Excel/PDF.
4. Para o editor, criar `editar/.env` a partir do exemplo com novos valores
   privados de `EDIT_PASSWORD` e `SECRET_KEY`. Configurar o proxy e restringir
   o acesso conforme `editar/README.md`. Os segredos antigos não estão no Git.
5. Se for necessário continuar trabalho editorial posterior ao depósito,
   recuperar a cópia privada do Excel completo antes de permitir novas escritas.
6. Usar uma cópia isolada para testes; o Compose editorial monta o Excel do host
   e as gravações alteram esse ficheiro de forma persistente.

A aplicação pública usa `/acl-novo/` com Docker e a interface editorial usa
também `/acl/`. Não trocar as regras de prefixo dos dois proxies. Não copiar
configuração institucional antiga para um novo domínio sem a adaptar.

## Limite da verificação de portabilidade

A existência dos ficheiros no GitHub demonstra disponibilidade da versão
depositada. Um teste local não demonstra que esse depósito contém as últimas
edições de produção. Para afirmar recuperação integral, comparar a cópia
autorizada do servidor com os ficheiros versionados e testar o arranque no
destino, registando o commit e o resultado.
