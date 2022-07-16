from django.db import models

# Create your models here.

class ImpersonalAccount(models.Model):
    name = models.CharField(max_length=255)
    parent_ac = models.ForeignKey('self', null=True, default=None, on_delete=models.DO_NOTHING)
    type_ac = models.CharField(max_length=2)
    code = models.CharField(max_length=256)
