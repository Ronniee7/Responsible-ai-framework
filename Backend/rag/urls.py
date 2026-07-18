from django.urls import path

from rag.views import (
    DocumentDetailView,
    DocumentListView,
    DocumentReprocessView,
    DocumentSearchView,
    DocumentStatusView,
    DocumentUploadView,
)

urlpatterns = [
    path("upload/", DocumentUploadView.as_view(), name="document-upload"),
    path("", DocumentListView.as_view(), name="document-list"),
    path("search/", DocumentSearchView.as_view(), name="document-search"),
    path("<uuid:doc_id>/", DocumentDetailView.as_view(), name="document-detail"),
    path("<uuid:doc_id>/reprocess/", DocumentReprocessView.as_view(), name="document-reprocess"),
    path("<uuid:doc_id>/status/", DocumentStatusView.as_view(), name="document-status"),
]