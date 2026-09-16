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
                "language": "en",
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


if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=8000,
    )
