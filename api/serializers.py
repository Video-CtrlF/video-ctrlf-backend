from rest_framework import serializers
from ai_model import models

class YTUrlSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.YouTubeURL
        fields = ('id', 'url', 'status')

class YTInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.YouTubeInfo
        fields = ('url_id', 'title', 'length')

class YTCaptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.YouTubeCaption
        fields = ('url_id', 'start_time', 'end_time', 'text')

class OCRResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OCRResult
        fields = ('url_id', 'time', 'text', 'conf')

class STTResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.STTResult
        fields = ('url_id', 'start_time', 'end_time', 'text')