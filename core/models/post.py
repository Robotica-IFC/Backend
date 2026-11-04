from django.db import models

from uploader.models import Image


class Post(models.Model):
    legenda = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
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

class PostLike(models.Model):
    post = models.ForeignKey(Post, related_name='likes', on_delete=models.CASCADE)
    user = models.ForeignKey('core.User', related_name='post_likes', on_delete=models.CASCADE)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['post', 'user'], name='unique_post_like')]


class PostComment(models.Model):
    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
    user = models.ForeignKey('core.User', related_name='post_comments', on_delete=models.CASCADE)
    texto = models.TextField(max_length=1000)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['criado_em', 'pk']
