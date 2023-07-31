from ai_model import models
from ai_model.ai_model_base import AiModel

from rest_framework.response import Response
from rest_framework.decorators import api_view

from .serializers import *

import threading
from pytube import YouTube

# Create your views here.

# api/check-existence?url=https://www.youtube.com/~~~/
@api_view(['GET'])
def url_check(request):
    # db에 url 이 있는지 확인
    if request.method == 'GET':
        try:
            url = request.GET.get('url', None) # Query param
            if url:
                url = get_watch_url(url)
                if models.YouTubeURL.objects.filter(url=url).exists(): # DB에 해당 URL이 존재하는지 확인
                    return Response({"isExist" : True})
                return Response({"isExist" : False})
            else:
                return Response({"Error" : "url was not sent"})
        except Exception as e:
            return Response({"Error" : e})

# api/captions/
@api_view(['POST'])
def get_caption(request):
    # youtube에서 제공하는 caption을 return
    if request.method == 'POST':
        try:
            url = request.data.get('url')
            if url:
                url = get_watch_url(url)
                if not models.YouTubeURL.objects.filter(url=url).exists(): # DB에 해당 URL이 없으면
                    # 기본 처리 (db에 url 저장 및 caption)
                    youtubeDefault(url=url)
                yt_url = models.YouTubeURL.objects.get(url=url)
                YTCaption_serializer = YTCaptionSerializer(models.YouTubeCaption.objects.filter(url_id=yt_url), many=True)
                return Response({
                        "info" : YTInfoSerializer(models.YouTubeInfo.objects.get(url_id=yt_url)).data,
                        "keywords" : CaptionKeywordSerializer(models.CaptionKeyword.objects.get(url_id=yt_url)).data['keywords']['topN'],
                        "caption" : YTCaption_serializer.data
                    })
            else:
                return Response({"Error" : "url was not sent"})
        except Exception as e:
            return Response({"Error" : e})
    
# api/ai/
@api_view(['POST'])
def ai_inference(request):
    # AI 모델 스레드로 돌리고 status 반환
    if request.method == 'POST':
        try:
            url = request.data.get('url')
            if url:
                url = get_watch_url(url)
                if not models.YouTubeURL.objects.filter(url=url).exists(): # DB에 해당 URL이 없으면
                    return Response({"Error" : "url not exists"})

                yt_url = models.YouTubeURL.objects.get(url=url)
                if yt_url.status == "success":
                    return Response({"status" : "success"})
                elif yt_url.status == "process":
                    return Response({"status" : "process"})
                elif yt_url == "fail":
                    # api/ai/result/ ['DELETE']와 동일한 코드
                    yt_url = models.YouTubeURL.objects.get(url=url)
                    ocrResult = models.OCRResult.objects.filter(url_id=yt_url)
                    ocrResult.delete()
                    ocrKeyword = models.OCRKeyword.objects.filter(url_id=yt_url)
                    ocrKeyword.delete()

                    sttResult = models.STTResult.objects.filter(url_id=yt_url)
                    sttResult.delete()
                    sttKeyword = models.STTKeyword.objects.filter(url_id=yt_url)
                    sttKeyword.delete()

                ai_obj = AiModel(url)

                # 스레드로 실행
                t = threading.Thread(target=inference, args=(yt_url, ai_obj, ))
                t.daemon = True
                t.start()

                # 상태 "process"로 변경
                yt_url.status = "process"
                yt_url.save()
            
                return Response({"status" : yt_url.status}) # db에서 가져오는 값은 아님. 사실상 "process"가 전달되는 것
            else:
                return Response({"Error" : "url was not sent"})
        except Exception as e:
            return Response({"Error" : e})

# api/statusurl=https://www.youtube.com/~~~/
@api_view(['GET'])
def get_status(request):
    # status 반환
    if request.method == 'GET':
        try:
            url = request.GET.get('url', None) # Query param
            if url:
                url = get_watch_url(url)
                if models.YouTubeURL.objects.filter(url=url).exists(): # DB에 해당 URL이 존재하면
                    yt_url = models.YouTubeURL.objects.get(url=url)
                    return Response({"status" : yt_url.status})
                else:
                    return Response({"status" : "url not exists"})
            else:
                return Response({"Error" : "url was not sent"})
        except Exception as e:
            return Response({"Error" : e})

