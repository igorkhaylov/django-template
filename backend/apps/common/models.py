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
    rank = models.PositiveIntegerField(
        _("Rank"),
        default=100,
        help_text=_("Lower appears first; use to control display order."),
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date and time of creation")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date and time of last update")
    )

    class Meta:
        abstract = True
        ordering = ("rank", "-created_at", "-id")
        indexes = [
            models.Index(fields=["rank"]),
        ]

    def __str__(self):
        """
        Универсальное текстовое представление для всех моделей, наследующих BaseModel.
        Отображает имя модели и её идентификаторы.
        """
        model_name = self.__class__.__name__
        # Используем getattr, чтобы не вызывать ошибку, если у модели нет title / name и т.п.
        display_field = getattr(self, "name", None) or getattr(self, "title", None)
        if display_field:
            return f"{model_name} [{display_field}] (id={self.id})"
        return f"{model_name} (id={self.id}, uid={getattr(self, "uid", None)})"

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

    def get_absolute_url(self):
        """
        Возвращает абсолютный URL для публичного просмотра объекта.
        Может быть переопределён в дочерних моделях.
        """
        return reverse(
            f"{self._meta.app_label}:{self._meta.model_name}_detail", args=[self.pk]
        )
