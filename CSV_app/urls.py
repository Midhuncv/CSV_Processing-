from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from .views import (
    CSVUploadView, 
    CSVResultsView, 
    DataSearchView, 
    CalculationSummaryView
)

urlpatterns = [
    # Home/Upload page
    path('', CSVUploadView.as_view(), name='csv_upload'),
    
    # Results page
    path('results/', CSVResultsView.as_view(), name='csv_results'),
    
    # API Endpoints
    path('api/search/', DataSearchView.as_view(), name='data_search'),
    path('api/calculations/', CalculationSummaryView.as_view(), name='calculation_summary'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)