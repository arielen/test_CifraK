from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticatedOrReadOnly

from .models import Place, WeatherSummary
from .serializers import PlaceSerializer, WeatherSummarySerializer


class PlaceViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = Place.objects.all()
    serializer_class = PlaceSerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update"):
            self.permission_classes = (IsAdminUser,)
        return super().get_permissions()


class WeatherViewSet(viewsets.ModelViewSet):
    queryset = WeatherSummary.objects.all()
    serializer_class = WeatherSummarySerializer
    http_method_names = ("get",)
