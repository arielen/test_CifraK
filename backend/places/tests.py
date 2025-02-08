from datetime import timedelta

import aiohttp
import pytest
from asgiref.sync import sync_to_async
from django.contrib.gis.geos import Point
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAdminUser
from rest_framework.test import APIClient

from .models import Place, WeatherSummary
from .serializers import LocationField, PlaceSerializer, WeatherSummarySerializer
from .tasks import fetch_weather_summary, process_weather_for_place_async
from .utils import get_weather
from .views import PlaceViewSet


# ============================================================
#                          HELPERS
# ============================================================
# region Helpers
class FakeResponse:
    def __init__(self, json_data):
        self._json = json_data

    async def json(self):
        return self._json

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass


class FakeClientSession:
    def __init__(self, json_data):
        self._json = json_data

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    def get(self, url):
        return FakeResponse(self._json)


# endregion


# ============================================================
#                          FIXTURES
# ============================================================
# region Fixtures
@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def create_place(db):
    def make_place(name="Test Place", rating=10, x=0.0, y=0.0):
        return Place.objects.create(name=name, location=Point(x, y), rating=rating)

    return make_place


# endregion


# ============================================================
#                          VIEWS TESTS
# ============================================================
# region View Tests
class TestPlaceViewSet:
    def test_get_permissions_for_create_action(self):
        view = PlaceViewSet()
        view.action = "create"
        permissions = view.get_permissions()
        assert any(isinstance(p, IsAdminUser) for p in permissions), (
            "Create action should use IsAdminUser permission."
        )


# endregion


# ============================================================
#                          SERIALIZERS TESTS
# ============================================================
# region Serializers Tests
class TestLocationField:
    def test_to_representation(self):
        point = Point(12.34, 56.78)
        field = LocationField()
        assert field.to_representation(point) == [point.x, point.y]

    def test_to_internal_value_valid(self):
        field = LocationField()
        data = [12.34, 56.78]
        point = field.to_internal_value(data)
        assert isinstance(point, Point) and point.x == 12.34 and point.y == 56.78

    def test_to_internal_value_invalid_length(self):
        field = LocationField()
        with pytest.raises(
            ValidationError, match="The location field must be a list of two numbers"
        ):
            field.to_internal_value([12.34])

    @pytest.mark.django_db
    def test_to_internal_value_invalid_data_type(self, monkeypatch):
        field = LocationField()
        with pytest.raises(
            ValidationError, match=r'Expected a list of items but got type "str"'
        ):
            field.to_internal_value("not a list")
        valid_data = [4.52, 1.23]

        def dummy_point(x, y):
            raise Exception("forced error")

        monkeypatch.setattr("places.serializers.Point", dummy_point)
        with pytest.raises(ValidationError, match="Incorrect coordinates:"):
            field.to_internal_value(valid_data)
        assert field.to_representation(None) is None

    def test_to_internal_value_invalid_coordinates(self):
        field = LocationField()
        with pytest.raises(ValidationError, match="A valid number is required"):
            field.to_internal_value(["a", "b"])


class TestPlaceSerializer:
    @pytest.mark.django_db
    def test_valid_data(self):
        data = {"name": "Test Place", "location": [12.34, 56.78], "rating": 10}
        serializer = PlaceSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        place = serializer.save()
        assert place.name == data["name"]
        assert isinstance(place.location, Point)
        assert place.location.x == data["location"][0]
        assert place.location.y == data["location"][1]
        assert place.rating == data["rating"]

    @pytest.mark.django_db
    def test_invalid_rating(self):
        data = {"name": "Test Place", "location": [12.34, 56.78], "rating": 30}
        serializer = PlaceSerializer(data=data)
        assert not serializer.is_valid() and "rating" in serializer.errors

    @pytest.mark.django_db
    def test_missing_field(self):
        data = {"name": "Test Place", "rating": 10}
        serializer = PlaceSerializer(data=data)
        assert not serializer.is_valid() and "location" in serializer.errors

    @pytest.mark.django_db
    def test_to_representation(self):
        point = Point(12.34, 56.78)
        place = Place.objects.create(name="Test Place", location=point, rating=10)
        rep = PlaceSerializer(instance=place).data
        assert rep["location"] == [point.x, point.y]
        assert rep["name"] == "Test Place"
        assert rep["rating"] == 10


