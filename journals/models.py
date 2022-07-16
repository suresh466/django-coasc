from django.db import models
from accounts.models import ImpersonalAccount

# Create your models here.

class Transaction(models.Model):

    description = models.TextField(blank=True, default='')

class Split(models.Model):

    account = models.ForeignKey(
        ImpersonalAccount,
        on_delete=models.DO_NOTHING
    )
    type_split = models.CharField(max_length=2)
    amount = models.DecimalField(decimal_places=2, max_digits=11)
