"""Weather tool using Open-Meteo API (free, no API key required)."""

from typing import Optional
import aiohttp
from small_agent.tools.registry import Tool, ToolResult


class WeatherTool(Tool):
    """Tool for getting current weather using Open-Meteo API."""

    name = "weather"
    description = "Get current weather information for a location. Returns temperature, weather conditions, wind speed, and other meteorological data."
    auto_use = True

    @property
    def schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City name or location (e.g., 'Beijing', 'New York', '杭州')",
                },
                "units": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "Temperature units (default: celsius)",
                },
            },
            "required": ["location"],
        }

    async def _geocode(self, location: str) -> Optional[dict]:
        """Geocode location name to lat/lon using Open-Meteo geocoding API."""
        try:
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                url = "https://geocoding-api.open-meteo.com/v1/search"
                params = {
                    "name": location,
                    "count": 5,  # Get multiple results
                    "language": "zh",
                    "format": "json",
                }
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("results") and len(data["results"]) > 0:
                            # Try to find the most relevant city (prefer large cities)
                            for result in data["results"]:
                                # Prefer cities with admin1 (province) info, skip small towns
                                feature_code = result.get("feature_code", "")
                                if feature_code == "PPLC" or feature_code == "PPLA":
                                    return {
                                        "name": result.get("name", location),
                                        "country": result.get("country", ""),
                                        "latitude": result.get("latitude"),
                                        "longitude": result.get("longitude"),
                                    }
                            # Fallback to first result
                            result = data["results"][0]
                            return {
                                "name": result.get("name", location),
                                "country": result.get("country", ""),
                                "latitude": result.get("latitude"),
                                "longitude": result.get("longitude"),
                            }
        except Exception as e:
            print(f"Geocoding error: {e}")
        return None

    async def execute(
        self,
        location: str,
        units: str = "celsius",
    ) -> ToolResult:
        """Get weather for the specified location."""
        try:
            # First, geocode the location to get lat/lon
            geocode_result = await self._geocode(location)
            if not geocode_result:
                return ToolResult(
                    success=False,
                    content="",
                    error=f"Could not find location: {location}",
                )

            lat = geocode_result["latitude"]
            lon = geocode_result["longitude"]
            city_name = f"{geocode_result['name']}, {geocode_result['country']}"

            # Get weather data from Open-Meteo API
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                url = "https://api.open-meteo.com/v1/forecast"
                params = {
                    "latitude": lat,
                    "longitude": lon,
                    "current": [
                        "temperature_2m",
                        "relative_humidity_2m",
                        "weather_code",
                        "wind_speed_10m",
                        "wind_direction_10m",
                    ],
                }
                if units == "fahrenheit":
                    params["temperature_unit"] = "fahrenheit"

                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        return ToolResult(
                            success=False,
                            content="",
                            error=f"Weather API error: {response.status}",
                        )

                    data = await response.json()
                    current = data.get("current", {})

                    if not current:
                        return ToolResult(
                            success=False,
                            content="",
                            error="No weather data available",
                        )

                    # Parse weather data
                    temp = current.get("temperature_2m", 0)
                    humidity = current.get("relative_humidity_2m", 0)
                    wind_speed = current.get("wind_speed_10m", 0)
                    wind_dir = current.get("wind_direction_10m", 0)
                    weather_code = current.get("weather_code", 0)

                    # Convert weather code to description
                    weather_desc = self._get_weather_description(weather_code)

                    # Format result
                    unit_symbol = "°F" if units == "fahrenheit" else "°C"
                    content = (
                        f"Weather in {city_name}:\n"
                        f"  Temperature: {temp}{unit_symbol}\n"
                        f"  Condition: {weather_desc}\n"
                        f"  Humidity: {humidity}%\n"
                        f"  Wind: {wind_speed} km/h (direction: {wind_dir}°)\n"
                    )

                    return ToolResult(
                        success=True,
                        content=content,
                        data={
                            "location": city_name,
                            "temperature": temp,
                            "units": units,
                            "condition": weather_desc,
                            "humidity": humidity,
                            "wind_speed": wind_speed,
                        },
                    )

        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=str(e),
            )

    def _get_weather_description(self, code: int) -> str:
        """Convert WMO weather code to human-readable description."""
        # WMO Weather interpretation codes (WW)
        descriptions = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Fog",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            56: "Light freezing drizzle",
            57: "Dense freezing drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            66: "Light freezing rain",
            67: "Heavy freezing rain",
            71: "Slight snow fall",
            73: "Moderate snow fall",
            75: "Heavy snow fall",
            77: "Snow grains",
            80: "Slight rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            85: "Slight snow showers",
            86: "Heavy snow showers",
            95: "Thunderstorm",
            96: "Thunderstorm with slight hail",
            99: "Thunderstorm with heavy hail",
        }
        return descriptions.get(code, "Unknown")
