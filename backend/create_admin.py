import os
import django
from django.contrib.auth import get_user_model

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

User = get_user_model()

USERNAME = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
EMAIL = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@example.com")
PASSWORD = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "admin")

if not User.objects.filter(username=USERNAME).exists():
    print(f"Creating superuser {USERNAME}...")
    User.objects.create_superuser(username=USERNAME, email=EMAIL, password=PASSWORD)
    print("Superuser created.")
else:
    print("Superuser already exists.")
