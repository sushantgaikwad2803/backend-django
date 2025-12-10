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
# import random
import os
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
        companies = CompName.objects.order_by("?")[:6]

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


class AllReportsOfCompany(APIView):
    def get(self, request, ticker, exchange):

        # Company MATCH ticker + exchange
        company = CompName.objects.filter(
            ticker__iexact=ticker,
            exchange__iexact=exchange
        ).values(
            "name", "ticker", "logo", "exchange", "sector", "industry"
        ).first()

        if not company:
            raise Http404("Company not found")

        # Optional comp info MATCH both
        comp_info = CompInfo.objects.filter(
            ticker__iexact=ticker,
            exchange__iexact=exchange
        ).first()

        # Logo handling
        logo_url = company.get("logo")
        if logo_url and not logo_url.startswith("http"):
            logo_url = request.build_absolute_uri(settings.MEDIA_URL + str(logo_url))

        # Reports MATCH ticker + exchange
        reports = Report.objects.filter(
            ticker__iexact=ticker,
            exchange__iexact=exchange
        ).order_by("-year")

        if reports.exists():
            report_data = ReportSerializer(reports, many=True, context={'request': request}).data
            report_message = ""
        else:
            report_data = []
            report_message = "No reports available for this company"

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
                "linkedin": getattr(comp_info, "linkedin_link", "") if comp_info else "",
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
                "exchange": comp.exchange,  # ✅ Added this
                "logo": logo_url
            })

        return Response({"companies": results})


import requests
from django.core.files.temp import NamedTemporaryFile
def download_report(request, report_id):
    # 1️⃣ Get the report
    report = get_object_or_404(Report, id=report_id)

    pdf_url = report.pdf_url  # Cloudinary URL
    if not pdf_url:
        raise Http404("PDF not found")

    # 2️⃣ Fetch PDF from Cloudinary
    try:
        r = requests.get(pdf_url, stream=True)
        if r.status_code != 200:
            raise Http404("Unable to fetch PDF")

        tmp = NamedTemporaryFile(delete=True)
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                tmp.write(chunk)
        tmp.seek(0)

        # 3️⃣ Return as attachment → forces download
        response = FileResponse(tmp, as_attachment=True)
        response['Content-Disposition'] = f'attachment; filename="{report.ticker}_{report.year}.pdf"'
        return response

    except Exception as e:
        print(e)
        raise Http404("Error downloading PDF")
    
    
@csrf_exempt
def upload_pdf(request):
    try:
        if request.method != "POST":
            return JsonResponse({"error": "Use POST method"}, status=400)

        files = request.FILES.getlist("pdf")

        if not files:
            return JsonResponse({"error": "PDF files are missing"}, status=400)

        result_list = []

        for file in files:
            file_name = file.name

            if not file_name.lower().endswith(".pdf"):
                result_list.append({
                    "file": file_name,
                    "status": "error",
                    "reason": "Only PDF allowed"
                })
                continue

            # EXCHANGE_TICKER_YEAR.pdf
            name_without_ext = file_name.rsplit(".", 1)[0]
            parts = name_without_ext.split("_")

            if len(parts) < 3:
                result_list.append({
                    "file": file_name,
                    "status": "error",
                    "reason": "Filename must be EXCHANGE_TICKER_YEAR.pdf"
                })
                continue

            exchange = parts[0]
            ticker = parts[1]
            year = int(parts[2])

            try:
                # -----------------------------------------------------
                # 1️⃣ RESET pointer before upload
                # -----------------------------------------------------
                file.seek(0)

                # -----------------------------------------------------
                # 2️⃣ Upload LARGE PDF to Cloudinary
                # -----------------------------------------------------
                upload_result = cloudinary.uploader.upload_large(
                    file,
                    resource_type="raw",
                    folder="pdf_reports",
                    chunk_size=6000000   # 6MB chunks (safe for 10MB+ files)
                )

                pdf_url = upload_result["secure_url"]

                # -----------------------------------------------------
                # 3️⃣ RESET pointer before thumbnail generation
                # -----------------------------------------------------
                file.seek(0)
                pdf_data = file.read()

                pages = convert_from_bytes(pdf_data, first_page=1, last_page=1)
                thumb_image = pages[0].resize((300, 400))

                image_io = BytesIO()
                thumb_image.save(image_io, format="JPEG")
                image_data = image_io.getvalue()

                # -----------------------------------------------------
                # 4️⃣ Upload thumbnail (normal upload is fine)
                # -----------------------------------------------------
                thumb_public_id = f"{exchange}_{ticker}_{year}_thumb"

                thumb_upload = cloudinary.uploader.upload(
                    image_data,
                    resource_type="image",
                    folder="report_thumbnails",
                    public_id=thumb_public_id,
                    overwrite=True
                )

                thumbnail_url = thumb_upload["secure_url"]

                # -----------------------------------------------------
                # 5️⃣ Save in Database
                # -----------------------------------------------------
                Report.objects.create(
                    exchange=exchange,
                    ticker=ticker,
                    year=year,
                    pdf_url=pdf_url,
                    thumbnail_url=thumbnail_url
                )

                result_list.append({
                    "file": file_name,
                    "status": "success",
                    "exchange": exchange,
                    "ticker": ticker,
                    "year": year
                })

            except Exception as e:
                result_list.append({
                    "file": file_name,
                    "status": "error",
                    "reason": str(e)
                })

        return JsonResponse({
            "message": "Multiple PDF upload completed",
            "results": result_list
        })

    except Exception as e:
        print("UPLOAD ERROR:", e)
        return JsonResponse({"error": str(e)}, status=500)



