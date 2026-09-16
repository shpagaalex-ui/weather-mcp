import httpx
from fastmcp import FastMCP

mcp = FastMCP("Weather MCP")

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


@mcp.tool()
async def get_weather(city: str) -> dict:
    """Get the current weather for any city in the world."""

    async with httpx.AsyncClient(timeout=20.0) as client:
        # 1. Find coordinates for the city
        geo_response = await client.get(
            GEOCODING_URL,
            params={
                "name": city,
                "count": 1,
                "language": "ru",
                "format": "json",
            },
        )
        geo_response.raise_for_status()
        geo_data = geo_response.json()

        if not geo_data.get("results"):
            return {
                "error": f"City '{city}' was not found."
            }

        location = geo_data["results"][0]

        latitude = location["latitude"]
        longitude = location["longitude"]

        # 2. Request current weather
        weather_response = await client.get(
            WEATHER_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": ",".join([
                    "temperature_2m",
                    "apparent_temperature",
                    "relative_humidity_2m",
                    "precipitation",
                    "weather_code",
                    "wind_speed_10m",
                ]),
                "timezone": "auto",
            },
        )
        weather_response.raise_for_status()
        weather_data = weather_response.json()

        current = weather_data["current"]

        return {
            "city": location["name"],
            "country": location.get("country"),
            "latitude": latitude,
            "longitude": longitude,
            "temperature_c": current["temperature_2m"],
            "feels_like_c": current["apparent_temperature"],
            "humidity_percent": current["relative_humidity_2m"],
            "precipitation_mm": current["precipitation"],
            "weather_code": current["weather_code"],
            "wind_speed_kmh": current["wind_speed_10m"],
            "timezone": weather_data.get("timezone"),
            "observation_time": current.get("time"),
        }
@mcp.tool()
async def get_forecast(city: str, days: int = 3) -> dict:
    """Get the weather forecast for a city for the next 1 to 7 days."""

    # Ограничиваем прогноз диапазоном 1–7 дней
    days = max(1, min(days, 7))

    async with httpx.AsyncClient(timeout=20.0) as client:

        # 1. Находим город
        geo_response = await client.get(
            GEOCODING_URL,
            params={
                "name": city,
                "count": 1,
                "language": "ru",
                "format": "json",
            },
        )
        geo_response.raise_for_status()
        geo_data = geo_response.json()

        if not geo_data.get("results"):
            return {
                "error": f"Город '{city}' не найден."
            }

        location = geo_data["results"][0]

        latitude = location["latitude"]
        longitude = location["longitude"]

        # 2. Получаем прогноз
        weather_response = await client.get(
            WEATHER_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "daily": ",".join([
                    "weather_code",
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "precipitation_sum",
                    "wind_speed_10m_max",
                ]),
                "timezone": "auto",
                "forecast_days": days,
            },
        )

        weather_response.raise_for_status()
        weather_data = weather_response.json()

        daily = weather_data["daily"]

        forecast = []

        for i in range(len(daily["time"])):
            forecast.append({
                "date": daily["time"][i],
                "temperature_max_c": daily["temperature_2m_max"][i],
                "temperature_min_c": daily["temperature_2m_min"][i],
                "precipitation_mm": daily["precipitation_sum"][i],
                "wind_speed_max_kmh": daily["wind_speed_10m_max"][i],
                "weather_code": daily["weather_code"][i],
            })

        return {
            "city": location["name"],
            "country": location.get("country"),
            "timezone": weather_data.get("timezone"),
            "days": days,
            "forecast": forecast,
        }

if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=8000,
    )
