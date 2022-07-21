from django.db import models
from django.dispatch import receiver
from django.db.models import signals

from accounts.models import ImpersonalAccount
from journals import exceptions as journal_exceptions
from accounts import exceptions as account_exceptions


class Transaction(models.Model):
    description = models.TextField(blank=True, default='')


class Split(models.Model):
    transaction = models.ForeignKey(
            Transaction, default=None, on_delete=models.CASCADE,)
    account = models.ForeignKey(ImpersonalAccount, on_delete=models.DO_NOTHING)
    type_split = models.CharField(max_length=2)
    amount = models.DecimalField(decimal_places=2, max_digits=11)


@receiver(signals.post_save, sender=Split)
def check_split_balance(sender, **kwargs):
    for split in kwargs['instance'].transaction.split_set.all():
        if split.amount <= 0:
            raise journal_exceptions.ZeroAmountError


@receiver(signals.post_save, sender=Split)
def check_split_ac_has_child(sender, **kwargs):
    split = kwargs['instance']
    if (split.account.who_am_i())['parent']:
        raise account_exceptions.TransactionOnParentAcError
