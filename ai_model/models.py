from django.db import models

class YouTubeURL(models.Model):
    id = models.BigAutoField(help_text="YouTube url ID", primary_key=True)
    url = models.URLField(help_text="YouTube url", max_length=200, blank=False, null=False)
    status = models.CharField(help_text="Status", max_length=10, default="created")
    def __str__(self):
        return str(self.id)

class YouTubeInfo(models.Model):
    url_id = models.ForeignKey("YouTubeURL", on_delete=models.CASCADE, db_column='url_id')
    title = models.CharField(help_text="YouTube Title", max_length=50)
    length = models.BigIntegerField(help_text="YouTube Length")
    video_size = models.JSONField()
    def __str__(self):
        return str(self.url_id) + " : " + self.title

class YouTubeCaption(models.Model):
    url_id = models.ForeignKey("YouTubeURL", on_delete=models.CASCADE, db_column='url_id')
    start_time = models.DecimalField(max_digits=20, decimal_places=4)
    end_time = models.DecimalField(max_digits=20, decimal_places=4)
    text = models.TextField(blank=True, null=True)
    def __str__(self):
        return f"{str(self.url_id)} : [{self.start_time:6.2f} ~ {self.end_time:6.2f}] {self.text}"

class OCRResult(models.Model):
    url_id = models.ForeignKey("YouTubeURL", on_delete=models.CASCADE, db_column='url_id')
    time = models.DecimalField(max_digits=20, decimal_places=4)
    text = models.TextField(blank=True, null=True)
    conf = models.DecimalField(max_digits=7, decimal_places=6, blank=True, null=True)
    bbox = models.JSONField(blank=True, null=True)
    def __str__(self):
        return f"{str(self.url_id)} : [{self.time:.2f}] {self.text} ({self.conf:.4f})"

class STTResult(models.Model):
    url_id = models.ForeignKey("YouTubeURL", on_delete=models.CASCADE, db_column='url_id')
    start_time = models.DecimalField(max_digits=20, decimal_places=4)
    end_time = models.DecimalField(max_digits=20, decimal_places=4)
    text = models.TextField(blank=True, null=True)
    def __str__(self):
        return f"{str(self.url_id)} : [{self.start_time:6.2f} ~ {self.end_time:6.2f}] {self.text}"

class CaptionKeyword(models.Model):
    url_id = models.ForeignKey("YouTubeURL", on_delete=models.CASCADE, db_column='url_id')
    keywords = models.JSONField()

class OCRKeyword(models.Model):
    url_id = models.ForeignKey("YouTubeURL", on_delete=models.CASCADE, db_column='url_id')
    keywords = models.JSONField()

class STTKeyword(models.Model):
    url_id = models.ForeignKey("YouTubeURL", on_delete=models.CASCADE, db_column='url_id')
    keywords = models.JSONField()