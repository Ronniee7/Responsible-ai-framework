from django.urls import path

from monitoring.settings_views import SettingsView

urlpatterns = [
    path("", SettingsView.as_view(), name="settings"),
]