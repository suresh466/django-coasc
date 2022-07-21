from django.test import TestCase
# from django.db import transaction as db_transaction

from accounts.models import ImpersonalAccount
from accounts import exceptions
from journals.models import Transaction, Split


class AccountModelTest(TestCase):

    def test_create_and_retreive_accounts(self):
        parent_ac = ImpersonalAccount.objects.create(
                name='Kosh', type_ac='LI', code='20',)
        ImpersonalAccount.objects.create(
                name='Jageda kosh', parent_ac=parent_ac, code='20.1',)

        saved_accounts = ImpersonalAccount.objects.all()

        self.assertEqual(saved_accounts.count(), 2)
        self.assertEqual(saved_accounts[0].name, 'Kosh')
        self.assertEqual(saved_accounts[0].parent_ac, None)
        self.assertEqual(saved_accounts[0].type_ac, 'LI')
        self.assertEqual(saved_accounts[0].code, '20')

        self.assertEqual(saved_accounts[1].name, 'Jageda kosh')
        self.assertEqual(saved_accounts[1].parent_ac, parent_ac)
        self.assertEqual(saved_accounts[1].type_ac, 'LI')
        self.assertEqual(saved_accounts[1].code, '20.1')

    def test_raises_exception_if_type_ac_set_manually_on_child_ac(self):
        parent_ac = ImpersonalAccount.objects.create(
             name='Kosh', type_ac='LI', code='20',)
        with self.assertRaises(exceptions.AccountTypeOnChildAccountError):
            ImpersonalAccount.objects.create(
                    name='Jageda kosh', parent_ac=parent_ac, type_ac='LI',
                    code='20.1',)

    def test_raises_exception_if_root_ac_selected_as_a_split_ac(self):
        single_ac = ImpersonalAccount.objects.create(
                name='Single ac', type_ac='LI', code='40')
        parent_ac = ImpersonalAccount.objects.create(
                name='Parent ac', type_ac='AS', code='30')
        ImpersonalAccount.objects.create(
                name='child ac', parent_ac=parent_ac, code='30')
        transaction = Transaction.objects.create()
        Split.objects.create(
                transaction=transaction, account=single_ac,
                type_split='dr', amount=100)

        with self.assertRaises(exceptions.TransactionOnParentAcError):
            Split.objects.create(
                    transaction=transaction, account=parent_ac,
                    type_split='cr', amount=100)
