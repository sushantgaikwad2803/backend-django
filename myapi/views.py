from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Report, CompName, CompInfo
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.conf import settings
from pdf2image import convert_from_bytes
from io import BytesIO
from .serializers import ReportSerializer 
from django.db.models.functions import Trim
import random
from django.http import HttpResponse
import cloudinary.uploader
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view


class ReportList(APIView):
    def get(self, request):
        reports = Report.objects.all()
        serializer = ReportSerializer(reports, many=True, context={'request': request})
        return Response(serializer.data)


def view_pdf(request, pk):
    report = get_object_or_404(Report, pk=pk)

    if not report.report_pdf:
        raise Http404("No PDF file available")

    file_path = report.report_pdf.path
    return FileResponse(open(file_path, "rb"), content_type="application/pdf")


class RandomCompanyReport(APIView):
    def get(self, request):
        companies = CompName.objects.order_by("?")[:10]

        if not companies:
            raise Http404("No companies found")

        results = []

        for comp in companies:
            report = Report.objects.filter(ticker=comp.ticker).order_by("?").first()

            results.append({
                "company": {
                    "id": comp.id,
                    "name": comp.name,
                    "ticker": comp.ticker,
                    "sector": comp.sector,
                    "exchange": comp.exchange,
                },
                "report": {
                    "id": report.id if report else None,
                    "year": report.year if report else None,
                    "has_report": bool(report),
                    "report_pdf": report.pdf_url if report else None,
                    "thumbnail_url": report.thumbnail_url if report else None,  # added thumbnail
                }
            })

        return Response({"results": results})



from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import Http404
from django.conf import settings

from .models import CompName, CompInfo, Report
from .serializers import ReportSerializer


class AllReportsOfCompany(APIView):
    def get(self, request, ticker):

        # 1️⃣ Check company (case-insensitive)
        company = CompName.objects.filter(ticker__iexact=ticker).values(
            "name", "ticker", "logo", "exchange", "sector", "industry"
        ).first()

        if not company:
            raise Http404("Company not found")

        # 2️⃣ Optional company info
        comp_info = CompInfo.objects.filter(ticker__iexact=ticker).first()

        # 3️⃣ Company logo URL
        logo_url = company.get("logo")  # take as-is from DB
        if logo_url and not logo_url.startswith("http"):
            logo_url = request.build_absolute_uri(settings.MEDIA_URL + str(logo_url))

        # 4️⃣ Reports
        reports = Report.objects.filter(ticker__iexact=ticker).order_by("-year")
        if reports.exists():
            report_data = ReportSerializer(reports, many=True, context={'request': request}).data
            report_message = ""
        else:
            report_data = []
            report_message = "No reports available for this company"

        # 5️⃣ Return full company + report data
        return Response({
            "ticker": company["ticker"],
            "company_name": company["name"],
            "exchange": company["exchange"],
            "sector": company["sector"],
            "industry": company["industry"],
            "logo": logo_url,
            "employee_count": getattr(comp_info, "emp_number", "") if comp_info else "",
            "address": getattr(comp_info, "address", "") if comp_info else "",
            "description": getattr(comp_info, "info", "") if comp_info else "",
            "social_links": {
                "instagram": getattr(comp_info, "insta_link", "") if comp_info else "",
                "facebook": getattr(comp_info, "face_link", "") if comp_info else "",
                "youtube": getattr(comp_info, "youtube_link", "") if comp_info else "",
                "twitter": getattr(comp_info, "twitter_link", "") if comp_info else "",
                "website": getattr(comp_info, "web_link", "") if comp_info else "",
            },
            "reports": report_data,
            "report_message": report_message
        })




class CompanyList(APIView):
    def get(self, request):
        exchange = request.GET.get("exchange", "").strip()
        qs = CompName.objects.all()

        if exchange:
            qs = qs.annotate(clean_exchange=Trim('exchange')).filter(clean_exchange__iexact=exchange)

        data = list(qs.values(
            "id", "name", "ticker", "sector", "industry", "exchange", "logo"
        ))

        return Response({"companies": data})


class CompanyReportView(APIView):
    def get(self, request, ticker):
        company = CompName.objects.get(ticker=ticker)
        reports = company.reports.all().order_by('-year')

        data = {
            "company_name": company.name,
            "exchange": company.exchange,
            "sector": company.sector,
            "industry": company.industry,
            "logo": request.build_absolute_uri(company.logo.url) if company.logo else None,
            "employee_count": company.employee_count,
            "address": company.address,
            "description": company.description,
            "social_links": company.social_links,

            "reports": ReportSerializer(reports, many=True, context={'request': request}).data
        }

        return Response(data)

