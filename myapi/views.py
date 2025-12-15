from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Report, CompName, CompInfo
from django.http import FileResponse, Http404
from django.conf import settings
from pdf2image import convert_from_bytes
from io import BytesIO
from .serializers import ReportSerializer 
from django.db.models.functions import Trim
from django.db import transaction
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
    try:
        report = Report.objects.get(id=report_id)
    except Report.DoesNotExist:
        return HttpResponse("Report not found", status=404)

    # PDF link stored in DB
    pdf_url = report.pdf_url

    if not pdf_url:
        return HttpResponse("PDF URL missing", status=400)

    # Download from Cloudinary
    response = FileResponse(
        requests.get(pdf_url, stream=True).raw,
        as_attachment=True,
        filename=f"{report.ticker}_{report.year}.pdf"
    )
    return response


@csrf_exempt
def upload_pdf(request):
    if request.method != "POST":
        return JsonResponse({"error": "Use POST method"}, status=400)

    files = request.FILES.getlist("pdf")
    if not files:
        return JsonResponse({"error": "PDF files are missing"}, status=400)

    result_list = []

    for file in files:
        file_name = file.name

        # Validate type
        if not file_name.lower().endswith(".pdf"):
            result_list.append({
                "file": file_name,
                "status": "error",
                "reason": "Only PDF allowed"
            })
            continue

        # Parse EXCHANGE_TICKER_YEAR
        name_without_ext = file_name.rsplit(".", 1)[0]
        parts = name_without_ext.split("_")

        if len(parts) != 3:
            result_list.append({
                "file": file_name,
                "status": "error",
                "reason": "Filename must be EXCHANGE_TICKER_YEAR.pdf"
            })
            continue

        exchange, ticker, year = parts[0], parts[1], int(parts[2])

        pdf_public_id = None
        thumb_public_id = None

        try:
            pdf_bytes = file.read()

            with transaction.atomic():
                # --------------------------
                # 1️⃣ Upload PDF to Cloudinary
                # --------------------------
                pdf_public_id = f"pdf_reports/{exchange}_{ticker}_{year}"

                pdf_upload = cloudinary.uploader.upload_large(
                    BytesIO(pdf_bytes),
                    public_id=pdf_public_id,
                    resource_type="raw",
                    folder="pdf_reports",
                    chunk_size=6000000,
                    format="pdf",  # ✅ ensures browser can open in new tab
                    overwrite=True
                )

                pdf_url = pdf_upload["secure_url"]

                # --------------------------
                # 2️⃣ Generate thumbnail
                # --------------------------
                try:
                    pages = convert_from_bytes(pdf_bytes, first_page=1, last_page=1)
                    thumb_image = pages[0].resize((300, 400))

                    img_io = BytesIO()
                    thumb_image.save(img_io, format="JPEG")
                    thumb_data = img_io.getvalue()

                    thumb_public_id = f"report_thumbnails/{exchange}_{ticker}_{year}_thumb"
                    thumb_upload = cloudinary.uploader.upload(
                        thumb_data,
                        public_id=thumb_public_id,
                        folder="report_thumbnails",
                        resource_type="image",
                        overwrite=True
                    )

                    thumbnail_url = thumb_upload["secure_url"]

                except Exception as thumb_err:
                    # If thumbnail generation fails, log None
                    thumbnail_url = None

                # --------------------------
                # 3️⃣ Insert into DB
                # --------------------------
                Report.objects.create(
                    exchange=exchange,
                    ticker=ticker,
                    year=year,
                    pdf_url=pdf_url,
                    thumbnail_url=thumbnail_url,
                )

            # Success
            result_list.append({
                "file": file_name,
                "status": "success",
                "exchange": exchange,
                "ticker": ticker,
                "year": year,
                "pdf_url": pdf_url,
                "thumbnail_url": thumbnail_url
            })

        except Exception as e:
            # Cleanup partial uploads
            try:
                if pdf_public_id:
                    cloudinary.uploader.destroy(pdf_public_id, resource_type="raw")
                if thumb_public_id:
                    cloudinary.uploader.destroy(thumb_public_id, resource_type="image")
            except:
                pass

            result_list.append({
                "file": file_name,
                "status": "error",
                "reason": str(e)
            })

    return JsonResponse({
        "message": "PDF Upload Completed",
        "results": result_list
    })

from bs4 import BeautifulSoup

