from decimal import Decimal

from django.db import models
from django.db.models import Case, F, Sum, When, signals
from django.db.models.query import Q
from django.dispatch import receiver
from django.utils import timezone

from coasc import exceptions


class Member(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255, unique=True)

    def __str__(self):
        string = f"{self.name}->{self.code}"
        return string


class Ac(models.Model):
    ASSET = "AS"
    LIABILITY = "LI"
    INCOME = "IN"
    EXPENSES = "EX"

    CATEGORY_CHOICES = [
        (ASSET, "Asset"),
        (LIABILITY, "Liability"),
        (INCOME, "Income"),
        (EXPENSES, "Expense"),
    ]

    PERSONAL = "P"
    IMPERSONAL = "I"

    TYPE_AC_CHOICES = [
        (PERSONAL, "Personal"),
        (IMPERSONAL, "Impersonal"),
    ]

    name = models.CharField(max_length=255)
    t_ac = models.CharField(max_length=1, choices=TYPE_AC_CHOICES)
    p_ac = models.ForeignKey(
        "self", null=True, blank=True, default=None, on_delete=models.PROTECT
    )
    cat = models.CharField(max_length=2, blank=True, choices=CATEGORY_CHOICES)
    mem = models.ForeignKey(
        Member, null=True, blank=True, default=None, on_delete=models.PROTECT
    )
    code = models.CharField(
        max_length=255, blank=True, null=True, default=None, unique=True
    )

    def __str__(self):
        string = f"{self.name} ({self.code})"
        return string

    @property
    def is_root(self):
        return self.cat is not None and self.p_ac is None

    @property
    def is_parent(self):
        return self.is_root and self.ac_set.exists()

    @property
    def is_child(self):
        return self.p_ac is not None and self.cat is None

    # A root but not a parent and not a child, with splits
    @property
    def is_standalone(self):
        return self.is_root and not self.is_parent and self.split_set.exists()

    def who_am_i(self):
        ac_is = dict.fromkeys(["parent", "child", "single"], None)
        if not self.cat:
            ac_is["child"] = True
            return ac_is
        elif self.ac_set.exists():
            ac_is["parent"] = True
            return ac_is
        elif self.cat and not self.ac_set.exists():
            ac_is["single"] = True
            return ac_is
        else:
            return "Something went wrong! Maybe this account should not exist"

    def bal(self, start_date=None, end_date=None):
        if self.who_am_i()["parent"]:
            sps = Split.objects.filter(ac__p_ac=self)
        else:
            sps = self.split_set.all()

        if start_date:
            sps = sps.filter(tx__tx_date__gte=start_date)
        if end_date:
            sps = sps.filter(tx__tx_date__lte=end_date)

        balances = sps.aggregate(
            total_debit=Sum(
                Case(
                    When(t_sp="dr", then=F("am")),
                )
            ),
            total_credit=Sum(
                Case(
                    When(t_sp="cr", then=F("am")),
                )
            ),
        )

        total_debit = balances["total_debit"] or Decimal(0)
        total_credit = balances["total_credit"] or Decimal(0)

        # handle child don't have category (TODO: rethink if child should have category too for consistency)
        ac_cat = self.p_ac.cat if self.who_am_i()["child"] else self.cat

        if ac_cat in [self.ASSET, self.EXPENSES]:
            net_balance = total_debit - total_credit
            net_debit = max(net_balance, Decimal(0))
            net_credit = max(-net_balance, Decimal(0))
        elif ac_cat in [self.LIABILITY, self.INCOME]:
            net_balance = total_credit - total_debit
            net_debit = max(-net_balance, Decimal(0))
            net_credit = max(net_balance, Decimal(0))

        return {
            "net_balance": net_balance,
            "net_debit": net_debit,
            "net_credit": net_credit,
            "total_debit": total_debit,
            "total_credit": total_credit,
        }

    @classmethod
    def get_flat_balances(cls, cat=None, start_date=None, end_date=None):
        top_level_accounts = cls.objects.filter(p_ac__isnull=True)
        if cat:
            top_level_accounts = top_level_accounts.filter(cat=cat)

        return [
            {"account": account, "balance": account.bal(start_date, end_date)}
            for account in top_level_accounts
        ]

    @classmethod
    def get_hierarchical_balances(cls, cat=None, start_date=None, end_date=None):
        top_level_accounts = cls.objects.filter(p_ac__isnull=True)
        if cat:
            top_level_accounts = top_level_accounts.filter(cat=cat)

        result = [
            {
                "account": account,
                "balance": account.bal(start_date, end_date),
                "children": [
                    {"account": child, "balance": child.bal(start_date, end_date)}
                    for child in account.ac_set.all()
                ],
            }
            for account in top_level_accounts
        ]

        return result

    @classmethod
    def validate_accounting_equation(cls):
        total_balance = Split.objects.aggregate(
            total_debit=Sum("am", filter=models.Q(t_sp="dr")),
            total_credit=Sum("am", filter=models.Q(t_sp="cr")),
        )

        total_debit = total_balance["total_debit"] or Decimal("0")
        total_credit = total_balance["total_credit"] or Decimal("0")
        difference = total_debit - total_credit

        if difference != Decimal("0"):
            raise exceptions.AccountingEquationViolationError(
                f"Accounting equation violation. Difference between debits and credits: {difference}"
            )

        return True


