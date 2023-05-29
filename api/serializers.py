from rest_framework import serializers
from ai_model import models

class YTUrlSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.YouTubeURL
        fields = ("__all__")
        # fields = ('id', 'url')

class YTInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.YouTubeInfo
        fields = ("__all__")

class YTCaptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.YouTubeCaption
        fields = ("__all__")

class OCRResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OCRResult
        fields = ("__all__")

class STTResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.STTResult
        fields = ("__all__")