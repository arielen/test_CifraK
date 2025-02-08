from .settings import *  # noqa

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.spatialite",
        "NAME": ":memory:",
    }
}

# SPATIALITE_LIBRARY_PATH = "/usr/lib/mod_spatialite.so"  # noqa
