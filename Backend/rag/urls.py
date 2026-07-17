from django.urls import path

from rag.views import DocumentUploadView

urlpatterns = [
    path("upload/", DocumentUploadView.as_view(), name="document-upload"),
]
