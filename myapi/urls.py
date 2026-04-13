from django.urls import path
from .views import (
    ReportList,
    # view_pdf,
    RandomCompanyReport,
    AllReportsOfCompany,
    CompanyList , 
    RandomSixCompanies , 
    download_report,
    # auto_upload_pdf_from_url
)
from . import views
from django.http import HttpResponse

def home(request):
    return HttpResponse("Backend is running 🚀")

# ✅ Add this new function
def sitemap(request):
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
   <url>
      <loc>https://arannualreport.com/</loc>
   </url>
</urlset>
"""
    return HttpResponse(xml, content_type='application/xml')

urlpatterns = [

    path('', home),  # THIS IS ROOT URL

     path('sitemap.xml', sitemap),

    # Companies API
    path('api/companies/', CompanyList.as_view(), name='company-list'),

    # List all reports
    path('api/reports/', ReportList.as_view(), name='report-list'),

    # View full PDF
    # path('report/view/<int:pk>/', view_pdf, name='view-pdf'),

    # Random company + report
    path('random-company-report/', RandomCompanyReport.as_view(), name='random-company-report'),

    # All reports of a company
    path('company-reports/<str:ticker>/<str:exchange>/', AllReportsOfCompany.as_view()),
    
    path("download-report/<int:report_id>/", download_report),
    
    path('random-logos/', RandomSixCompanies.as_view(), name='random-logos'),
    
    # path("upload-pdf/", views.upload_pdf, name="upload_pdf"),
    
    
    # path("auto-upload-pdf/", auto_upload_pdf_from_url),

    
]
