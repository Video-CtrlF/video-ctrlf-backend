from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(YouTubeURL)
admin.site.register(YouTubeInfo)
admin.site.register(YouTubeCaption)
admin.site.register(OCRResult)
admin.site.register(STTResult)
admin.site.register(CaptionKeyword)
admin.site.register(OCRKeyword)
admin.site.register(STTKeyword)