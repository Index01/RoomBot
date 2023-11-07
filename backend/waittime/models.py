from django.db import models

class Wait(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField("WaitName", max_length=200)
    short_name = models.CharField("ShortName", max_length=20, unique=True)
    password = models.CharField("Password", max_length=30, blank=True, null=True)
    time = models.IntegerField("WaitTime")
