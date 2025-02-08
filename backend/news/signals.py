from io import BytesIO

from django.core.files.base import ContentFile
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from PIL import Image

from .models import News


@receiver(pre_save, sender=News)
def news_pre_save(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old_instance = News.objects.get(pk=instance.pk)
    except News.DoesNotExist:
        return

    if old_instance.main_image != instance.main_image:
        if old_instance.preview_image:
            old_instance.preview_image.delete(save=False)


@receiver(post_save, sender=News)
def news_post_save(sender, instance, created, **kwargs):
    if hasattr(instance, "_preview_generated"):
        return
    if not instance.main_image:
        return

    try:
        img = Image.open(instance.main_image)
        img.thumbnail((200, 200))
        buffer = BytesIO()
        img.save(buffer, format="JPEG")
        buffer.seek(0)

        instance.preview_image.save(
            "preview.jpg", ContentFile(buffer.read()), save=False
        )
        instance._preview_generated = True

        News.objects.filter(pk=instance.pk).update(preview_image=instance.preview_image)
    except Exception as e:
        print(f"Error generating preview: {e}")
