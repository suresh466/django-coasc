from django.test import TestCase
# from django.db import transaction as db_transaction

from accounts.models import ImpersonalAccount
from accounts import exceptions
from journals.models import Transaction, Split


class AccountModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.single_ac1 = ImpersonalAccount.objects.create(
                name='single ac1', type_ac='AS', code='1')
        cls.parent_ac1 = ImpersonalAccount.objects.create(
                name='parent ac1', type_ac='LI', code='2')
        cls.child_ac1 = ImpersonalAccount.objects.create(
                name='child ac1', parent_ac=cls.parent_ac1, code='2.1')

        cls.transaction1 = Transaction.objects.create(
                description='transaction1')

    def test_create_and_retreive_accounts(self):
        saved_accounts = ImpersonalAccount.objects.all()

        self.assertEqual(saved_accounts.count(), 3)
        self.assertEqual(saved_accounts[0].name, 'single ac1')
        self.assertEqual(saved_accounts[0].parent_ac, None)
        self.assertEqual(saved_accounts[0].type_ac, 'AS')
        self.assertEqual(saved_accounts[0].code, '1')

        self.assertEqual(saved_accounts[1].name, 'parent ac1')
        self.assertEqual(saved_accounts[1].parent_ac, None)
        self.assertEqual(saved_accounts[1].type_ac, 'LI')
        self.assertEqual(saved_accounts[1].code, '2')

        self.assertEqual(saved_accounts[2].name, 'child ac1')
        self.assertEqual(saved_accounts[2].parent_ac, self.parent_ac1)
        self.assertEqual(saved_accounts[2].type_ac, 'LI')
        self.assertEqual(saved_accounts[2].code, '2.1')

    def test_raises_exception_if_type_ac_set_manually_on_child_ac(self):
        with self.assertRaises(exceptions.AccountTypeOnChildAccountError):
            ImpersonalAccount.objects.create(
                    name='child ac2', parent_ac=self.parent_ac1, type_ac='LI',
                    code='2.2')

    def test_raises_exception_if_root_ac_selected_as_a_split_ac(self):
        Split.objects.create(
                transaction=self.transaction1, account=self.single_ac1,
                type_split='dr', amount=100)

        with self.assertRaises(exceptions.TransactionOnParentAcError):
            Split.objects.create(
                    transaction=self.transaction1, account=self.parent_ac1,
                    type_split='cr', amount=100)
