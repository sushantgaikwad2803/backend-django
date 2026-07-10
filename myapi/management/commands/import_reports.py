# import os
# from django.core.management.base import BaseCommand
# from django.db import transaction

# import cloudinary.uploader
# from myapi.models import Report


# class Command(BaseCommand):
#     help = "Import PDFs from local folder and save to DB + Cloudinary"

#     # 🔁 CHANGE THIS FOLDER
#     FOLDER_PATH = r"C:\Users\kumar\OneDrive\Desktop\Report\amtd-international-inc"

#     def handle(self, *args, **kwargs):
#         self.stdout.write("\n🚀 Starting local PDF import...\n")

#         if not os.path.exists(self.FOLDER_PATH):
#             self.stdout.write(self.style.ERROR("❌ Folder not found"))
#             return

#         pdf_files = [
#             f for f in os.listdir(self.FOLDER_PATH)
#             if f.lower().endswith(".pdf")
#         ]

#         if not pdf_files:
#             self.stdout.write(self.style.ERROR("❌ No PDF files found"))
#             return

#         success, failed = 0, 0

#         for file_name in pdf_files:
#             self.stdout.write(f"⬇️ Processing {file_name}")

#             # --------------------------
#             # 1️⃣ Validate filename
#             # --------------------------
#             try:
#                 exchange, ticker, year = file_name.replace(".pdf", "").split("_")
#                 year = int(year)
#             except Exception:
#                 self.stdout.write(
#                     self.style.WARNING(f"⚠️ Invalid filename format: {file_name}")
#                 )
#                 continue

#             # --------------------------
#             # 2️⃣ Skip duplicates
#             # --------------------------
#             if Report.objects.filter(
#                 exchange=exchange,
#                 ticker=ticker,
#                 year=year
#             ).exists():
#                 self.stdout.write(f"⚠️ Already exists: {file_name}")
#                 continue

#             pdf_path = os.path.join(self.FOLDER_PATH, file_name)

#             pdf_public_id = None
#             thumb_public_id = None

#             try:
#                 with transaction.atomic():

#                     # --------------------------
#                     # 3️⃣ Upload PDF (Cloudinary)
#                     # --------------------------
#                     pdf_public_id = f"pdf_reports/{exchange}_{ticker}_{year}"

#                     pdf_upload = cloudinary.uploader.upload_large(
#                         pdf_path,
#                         public_id=pdf_public_id,
#                         resource_type="raw",
#                         format="pdf",
#                         overwrite=True,
#                         chunk_size=6000000,
#                     )

#                     pdf_url = pdf_upload["secure_url"]

#                     # --------------------------
#                     # 4️⃣ Generate thumbnail (Cloudinary 🔥)
#                     # --------------------------
#                     thumbnail_url = None
#                     try:
#                         thumb_public_id = (
#                             f"report_thumbnails/{exchange}_{ticker}_{year}_thumb"
#                         )

#                         thumb_upload = cloudinary.uploader.upload(
#                             pdf_path,
#                             public_id=thumb_public_id,
#                             resource_type="image",  # 🔥 PDF → Image
#                             format="jpg",
#                             page=1,
#                             overwrite=True,
#                         )

#                         thumbnail_url = thumb_upload["secure_url"]

#                     except Exception as thumb_err:
#                         self.stdout.write(
#                             self.style.WARNING(
#                                 f"⚠️ Thumbnail skipped: {thumb_err}"
#                             )
#                         )

#                     # --------------------------
#                     # 5️⃣ Save to database
#                     # --------------------------
#                     Report.objects.create(
#                         exchange=exchange,
#                         ticker=ticker,
#                         year=year,
#                         pdf_url=pdf_url,
#                         thumbnail_url=thumbnail_url,
#                     )

#                 success += 1
#                 self.stdout.write(self.style.SUCCESS(f"✅ Saved {file_name}"))

#             except Exception as e:
#                 failed += 1

#                 # Cleanup partial uploads
#                 try:
#                     if pdf_public_id:
#                         cloudinary.uploader.destroy(
#                             pdf_public_id, resource_type="raw"
#                         )
#                     if thumb_public_id:
#                         cloudinary.uploader.destroy(
#                             thumb_public_id, resource_type="image"
#                         )
#                 except:
#                     pass

#                 self.stdout.write(
#                     self.style.ERROR(f"❌ Failed {file_name}: {e}")
#                 )

#         self.stdout.write("\n==============================")
#         self.stdout.write(self.style.SUCCESS(f"✅ Success: {success}"))
#         self.stdout.write(self.style.ERROR(f"❌ Failed: {failed}"))
#         self.stdout.write("==============================\n")


import requests
import time
from io import BytesIO

from django.core.management.base import BaseCommand
from django.db import transaction

from bs4 import BeautifulSoup
from pdf2image import convert_from_bytes
# import cloudinary.uploader


from myapi.models import Report


