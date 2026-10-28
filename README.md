# Template de projeto Django com DRF e PDM

Esse é um template de projeto Django com DRF, PDM e muito mais. Ele já vem com algumas configurações e pacotes pré-instalados, como o PDM, Django, Django REST Framework, PostgreSQL, SQLite, Swagger, black, isort, Render, Cloudinary, Corsheaders, Django-Extensions, Django-Filter, dotenv, dj-database-url, drf-spectacular, gunicorn, netifaces, rest-framework-simplejwt, whitenoise e passage.id

Esse template já está pronto para ser utilizado em produção, com o [Render](http://render.com) e o [PostgreSQL](https://www.postgresql.org/). Mas também pode ser utilizado em desenvolvimento, com o [PDM](https://pdm.fming.dev/) e o [SQLite](https://www.sqlite.org/index.html).

O template também já vem com alguns arquivos de configuração pré-configurados, como:

- `pyproject.toml`: Arquivo de configuração do PDM.
- `Procfile`: Arquivo de configuração do Fl0.
- `settings.py`: Arquivo de configuração do Django.
- `urls.py`: Arquivo de configuração das rotas do Django.
- `wsgi.py`: Arquivo de configuração do Gunicorn.
- `.env.exemplo`: Arquivo de exemplo de configuração das variáveis de ambiente.
- `.gitignore`: Arquivo de configuração do Git, para ignorar arquivos e diretórios.

O template também traz o usuário padrão modificado, com o login sendo feito com o `e-mail` e não com o `username`. Inclusões de campos, como `telefone`, `data de nascimento` e `foto de perfil`, podem ser feitas facilmente.

O projeto Django criado chama-se `app` e a aplicação Django criada chama-se `core`. O projeto já vem com um modelo de usuário customizado, com autenticação pelo `passage.id`. Arquivos estáticos, como fotos, podem ser armazenados no [Cloudinary](https://cloudinary.com/).

O projeto também já vem com a documentação da API, gerada automaticamente pelo Swagger, e com a formatação de código Python, feita pelo black e pelo isort.

## Instalação e Configuração

1. Certifique-se de ter o [Python](https://www.python.org/) instalado em seu sistema.

2. Crie um novo projeto a partir desse template:
- Acesse o _template_ em https://github.com/marrcandre/template_django_pdm.
- Clique no botão `Use this template` em `Create a new repository`.
- Preencha as informações solicitadas:
  - `Owner`: <seu usuário no GitHub>
  - `Repository name`: `livraria`
- Click no botão `Create repository`.

3. Abra o projeto no vscode e execute o terminal.

2. Crie um ambiente virtual usando o [PDM](https://pdm.fming.dev/):

   ```
   pdm install
   ```

3. Crie o arquivo .env, a partir do arquivo .env.exemplo, e configure as variáveis de ambiente:

   ```
   cp .env.exemplo .env
   ```

4. Execute o servidor de desenvolvimento:

   ```
   pdm run dev
   ```

5. Acesse a API em http://localhost:19003/api/

## Uso da API

A documentação completa dos endpoints da API e exemplos de uso estão disponíveis na [Documentação da API](http://localhost:19003/api/swagger/).

## Sugestões de projeto

O formulário "Sugira um projeto" envia sugestões para uma equipe cadastrada. Uma sugestão é armazenada separadamente e não cria um projeto em andamento.

- Opções de equipes para o formulário: `GET /api/equipes/opcoes/?ativo=true`. Cada item retorna apenas `id`, `nome` e `image_perfil`, com `attachment_key` e `url` da imagem (ou `null` quando não houver imagem).
- Busca por parte do nome: `GET /api/equipes/opcoes/?search=cypher&ativo=true&page=1`. O `SearchFilter` já configurado busca no campo `nome`, sem diferenciar maiúsculas de minúsculas. O `DjangoFilterBackend` mantém os filtros existentes, como `ativo`, `instituicao` e `categorias__nome`.
- A resposta mantém a paginação de equipes: `total`, `paginas`, `pagina_atual` e `items`. Use `page` para navegar e `page_size` para ajustar a quantidade de resultados (padrão 4, máximo 15).
- Envio: `POST /api/sugestoes-projetos/`, com JSON e autenticação JWT (`Authorization: Bearer <token>`).

```json
{
  "titulo": "Robô de coleta seletiva",
  "equipe": "<uuid da equipe>",
  "descricao": "Construir um robô para separar materiais recicláveis.",
  "anonimo": true,
  "anexos": []
}
```

`titulo`, `equipe` e `descricao` são obrigatórios. O título aceita até 30 caracteres, seguindo o limite de projetos; a descrição aceita até 1.000 caracteres, conforme o contador do formulário. A equipe precisa estar cadastrada e ativa. Não é necessário enviar instituição.

No componente Vue, use um campo de busca para consultar o endpoint de equipes após uma pausa de aproximadamente 300 ms na digitação (debounce). Cancele a requisição anterior com `AbortController` quando a busca mudar e volte à página 1. Exiba `nome` nas opções e envie o `id` da equipe selecionada no campo `equipe` da sugestão. Para mais resultados, use `page` e os metadados `paginas` e `pagina_atual` da resposta.

Todo envio exige login, inclusive o anônimo. "Não quero me identificar" corresponde a `anonimo: true` (padrão): a sugestão é salva sem vínculo com o autor. "Quero me identificar" corresponde a `anonimo: false`: o backend vincula a sugestão ao usuário autenticado. O cliente não pode escolher outro autor. Sem um token JWT válido, o envio retorna `401 Unauthorized`.

Para inserir anexos, envie cada PDF ao endpoint existente `POST /api/media/documents/`, como `multipart/form-data`, no campo `file` (`description` é opcional). Envie os valores de `attachment_key` retornados na lista `anexos` da sugestão. Os anexos são opcionais e seguem a validação de PDF já adotada pelo uploader.

O envio retorna `201 Created`, com o identificador e os dados da sugestão. Dados inválidos retornam `400 Bad Request`, com os erros associados aos campos. O botão "Limpar" deve resetar os campos e a seleção de anexos no frontend; não exige uma chamada à API.

A consulta requer autenticação:

- `GET /api/sugestoes-projetos/`: sugestões enviadas pelo próprio usuário com identificação ou recebidas pelas equipes das quais participa como aluno ou professor. Administradores (`is_staff`) têm acesso a todas.
- Filtros disponíveis: `equipe` e `anonimo`, sem ampliar o acesso do usuário.
- `GET /api/sugestoes-projetos/<id>/`: detalhes com identificação do autor quando informada e URLs dos anexos. Sugestões fora do acesso do usuário retornam `404`.

As sugestões também estão registradas no Django Admin. Antes de usar o endpoint, aplique a migração com `pdm run python manage.py migrate`.

## Comandos Úteis

- `pdm run dev`: Executa o servidor de desenvolvimento. Antes de executar o servidor, descobre o endereço IP da máquina e atualiza o arquivo `.env` com o endereço IP.
- `pdm run migrate`: Executa as migrações do banco de dados. Antes de executar o `migrate`, executa o `makemigrations`. Depois de executar o `migrate`, executa o `graph_models`, atualizando o diagrama de classes dos modelos do projeto.
- Para mais detalhes, consulte o arquivo `pyproject.toml`, na seção `[tool.pdm.scripts]`.

## Detalhes do Projeto

Esse projeto utiliza os seguintes pacotes e tecnologias:

- [PDM](https://pdm.fming.dev/): Gerenciador de pacotes e ambiente virtual para Python.
- [Django](https://www.djangoproject.com/): Framework web de alto nível escrito em Python.
- [Django REST Framework](https://www.django-rest-framework.org/): Framework para desenvolvimento de APIs REST com Django.
- [PostgreSQL](https://www.postgresql.org/): Banco de dados relacional, utilizado no ambiente de produção.
- [SQLite](https://www.sqlite.org/index.html): Banco de dados relacional, utilizado no ambiente de desenvolvimento.
- [Swagger](https://swagger.io/): Framework para documentação de APIs REST.
- [Ruff] (http://https://docs.astral.sh/ruff/): Linter e formatador de código Python, escrito em Rust.
- [Render](http://render.com): Ferramenta de _deploy_ de aplicações _backend_.
- [Cloudinary](https://cloudinary.com/): Serviço de armazenamento de arquivos estáticos em nuvem.
- [Corsheaders](https://pypi.org/project/django-cors-headers/): Pacote para permitir que aplicações frontend acessem a API.
- [Django-Extensions](https://django-extensions.readthedocs.io/en/latest/): Pacote com extensões para o Django, como o `shell_plus`, que permite acessar o shell do Django com todos os modelos importados e o comando `graph_models`, que gera um diagrama de classes dos modelos do projeto.
- [Django-Filter](https://django-filter.readthedocs.io/en/stable/): Pacote para filtragem, ordenação e paginação de dados em APIs REST.
- [dotenv](https://pypi.org/project/python-dotenv/): Pacote para carregar variáveis de ambiente a partir de um arquivo `.env`.
- [dj-database-url](https://pypi.org/project/dj-database-url/): Pacote para configurar o banco de dados a partir de uma URL.
- [drf-spectacular](https://drf-spectacular.readthedocs.io/en/latest/): Pacote para geração de documentação de APIs REST com o Swagger.
- [gunicorn](https://gunicorn.org/): Pacote para servir aplicações Django em produção.
- [netifaces](https://pypi.org/project/netifaces/): Pacote para obter o endereço IP da máquina.
- [rest-framework-simplejwt](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/): Pacote para autenticação JWT em APIs REST.
- [whitenoise](http://whitenoise.evans.io/en/stable/): Pacote para servir arquivos estáticos em aplicações Django.
- [passage.id](https://passage.id): Pacote para autenticação de usuários.

## Licença

Este projeto está licenciado sob a [Licença GPL](https://www.gnu.org/licenses/gpl-3.0.html), uma licença de software livre.



