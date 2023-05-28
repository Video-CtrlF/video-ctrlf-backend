from django.urls import path
from django.http import HttpResponse
from ai_model.ai_model_base import AiModel
from . import models

def index(req):
    return HttpResponse('AI Model 페이지입니다.')

def test(req):
    print("---------START-----------")
    url = "https://www.youtube.com/watch?v=bGcVkNP1tPs&t=2s&ab_channel=1%EB%B6%84%EB%AF%B8%EB%A7%8C"
    if models.YouTubeURL.objects.filter(url=url).exists(): # 이미 DB에 해당 URL이 존재하는지 확인
        print("already exist!!!")
        return HttpResponse("이미 존재")

    # YouTubeURL에 저장
    yt_url = models.YouTubeURL(url=url)
    yt_url.save()
    
    test_ = AiModel(url)

    # YouTubeInfo에 저장
    yt_info = models.YouTubeInfo(url_id=yt_url, title=test_.yt.title, length=test_.yt.length)
    yt_info.save()

    # YouTubeCaption에 저장
    yt_caption = test_.get_captions()
    for _, row in yt_caption.iterrows():
        data_model = models.YouTubeCaption(url_id=yt_url, start_time=row['start'], end_time=row['end'], text=row['text'])
        data_model.save()

    # OCRResult에 저장
    ocr_result = test_.get_easyocr_result()
    for _, row in ocr_result.iterrows():
        data_model = models.OCRResult(url_id=yt_url, time=row['time'], text=row['text'], conf=row['conf'])
        data_model.save()

    # STTResult에 저장
    stt_result = test_.get_whisper_result()
    for _, row in stt_result.iterrows():
        data_model = models.STTResult(url_id=yt_url, start_time=row['start'], end_time=row['end'], text=row['text'])
        data_model.save()
    print("---------DONE-----------")
    return HttpResponse("완료")

urlpatterns = [
    path("", index),
    path("test/", test),
]
