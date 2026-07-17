from django.urls import include, path

urlpatterns = [
    path("chat/", include("chat.urls")),
    path("documents/", include("rag.urls")),
]
