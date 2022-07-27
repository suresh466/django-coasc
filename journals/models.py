from django.db import models
from django.dispatch import receiver
from django.db.models import signals

from accounts.models import ImpersonalAccount
from journals import exceptions as journal_exceptions
from accounts import exceptions as account_exceptions


class Transaction(models.Model):
    description = models.TextField(blank=True, default='')


class Split(models.Model):
    DEBIT = 'dr'
    CREDIT = 'cr'
    TYPE_SPLIT_CHOICES = [
        (DEBIT, 'Debit'),
        (CREDIT, 'Credit'),
    ]
    transaction = models.ForeignKey(
            Transaction, on_delete=models.PROTECT)
    account = models.ForeignKey(ImpersonalAccount, on_delete=models.PROTECT)
    type_split = models.CharField(max_length=2, choices=TYPE_SPLIT_CHOICES)
    amount = models.DecimalField(decimal_places=2, max_digits=11)


@receiver(signals.pre_save, sender=Split)
def check_for_exceptions(sender, **kwargs):
    split_instance = kwargs['instance']
    if (split_instance.account.who_am_i())['parent']:
        raise account_exceptions.TransactionOnParentAcError
    if split_instance.amount <= 0:
        raise journal_exceptions.ZeroAmountError
