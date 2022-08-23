from django.test import TestCase

from coasc.models import ImpersonalAccount
from coasc import exceptions
from coasc.models import Transaction, Split


class AccountModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.single = ImpersonalAccount.objects.create(
                name='single', t_ac='AS', code='1')
        cls.parent = ImpersonalAccount.objects.create(
                name='parent', t_ac='LI', code='2')
        cls.child = ImpersonalAccount.objects.create(
                name='child', p_ac=cls.parent, code='2.1')
        cls.child1 = ImpersonalAccount.objects.create(
                name='child1', p_ac=cls.parent, code='2.2')

        cls.tx = Transaction.objects.create(description='tx')

    def test_create_and_retreive(self):
        saved_accounts = ImpersonalAccount.objects.all()

        self.assertEqual(saved_accounts.count(), 4)
        self.assertEqual(saved_accounts[0].name, 'single')
        self.assertEqual(saved_accounts[0].p_ac, None)
        self.assertEqual(saved_accounts[0].t_ac, 'AS')
        self.assertEqual(saved_accounts[0].code, '1')

        self.assertEqual(saved_accounts[1].name, 'parent')
        self.assertEqual(saved_accounts[1].p_ac, None)
        self.assertEqual(saved_accounts[1].t_ac, 'LI')
        self.assertEqual(saved_accounts[1].code, '2')

        self.assertEqual(saved_accounts[2].name, 'child')
        self.assertEqual(saved_accounts[2].p_ac, self.parent)
        self.assertEqual(saved_accounts[2].code, '2.1')

    def test_raises_exception_if_t_ac_set_on_child(self):
        with self.assertRaises(exceptions.AccountTypeOnChildAccountError):
            ImpersonalAccount.objects.create(
                    name='child ac2', p_ac=self.parent, t_ac='LI',
                    code='2.2')

    def test_raises_exception_if_p_ac_selected_as_a_split_ac(self):
        Split.objects.create(
                transaction=self.tx, account=self.single,
                type_split='dr', amount=100)

        with self.assertRaises(exceptions.TransactionOnParentAcError):
            Split.objects.create(
                    transaction=self.tx, account=self.parent,
                    type_split='cr', amount=100)

    def test_who_am_i(self):
        ac_is = self.single.who_am_i()
        ac1_is = self.parent.who_am_i()
        ac2_is = self.child.who_am_i()

        self.assertTrue(ac_is['single'])
        self.assertTrue(ac1_is['parent'])
        self.assertTrue(ac2_is['child'])

        self.assertTrue(not ac_is['parent'])
        self.assertTrue(not ac1_is['child'])
        self.assertTrue(not ac2_is['single'])

    def test_bal(self):
        Split.objects.create(
                transaction=self.tx, account=self.single,
                type_split='dr', amount=100)
        Split.objects.create(
                transaction=self.tx, account=self.single,
                type_split='cr', amount=50)
        Split.objects.create(
                transaction=self.tx, account=self.child,
                type_split='dr', amount=200)
        Split.objects.create(
                transaction=self.tx, account=self.child,
                type_split='cr', amount=150)
        Split.objects.create(
                transaction=self.tx, account=self.child1,
                type_split='dr', amount=300)
        Split.objects.create(
                transaction=self.tx, account=self.child1,
                type_split='cr', amount=250)

        single_bal = self.single.bal()
        child_bal = self.child.bal()
        child1_bal = self.child1.bal()
        parent_bal = self.parent.bal()

        self.assertEqual(single_bal['dr_sum'], 100)
        self.assertEqual(single_bal['cr_sum'], 50)
        self.assertEqual(child_bal['dr_sum'], 200)
        self.assertEqual(child_bal['cr_sum'], 150)
        self.assertEqual(child1_bal['dr_sum'], 300)
        self.assertEqual(child1_bal['cr_sum'], 250)
        self.assertEqual(parent_bal['dr_sum'], 500)
        self.assertEqual(parent_bal['cr_sum'], 400)

    def test_total_bal_with_no_arguments(self):
        Split.objects.create(
                transaction=self.tx, account=self.single,
                type_split='dr', amount=100)
        Split.objects.create(
                transaction=self.tx, account=self.single,
                type_split='cr', amount=50)
        Split.objects.create(
                transaction=self.tx, account=self.child,
                type_split='dr', amount=200)
        Split.objects.create(
                transaction=self.tx, account=self.child,
                type_split='cr', amount=150)
        Split.objects.create(
                transaction=self.tx, account=self.child1,
                type_split='dr', amount=300)
        Split.objects.create(
                transaction=self.tx, account=self.child1,
                type_split='cr', amount=250)

        total_dr_sum = ImpersonalAccount.total_bal()[
                'total_dr_sum']
        total_cr_sum = ImpersonalAccount.total_bal()[
                'total_cr_sum']

        self.assertEqual(total_dr_sum, 600)
        self.assertEqual(total_cr_sum, 450)

    def test_total_bal_with_arguments(self):
        Split.objects.create(
                transaction=self.tx, account=self.single,
                type_split='dr', amount=100)
        Split.objects.create(
                transaction=self.tx, account=self.single,
                type_split='cr', amount=50)
        Split.objects.create(
                transaction=self.tx, account=self.child,
                type_split='dr', amount=200)
        Split.objects.create(
                transaction=self.tx, account=self.child,
                type_split='cr', amount=150)
        Split.objects.create(
                transaction=self.tx, account=self.child1,
                type_split='dr', amount=300)
        Split.objects.create(
                transaction=self.tx, account=self.child1,
                type_split='cr', amount=450)

        total_bal = ImpersonalAccount.total_bal(
                t_ac='AS')
        total_bal1 = ImpersonalAccount.total_bal(
                t_ac='LI')

        expected_total_bal = {
                'total_dr_sum': 100,
                'total_cr_sum': 50,
                'diff': 50
        }
        expected_total_bal1 = {
                'total_dr_sum': 500,
                'total_cr_sum': 600,
                'diff': -100
        }

        self.assertEqual(total_bal, expected_total_bal)
        self.assertEqual(total_bal1, expected_total_bal1)

    def test_validate_accounting_equation(self):
        with self.assertRaises(
                exceptions.AccountingEquationViolationError):
            Split.objects.create(
                    transaction=self.tx, account=self.single,
                    type_split='dr', amount=100)
            Split.objects.create(
                    transaction=self.tx, account=self.child,
                    type_split='cr', amount=50)
            ImpersonalAccount.validate_accounting_equation()

    def test_raises_exception_if_ac_has_no_parent_and_type_ac(self):
        with self.assertRaises(exceptions.OrphanAccountCreationError):
            ImpersonalAccount.objects.create(name='orphan', code='0')

    def test_raises_exception_if_single_ac_selected_as_parent(self):
        single = ImpersonalAccount.objects.create(
                name='single', code='3', t_ac='AS')
        tx = Transaction.objects.create(description='demo')
        Split.objects.create(
                account=single, type_split='dr', amount=1, transaction=tx)

        with self.assertRaises(exceptions.SingleAccountIsNotParentError):
            ImpersonalAccount.objects.create(
                    name='child', code='3.1', p_ac=single)


class TransactionAndSplitModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.single_ac1 = ImpersonalAccount.objects.create(
                name='single_ac11', t_ac='AS', code='1')
        cls.parent_ac1 = ImpersonalAccount.objects.create(
                name='parent_ac1', t_ac='LI', code='2')
        cls.child_ac1 = ImpersonalAccount.objects.create(
                name='child_ac1', p_ac=cls.parent_ac1, code='2.1')

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
        Split.objects.create(
                transaction=self.transaction1, account=self.single_ac1,
                type_split='dr', amount=100)
        with self.assertRaises(exceptions.ZeroAmountError):
            Split.objects.create(
                    transaction=self.transaction1, account=self.child_ac1,
                    type_split='cr', amount=0)