class TestWeatherSummarySerializer:
    @pytest.mark.django_db
    def test_valid_data(self):
        place = Place.objects.create(
            name="Test Place", location=Point(12.34, 56.78), rating=10
        )
        weather_data = {
            "place": place,
            "temperature": 25.0,
            "humidity": 70,
            "pressure": 1012,
            "wind_direction": "N",
            "wind_speed": 5.5,
            "timestamp": timezone.now(),
        }
        weather_summary = WeatherSummary.objects.create(**weather_data)
        rep = WeatherSummarySerializer(instance=weather_summary).data
        assert rep["temperature"] == weather_data["temperature"]
        assert rep["humidity"] == weather_data["humidity"]
        assert rep["pressure"] == weather_data["pressure"]
        assert rep["wind_direction"] == weather_data["wind_direction"]
        assert rep["wind_speed"] == weather_data["wind_speed"]
        assert rep["place"] == place.id


# endregion


# ============================================================
#                          TASKS TESTS
# ============================================================
# region Tasks Tests
DUMMY_WEATHER = {
    "temperature": 20.5,
    "humidity": 55,
    "pressure": 1010,
    "wind_direction": "NE",
    "wind_speed": 3.3,
}


class TestWeatherTasks:
    @pytest.mark.django_db(transaction=True)
    @pytest.mark.asyncio
    async def test_process_weather_for_place_async(self, monkeypatch):
        place = await sync_to_async(Place.objects.create)(
            name="Test Place", location=Point(12.34, 56.78), rating=10
        )

        async def dummy_get_weather(x, y):
            return DUMMY_WEATHER

        monkeypatch.setattr("places.tasks.get_weather", dummy_get_weather)
        await process_weather_for_place_async(place)
        weather_summary = await sync_to_async(WeatherSummary.objects.get)(place=place)
        assert weather_summary.temperature == DUMMY_WEATHER["temperature"]
        assert weather_summary.humidity == DUMMY_WEATHER["humidity"]
        assert weather_summary.pressure == DUMMY_WEATHER["pressure"]
        assert weather_summary.wind_direction == DUMMY_WEATHER["wind_direction"]
        assert weather_summary.wind_speed == DUMMY_WEATHER["wind_speed"]

    @pytest.mark.django_db(transaction=True)
    def test_fetch_weather_summary(self, monkeypatch):
        place = Place.objects.create(
            name="Test Place", location=Point(12.34, 56.78), rating=10
        )

        async def dummy_get_weather(x, y):
            return DUMMY_WEATHER

        monkeypatch.setattr("places.tasks.get_weather", dummy_get_weather)
        result = fetch_weather_summary()
        assert "Weather summary tasks dispatched at" in result
        weather_summary = WeatherSummary.objects.get(place=place)
        assert weather_summary.temperature == DUMMY_WEATHER["temperature"]
        assert weather_summary.humidity == DUMMY_WEATHER["humidity"]
        assert weather_summary.pressure == DUMMY_WEATHER["pressure"]
        assert weather_summary.wind_direction == DUMMY_WEATHER["wind_direction"]
        assert weather_summary.wind_speed == DUMMY_WEATHER["wind_speed"]

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.asyncio
    async def test_process_weather_for_place_async_exception(self, monkeypatch, capsys):
        place = await sync_to_async(Place.objects.create)(
            name="Test Place", location=Point(12.34, 56.78), rating=10
        )

        async def dummy_get_weather(x, y):
            raise Exception("Dummy error")

        monkeypatch.setattr("places.tasks.get_weather", dummy_get_weather)
        with pytest.raises(Exception, match="Dummy error"):
            await process_weather_for_place_async(place)
        captured = capsys.readouterr().out
        assert f"Error processing place {place.id}:" in captured

    @pytest.mark.django_db(transaction=True)
    def test_fetch_weather_summary_print_exception(self, monkeypatch, capsys):
        place = Place.objects.create(
            name="Test Place", location=Point(12.34, 56.78), rating=10
        )

        async def dummy_get_weather(x, y):
            raise Exception("Test error")

        monkeypatch.setattr("places.tasks.get_weather", dummy_get_weather)
        result = fetch_weather_summary()
        captured = capsys.readouterr().out
        assert f"Error for place {place.pk}: Test error" in captured
        assert "Weather summary tasks dispatched at" in result


