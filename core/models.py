from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class User(AbstractUser):
    email = models.EmailField(unique=True)
    wallet_address = models.CharField(max_length=70, unique=True)
    public_key = models.CharField(max_length=600, unique=True)
    verified = models.BooleanField(default=False)
    randomString = models.CharField(max_length=50, default='')