class Command(BaseCommand):
    
    help = "Import annual report PDFs from AnnualReports.com"

    BASE_URL = "https://www.annualreports.com"
    COMPANY_URL = "https://www.annualreports.com/Company/1spatial-plc"

    # 🔒 SAME AS MANUAL UPLOAD
    EXCHANGE = "NYSE"
    TICKER = "SPA"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "text/html,application/pdf",
    }

    def handle(self, *args, **kwargs):
        self.stdout.write("🚀 Starting annual report import...\n")

        # --------------------------
        # 1️⃣ Fetch company page
        # --------------------------
        try:
            response = requests.get(
                self.COMPANY_URL,
                headers=self.HEADERS,
                timeout=30
            )
            response.raise_for_status()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Failed to open page: {e}"))
            return

        soup = BeautifulSoup(response.text, "html.parser")
        links = soup.select("a[href$='.pdf']")

        if not links:
            self.stdout.write(self.style.ERROR("❌ No PDF links found"))
            return

        self.stdout.write(f"📄 Found {len(links)} PDF reports\n")

        success, failed = 0, 0

        # --------------------------
        # 2️⃣ Process PDFs
        # --------------------------
        for link in links:
            pdf_url = link["href"]
            if not pdf_url.startswith("http"):
                pdf_url = self.BASE_URL + pdf_url

            filename = pdf_url.split("/")[-1]

            # 🔍 Extract year
            digits = "".join(filter(str.isdigit, filename))
            if len(digits) < 4:
                self.stdout.write(f"⚠️ Skipped (no year): {filename}")
                continue

            year = int(digits[:4])

            # ❌ Prevent duplicates
            if Report.objects.filter(
                exchange=self.EXCHANGE,
                ticker=self.TICKER,
                year=year
            ).exists():
                self.stdout.write(f"⚠️ Already exists: {year}")
                continue

            self.stdout.write(f"⬇️ Downloading {year} report")

            pdf_public_id = None
            thumb_public_id = None

            try:
                pdf_response = requests.get(
                    pdf_url,
                    headers=self.HEADERS,
                    timeout=60
                )
                pdf_response.raise_for_status()

                pdf_bytes = pdf_response.content

                with transaction.atomic():
                    # --------------------------
                    # 3️⃣ Upload PDF (Cloudinary)
                    # --------------------------
                    pdf_public_id = f"pdf_reports/{self.EXCHANGE}_{self.TICKER}_{year}"

                    pdf_upload = cloudinary.uploader.upload_large(
                        BytesIO(pdf_bytes),
                        public_id=pdf_public_id,
                        resource_type="raw",
                        folder="pdf_reports",
                        format="pdf",
                        overwrite=True,
                        chunk_size=6000000
                    )

                    pdf_cloud_url = pdf_upload["secure_url"]

                    # --------------------------
                    # 4️⃣ Generate thumbnail
                    # --------------------------
                    thumbnail_url = None
                    try:
                        pages = convert_from_bytes(
                            pdf_bytes,
                            first_page=1,
                            last_page=1
                        )

                        thumb_image = pages[0].resize((300, 400))
                        img_io = BytesIO()
                        thumb_image.save(img_io, format="JPEG")

                        thumb_public_id = (
                            f"report_thumbnails/"
                            f"{self.EXCHANGE}_{self.TICKER}_{year}_thumb"
                        )

                        thumb_upload = cloudinary.uploader.upload(
                            img_io.getvalue(),
                            public_id=thumb_public_id,
                            folder="report_thumbnails",
                            resource_type="image",
                            overwrite=True
                        )

                        thumbnail_url = thumb_upload["secure_url"]

                    except Exception as thumb_err:
                        self.stdout.write(
                            self.style.WARNING(
                                f"⚠️ Thumbnail failed for {year}: {thumb_err}"
                            )
                        )

                    # --------------------------
                    # 5️⃣ Save DB (SAME AS API)
                    # --------------------------
                    Report.objects.create(
                        exchange=self.EXCHANGE,
                        ticker=self.TICKER,
                        year=year,
                        pdf_url=pdf_cloud_url,
                        thumbnail_url=thumbnail_url,
                    )

                success += 1
                self.stdout.write(self.style.SUCCESS(f"✅ Saved {year}"))

                time.sleep(2)  # prevent IP block

            except Exception as e:
                failed += 1

                # Cleanup partial uploads
                try:
                    if pdf_public_id:
                        cloudinary.uploader.destroy(
                            pdf_public_id, resource_type="raw"
                        )
                    if thumb_public_id:
                        cloudinary.uploader.destroy(
                            thumb_public_id, resource_type="image"
                        )
                except:
                    pass

                self.stdout.write(self.style.ERROR(f"❌ Failed {year}: {e}"))

        self.stdout.write("\n==============================")
        self.stdout.write(self.style.SUCCESS(f"✅ Success: {success}"))
        self.stdout.write(self.style.ERROR(f"❌ Failed: {failed}"))
        self.stdout.write("==============================\n")
