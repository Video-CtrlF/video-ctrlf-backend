"""
URL configuration for conf project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.http import JsonResponse
from ai_model.ai_model_base import *
import pandas as pd
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

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', test),
    path('success/', success),
]