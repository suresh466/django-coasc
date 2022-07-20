from django.test import TestCase
from accounts.models import ImpersonalAccount


class AccountModelTest(TestCase):

    def test_create_and_retreive_accounts(self):
        parent_ac = ImpersonalAccount.objects.create(
                name='Kosh', type_ac='LI', code='20',)
        ImpersonalAccount.objects.create(
                name='Jageda kosh', parent_ac=parent_ac, type_ac='LI',
                code='20.1',)

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
