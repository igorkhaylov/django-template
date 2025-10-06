import uuid

from django.db import models
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _


class BaseModel(models.Model):
    """
    Base Model
    """

    uid = models.UUIDField(
        editable=False,
        unique=True,
        verbose_name=_("Unique identifier"),
        db_index=True,
        default=uuid.uuid4,
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date and time of creation")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date and time of last update")
    )

    class Meta:
        abstract = True
        ordering = ("-created_at", "-id")

    def get_admin_url(self):
        """Генерирует ссылку для открытия страницы редактирования объекта в Django Admin"""
        opts = self._meta
        app_label = opts.app_label
        model_name = opts.model_name

        if self.pk:
            url = reverse(f"admin:{app_label}_{model_name}_change", args=[self.pk])
            return format_html('<a href="{}" target="_blank">Открыть объект</a>', url)
        else:
            url = reverse(f"admin:{app_label}_{model_name}_add")
            return format_html('<a href="{}" target="_blank">Создать объект</a>', url)
