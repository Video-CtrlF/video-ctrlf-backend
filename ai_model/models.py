from django.db import models

class YouTubeURL(models.Model):
    id = models.BigAutoField(help_text="YouTube url ID", primary_key=True)
    url = models.URLField(help_text="YouTube url", max_length=200, blank=False, null=False)

class YouTubeInfo(models.Model):
    url_id = models.ForeignKey("YouTubeURL", on_delete=models.CASCADE)
    title = models.CharField(help_text="YouTube Title", max_length=50)
    length = models.IntegerField(help_text="YouTube Length")

class YouTubeCaption(models.Model):
    url_id = models.ForeignKey("YouTubeURL", on_delete=models.CASCADE)
    start_time = models.DecimalField(max_digits=20, decimal_places=4, blank=True, null=True)
    end_time = models.DecimalField(max_digits=20, decimal_places=4, blank=True, null=True)
    text = models.TextField(blank=True, null=True)

class OCRResult(models.Model):
    url_id = models.ForeignKey("YouTubeURL", on_delete=models.CASCADE)
    time = models.DecimalField(max_digits=20, decimal_places=4, blank=True, null=True)
    text = models.TextField(blank=True, null=True)
    conf = models.DecimalField(max_digits=7, decimal_places=6, blank=True, null=True)
    # bbox 는 나중에 추가

class STTResult(models.Model):
    url_id = models.ForeignKey("YouTubeURL", on_delete=models.CASCADE)
    start_time = models.DecimalField(max_digits=20, decimal_places=4, blank=True, null=True)
    end_time = models.DecimalField(max_digits=20, decimal_places=4, blank=True, null=True)
    text = models.TextField(blank=True, null=True)
