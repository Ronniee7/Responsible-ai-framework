from django.urls import path

from monitoring.views import DashboardAnalyticsView, DashboardSummaryView

urlpatterns = [
    path("summary/", DashboardSummaryView.as_view(), name="dashboard-summary"),
    path("analytics/", DashboardAnalyticsView.as_view(), name="dashboard-analytics"),
]