@csrf_exempt
def auto_upload_pdf_from_url(request):
    if request.method != "POST":
        return JsonResponse({"error": "Use POST method"}, status=400)

    url = request.POST.get("url")
    exchange = request.POST.get("exchange")
    ticker = request.POST.get("ticker")

    if not all([url, exchange, ticker]):
        return JsonResponse({
            "error": "url, exchange and ticker are required"
        }, status=400)

    # Fetch page
    page_response = requests.get(url, timeout=30)
    soup = BeautifulSoup(page_response.text, "html.parser")

    # Collect PDF links
    pdf_links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.lower().endswith(".pdf"):
            pdf_links.append(
                href if href.startswith("http")
                else f"https://www.annualreports.com{href}"
            )

    if not pdf_links:
        return JsonResponse({"error": "No PDF links found"}, status=404)

    results = []

    for pdf_link in pdf_links:
        pdf_public_id = None
        thumb_public_id = None

        try:
            # Download PDF
            pdf_resp = requests.get(pdf_link, timeout=60)
            pdf_resp.raise_for_status()
            pdf_bytes = pdf_resp.content

            # Extract year from filename
            filename = pdf_link.split("/")[-1]
            year_digits = "".join(filter(str.isdigit, filename))
            year = int(year_digits[:4])

            with transaction.atomic():
                # -----------------------------
                # 1️⃣ Upload PDF (IMAGE TYPE)
                # -----------------------------
                pdf_public_id = f"pdf_reports/{exchange}_{ticker}_{year}"

                pdf_upload = cloudinary.uploader.upload_large(
                    BytesIO(pdf_bytes),
                    public_id=pdf_public_id,
                    resource_type="image",   # 🔥 KEY FIX
                    folder="pdf_reports",
                    format="pdf",            # 🔥 KEY FIX
                    overwrite=True,
                    chunk_size=6000000
                )

                pdf_url = pdf_upload["secure_url"]

                # -----------------------------
                # 2️⃣ Generate Thumbnail
                # -----------------------------
                thumbnail_url = None
                try:
                    pages = convert_from_bytes(pdf_bytes, first_page=1, last_page=1)
                    thumb_image = pages[0].resize((300, 400))

                    img_io = BytesIO()
                    thumb_image.save(img_io, format="JPEG")

                    thumb_public_id = f"report_thumbnails/{exchange}_{ticker}_{year}_thumb"

                    thumb_upload = cloudinary.uploader.upload(
                        img_io.getvalue(),
                        public_id=thumb_public_id,
                        resource_type="image",
                        overwrite=True
                    )

                    thumbnail_url = thumb_upload["secure_url"]
                except:
                    pass

                # -----------------------------
                # 3️⃣ Insert / Update DB
                # -----------------------------
                Report.objects.update_or_create(
                    exchange=exchange,
                    ticker=ticker,
                    year=year,
                    defaults={
                        "pdf_url": pdf_url,
                        "thumbnail_url": thumbnail_url,
                    }
                )

            results.append({
                "year": year,
                "status": "success",
                "pdf_url": pdf_url
            })

        except Exception as e:
            # Cleanup Cloudinary if partial failure
            try:
                if pdf_public_id:
                    cloudinary.uploader.destroy(pdf_public_id, resource_type="image")
                if thumb_public_id:
                    cloudinary.uploader.destroy(thumb_public_id, resource_type="image")
            except:
                pass

            results.append({
                "pdf": pdf_link,
                "status": "error",
                "reason": str(e)
            })

    return JsonResponse({
        "message": "Auto PDF Upload Completed",
        "results": results
    })

@api_view(['POST'])
def upload_logo(request):
    cloudinary_public_id = None   # Track uploaded image for rollback

    try:
        file = request.FILES.get('image')
        if not file:
            return Response({"error": "No image file provided"}, status=400)

        # ================================================
        # Validate filename format: EXCHANGE_TICKER.ext
        # ================================================
        filename = file.name.split(".")[0]  
        parts = filename.split("_")

        if len(parts) != 2:
            return Response(
                {"error": "Filename must be EXCHANGE_TICKER.ext (e.g. TSX_TCS.png)"},
                status=400
            )

        exchange, ticker = parts[0], parts[1]

        # ==================================================
        # Upload to Cloudinary (this must happen first)
        # ==================================================
        try:
            upload = cloudinary.uploader.upload(
                file,
                folder="company_logos",
                overwrite=True,
                resource_type="image"
            )
        except Exception as cloud_err:
            return Response({"error": "Cloudinary upload failed", "reason": str(cloud_err)}, status=500)

        logo_url = upload.get("secure_url")
        cloudinary_public_id = upload.get("public_id")

        if not logo_url:
            return Response({"error": "Cloudinary did not return a URL"}, status=500)

        # ======================================================
        # Read ALL form fields
        # ======================================================
        data = {
            "name": request.data.get("name", ""),
            "sector": request.data.get("sector", ""),
            "industry": request.data.get("industry", ""),
            "emp_number": request.data.get("emp_number", ""),
            "address": request.data.get("address", ""),
            "info": request.data.get("info", ""),
            "insta_link": request.data.get("insta_link", ""),
            "face_link": request.data.get("face_link", ""),
            "youtube_link": request.data.get("youtube_link", ""),
            "twitter_link": request.data.get("twitter_link", ""),
            "web_link": request.data.get("web_link", ""),
            "linkedin_link": request.data.get("linkedin_link", ""),
        }

        # ======================================================
        # DATABASE SAVE (ATOMIC) — All or nothing
        # ======================================================
        with transaction.atomic():

            comp_name_obj, created_name = CompName.objects.update_or_create(
                ticker=ticker,
                defaults={
                    "name": data["name"],
                    "exchange": exchange,
                    "sector": data["sector"],
                    "industry": data["industry"],
                    "logo": logo_url,
                }
            )

            comp_info_obj, created_info = CompInfo.objects.update_or_create(
                ticker=ticker,
                defaults={
                    "exchange": exchange,
                    "emp_number": data["emp_number"],
                    "address": data["address"],
                    "info": data["info"],
                    "insta_link": data["insta_link"],
                    "face_link": data["face_link"],
                    "youtube_link": data["youtube_link"],
                    "twitter_link": data["twitter_link"],
                    "web_link": data["web_link"],
                    "linkedin_link": data["linkedin_link"],
                }
            )

        # If code reaches here → everything OK
        return Response({
            "message": "Company data saved successfully",
            "ticker": ticker,
            "exchange": exchange,
            "logo_url": logo_url,
            "comp_name_created": created_name,
            "comp_info_created": created_info,
        })

    except Exception as e:
        # ====================================================
        # ROLLBACK: Delete Cloudinary image if DB fails
        # ====================================================
        if cloudinary_public_id:
            try:
                cloudinary.api.delete_resources([cloudinary_public_id], resource_type="image")
            except:
                pass  # Avoid crash

        return Response({"error": str(e)}, status=500)