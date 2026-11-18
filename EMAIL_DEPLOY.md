# Confirmação de e-mail em produção

O front inicia o cadastro em `/api/alunos/` ou `/api/professores/`. A API responde com HTTP 202 e um `registration_token`, sem criar `User`, `Aluno` ou `Professor` e sem emitir tokens de login. Os dados ficam em um cadastro temporário por até 24 horas, com a senha armazenada apenas como hash. Cadastros temporários expirados são removidos ao iniciar novos cadastros.

O front guarda o identificador na sessão da aba e o envia com o e-mail e o código para `/api/verificar-email/`. Só depois da confirmação a API cria a conta e o perfil, marca o e-mail como verificado e devolve os tokens de login. O mesmo identificador deve acompanhar `/api/reenviar-codigo/`. O código expira em 10 minutos, permite cinco erros e o reenvio exige 60 segundos de intervalo. Após cinco erros, espere a expiração para reenviar.

Se o SMTP falhar no envio inicial, a API retorna HTTP 503 e não cria conta nem cadastro temporário: corrija a configuração e tente enviar o formulário novamente. Falhas no reenvio preservam o código anterior. Contas antigas ainda não verificadas continuam podendo confirmar o e-mail pelo fluxo anterior, mas não podem fazer login, renovar tokens ou acessar endpoints autenticados antes da confirmação.

## Backend — Fábrica de Software IFC

URL pública: https://roboticaifc.class.fabricadesoftware.ifc.edu.br/

Cadastre estas variáveis no mecanismo de configuração de ambiente usado pela hospedagem, com os valores reais do seu provedor SMTP. Se você não tiver acesso a essa configuração, peça ao responsável pela infraestrutura da Fábrica de Software para defini-las e reiniciar o backend:

```dotenv
EMAIL_HOST=smtp.seu-provedor.com
EMAIL_PORT=587
EMAIL_HOST_USER=seu-usuario-smtp
EMAIL_HOST_PASSWORD=sua-senha-smtp
EMAIL_USE_TLS=true
EMAIL_USE_SSL=false
DEFAULT_FROM_EMAIL=Nome do projeto <email-autorizado@seu-dominio.com>
CORS_ALLOWED_ORIGINS=https://robotica-ifc.vercel.app
```

O remetente deve ser autorizado pelo provedor. Se o provedor exigir porta 465, use `EMAIL_USE_TLS=false` e `EMAIL_USE_SSL=true`. A hospedagem precisa permitir conexões SMTP. Não coloque essas credenciais na Vercel nem no Git.

Publique as alterações do backend e execute `python manage.py migrate --noinput` no ambiente de produção. O Procfile já contém esse comando na fase `release`; confira no log se a hospedagem o executou. O script build.sh também executa migrations. Não rode migrations locais apontando para o banco de produção.

A migration 0010 preserva o acesso de todas as contas existentes, marcando-as como verificadas; somente cadastros posteriores exigirão confirmação. Essa marcação preserva compatibilidade, não comprova que esses e-mails antigos foram validados.

## Frontend (Vercel)

Configure a variável de build:

```dotenv
VITE_URL_BACKEND=https://roboticaifc.class.fabricadesoftware.ifc.edu.br/api/
```

O front também contém `.env.production` com essa URL como padrão para o build de produção. Uma variável `VITE_URL_BACKEND` definida na Vercel prevalece sobre esse arquivo: atualize ou remova valores antigos. Use a URL HTTPS real da API, incluindo `/api/`. Faça um novo deploy depois de alterar a variável. Se a URL do front for diferente de `https://robotica-ifc.vercel.app`, inclua a origem exata em `CORS_ALLOWED_ORIGINS` no backend. Múltiplas origens são separadas por vírgula, sem caminhos. Configure explicitamente URLs de preview se precisar testá-las.

O arquivo vercel.json permite abrir e atualizar rotas do Vue como `/verificar-email`.

## Verificação após publicar

1. Inicie um cadastro de aluno e confirme que ele fica na tela do código, sem criar usuário ou perfil no banco.
2. Confira o e-mail e o spam. Se não chegar, consulte o log do backend, ajuste SMTP e reenvie.
3. Teste um código incorreto: deve haver erro, sem login.
4. Informe o código correto: somente agora o usuário e o perfil devem ser criados, e o front deve abrir `/home-page`.
5. Repita com uma conta nova de professor.
6. Tente entrar antes de confirmar: o acesso deve ser negado. Na mesma aba, o login deve oferecer “Verificar e-mail” para retomar o cadastro temporário, inclusive depois de atualizar a página.

Para desenvolvimento sem SMTP, use `EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend` somente no ambiente local. O código será exibido no terminal local.
