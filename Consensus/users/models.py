from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.


class User(AbstractUser):
    intro = models.CharField(max_length=200, verbose_name='个人简介')

    def __str__(self):
        return self.username
