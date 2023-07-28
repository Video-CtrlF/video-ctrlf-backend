from django.urls import path
from . import views

urlpatterns = [
    path("check-existence/", views.url_check), 
    path("captions/", views.get_caption), 
    path("status/", views.get_status),
    path("ai/", views.ai_inference),
    path("ai/result/", views.ai_result),
]