from decimal import Decimal

from django.db import models
from django.db.models import Sum

from accounts import exceptions


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

    def save(self, *args, **kwargs):
        if self.parent_ac and self.type_ac:
            raise exceptions.AccountTypeOnChildAccountError
        if self.parent_ac:
            self.type_ac = self.parent_ac.type_ac
        super(ImpersonalAccount, self).save(*args, **kwargs)

    def __simple_balance(self):
        account_splits = self.split_set.all()
        dr_splits = account_splits.filter(type_split='dr')
        cr_splits = account_splits.filter(type_split='cr')
        dr_sum = dr_splits.aggregate(
                dr_sum=Sum('amount'))['dr_sum'] or Decimal(0)
        cr_sum = cr_splits.aggregate(
                cr_sum=Sum('amount'))['cr_sum'] or Decimal(0)
        return {'dr_sum': dr_sum, 'cr_sum': cr_sum}

    def __accumulated_balance(self):
        dr_sum = Decimal(0)
        cr_sum = Decimal(0)
        for account in self.impersonalaccount_set.all():
            account_splits = account.split_set.all()
            dr_splits = account_splits.filter(type_split='dr')
            cr_splits = account_splits.filter(type_split='cr')
            dr_sum += dr_splits.aggregate(
                    dr_sum=Sum('amount'))['dr_sum'] or Decimal(0)
            cr_sum += cr_splits.aggregate(
                    cr_sum=Sum('amount'))['cr_sum'] or Decimal(0)
        return {'dr_sum': dr_sum, 'cr_sum': cr_sum}

    def who_am_i(self):
        ac = dict.fromkeys(['parent', 'child', 'single'], None)
        if self.impersonalaccount_set.count() > 0:
            ac['parent'] = True
            return ac
        if self.parent_ac:
            ac['child'] = True
            return ac
        if self.impersonalaccount_set.count() == 0 and not self.parent_ac:
            ac['single'] = True
            return ac

    def current_balance(self):
        ac = self.who_am_i()
        if ac['parent']:
            return self.__accumulated_balance()
        if ac['single'] or ac['child']:
            return self.__simple_balance()

    @staticmethod
    def total_current_balance():
        accounts = ImpersonalAccount.objects.all()
        total_dr_sum = Decimal(0)
        total_cr_sum = Decimal(0)
        for account in accounts:
            ac = account.who_am_i()
            if ac['child']:
                continue
            balances = account.current_balance()
            total_dr_sum += balances['dr_sum']
            total_cr_sum += balances['cr_sum']
        return {'total_dr_sum': total_dr_sum, 'total_cr_sum': total_cr_sum}

    @classmethod
    def validate_accounting_equation(cls):
        total_balances = cls.total_current_balance()
        total_dr_sum = total_balances['total_dr_sum']
        total_cr_sum = total_balances['total_cr_sum']
        if total_dr_sum != total_cr_sum:
            raise exceptions.AccountingEquationViolationError
