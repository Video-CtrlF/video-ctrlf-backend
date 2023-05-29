from django.shortcuts import render
from rest_framework import viewsets
from . import serializers
from ai_model import models
# Create your views here.
class YTUrlViewSet(viewsets.ModelViewSet):
    queryset = models.YouTubeURL.objects.all()
    serializer_class = serializers.YTUrlSerializer
    
class YTInfoViewSet(viewsets.ModelViewSet):
    queryset = models.YouTubeInfo.objects.all()
    serializer_class = serializers.YTInfoSerializer
    
class YTCaptionViewSet(viewsets.ModelViewSet):
    queryset = models.YouTubeCaption.objects.all()
    serializer_class = serializers.YTCaptionSerializer
    
class OCRResultViewSet(viewsets.ModelViewSet):
    queryset = models.OCRResult.objects.all()
    serializer_class = serializers.OCRResultSerializer
    
class STTResultViewSet(viewsets.ModelViewSet):
    queryset = models.STTResult.objects.all()
    serializer_class = serializers.STTResultSerializer
    