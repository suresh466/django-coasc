from django.test import TestCase
from accounts.models import ImpersonalAccount
from journals.models import Split

# Create your tests here.

class SplitModelTest(TestCase):

    def test_create_and_retreive_split(self):
        ac_1 = ImpersonalAccount.objects.create(
            name='Share pujji',
            type_ac='LI',
            code='10',
        )
        ac_2 = ImpersonalAccount.objects.create(
            name='Nagad hissab',
            type_ac='AS',
            code='80',
        )
        Split.objects.create(
            account=ac_2,
            type_split='dr',
            amount=15500,
        )
        Split.objects.create(
            account=ac_1,
            type_split='cr',
            amount=15500,
        )

        saved_split = Split.objects.all()

        self.assertEqual(saved_split.count(), 2)
        self.assertEqual(saved_split[0].account, ac_2)
        self.assertEqual(saved_split[0].type_split, 'dr')
        self.assertEqual(saved_split[0].amount, 15500)

        self.assertEqual(saved_split[1].account, ac_1)
        self.assertEqual(saved_split[1].type_split, 'cr')
        self.assertEqual(saved_split[1].amount, 15500)
