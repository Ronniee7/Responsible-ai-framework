from django.urls import include, path

urlpatterns = [
    path("chat/", include("chat.urls")),
    path("documents/", include("rag.urls")),
    path("governance/", include("governance.urls")),
    path("dashboard/", include("monitoring.urls")),
    path("settings/", include("monitoring.settings_urls")),
]
