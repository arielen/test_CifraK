from django.contrib.auth.models import User
from django.db import models

from .utils import upload_to_image


class News(models.Model):
    title = models.CharField(max_length=255)
    main_image = models.ImageField(upload_to=upload_to_image)
    preview_image = models.ImageField(upload_to=upload_to_image, blank=True, null=True)
    content = models.TextField()
    publication_date = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
