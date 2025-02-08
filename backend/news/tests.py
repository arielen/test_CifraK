from io import BytesIO

import pytest
from constance import config
from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from PIL import Image
from rest_framework.test import APIClient

from .models import News
from .signals import news_post_save, news_pre_save
from .tasks import send_news_email


# ============================================================
#                          HELPERS
# ============================================================
# region Helpers
def generate_test_image_bytes(filename="test.jpg", size=(100, 100), color="blue"):
    """Генерирует байты изображения с помощью Pillow."""
    image = Image.new("RGB", size, color)
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    buffer.seek(0)
    return buffer.read()


# endregion


# ============================================================
#                          FIXTURES
# ============================================================
# region Fixtures
@pytest.fixture
def test_image_bytes():
    return generate_test_image_bytes()


@pytest.fixture
def test_content_file(test_image_bytes):
    """ContentFile для тестирования сигналов (используется в ImageField)."""
    return ContentFile(test_image_bytes, name="test.jpg")


@pytest.fixture
def test_uploaded_file(test_image_bytes):
    """SimpleUploadedFile для API тестов (используется в ImageField)."""
    return SimpleUploadedFile("test.jpg", test_image_bytes, content_type="image/jpeg")


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_a(db):
    return User.objects.create_user(username="usera", password="password")


@pytest.fixture
def user_b(db):
    return User.objects.create_user(username="userb", password="password")


@pytest.fixture
def default_test_user(db):
    return User.objects.create_user(
        username="testuser", email="test@example.com", password="password"
    )


@pytest.fixture
def news_item(user_a, test_uploaded_file):
    return News.objects.create(
        title="Test News",
        content="This is a test news item.",
        author=user_a,
        main_image=test_uploaded_file,
    )


# endregion


# ============================================================
#                          SIGNALS TESTS
# ============================================================
# region Signals Tests
@pytest.mark.django_db
class TestNewsSignals:
    def test_news_pre_save_new_instance(self, default_test_user, test_content_file):
        """
        Если объект News еще не сохранён (нет pk),
        сигнал pre_save не должен выполнять никаких действий.
        """
        news = News(
            title="New News",
            content="Some content",
            author=default_test_user,
            main_image=test_content_file,
        )
        news_pre_save(News, news)  # Если ошибка не возникает – всё ок.

    def test_news_pre_save_instance_not_found(
        self, default_test_user, monkeypatch, test_content_file
    ):
        """
        Если получение предыдущей версии объекта вызывает News.DoesNotExist,
        сигнал pre_save завершается без ошибок.
        """
        news = News.objects.create(
            title="Existing News",
            content="Initial content",
            author=default_test_user,
            main_image=test_content_file,
            preview_image=test_content_file,
        )
        news.main_image = test_content_file
        monkeypatch.setattr(
            News.objects,
            "get",
            lambda **kwargs: (_ for _ in ()).throw(News.DoesNotExist),
        )
        news_pre_save(News, news)

    def test_news_pre_save_deletes_old_preview(
        self, default_test_user, monkeypatch, test_content_file
    ):
        """
        При обновлении main_image, если старая версия имеет preview_image,
        должна быть вызвана функция delete() у старого preview_image.
        """
        news = News.objects.create(
            title="Test News",
            content="Test content",
            author=default_test_user,
            main_image=test_content_file,
            preview_image=test_content_file,
        )
        old_preview = news.preview_image
        assert old_preview, "Изначально preview не создан"
        assert default_storage.exists(old_preview.name), (
            "Файл preview отсутствует в хранилище"
        )

        news.main_image = test_content_file
        old_instance = News.objects.get(pk=news.pk)
        delete_called = False

        def fake_delete(save):
            nonlocal delete_called
            delete_called = True

        monkeypatch.setattr(old_instance.preview_image, "delete", fake_delete)
        monkeypatch.setattr(News.objects, "get", lambda **kwargs: old_instance)
        news_pre_save(News, news)
        assert delete_called, "delete() не был вызван для старого preview_image"

    def test_news_post_save_generates_preview(
        self, default_test_user, test_uploaded_file
    ):
        """
        Если присутствует main_image, сигнал post_save должен создать preview_image.
        """
        news = News.objects.create(
            title="Test News",
            content="Test content",
            author=default_test_user,
            main_image=test_uploaded_file,
        )
        assert news.preview_image, "Preview не был создан"
        assert default_storage.exists(news.preview_image.name), (
            "Файл preview отсутствует в хранилище"
        )
        assert getattr(news, "_preview_generated", False), (
            "_preview_generated не установлен"
        )

    def test_news_post_save_no_main_image(self, default_test_user):
        """
        Если main_image отсутствует, сигнал post_save не должен создавать preview_image.
        """
        news = News.objects.create(
            title="Test News",
            content="Test content",
            author=default_test_user,
            main_image=None,
        )
        news_post_save(News, news, created=False)
        assert not news.preview_image, "Preview создан, хотя main_image отсутствует"

    def test_news_post_save_already_generated(
        self, default_test_user, test_uploaded_file
    ):
        """
        Если флаг _preview_generated уже установлен, preview_image не должен изменяться.
        """
        news = News.objects.create(
            title="Test News",
            content="Test content",
            author=default_test_user,
            main_image=test_uploaded_file,
        )
        news._preview_generated = True
        prev_preview = news.preview_image
        news_post_save(News, news, created=False)
        assert news.preview_image == prev_preview, (
            "Preview изменился, несмотря на установленный флаг"
        )


