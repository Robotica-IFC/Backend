import secrets
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from django.db import models
from django.utils import timezone

maximo_convites_equipe = 5
tempo_expiracao_codigo = 15
maximo_tentativas = 5


class Convite(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        AWAITING_CONFIRMATION = "awaiting_confirmation", "Aguardando confirmação"
        ACCEPTED = "accepted", "Aceito"
        DECLINED = "declined", "Recusado"

    equipe = models.ForeignKey(
        "core.Equipe", on_delete=models.CASCADE, related_name="convites"
    )

    aluno = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="convite_recebido",
    )

    enviadosPor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="convites_enviados")

    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING)

    codigoConfirmacao = models.CharField(max_length= 128, null=True, blank=True)
    codigoExpiracao= models.DateTimeField(null=True, blank=True)
    tentativas = models.PositiveSmallIntegerField(default=0)
    criacao = models.DateTimeField(auto_now_add=True)
    resposta = models.DateTimeField(null=True, blank=True)

    class Meta: 
        constraints = [
            models.UniqueConstraint(
                fields = ["equipe", "aluno"],
                condition = models.Q(status__in=["pending", "awaiting_confirmation"]), name = "conviteUnicoPorAluno"
            )
        ]

    def is_active(self):
        return self.status in (self.Status.PENDING, self.Status.AWAITING_CONFIRMATION)

    def geradorCodigoAleatorio (self):
        code = f"{secrets.randbelow(1_000_000):06d}"
        self.codigoConfirmacao = make_password(code)
        self.codigoExpiracao = timezone.now() + timezone.timedelta( minutes= tempo_expiracao_codigo )
        self.tentativas = 0
        self.status = self.Status.AWAITING_CONFIRMATION
        self.save(update_fields=[
            "codigoConfirmacao", "codigoExpiracao", "tentativas", "status"
        ])

        return code

    def checarConfirmacao(self, code):
        if self.status != self.Status.AWAITING_CONFIRMATION:
            return False, "Convite não está aguardando confirmação."
        if self.codigoExpiracao and timezone.now() > self.codigoExpiracao:
            return False, "Código expirado. Solicite um novo."
        if self.tentativas >= maximo_tentativas:
            return False, "Número máximo de tentativas excedido."

        self.tentativas += 1
        self.save(update_fields=["tentativas"])

        if not check_password(code, self.codigoConfirmacao):
            return False, "Código incorreto"


        return True, None
 