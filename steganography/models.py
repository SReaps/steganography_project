
from django.db import models

class UploadedImage(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    original_image = models.ImageField(upload_to='uploaded_images/')
    encoded_image = models.ImageField(upload_to='encoded_images/', blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    bits_used = models.IntegerField(default=1)
    date_uploaded = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name or f"Image {self.id} (Uploaded on {self.date_uploaded.strftime('%Y-%m-%d')})"