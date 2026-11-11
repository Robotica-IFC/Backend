# Notificações de equipes

As notificações ficam no banco do backend, na tabela `core_notificacao`. Cada usuário possui seu próprio registro e instante de leitura (`lida_em`), compartilhados entre seus dispositivos e sessões.

## Eventos e destinatários

- Um projeto novo gera um aviso para os alunos e professores ativos da equipe.
- Um post vinculado a um projeto gera um aviso para os membros ativos da equipe desse projeto.
- O criador também recebe o aviso se participar da equipe. Um usuário com os dois perfis recebe apenas um aviso por evento.
- Edições, posts sem projeto e registros importados por fixtures não geram avisos.
- Entrar em uma equipe não gera notificações retroativas.
- Excluir um post preserva o aviso e o acesso ao projeto. Excluir o projeto remove seus avisos.

Os eventos são tratados pelos sinais de criação dos modelos. A criação de projetos pela API e a criação de posts incluem as notificações na mesma transação do evento.

## API autenticada

- `GET /api/notificacoes/`: histórico do usuário, do mais recente para o mais antigo, com páginas de 20 itens. A resposta inclui `results`, `next`, `count` e `nao_lidas` (total de não lidas, incluindo outras páginas).
- `GET /api/notificacoes/nao-lidas/`: contador global do usuário (`nao_lidas`) e identificador do aviso não lido mais recente (`ultima_nao_lida`).
- `POST /api/notificacoes/{id}/ler/`: registra a leitura e retorna o aviso atualizado. Repetir a chamada preserva a primeira data de leitura.

O destinatário é sempre obtido da autenticação. Um usuário não pode listar ou marcar avisos de outra pessoa nem criar avisos diretamente pela API.

## Frontend

A sidebar abre a página de notificações e mostra o total de atividades não lidas. O botão que abre a sidebar também mostra uma bolinha vermelha enquanto houver atividades não lidas. Convites não aparecem nessa página e não entram nesse contador. Clicar em uma atividade salva a leitura no backend e navega para `/project/{id}`. Avisos lidos ficam com cores mais suaves e o texto “Lida”.

A lista atualiza a cada 30 segundos enquanto a página está visível e ao retornar à aba. O cabeçalho atualiza o contador a cada 30 segundos enquanto a aba está visível, mesmo com a sidebar fechada, e ao retornar à aba. Há atualização manual e paginação para consultar todo o histórico. Não há Web Push, pedido de permissão nem avisos com o site fechado.

## Hospedagem e desenvolvimento

Execute a migração antes de usar a versão nova do frontend:

```bash
python manage.py migrate
```

O `build.sh` existente já executa as migrações no deploy. Não são necessárias variáveis de ambiente adicionais ou chaves VAPID.

Para validar:

```bash
python manage.py test core.test_notificacoes
```

No repositório do frontend:

```bash
npm run test:notifications
npm run build
```

## Contas em abas diferentes

Os tokens e o cache de perfil são separados por aba com `sessionStorage`. Uma nova aba pode iniciar com a última sessão lembrada; fazer login em outra conta nessa aba não altera as abas que já estavam abertas. Sair limpa somente a sessão da aba atual.

O aviso no canto da tela aparece quando existem atividades não lidas e quando chega um novo aviso. Fechar o aviso ou abrir a lista não marca atividades como lidas; isso acontece ao clicar na atividade. O monitoramento permanece ativo nas páginas do site enquanto a aba estiver visível, inclusive nas telas sem cabeçalho.
