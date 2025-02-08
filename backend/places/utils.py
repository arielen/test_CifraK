import aiohttp


async def get_weather(lat: float, lon: float) -> dict:
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&current_weather=true"
        f"&hourly=relativehumidity_2m,pressure_msl"
        f"&timezone=auto"
    )

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()

    if "current_weather" not in data:
        raise Exception("No data on the current weather.")

    current = data["current_weather"]
    temperature = current["temperature"]
    wind_speed = current["windspeed"]
    wind_direction = current["winddirection"]
    current_time = current["time"]

    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    humidity_values = hourly.get("relativehumidity_2m", [])
    pressure_values = hourly.get("pressure_msl", [])

    if not times:
        raise Exception("Failed to match the current time to the clock data.")

    if current_time not in times:
        current_time = current_time[:-2] + "00"

    index = times.index(current_time)
    try:
        humidity = humidity_values[index]
        pressure_hpa = pressure_values[index]
    except IndexError:
        raise Exception("Incomplete data in the clock array.")

    pressure_mmHg = round(pressure_hpa * 0.75006, 2)

    return {
        "current_time": current_time,
        "temperature": temperature,
        "humidity": humidity,
        "pressure": pressure_mmHg,
        "wind_speed": wind_speed,
        "wind_direction": wind_direction,
    }
