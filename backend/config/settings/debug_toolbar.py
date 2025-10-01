from .installed_apps import INSTALLED_APPS
from .middleware import MIDDLEWARE

__all__ = (
    "INSTALLED_APPS",
    "MIDDLEWARE",
    "DEBUG_TOOLBAR_CONFIG",
    "DEBUG_TOOLBAR_PANELS",
)

INSTALLED_APPS = [
    *INSTALLED_APPS,
    "debug_toolbar",
]
MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    *MIDDLEWARE,
]
DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda request: True,
    # "SHOW_TOOLBAR_CALLBACK": "debug_toolbar.middleware.show_toolbar_with_docker",
}
DEBUG_TOOLBAR_PANELS = [
    "debug_toolbar.panels.history.HistoryPanel",
    "debug_toolbar.panels.versions.VersionsPanel",
    "debug_toolbar.panels.timer.TimerPanel",
    "debug_toolbar.panels.settings.SettingsPanel",
    "debug_toolbar.panels.headers.HeadersPanel",
    "debug_toolbar.panels.request.RequestPanel",
    "debug_toolbar.panels.sql.SQLPanel",
    "debug_toolbar.panels.staticfiles.StaticFilesPanel",
    "debug_toolbar.panels.templates.TemplatesPanel",
    # "debug_toolbar.panels.alerts.AlertsPanel",
    "debug_toolbar.panels.cache.CachePanel",
    "debug_toolbar.panels.signals.SignalsPanel",
    # "debug_toolbar.panels.community.CommunityPanel",
    "debug_toolbar.panels.redirects.RedirectsPanel",
    # "debug_toolbar.panels.profiling.ProfilingPanel",
]
