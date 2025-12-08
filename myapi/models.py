from django.db import models

# Create your models here.

class Report(models.Model):
    ticker = models.CharField(max_length=20)
    year = models.IntegerField()
    pdf_url = models.TextField(null=True, blank=True)
    thumbnail_url = models.TextField(null=True, blank=True)


    class Meta:
        db_table = 'report'

class CompName(models.Model):
    name = models.CharField(max_length=255)
    ticker = models.CharField(max_length=20, unique=True, blank=True, null=True)
    logo = models.TextField(blank=True, null=True)       # URL or Base64
    exchange = models.CharField(max_length=50, blank=True, null=True)
    sector = models.CharField(max_length=100, blank=True, null=True)
    industry = models.CharField(max_length=150, blank=True, null=True)

    class Meta:
        db_table = 'comp_name'   # ensures Django uses your exact table name

    def __str__(self):
        return f"{self.name} ({self.ticker})"
    

class CompInfo(models.Model):
    ticker = models.CharField(max_length=20, primary_key=True)
    emp_number = models.CharField(max_length=100, null=True, blank=True)  # ← now TEXT
    address = models.TextField(null=True, blank=True)
    info = models.TextField(null=True, blank=True)

    insta_link = models.URLField(max_length=300, null=True, blank=True)
    face_link = models.URLField(max_length=300, null=True, blank=True)
    youtube_link = models.URLField(max_length=300, null=True, blank=True)
    twitter_link = models.URLField(max_length=300, null=True, blank=True)
    web_link = models.URLField(max_length=300, null=True, blank=True)

    class Meta:
        db_table = 'comp_info'
          
    def __str__(self):
        return self.ticker