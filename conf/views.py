from django.shortcuts import render
from django.http import JsonResponse
from ai_model.ai_model_base import *
from ai_model.models import *

def test(request):
    return render(request,'test.html')

def success(request):
    url = request.POST.get('areadata')
    test = AiModel(url)
    yt_url = YouTubeURL(url = url)
    yt_url.save()
    result = test.get_whisper_result()
    for index, row in result.iterrows():
        my_model_instance = STTResult(
            start_time=row['start'],
            end_time=row['end'],
            text =row['text'],
            url_id = yt_url
        )
        my_model_instance.save()
    return JsonResponse({'js': 'ok'})