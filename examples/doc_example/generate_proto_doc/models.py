import uuid

from django.db import models
from django.utils.translation import gettext as _


class Something(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    start_date = models.DateField(verbose_name=_("Start Date"))
    rate = models.CharField(max_length=255, null=True, blank=True, verbose_name=_("Rate"))

    class Meta:
        verbose_name_plural = _("Somethings")
        verbose_name = _("Something")
