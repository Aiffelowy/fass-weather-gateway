import httpx
from fastapi import FastAPI, HTTPException, Query
from cachetools import TTLCache
from typing import Any, Dict

app = FastAPI(title="Weather Gateway");

weather_cache = TTLCache(maxsize=1000, ttl=600);

@app.get("/weather")
async def get_weather(
    latitude: float = Query(...),
    longitude: float = Query(...)
) -> Dict[str, Any]:
    
    lat_rounded = round(latitude, 4);
    lon_rounded = round(longitude, 4);
    cache_key = f"{lat_rounded},{lon_rounded}";

    if cache_key in weather_cache:
        return weather_cache[cache_key];

    url = f"https://api.open-meteo.com/v1/forecast";
    params = {
        "latitude": lat_rounded,
        "longitude": lon_rounded,
        "current_weather": True,
    };

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=5.0);
            response.raise_for_status();
            data = response.json();
            
            result = {
                "latitude": lat_rounded,
                "longitude": lon_rounded,
                "weather": data.get("current_weather", {})
            };

            weather_cache[cache_key] = result;
            return result;

        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail="Weather API Error");
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Cannot connect to Weather API");

@app.get("/health")
async def health():
    return {"status": "ok"};
