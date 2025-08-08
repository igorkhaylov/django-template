"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from django.utils.translation import gettext_lazy as _

APP_NAME = settings.APP_NAME

admin.site.site_title = _("%(app_name)s site admin") % {"app_name": APP_NAME}
admin.site.site_header = _("%(app_name)s administration") % {"app_name": APP_NAME}
admin.site.index_title = _("Site administration")
admin.site.enable_nav_sidebar = True
admin.site.empty_value_display = "-"

urlpatterns = [
    path(
        "healthcheck/",
        lambda request: JsonResponse({"status": "ok"}),
        name="healthcheck",
    ),
]

urlpatterns += i18n_patterns(
    path("admin/", admin.site.urls),
)


# if settings.DEBUG:
#     from django.conf.urls.static import static
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
#     urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
