from django.shortcuts import render
from django.http import JsonResponse
from ai_model import models
from ai_model.ai_model_base import AiModel

from rest_framework.response import Response
from rest_framework.decorators import api_view

from .serializers import *

# Create your views here.

@api_view(['POST'])
def api(request):
    url = request.data.get('url')
    if models.YouTubeURL.objects.filter(url=url).exists(): # 이미 DB에 해당 URL이 존재하는지 확인
        yt_url = models.YouTubeURL.objects.get(url=url)
        STTserializer = STTResultSerializer(models.STTResult.objects.filter(url_id=yt_url), many=True)
        OCRserializer = OCRResultSerializer(models.OCRResult.objects.filter(url_id=yt_url), many=True)

        return Response({"STT" : STTserializer.data, "OCR" : OCRserializer.data})
    else: # DB에 없으면
        # YouTubeURL에 저장
        yt_url = models.YouTubeURL(url=url)
        yt_url.save()

        ai_obj = AiModel(url)
        
        # YouTubeInfo에 저장
        models.YouTubeInfo(url_id=yt_url, title=ai_obj.yt.title, length=ai_obj.yt.length).save()

        # YouTubeCaption에 저장
        yt_caption = ai_obj.get_captions()
        for _, row in yt_caption.iterrows():
            data_model = models.YouTubeCaption(url_id=yt_url, start_time=row['start'], end_time=row['end'], text=row['text'])
            data_model.save()
        
        # ########################
        # OCRResult에 저장
        ocr_result = ai_obj.get_easyocr_result()
        for _, row in ocr_result.iterrows():
            data_model = models.OCRResult(url_id=yt_url, time=row['time'], text=row['text'], conf=row['conf'])
            data_model.save()

        # STTResult에 저장
        stt_result = ai_obj.get_whisper_result()
        for _, row in stt_result.iterrows():
            data_model = models.STTResult(url_id=yt_url, start_time=row['start'], end_time=row['end'], text=row['text'])
            data_model.save()
        # #########################
        YTCaption_serializer = YTCaptionSerializer(models.YouTubeCaption.objects.filter(url_id=yt_url), many=True)
        return Response({"caption" : YTCaption_serializer.data})