class RandomSixCompanies(APIView):
    def get(self, request):
        companies = CompName.objects.order_by("?")[:6]

        if not companies:
            return Response({"companies": []})

        results = []

        for comp in companies:
            logo_url = comp.logo  # take as-is

            # Only prepend MEDIA_URL if logo is a relative path
            if logo_url and not logo_url.startswith("http"):
                logo_url = request.build_absolute_uri(settings.MEDIA_URL + str(logo_url))

            results.append({
                "id": comp.id,
                "name": comp.name,
                "ticker": comp.ticker,
                "logo": logo_url
            })

        return Response({"companies": results})


def download_report(request, report_id):
    report = Report.objects.get(id=report_id)
    file_path = report.report_pdf.path
    
    with open(file_path, "rb") as pdf:
        response = HttpResponse(pdf.read(), content_type="application/pdf")
        response['Content-Disposition'] = f'attachment; filename="{report.ticker}_{report.year}.pdf"'
        return response
    
    
@csrf_exempt
def upload_pdf(request):
    try:
        if request.method != "POST":
            return JsonResponse({"error": "Use POST method"}, status=400)

        if "pdf" not in request.FILES:
            return JsonResponse({"error": "PDF file is missing"}, status=400)

        file = request.FILES["pdf"]
        file_name = file.name

        # Ensure PDF
        if not file_name.lower().endswith(".pdf"):
            return JsonResponse({"error": "Only PDF format allowed"}, status=400)

        # Extract ticker + year (AIM_TCS_2002.pdf → ticker=TCS, year=2002)
        name_without_ext = file_name.replace(".pdf", "")
        parts = name_without_ext.split("_")

        if len(parts) < 3:
            return JsonResponse({"error": "Filename must be AIM_TICKER_YEAR.pdf"}, status=400)

        ticker = parts[1]
        year = int(parts[2])

        # =================================================
        # 1️⃣ Upload original PDF to Cloudinary (raw upload)
        # =================================================
        upload_result = cloudinary.uploader.upload(
            file,
            resource_type="raw",
            folder="pdf_reports"
        )

        pdf_url = upload_result["secure_url"]

        # =================================================
        # 2️⃣ Read PDF bytes for thumbnail
        # =================================================
        file.open()  # Reset pointer
        pdf_data = file.read()

        # =================================================
        # 3️⃣ Generate thumbnail using pdf2image
        # =================================================
        pages = convert_from_bytes(
            pdf_data,
            first_page=1,
            last_page=1
        )

        # Resize thumbnail (optional)
        thumb_image = pages[0]
        thumb_image = thumb_image.resize((300, 400))

        # Save thumbnail to memory buffer
        image_io = BytesIO()
        thumb_image.save(image_io, format="JPEG")
        image_data = image_io.getvalue()

        # =================================================
        # 4️⃣ Upload thumbnail to Cloudinary
        # =================================================
        thumb_public_id = f"{ticker}_{year}_thumb"

        thumb_upload = cloudinary.uploader.upload(
            image_data,
            resource_type="image",
            folder="report_thumbnails",
            public_id=thumb_public_id,
            overwrite=True
        )

        thumbnail_url = thumb_upload["secure_url"]

        # =================================================
        # 5️⃣ Save record in PostgreSQL
        # =================================================
        Report.objects.create(
            ticker=ticker,
            year=year,
            pdf_url=pdf_url,
            thumbnail_url=thumbnail_url
        )

        return JsonResponse({
            "message": "Uploaded successfully",
            "ticker": ticker,
            "year": year,
            "pdf_url": pdf_url,
            "thumbnail_url": thumbnail_url
        })

    except Exception as e:
        print("UPLOAD ERROR:", e)
        return JsonResponse({"error": str(e)}, status=500)


@api_view(['POST'])
def upload_logo(request):
    """
    Upload an image to Cloudinary and update the 'logo' field in CompName table
    for the row where exchange and ticker match the filename.
    """
    file = request.FILES.get('image')
    if not file:
        return Response({"error": "No file provided"}, status=400)

    # Upload image to Cloudinary
    result = cloudinary.uploader.upload(file)
    logo_url = result.get("secure_url")

    # Extract tickers/exchange from filename
    filename = file.name.split(".")[0]  # "AIM_CRW"
    parts = filename.split("_")

    if len(parts) != 2:
        return Response({"error": "Filename should be in format EXCHANGE_TICKER.png"}, status=400)

    exchange, ticker = parts[0], parts[1]

    try:
        # Update the row where exchange and ticker match
        company = CompName.objects.get(exchange=exchange, ticker=ticker)
        company.logo = logo_url
        company.save()
        return Response({
            "message": "Logo updated successfully",
            "exchange": exchange,
            "ticker": ticker,
            "logo_url": logo_url
        })
    except CompName.DoesNotExist:
        return Response({"error": f"No row found for exchange={exchange} and ticker={ticker}"}, status=404)