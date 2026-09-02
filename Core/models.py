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
    applied_verification = models.IntegerField(default=1)
    verified = models.IntegerField(default=1)

    def __str__(self) :
        return self.public_addr




class IssuedCertificate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    signer_address = models.CharField(max_length=100, db_index=True)
    recipient_name = models.CharField(max_length=200)
    file_name = models.CharField(max_length=200)
    file_hash = models.CharField(max_length=200, db_index=True)
    tx_hash = models.CharField(max_length=200, blank=True)
    validator_name = models.CharField(max_length=200, blank=True)
    is_valid = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.recipient_name} - {self.file_name} ({'Valid' if self.is_valid else 'Revoked'})"