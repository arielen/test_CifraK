from django.contrib.gis.geos import Point
from rest_framework import fields, serializers

from .models import Place, WeatherSummary


class LocationField(serializers.ListField):
    child = serializers.FloatField()

    def to_representation(self, value):
        if value:
            return [value.x, value.y]
        return None

    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        if not isinstance(data, list) or len(data) != 2:
            raise serializers.ValidationError(
                "The location field must be a list of two numbers: "
                "[longitude, latitude]."
            )
        try:
            return Point(data[0], data[1])
        except Exception as e:
            raise serializers.ValidationError("Incorrect coordinates: " + str(e))


class PlaceSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=255, required=True)
    location = LocationField(required=True)
    rating = serializers.IntegerField(
        validators=(fields.MinValueValidator(0), fields.MaxValueValidator(25)),
        required=True,
    )

    class Meta:
        model = Place
        geo_field = "location"
        fields = "__all__"


class WeatherSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = WeatherSummary
        fields = "__all__"
