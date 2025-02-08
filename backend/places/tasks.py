import asyncio

from asgiref.sync import sync_to_async
from celery import shared_task
from django.utils import timezone

from .models import Place, WeatherSummary
from .utils import get_weather


async def process_weather_for_place_async(place: Place):
    try:
        weather = await get_weather(place.location.x, place.location.y)
        await sync_to_async(WeatherSummary.objects.create)(
            place=place,
            temperature=weather["temperature"],
            humidity=weather["humidity"],
            pressure=weather["pressure"],
            wind_direction=weather["wind_direction"],
            wind_speed=weather["wind_speed"],
        )
    except Exception as exc:
        print(f"Error processing place {place.id}: {exc}")
        raise exc


@shared_task
def fetch_weather_summary():
    async def main():
        places = await sync_to_async(list)(Place.objects.all())
        tasks = [process_weather_for_place_async(place) for place in places]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Error for place {places[idx].pk}: {result}")

    asyncio.run(main())
    return f"Weather summary tasks dispatched at {timezone.now()}"
