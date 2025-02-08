from datetime import date

from celery import shared_task
from constance import config
from django.conf import settings
from django.core.mail import send_mail

from .models import News


@shared_task
def send_news_email():
    today_news = News.objects.filter(publication_date__date=date.today())
    if not today_news:
        return

    news_titles = "\n".join(news.title for news in today_news)
    message = f"{config.EMAIL_MESSAGE}\n\n{news_titles}"

    send_mail(
        subject=config.EMAIL_SUBJECT,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=config.EMAIL_RECIPIENTS.split(","),
    )