# endregion


# ============================================================
#                          VIEWS TESTS
# ============================================================
# region View Tests
@pytest.mark.django_db
class TestNewsViews:
    def test_get_news_list(self, api_client, news_item):
        """Проверка, что GET /news/ возвращает список новостей."""
        url = reverse("news-list")
        response = api_client.get(url)
        assert response.status_code == 200
        assert any(item["id"] == news_item.id for item in response.data)

    def test_get_news_detail(self, api_client, news_item):
        """Проверка, что GET /news/<id>/ возвращает детали новости."""
        url = reverse("news-detail", args=[news_item.id])
        response = api_client.get(url)
        assert response.status_code == 200
        assert response.data["id"] == news_item.id

    def test_create_news_unauthenticated(self, api_client, test_uploaded_file):
        """
        Проверка, что неавторизованным пользователям запрещено создавать новости.
        Даже если передан author.
        """
        url = reverse("news-list")
        data = {
            "title": "New News",
            "content": "Content of new news.",
            "author": 1,
            "main_image": test_uploaded_file,
        }
        response = api_client.post(url, data, format="multipart")
        assert response.status_code in (401, 403)

    def test_create_news_authenticated(self, api_client, user_a, test_uploaded_file):
        """Проверка, что авторизованный пользователь может создать новость."""
        api_client.force_authenticate(user=user_a)
        url = reverse("news-list")
        data = {
            "title": "Created News",
            "content": "New content",
            "author": user_a.id,
            "main_image": test_uploaded_file,
        }
        response = api_client.post(url, data, format="multipart")
        assert response.status_code == 201
        assert response.data["author"] == user_a.id

    def test_update_news_as_author(self, api_client, user_a, news_item):
        """Проверка, что автор может обновить свою новость."""
        api_client.force_authenticate(user=user_a)
        url = reverse("news-detail", args=[news_item.id])
        data = {
            "title": "Updated Title",
            "content": news_item.content,
            "author": user_a.id,
        }
        response = api_client.patch(url, data, format="json")
        assert response.status_code == 200
        assert response.data["title"] == "Updated Title"

    def test_update_news_as_non_author(self, api_client, user_b, news_item):
        """Проверка, что неавторизованный (не автор) не может обновить новость."""
        api_client.force_authenticate(user=user_b)
        url = reverse("news-detail", args=[news_item.id])
        data = {"title": "Hacked Title"}
        response = api_client.patch(url, data, format="json")
        assert response.status_code == 403

    def test_delete_news_as_author(self, api_client, user_a, news_item):
        """Проверка, что автор может удалить свою новость."""
        api_client.force_authenticate(user=user_a)
        url = reverse("news-detail", args=[news_item.id])
        response = api_client.delete(url)
        assert response.status_code == 204

    def test_delete_news_as_non_author(self, api_client, user_b, news_item):
        """Проверка, что неавтор (и не админ) не может удалить новость."""
        api_client.force_authenticate(user=user_b)
        url = reverse("news-detail", args=[news_item.id])
        response = api_client.delete(url)
        assert response.status_code == 403


# endregion


# ============================================================
#                          TASKS TESTS
# ============================================================
# region Task Tests
@pytest.mark.django_db
class TestNewsEmailTask:
    def test_send_news_email_no_news(self, monkeypatch):
        """
        Если сегодня не опубликовано ни одной новости,
        задача должна вернуть None и не отправить письмо.
        """
        News.objects.all().delete()
        monkeypatch.setattr(config, "EMAIL_MESSAGE", "Test Email Message")
        monkeypatch.setattr(config, "EMAIL_SUBJECT", "Test Email Subject")
        monkeypatch.setattr(config, "EMAIL_RECIPIENTS", "recipient@example.com")
        mail.outbox = []
        result = send_news_email()
        assert result is None, "При отсутствии новостей задача должна вернуть None."
        assert len(mail.outbox) == 0, (
            "Письмо не должно отправляться, если новостей нет."
        )

    def test_send_news_email_with_news(
        self, monkeypatch, user_a, user_b, test_uploaded_file
    ):
        """
        Если сегодня опубликованы новости, задача должна отправить письмо,
        содержащее сконфигурированное сообщение и заголовки новостей.
        """
        now_dt = timezone.now()
        News.objects.create(
            title="News One",
            content="Content One",
            author=user_a,
            main_image=test_uploaded_file,
            publication_date=now_dt,
        )
        News.objects.create(
            title="News Two",
            content="Content Two",
            author=user_b,
            main_image=test_uploaded_file,
            publication_date=now_dt,
        )
        monkeypatch.setattr(config, "EMAIL_MESSAGE", "Daily News:")
        monkeypatch.setattr(config, "EMAIL_SUBJECT", "Today's News")
        monkeypatch.setattr(
            config, "EMAIL_RECIPIENTS", "recipient@example.com,another@example.com"
        )
        mail.outbox = []
        send_news_email()
        assert len(mail.outbox) == 1, "При наличии новостей должно отправляться письмо."
        email = mail.outbox[0]
        assert email.subject == "Today's News"
        expected_message = "Daily News:\n\nNews One\nNews Two"
        assert email.body == expected_message, "Тело письма сформировано неверно."
        assert email.from_email == settings.DEFAULT_FROM_EMAIL
        expected_recipients = ["recipient@example.com", "another@example.com"]
        assert email.to == expected_recipients


# endregion
