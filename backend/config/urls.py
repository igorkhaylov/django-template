from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.utils.translation import gettext_lazy as _
from redirector.views import redirector

APP_NAME = "Redirector"


admin.site.site_title = _("%(app_name)s site admin") % {"app_name": APP_NAME}
admin.site.site_header = _("%(app_name)s administration") % {"app_name": APP_NAME}
admin.site.index_title = _("Site administration")
admin.site.enable_nav_sidebar = True
admin.site.empty_value_display = "-"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("rosetta/", include("rosetta.urls")),
]


urlpatterns += i18n_patterns()

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