# api/ai/result/
@api_view(['GET', 'DELETE'])
def ai_result(request):
    # AI Inference 결과 반환
    if request.method == 'GET':
        try:
            url = request.GET.get('url', None) # Query param
            if url:
                url = get_watch_url(url)
                yt_url = models.YouTubeURL.objects.get(url=url)

                STTserializer = STTResultSerializer(models.STTResult.objects.filter(url_id=yt_url), many=True)
                OCRserializer = OCRResultSerializer(models.OCRResult.objects.filter(url_id=yt_url), many=True)
                sttKeyword = models.STTKeyword.objects.filter(url_id=yt_url)
                if sttKeyword:
                    retSttKeyword = STTKeywordSerializer(sttKeyword, many=True).data[0]['keywords']['topN'],
                else:
                    retSttKeyword = None
                ocrKeyword = models.OCRKeyword.objects.filter(url_id=yt_url)
                if ocrKeyword:
                    retOcrKeyword = OCRKeywordSerializer(ocrKeyword, many=True).data[0]['keywords']['topN'],
                else:
                    retOcrKeyword = None
                return Response({
                    "info" : YTInfoSerializer(models.YouTubeInfo.objects.get(url_id=yt_url)).data,
                    "STTkeywords" : retSttKeyword,
                    "OCRkeywords" : retOcrKeyword,
                    "scripts" : {
                        "STT" : STTserializer.data, 
                        "OCR" : OCRserializer.data
                    }
                })
            else:
                return Response({"Error" : "url was not sent"})
        except Exception as e:
            return Response({"Error" : e})
    if request.method == 'DELETE':
        try:
            url = request.data.get('url')
            yt_url = models.YouTubeURL.objects.get(url=url)
            ocrResult = models.OCRResult.objects.filter(url_id=yt_url)
            ocrResult.delete()
            ocrKeyword = models.OCRKeyword.objects.filter(url_id=yt_url)
            ocrKeyword.delete()

            sttResult = models.STTResult.objects.filter(url_id=yt_url)
            sttResult.delete()
            sttKeyword = models.STTKeyword.objects.filter(url_id=yt_url)
            sttKeyword.delete()

            return Response({"message" : "delete complete"})
        except Exception as e:
            return Response({"Error" : e})

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
    video_size = {
            "height": ai_obj.height,
            "width": ai_obj.width
        }
    models.YouTubeInfo(url_id=yt_url, title=ai_obj.yt.title, length=ai_obj.yt.length, video_size=video_size).save()

    # YouTubeCaption에 저장
    yt_caption, keywords = ai_obj.get_captions()
    models.CaptionKeyword(url_id=yt_url, keywords={"topN" : keywords}).save()

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
        stt_result, stt_keywords = ai_obj.get_whisper_result()
        for _, row in stt_result.iterrows():
            data_model = models.STTResult(url_id=yt_url, start_time=row['start'], end_time=row['end'], text=row['text'])
            data_model.save()
        
        # 핵심 Keyword 저장
        models.STTKeyword(url_id=yt_url, keywords={"topN" : stt_keywords}).save()

        ocr_result, ocr_keywords = ai_obj.get_easyocr_result()
        bbox = ("tl", "tr", "br", "bl")
        for _, row in ocr_result.iterrows():
            data_model = models.OCRResult(url_id=yt_url, time=row['time'], text=row['text'], conf=row['conf'])
            coordinates = {}
            for i, (x, y) in enumerate(row['bbox']):
                coordinates[bbox[i]] = (x, y)
            data_model.bbox = coordinates
            data_model.save()

        # 핵심 Keyword 저장
        models.OCRKeyword(url_id=yt_url, keywords={"topN" : ocr_keywords}).save()

        yt_url.status = "success"
        yt_url.save()
    except Exception as e: # 에러 발생 시 status = fail으로 변경 
            print("[AI INFERENCE Error] : ", e)
            yt_url.status = "fail"
            yt_url.save()

def get_watch_url(url):
    return YouTube(url).watch_url