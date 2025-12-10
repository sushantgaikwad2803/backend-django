from rest_framework import serializers
from .models import CompName, CompInfo, Report

class CompanySerializer(serializers.ModelSerializer):
   class CompanySerializer(serializers.ModelSerializer):
    logo_url = serializers.SerializerMethodField()

    class Meta:
        model = CompName
        fields = [
            "id",
            "name",
            "ticker",
            "sector",
            "industry",
            "exchange", 
            "logo",
            "logo_url",
        ]

    def get_logo_url(self, obj):
        request = self.context.get("request")
        if obj.logo:
            return request.build_absolute_uri(obj.logo.url)
        return None


class CompanyInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompInfo
        fields = '__all__'
    
        
class ReportSerializer(serializers.ModelSerializer):

    class Meta:
        model = Report
        fields = ["id", "year",  'pdf_url', 'thumbnail_url', 'exchange']

