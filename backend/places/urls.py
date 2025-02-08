from rest_framework.routers import DefaultRouter

from .views import PlaceViewSet, WeatherViewSet

router = DefaultRouter()
router.register(r"places", PlaceViewSet, basename="places")
router.register(r"weather", WeatherViewSet, basename="weather")

urlpatterns = router.urls