@api_view(['POST'])
def upload_logo(request):
    """
    Upload logo → Auto extract exchange + ticker → Insert into CompName & CompInfo
    Accepts form fields for both tables.
    """
    file = request.FILES.get('image')
    if not file:
        return Response({"error": "No image file provided"}, status=400)

    # Upload to Cloudinary
    result = cloudinary.uploader.upload(file)
    logo_url = result.get("secure_url")

    # Extract EXCHANGE + TICKER from filename
    filename = file.name.split(".")[0]       # AIM_TCS
    parts = filename.split("_")

    if len(parts) != 2:
        return Response(
            {"error": "Filename must be EXCHANGE_TICKER.ext e.g. AIM_TCS.png"},
            status=400
        )

    exchange, ticker = parts[0], parts[1]

    # ===================================================
    #  READ ALL FIELDS FROM FORM
    # ===================================================
    name = request.data.get("name", "")
    sector = request.data.get("sector", "")
    industry = request.data.get("industry", "")

    emp_number = request.data.get("emp_number", "")
    address = request.data.get("address", "")
    info = request.data.get("info", "")

    insta_link = request.data.get("insta_link", "")
    face_link = request.data.get("face_link", "")
    youtube_link = request.data.get("youtube_link", "")
    twitter_link = request.data.get("twitter_link", "")
    web_link = request.data.get("web_link", "")
    linkedin_link = request.data.get("linkedin_link", "")

    # ===================================================
    #  INSERT OR UPDATE CompName
    # ===================================================
    comp_name_obj, created_name = CompName.objects.update_or_create(
        ticker=ticker,
        defaults={
            "name": name,
            "exchange": exchange,
            "sector": sector,
            "industry": industry,
            "logo": logo_url,
        }
    )

    # ===================================================
    #  INSERT OR UPDATE CompInfo
    # ===================================================
    comp_info_obj, created_info = CompInfo.objects.update_or_create(
        ticker=ticker,
        defaults={
            "exchange": exchange,
            "emp_number": emp_number,
            "address": address,
            "info": info,
            "insta_link": insta_link,
            "face_link": face_link,
            "youtube_link": youtube_link,
            "twitter_link": twitter_link,
            "web_link": web_link,
            "linkedin_link": linkedin_link,
        }
    )

    return Response({
        "message": "Data saved successfully",
        "ticker": ticker,
        "exchange": exchange,
        "logo_url": logo_url,
        "comp_name_created": created_name,   # True = new row inserted
        "comp_info_created": created_info,
    })
