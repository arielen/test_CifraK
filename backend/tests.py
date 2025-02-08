import importlib
import sys
from datetime import datetime

import pytest
from config.schedules import EmailCrontabSchedule
from constance import config
from django.contrib.auth import get_user_model

User = get_user_model()


# Автоматически удаляем суперпользователя "admin" перед каждым тестом
@pytest.fixture(autouse=True)
def clean_superuser(db):
    User.objects.filter(username="admin").delete()


# Автоматически сбрасываем модуль create_admin, чтобы его код выполнялся заново
@pytest.fixture(autouse=True)
def reset_create_admin_module():
    sys.modules.pop("create_admin", None)


class TestCreateAdmin:
    @pytest.mark.django_db
    def test_create_superuser_when_not_exists(self, capsys, monkeypatch):
        """
        Проверяем, что если суперпользователь не существует,
        модуль create_admin создаёт его и выводит соответствующие сообщения.
        """
        monkeypatch.setenv("DJANGO_SUPERUSER_USERNAME", "admin")
        monkeypatch.setenv("DJANGO_SUPERUSER_EMAIL", "admin@example.com")
        monkeypatch.setenv("DJANGO_SUPERUSER_PASSWORD", "admin")

        import create_admin

        importlib.reload(create_admin)

        captured = capsys.readouterr().out
        assert "Creating superuser admin..." in captured
        assert "Superuser created." in captured

        user = User.objects.get(username="admin")
        assert user.is_superuser
        assert user.is_staff

    @pytest.mark.django_db
    def test_create_superuser_when_already_exists(self, capsys, monkeypatch):
        """
        Проверяем, что если суперпользователь уже существует,
        модуль create_admin выводит сообщение о его наличии.
        """
        User.objects.create_superuser(
            username="admin", email="admin@example.com", password="admin"
        )
        monkeypatch.setenv("DJANGO_SUPERUSER_USERNAME", "admin")
        monkeypatch.setenv("DJANGO_SUPERUSER_EMAIL", "admin@example.com")
        monkeypatch.setenv("DJANGO_SUPERUSER_PASSWORD", "admin")

        import create_admin

        importlib.reload(create_admin)

        captured = capsys.readouterr().out
        assert "Superuser already exists." in captured


class TestEmailCrontabSchedule:
    @pytest.mark.django_db
    def test_valid_config(self, monkeypatch):
        """
        Если в конфигурации указан корректный EMAIL_SEND_TIME,
        EmailCrontabSchedule должен использовать заданное время.
        """
        monkeypatch.setattr(config, "EMAIL_SEND_TIME", "10:15")
        schedule = EmailCrontabSchedule()
        schedule.is_due(datetime.now())
        assert schedule.hour == {10}
        assert schedule.minute == {15}

    @pytest.mark.django_db
    def test_invalid_config(self, monkeypatch):
        """
        Если в конфигурации указан некорректный EMAIL_SEND_TIME,
        EmailCrontabSchedule должен использовать значения по умолчанию.
        """
        monkeypatch.setattr(config, "EMAIL_SEND_TIME", "invalid")
        schedule = EmailCrontabSchedule()
        schedule.is_due(datetime.now())
        assert schedule.hour == {8}
        assert schedule.minute == {0}
