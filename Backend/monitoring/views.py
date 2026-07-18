from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from monitoring.services import DashboardService


class DashboardSummaryView(APIView):
    """Return a high-level summary of system metrics."""

    @extend_schema(
        responses={200: dict},
        description="Return aggregated dashboard summary metrics.",
    )
    def get(self, request, *args, **kwargs):
        summary = DashboardService.get_summary()
        return Response(summary, status=status.HTTP_200_OK)


class DashboardAnalyticsView(APIView):
    """Return detailed analytics data for charts and visualizations."""

    @extend_schema(
        responses={200: dict},
        description="Return detailed analytics data for charts.",
    )
    def get(self, request, *args, **kwargs):
        analytics = DashboardService.get_analytics()
        return Response(analytics, status=status.HTTP_200_OK)