@receiver(signals.pre_save, sender=Ac)
def raise_exceptions_ac(sender, **kwargs):
    ac_instance = kwargs["instance"]
    if not ac_instance.p_ac and not ac_instance.cat:
        raise exceptions.OrphanAccountCreationError("must have a parent or category")

    if ac_instance.p_ac:
        if ac_instance.cat:
            raise exceptions.AccountTypeOnChildAccountError(
                "category on a child not allowed"
            )

        elif ac_instance.p_ac.split_set.exists():
            raise exceptions.SingleAccountIsNotParentError(
                "single account cannot be a parent"
            )

    if ac_instance.t_ac == "P":
        if ac_instance.mem is None:
            raise exceptions.MemberRequiredOnPersonalAcError(
                "Personal Ac must have a member"
            )

    if ac_instance.t_ac == "I":
        if ac_instance.mem:
            raise exceptions.MemberOnImpersonalAcError(
                "Impersonal Ac cannot have a member"
            )


class Transaction(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    tx_date = models.DateField(default=timezone.now)
    desc = models.TextField(blank=True, default="")

    def __str__(self):
        string = f"{self.pk}->{self.split_set.count()}"
        return string

    def validate_transaction(self):
        # None is returned if no splits are found
        split_sums = self.split_set.aggregate(
            total_debit=Sum("am", filter=Q(t_sp="dr")),
            total_credit=Sum("am", filter=Q(t_sp="cr")),
        )

        total_debit = split_sums["total_debit"]
        total_credit = split_sums["total_credit"]

        if total_debit is None and total_credit is None:
            raise exceptions.EmptyTransactionError(
                "Transaction must have at least one split each for debit and credit"
            )

        # this also handles when only one type of split is present
        if total_debit != total_credit:
            raise exceptions.UnbalancedTransactionError(
                f"Transaction is not balanced. Debit: {total_debit}, Credit: {total_credit}"
            )

        return True


class Split(models.Model):
    DEBIT = "dr"
    CREDIT = "cr"
    TYPE_SPLIT_CHOICES = [
        (DEBIT, "Debit"),
        (CREDIT, "Credit"),
    ]
    tx = models.ForeignKey(Transaction, on_delete=models.PROTECT)
    ac = models.ForeignKey(Ac, on_delete=models.PROTECT)
    t_sp = models.CharField(max_length=2, choices=TYPE_SPLIT_CHOICES)
    am = models.DecimalField(decimal_places=2, max_digits=11)

    def __str__(self):
        string = f"{self.tx.pk}->{self.t_sp}={self.am}"
        return string


@receiver(signals.pre_save, sender=Split)
def raise_exceptions_split(sender, **kwargs):
    sp_instance = kwargs["instance"]
    if (sp_instance.ac.who_am_i())["parent"]:
        raise exceptions.TransactionOnParentAcError("transaction on parent not allowed")