# endregion


# ============================================================
#                          MODELS TESTS
# ============================================================
# region Models Tests
class TestPlaceModel:
    @pytest.mark.django_db
    def test_str(self):
        point = Point(12.34, 56.78)
        place = Place.objects.create(name="Test Place", location=point, rating=10)
        expected_str = "Test Place (10) at 12.34, 56.78"
        assert str(place) == expected_str

    @pytest.mark.django_db
    def test_rating_min_validator(self):
        point = Point(12.34, 56.78)
        place = Place(name="Test Place", location=point, rating=-1)
        with pytest.raises(DjangoValidationError) as exc_info:
            place.full_clean()
        errors = exc_info.value.message_dict
        assert (
            "rating" in errors
            and "Ensure this value is greater than or equal to 0" in errors["rating"][0]
        )

    @pytest.mark.django_db
    def test_rating_max_validator(self):
        point = Point(12.34, 56.78)
        place = Place(name="Test Place", location=point, rating=30)
        with pytest.raises(DjangoValidationError) as exc_info:
            place.full_clean()
        errors = exc_info.value.message_dict
        assert (
            "rating" in errors
            and "Ensure this value is less than or equal to 25" in errors["rating"][0]
        )


class TestWeatherSummaryModel:
    @pytest.mark.django_db
    def test_str(self):
        point = Point(12.34, 56.78)
        place = Place.objects.create(name="Test Place", location=point, rating=10)
        weather = WeatherSummary.objects.create(
            place=place,
            temperature=25.0,
            humidity=70,
            pressure=760,
            wind_direction="NE",
            wind_speed=5.0,
        )
        assert str(weather).startswith(f"{place.name} at ")

    @pytest.mark.django_db
    def test_ordering(self):
        point = Point(12.34, 56.78)
        place = Place.objects.create(name="Test Place", location=point, rating=10)
        now = timezone.now()
        weather_old = WeatherSummary.objects.create(
            place=place,
            timestamp=now - timedelta(days=1),
            temperature=20.0,
            humidity=60,
            pressure=750,
            wind_direction="N",
            wind_speed=3.0,
        )
        weather_new = WeatherSummary.objects.create(
            place=place,
            timestamp=now,
            temperature=25.0,
            humidity=70,
            pressure=760,
            wind_direction="NE",
            wind_speed=5.0,
        )
        summaries = list(WeatherSummary.objects.all())
        assert summaries[0] == weather_new and summaries[1] == weather_old

    @pytest.mark.django_db
    def test_default_timestamp(self):
        point = Point(12.34, 56.78)
        place = Place.objects.create(name="Test Place", location=point, rating=10)
        weather = WeatherSummary.objects.create(
            place=place,
            temperature=22.0,
            humidity=65,
            pressure=755,
            wind_direction="NW",
            wind_speed=4.0,
        )
        now = timezone.now()
        assert (
            weather.timestamp is not None
            and abs((now - weather.timestamp).total_seconds()) < 10
        )


# endregion


