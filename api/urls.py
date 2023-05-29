from django.urls import path, include
from rest_framework import routers
from . import views

router = routers.DefaultRouter() # DefaultRouter를 설정
router.register("YTUrl", views.YTUrlViewSet) # yturlviewset과 yturl이라는 router 등록
router.register("YTInfo", views.YTInfoViewSet)
router.register("YTCaption", views.YTCaptionViewSet)
router.register("OCRResult", views.OCRResultViewSet)
router.register("STTResult", views.STTResultViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
