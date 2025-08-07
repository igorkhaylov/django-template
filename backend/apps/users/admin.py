from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as AuthUserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import User


@admin.register(User)
class UserAdmin(AuthUserAdmin):
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            _("Personal info2"),
            {
                "fields": (
                    "name",
                    "date_of_birth",
                    "gender",
                    ("picture", "picture_preview"),
                )
            },
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "password1", "password2"),
            },
        ),
    )
    list_display = (
        "username",
        "is_active",
        "is_staff",
        "is_superuser",
        "last_login",
        "date_joined",
    )
    list_filter = ("is_active", "is_staff", "is_superuser", "groups")
    search_fields = ("username", "name")
    readonly_fields = ("picture_preview",)
    save_on_top = True

    @admin.display(description=_("Превью"), ordering="picture")
    def picture_preview(self, obj):
        if obj.picture:
            return format_html('<img src="{}" height="200" />', obj.picture.small.url)
        return "No Image"


class LogEntryUserFilter(admin.SimpleListFilter):
    title = "Пользователь"
    parameter_name = "logentry_user"

    def lookups(self, request, model_admin):
        out = []
        # # sqlite3
        # for i in admin.models.LogEntry.objects.values(
        #     "user_id", "user__username"
        # ).distinct():
        #     out += [(f"{i['user_id']}", f"{i['user__username']}")]
        # postgres
        for i in (
            admin.models.LogEntry.objects.all().order_by("user_id").distinct("user_id")
        ):
            out += [(f"{i.user_id}", f"{i.user.username}")]
        return out

    def queryset(self, request, queryset):
        value = self.value()
        if value is None:
            return queryset
        return queryset.filter(user_id=int(value))


@admin.register(admin.models.LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = (
        "__str__",
        "action_flag",
        "content_type",
        "object_id",
        "user",
        "action_time",
    )
    list_filter = (
        LogEntryUserFilter,
        "action_flag",
        "content_type",
    )

    has_add_permission = lambda self, request: False
    has_change_permission = lambda self, request, obj=None: False
    has_delete_permission = lambda self, request, obj=None: False
    # has_view_permission = lambda self, request, obj=None: request.user.is_superuser
