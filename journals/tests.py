from django.test import TestCase
from django.db import transaction as db_transaction

from journals.models import Split, Transaction
from journals import exceptions
from accounts.models import ImpersonalAccount


class TransactionAndSplitModelTest(TestCase):
    def create_impersonal_account(self, name, type_ac, code, parent_ac=None):
        return ImpersonalAccount.objects.create(
            name=name, code=code, type_ac=type_ac, parent_ac=parent_ac)

    def create_transaction(self, description=''):
        return Transaction.objects.create(description=description)

    def create_split(self, transaction, account, type_split, amount):
        return Split.objects.create(
                transaction=transaction, account=account,
                type_split=type_split, amount=amount)

    def test_create_and_retreive_splits(self):
        transaction = self.create_transaction(description='')
        ac_1 = self.create_impersonal_account('Share pujji', 'LI', '10')
        ac_2 = self.create_impersonal_account('Nagad hissab', 'AS', '80')

        self.create_split(transaction, ac_2, 'dr', 1000)
        self.create_split(transaction, ac_1, 'cr', 1000)

        saved_split = Split.objects.all()

        self.assertEqual(saved_split.count(), 2)
        self.assertEqual(saved_split[0].account, ac_2)
        self.assertEqual(saved_split[0].type_split, 'dr')
        self.assertEqual(saved_split[0].amount, 1000)

        self.assertEqual(saved_split[1].account, ac_1)
        self.assertEqual(saved_split[1].type_split, 'cr')
        self.assertEqual(saved_split[1].amount, 1000)

    def test_create_and_retreive_transactions(self):
        self.create_transaction('first description')
        self.create_transaction('')
        self.create_transaction()

        saved_transactions = Transaction.objects.all()

        self.assertEqual(saved_transactions.count(), 3)
        self.assertEqual(
                saved_transactions[0].description, 'first description')
        self.assertEqual(saved_transactions[1].description, '')
        self.assertEqual(saved_transactions[2].description, '')

    def test_create_and_retreive_transaction_with_splits(self):
        ac_1 = self.create_impersonal_account('Share pujji', 'LI', '10')
        ac_2 = self.create_impersonal_account('Nagad hissab', 'AS', '80')
        transaction = Transaction.objects.create(
                description='first description')

        split_1 = self.create_split(
                transaction=transaction, account=ac_2, type_split='dr',
                amount=2000)
        split_2 = self.create_split(
                transaction=transaction, account=ac_1, type_split='cr',
                amount=2000)

        saved_transaction = Transaction.objects.all()
        split_sets = saved_transaction[0].split_set.all()

        self.assertEqual(saved_transaction.count(), 1)
        self.assertEqual(
                saved_transaction[0].description, 'first description')
        self.assertEqual(split_sets[0], split_1)
        self.assertEqual(split_sets[1], split_2)

    def test_raises_exception_if_split_amount_zero(self):
        ac_1 = self.create_impersonal_account('Share pujji', 'LI', '10')
        ac_2 = self.create_impersonal_account('Nagad hissab', 'AS', '80')
        transaction = Transaction(description='first description')
        split_1 = Split(account=ac_2, type_split='dr', amount=3000)
        split_2 = Split(account=ac_1, type_split='cr', amount=0)

        with self.assertRaises(exceptions.ZeroAmountError):
            with db_transaction.atomic():
                transaction.save()
                split_1.transaction = transaction
                split_2.transaction = transaction
                split_1.save()
                split_2.save()

    def test_raises_exception_if_transaction_unbalanced(self):
        pass

    def test_transaction_not_saved_for_root_account(self):
        pass
