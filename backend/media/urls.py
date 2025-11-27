from django.urls import path
from media.api.views.file_view import FileUploadInitView, FileUploadConfirmView, CleanupStagingFilesView, PublicDownloadFileView

urlpatterns = [
    # Public
    path('upload/init/', FileUploadInitView.as_view(), name='file-upload'),
    path('upload/confirm/<uuid:file_id>/', FileUploadConfirmView.as_view(), name='file-upload-confirm'), 
    path('files/<uuid:file_id>/', PublicDownloadFileView.as_view(), name='file-download'),


    # Admin
    path('admin/cleanup/', CleanupStagingFilesView.as_view(), name='admin-cleanup-files'),
    # path('admin/files/', ListAllFilesView.as_view(), name='admin-list-files'),
    # path('admin/files/<uuid:file_id>/', FileDetailView.as_view(), name='admin-file-detail'),
]