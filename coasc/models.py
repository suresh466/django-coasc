from decimal import Decimal

from django.db import models
from django.db.models import Sum

from django.dispatch import receiver
from django.db.models import signals

from coasc import exceptions


class ImpersonalAccount(models.Model):
    ASSET = 'AS'
    LIABILITY = 'LI'
    INCOME = 'IN'
    EXPENSES = 'EX'
    TYPE_AC_CHOICES = [
        (ASSET, 'Asset'),
        (LIABILITY, 'Liability'),
        (INCOME, 'Income'),
        (EXPENSES, 'Expense'),
    ]
    name = models.CharField(max_length=255)
    parent_ac = models.ForeignKey(
            'self', null=True, blank=True, default=None,
            on_delete=models.PROTECT)
    type_ac = models.CharField(
            max_length=2, blank=True, choices=TYPE_AC_CHOICES)
    code = models.CharField(
            max_length=255, blank=True, null=True, default=None, unique=True)

    def __str__(self):
        string = f'{self.name}->({self.code})'
        return string

    def who_am_i(self):
        ac_is = dict.fromkeys(['parent', 'child', 'single'], None)
        if not self.type_ac:
            ac_is['child'] = True
            return ac_is

        elif self.impersonalaccount_set.exists():
            ac_is['parent'] = True
            return ac_is

        elif self.type_ac and not self.impersonalaccount_set.exists():
            ac_is['single'] = True
            return ac_is
        else:
            return 'Something went wrong! Maybe this account should not exist'

    def bal(self):
        if self.who_am_i()['parent']:
            sps = Split.objects.filter(account__parent_ac=self)
        else:
            sps = self.split_set.all()

        dr_sps = sps.filter(type_split='dr')
        cr_sps = sps.filter(type_split='cr')

        dr_sum = dr_sps.aggregate(dr_sum=Sum('amount'))['dr_sum'] or 0
        cr_sum = cr_sps.aggregate(cr_sum=Sum('amount'))['cr_sum'] or 0
        diff = dr_sum - cr_sum

        return {'dr_sum': dr_sum, 'cr_sum': cr_sum, 'diff': diff}

    @classmethod
    def total_bal(cls, type_ac=None):
        if type_ac is None:
            accounts = cls.objects.filter(parent_ac=None)
        else:
            accounts = cls.objects.filter(type_ac=type_ac)

        tds = Decimal(0)
        tcs = Decimal(0)
        for account in accounts:
            bals = account.bal()
            tds += bals['dr_sum']
            tcs += bals['cr_sum']

        diff = tds - tcs
        return {'total_dr_sum': tds, 'total_cr_sum': tcs, 'diff': diff}

    @classmethod
    def validate_accounting_equation(cls):
        total_bals = cls.total_bal()
        if total_bals['diff'] != 0:
            raise exceptions.AccountingEquationViolationError(
                    'Dr, Cr side not balanced; equation, "AS=LI+CA" not true;')


@receiver(signals.pre_save, sender=ImpersonalAccount)
def raise_exceptions_impersonalaccount(sender, **kwargs):
    ac_instance = kwargs['instance']
    if not ac_instance.parent_ac and not ac_instance.type_ac:
        raise exceptions.OrphanAccountCreationError(
                'must have a parent or type')

    elif ac_instance.parent_ac:
        if ac_instance.type_ac:
            raise exceptions.AccountTypeOnChildAccountError(
                    'type on a child not allowed')

        elif ac_instance.parent_ac.split_set.exists():
            raise exceptions.SingleAccountIsNotParentError(
                    'single account cannot be a parent')


class Transaction(models.Model):
    description = models.TextField(blank=True, default='')

    def __str__(self):
        string = f'{self.pk}->{self.split_set.count()}'
        return string


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

    def __str__(self):
        string = (f'{self.transaction.pk}->{self.type_split}={self.amount}')
        return string


@receiver(signals.pre_save, sender=Split)
def raise_exceptions_split(sender, **kwargs):
    sp_instance = kwargs['instance']
    if (sp_instance.account.who_am_i())['parent']:
        raise exceptions.TransactionOnParentAcError(
                'transaction on parent not allowed')
    if sp_instance.amount <= 0:
        raise exceptions.ZeroAmountError('amount must be greater than 0')
