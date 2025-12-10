from django.urls import path
from .views import (
    ReportList,
    view_pdf,
     upload_logo,
    RandomCompanyReport,
    AllReportsOfCompany,
    CompanyList , 
    RandomSixCompanies , 
    download_report
)
from . import views

urlpatterns = [
    # Companies API
    path('api/companies/', CompanyList.as_view(), name='company-list'),

    # List all reports
    path('api/reports/', ReportList.as_view(), name='report-list'),

    # View full PDF
    path('report/view/<int:pk>/', view_pdf, name='view-pdf'),

    # Random company + report
    path('random-company-report/', RandomCompanyReport.as_view(), name='random-company-report'),

    # All reports of a company
    path('company-reports/<str:ticker>/<str:exchange>/', AllReportsOfCompany.as_view()),
    
    path("download-report/<int:report_id>/", download_report),
    
    path('random-logos/', RandomSixCompanies.as_view(), name='random-logos'),
    
    path("upload-pdf/", views.upload_pdf, name="upload_pdf"),
    
    path('upload-logo/', upload_logo, name='upload-logo'),

    
]
