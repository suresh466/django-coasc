from django.test import TestCase

from journals.models import Split, Transaction
from journals import exceptions as journal_exceptions
from accounts import exceptions as account_exceptions
from accounts.models import ImpersonalAccount


class TransactionAndSplitModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.single_ac1 = ImpersonalAccount.objects.create(
                name='single_ac11', type_ac='AS', code='1')
        cls.parent_ac1 = ImpersonalAccount.objects.create(
                name='parent_ac1', type_ac='LI', code='2')
        cls.child_ac1 = ImpersonalAccount.objects.create(
                name='child_ac1', parent_ac=cls.parent_ac1, code='2.1')

        cls.transaction1 = Transaction.objects.create(
            description='transaction1')

    def test_create_and_retreive_transactions(self):
        saved_transactions = Transaction.objects.all()

        self.assertEqual(saved_transactions.count(), 1)
        self.assertEqual(
                saved_transactions[0].description, 'transaction1')

    def test_create_and_retreive_splits(self):
        Split.objects.create(
                transaction=self.transaction1, account=self.single_ac1,
                type_split='dr', amount=100)
        Split.objects.create(
                transaction=self.transaction1, account=self.child_ac1,
                type_split='cr', amount=100)

        saved_split = Split.objects.all()

        self.assertEqual(saved_split.count(), 2)
        self.assertEqual(saved_split[0].account, self.single_ac1)
        self.assertEqual(saved_split[0].type_split, 'dr')
        self.assertEqual(saved_split[0].amount, 100)

        self.assertEqual(saved_split[1].account, self.child_ac1)
        self.assertEqual(saved_split[1].type_split, 'cr')
        self.assertEqual(saved_split[1].amount, 100)

    def test_raises_exception_if_split_amount_zero(self):
        with self.assertRaises(journal_exceptions.ZeroAmountError):
            Split.objects.create(
                    transaction=self.transaction1, account=self.single_ac1,
                    type_split='dr', amount=100)
            Split.objects.create(
                    transaction=self.transaction1, account=self.child_ac1,
                    type_split='cr', amount=0)

    def test_raises_exception_if_transaction_unbalanced(self):
        with self.assertRaises(
                account_exceptions.AccountingEquationViolationError):
            Split.objects.create(
                    transaction=self.transaction1, account=self.single_ac1,
                    type_split='dr', amount=100)
            Split.objects.create(
                    transaction=self.transaction1, account=self.child_ac1,
                    type_split='cr', amount=50)
            ImpersonalAccount.validate_accounting_equation()
