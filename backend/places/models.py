from django.contrib.gis.db import models as gis_models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class Place(models.Model):
    name = models.CharField("Name of place", max_length=255)
    location = gis_models.PointField(
        "Geo-coordinates", help_text="Indicate a point on the map"
    )
    rating = models.PositiveSmallIntegerField(
        "Rating",
        help_text="From 0 to 25",
        validators=[MinValueValidator(0), MaxValueValidator(25)],
    )

    def __str__(self):
        return f"{self.name} ({self.rating}) at {self.location.x}, {self.location.y}"


class WeatherSummary(models.Model):
    place = models.ForeignKey(
        Place, on_delete=models.CASCADE, related_name="weather_summaries"
    )
    timestamp = models.DateTimeField(
        "Time of readings",
        default=timezone.now,
        editable=False,
    )
    temperature = models.FloatField("Temperature (°C)")
    humidity = models.PositiveSmallIntegerField("Humidity (%)")
    pressure = models.PositiveSmallIntegerField("Atmospheric pressure (mmHg)")
    wind_direction = models.CharField("Wind direction", max_length=50)
    wind_speed = models.FloatField("Wind speed (m/s)")

    class Meta:
        verbose_name = "Weather Summary"
        verbose_name_plural = "Weather Summary"
        ordering = ("-timestamp",)

    def __str__(self):
        return f"{self.place.name} at {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
