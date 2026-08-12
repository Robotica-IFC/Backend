from django.db import models

<<<<<<< HEAD
=======
from core.models import Projeto
>>>>>>> 00995e4759522ff1301f360a2355abcaa881ec19
from uploader.models import Image


class Post(models.Model):
    legenda = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
<<<<<<< HEAD
    aluno_criador = models.ForeignKey(
        'core.Aluno',
        related_name='posts',
        on_delete=models.PROTECT,
        null=True,
        blank=True
        )
    professor_criador = models.ForeignKey(
        'core.Professor',
        related_name='posts',
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    projeto = models.ForeignKey(
        'core.Projeto',
        on_delete=models.CASCADE,
        related_name='posts',
        null=True,
        blank=True
    )
=======
    criador = 
>>>>>>> 00995e4759522ff1301f360a2355abcaa881ec19


class PostImage(models.Model):
    post = models.ForeignKey(
<<<<<<< HEAD
        Post,
=======
        Post, 
>>>>>>> 00995e4759522ff1301f360a2355abcaa881ec19
        related_name="images",
        on_delete=models.CASCADE
    )
    image = models.ForeignKey(
<<<<<<< HEAD
        Image,
        related_name="+",
=======
        Image, 
        related_name="+", 
>>>>>>> 00995e4759522ff1301f360a2355abcaa881ec19
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