# ============================================================
#                          UTILS TESTS
# ============================================================
# region Utils Tests
class TestGetWeather:
    @pytest.mark.asyncio
    async def test_success(self, monkeypatch):
        fake_data = {
            "current_weather": {
                "temperature": 25.0,
                "windspeed": 4.5,
                "winddirection": 90,
                "time": "2022-01-01T12:00:00",
            },
            "hourly": {
                "time": ["2022-01-01T12:00:00", "2022-01-01T13:00:00"],
                "relativehumidity_2m": [60, 65],
                "pressure_msl": [1010, 1012],
            },
        }
        monkeypatch.setattr(
            aiohttp,
            "ClientSession",
            lambda *args, **kwargs: FakeClientSession(fake_data),
        )
        result = await get_weather(55.7558, 37.6173)
        expected_pressure = round(1010 * 0.75006, 2)
        assert result["current_time"] == "2022-01-01T12:00:00"
        assert result["temperature"] == 25.0
        assert result["humidity"] == 60
        assert result["pressure"] == expected_pressure
        assert result["wind_speed"] == 4.5
        assert result["wind_direction"] == 90

    @pytest.mark.asyncio
    async def test_no_current_weather(self, monkeypatch):
        fake_data = {
            "hourly": {
                "time": ["2022-01-01T12:00:00"],
                "relativehumidity_2m": [60],
                "pressure_msl": [1010],
            }
        }
        monkeypatch.setattr(
            aiohttp,
            "ClientSession",
            lambda *args, **kwargs: FakeClientSession(fake_data),
        )
        with pytest.raises(Exception, match=r"No data on the current weather\."):
            await get_weather(55.7558, 37.6173)

    @pytest.mark.asyncio
    async def test_empty_times(self, monkeypatch):
        fake_data = {
            "current_weather": {
                "temperature": 25.0,
                "windspeed": 4.5,
                "winddirection": 90,
                "time": "2022-01-01T12:00:00",
            },
            "hourly": {"time": [], "relativehumidity_2m": [], "pressure_msl": []},
        }
        monkeypatch.setattr(
            aiohttp,
            "ClientSession",
            lambda *args, **kwargs: FakeClientSession(fake_data),
        )
        with pytest.raises(
            Exception, match=r"Failed to match the current time to the clock data\."
        ):
            await get_weather(55.7558, 37.6173)

    @pytest.mark.asyncio
    async def test_incomplete_clock_array(self, monkeypatch):
        fake_data = {
            "current_weather": {
                "temperature": 25.0,
                "windspeed": 4.5,
                "winddirection": 90,
                "time": "2022-01-01T12:00:00",
            },
            "hourly": {
                "time": ["2022-01-01T12:00:00"],
                "relativehumidity_2m": [],
                "pressure_msl": [],
            },
        }
        monkeypatch.setattr(
            aiohttp,
            "ClientSession",
            lambda *args, **kwargs: FakeClientSession(fake_data),
        )
        with pytest.raises(Exception, match=r"Incomplete data in the clock array\."):
            await get_weather(55.7558, 37.6173)

    @pytest.mark.asyncio
    async def test_adjusts_current_time(self, monkeypatch):
        fake_data = {
            "current_weather": {
                "temperature": 25.0,
                "windspeed": 4.5,
                "winddirection": 90,
                "time": "2022-01-01T12:34:56",
            },
            "hourly": {
                "time": ["2022-01-01T12:34:00", "2022-01-01T13:00:00"],
                "relativehumidity_2m": [60, 65],
                "pressure_msl": [1010, 1012],
            },
        }
        monkeypatch.setattr(
            aiohttp,
            "ClientSession",
            lambda *args, **kwargs: FakeClientSession(fake_data),
        )
        result = await get_weather(55.7558, 37.6173)
        expected_pressure = round(1010 * 0.75006, 2)
        assert result["current_time"] == "2022-01-01T12:34:00"
        assert result["temperature"] == 25.0
        assert result["humidity"] == 60
        assert result["pressure"] == expected_pressure
        assert result["wind_speed"] == 4.5
        assert result["wind_direction"] == 90


# endregion
