from django.contrib.auth.models import AbstractUser

from django.db import models

USER_ROLE = 'user'
MODER_ROLE = 'moderator'
ADMIN_ROLE = 'admin'
CHOICES = [
    (USER_ROLE, 'user'),
    (MODER_ROLE, 'moderator'),
    (ADMIN_ROLE, 'admin'),
]


class User(AbstractUser):
    bio = models.TextField(blank=True)
    role = models.CharField(
        choices=CHOICES,
        default='user',
        max_length=9,
    )
    email = models.EmailField('email address', unique=True)
    REQUIRED_FIELDS = ['email']

    class Meta:
        ordering = ['id']


class ConfCode(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='conf_code',
    )
    code = models.CharField(max_length=64)
    expires = models.DateTimeField()
