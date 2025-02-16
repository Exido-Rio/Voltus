from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid


# Create your models here.


class Signer(models.Model):
    id = models.UUIDField(primary_key=True,default=uuid.uuid4)
    public_addr = models.CharField(max_length=100)
    position = models.TextField(max_length=200,blank=True)
    info = models.TextField(max_length=200,blank=True)
    Company_Name = models.CharField(max_length=100,blank=True)
    created_at = models.DateTimeField(auto_now=True)
    applied_verification = models.IntegerField(default=0)
    verified = models.IntegerField(default=0)

    def __str__(self) :
        return self.public_addr




# blacklist 