from rest_framework import serializers
from ai_model import models

class YTUrlSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.YouTubeURL
        fields = ('id', 'url', 'status')

class YTInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.YouTubeInfo
        fields = ('url_id', 'title', 'length', 'video_size')

class YTCaptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.YouTubeCaption
        fields = ('url_id', 'start_time', 'end_time', 'text')

class OCRResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OCRResult
        fields = ('time', 'text', 'conf', 'bbox')

class STTResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.STTResult
        fields = ('start_time', 'end_time', 'text')

class CaptionKeywordSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CaptionKeyword
        fields = ('keywords', )

class OCRKeywordSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OCRKeyword
        fields = ('keywords', )

class STTKeywordSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.STTKeyword
        fields = ('keywords', )

