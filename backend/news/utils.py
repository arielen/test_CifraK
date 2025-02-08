from news import models


def upload_to_image(instance: "models.News", filename: str) -> str:
    return f"news/{instance.pk}/{filename}"
