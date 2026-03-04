import uuid

from django.db import models
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from common.utils import Base62


class UIDMixin(models.Model):
    """Adds a UUID field for external identification (public API, integrations)."""

    uid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
        verbose_name=_("Unique identifier"),
    )

    class Meta:
        abstract = True


class TimestampMixin(models.Model):
    """Adds created_at / updated_at timestamps."""

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date and time of creation"),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date and time of last update"),
    )

    class Meta:
        abstract = True
        ordering = ("-created_at", "-id")


class RankMixin(models.Model):
    """Adds a rank field for manual ordering (lower value = appears first)."""

    rank = models.PositiveIntegerField(
        _("Rank"),
        default=100,
        db_index=True,
        help_text=_("Lower appears first; use to control display order."),
    )

    class Meta:
        abstract = True
        ordering = ("rank",)


class BaseModel(UIDMixin, TimestampMixin, RankMixin):
    """
    Full-featured abstract base model.

    Combines: UIDMixin + TimestampMixin + RankMixin.
    Use individual mixins when you don't need all fields.
    """

    class Meta(UIDMixin.Meta, TimestampMixin.Meta, RankMixin.Meta):
        abstract = True
        ordering = ("rank", "-created_at", "-id")

    def __str__(self):
        model_name = self.__class__.__name__
        display = getattr(self, "name", None) or getattr(self, "title", None)
        if display:
            return f"{model_name} [{display}] (id={self.id})"
        return f"{model_name} (id={self.id}, uid={self.uid})"

    def get_admin_url(self):
        """Returns an HTML link to the object's admin change/add page."""
        app_label = self._meta.app_label
        model_name = self._meta.model_name
        if self.pk:
            url = reverse(f"admin:{app_label}_{model_name}_change", args=[self.pk])
            return format_html('<a href="{}" target="_blank">{}</a>', url, self)
        url = reverse(f"admin:{app_label}_{model_name}_add")
        return format_html('<a href="{}" target="_blank">+</a>', url)

    @property
    def short_id(self) -> str:
        """Возвращает id объекта в виде base62-строки."""
        return Base62.encode(self.pk)

    @classmethod
    def get_by_short_id(cls, token: str):
        """
        Возвращает объект по base62-токен или None, если токен невалиден
        либо объект не найден.

        Пример::

            news = News.get_by_short_id(token)
            if news is None:
                raise Http404
        """
        try:
            pk = Base62.decode(token)
        except (ValueError, TypeError):
            return None
        return cls._default_manager.filter(pk=pk).first()
