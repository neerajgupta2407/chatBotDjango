from django.urls import path

from . import views

urlpatterns = [
    path("upload", views.FileUploadView.as_view(), name="file-upload"),
    path("info/<uuid:session_id>", views.FileInfoView.as_view(), name="file-info"),
    path("query/<uuid:session_id>", views.FileQueryView.as_view(), name="file-query"),
    path("<uuid:session_id>", views.FileDeleteView.as_view(), name="file-delete"),
]
