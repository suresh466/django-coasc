from django.db import models


class ImpersonalAccount(models.Model):
    name = models.CharField(max_length=255)
    parent_ac = models.ForeignKey(
            'self', null=True, default=None, on_delete=models.DO_NOTHING)
    type_ac = models.CharField(max_length=2)
    code = models.CharField(max_length=256)

    def has_child(self):
        if self.impersonalaccount_set.count() > 0:
            return True
        else:
            return False
