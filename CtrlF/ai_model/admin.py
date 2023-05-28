from django.contrib import admin
from . import models

# Register your models here.
admin.site.register(models.YouTubeURL)
admin.site.register(models.YouTubeCaption)
admin.site.register(models.OCRResult)
admin.site.register(models.STTResult)