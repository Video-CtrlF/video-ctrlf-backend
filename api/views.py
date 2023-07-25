from django.shortcuts import render
from django.http import JsonResponse
from ai_model import models
from ai_model.ai_model_base import AiModel

from rest_framework.response import Response
from rest_framework.decorators import api_view

from .serializers import *

import time
import threading

# Create your views here.

# api/url-check/
@api_view(['POST'])
def url_check(request):
    # db에 url 이 있는지 확인
    if request.method == 'POST':
        url = request.data.get('url')
        if models.YouTubeURL.objects.filter(url=url).exists(): # DB에 해당 URL이 존재하는지 확인
            return JsonResponse({"isExist" : True})
        return JsonResponse({"isExist" : False})

# api/caption/
@api_view(['POST'])
def get_caption(request):
    # youtube에서 제공하는 caption을 return
    if request.method == 'POST':
        try:
            url = request.data.get('url')
            if not models.YouTubeURL.objects.filter(url=url).exists(): # DB에 해당 URL이 없으면
                # 기본 처리 (db에 url 저장 및 caption)
                youtubeDefault(url=url)
            yt_url = models.YouTubeURL.objects.get(url=url)
            YTCaption_serializer = YTCaptionSerializer(models.YouTubeCaption.objects.filter(url_id=yt_url), many=True)
            return JsonResponse({"caption" : YTCaption_serializer.data})
        except Exception as e:
            return JsonResponse({"Error" : e})
    
# api/ai/
@api_view(['POST'])
def ai_inference(request):
    # AI 모델 스레드로 돌리고 status 반환
    if request.method == 'POST':
        url = request.data.get('url')
        try:
            ai_obj = AiModel(url)
            yt_url = models.YouTubeURL.objects.get(url=url)

            # 스레드로 실행
            t = threading.Thread(target=inference, args=(yt_url, ai_obj, ))
            t.daemon = True
            t.start()

            # 상태 "process"로 변경
            yt_url.status = "process"
            yt_url.save()
        
            return JsonResponse({"status" : yt_url.status}) # db에서 가져오는 값은 아님. 사실상 "process"가 전달되는 것
            
        except Exception as e:
            return JsonResponse({"Error" : e})

# api/status/
@api_view(['POST'])
def get_status(request):
    # status 반환
    if request.method == 'POST':
        url = request.data.get('url')
        if models.YouTubeURL.objects.filter(url=url).exists(): # DB에 해당 URL이 존재하면
            yt_url = models.YouTubeURL.objects.get(url=url)
            return JsonResponse({"status" : yt_url.status})
        else:
            return JsonResponse({"status" : "not exists"})

# api/ai/result/
@api_view(['POST', 'DELETE'])
def ai_result(request):
    # AI Inference 결과 반환
    if request.method == 'POST':
        url = request.data.get('url')
        try:
            yt_url = models.YouTubeURL.objects.get(url=url)

            STTserializer = STTResultSerializer(models.STTResult.objects.filter(url_id=yt_url), many=True)
            OCRserializer = OCRResultSerializer(models.OCRResult.objects.filter(url_id=yt_url), many=True)
            return Response({"STT" : STTserializer.data, "OCR" : OCRserializer.data})
        except Exception as e:
            return JsonResponse({"Error" : e})
    if request.method == 'DELETE':
        try:
            url = request.data.get('url')
            yt_url = models.YouTubeURL.objects.get(url=url)
            ocrResult = models.OCRResult.objects.filter(url_id=yt_url)
            ocrResult.delete()
            sttResult = models.STTResult.objects.filter(url_id=yt_url)
            sttResult.delete()
            return Response({"message" : "delete complete"})
        except Exception as e:
            return JsonResponse({"Error" : e})



def youtubeDefault(url):
    """
    args:
        url : youtube url
    """

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
        
def inference(yt_url, ai_obj):
    """
    args:
        yt_url : YouTubeURL Table Object
        ai_obj : AiModel Class Object
    """
    # OCRResult에 저장
    try:
        # STTResult에 저장
        stt_result = ai_obj.get_whisper_result()
        for _, row in stt_result.iterrows():
            data_model = models.STTResult(url_id=yt_url, start_time=row['start'], end_time=row['end'], text=row['text'])
            data_model.save()

        ocr_result = ai_obj.get_easyocr_result()
        for _, row in ocr_result.iterrows():
            data_model = models.OCRResult(url_id=yt_url, time=row['time'], text=row['text'], conf=row['conf'])
            data_model.save()

        yt_url.status = "success"
        yt_url.save()
    except Exception as e: # 에러 발생 시 status = fail으로 변경 
            print("[AI INFERENCE Error] : ", e)
            yt_url.status = "fail"
            yt_url.save()
