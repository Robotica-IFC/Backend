from django.db import models

from core.models import Projeto
from uploader.models import Image


class Post(models.Model):
    legenda = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    criador = 


class PostImage(models.Model):
    post = models.ForeignKey(
        Post, 
        related_name="images",
        on_delete=models.CASCADE
    )
    image = models.ForeignKey(
        Image, 
        related_name="+", 
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
