import httpx

from loguru import logger


async def fetch_weather(client: httpx.AsyncClient, city: str):
    city = city.strip()
    try:
        # 1) 获取经纬度
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&language=zh&count=1"
        geo_response = await client.get(geo_url)
        geo_response.raise_for_status()
        geo_data = geo_response.json()

        if "results" not in geo_data or len(geo_data["results"]) == 0:
            logger.error(f"未找到城市: {city}")
            return None

        lat = geo_data["results"][0]["latitude"]
        lon = geo_data["results"][0]["longitude"]

        # 2) 获取当天天气（每日最高/最低温 + 天气代码）
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&daily=temperature_2m_max,temperature_2m_min,weathercode"
            f"&current_weather=true"
            f"&timezone=Asia/Shanghai&language=zh"
        )

        weather_response = await client.get(weather_url)
        weather_response.raise_for_status()
        weather_data = weather_response.json()

        current = weather_data.get("current_weather", {})
        daily = weather_data.get("daily", {})

        if not current or not daily:
            logger.error("天气数据缺失")
            return None

        # 天气代码表
        weather_codes = {
            0: "晴",
            1: "多云",
            2: "部分多云",
            3: "阴",
            45: "雾",
            48: "霾",
            51: "毛毛雨",
            61: "小雨",
            63: "中雨",
            65: "大雨",
            71: "小雪",
            73: "中雪",
            75: "大雪",
            95: "雷阵雨",
        }

        code_today = current.get("weathercode")
        if code_today is None:
            description = "暂无天气描述"
        else:
            description = weather_codes.get(code_today, f"天气代码 {code_today}")

        min_t = daily.get("temperature_2m_min", [None])[0]
        max_t = daily.get("temperature_2m_max", [None])[0]

        return {
            "城市": city,
            "最低气温": f"{min_t}°C" if min_t is not None else "N/A",
            "最高气温": f"{max_t}°C" if max_t is not None else "N/A",
            "天气": description,
        }

    except httpx.HTTPError as e:
        logger.error(f"HTTP 错误: {e}")
        return None
    except Exception as e:
        logger.error(f"未知错误: {e}")
        return None


# 获取未来天气
async def fetch_forecast(client: httpx.AsyncClient, city: str, days: int = 5):
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&language=zh&count=1"
        geo = await client.get(geo_url)
        geo.raise_for_status()
        geo_data = geo.json()

        if "results" not in geo_data or not geo_data["results"]:
            return None

        lat = geo_data["results"][0]["latitude"]
        lon = geo_data["results"][0]["longitude"]

        forecast_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}"
            f"&daily=temperature_2m_max,temperature_2m_min,weathercode"
            f"&forecast_days={days}&timezone=Asia/Shanghai&language=zh"
        )

        forecast_response = await client.get(forecast_url)
        forecast_response.raise_for_status()
        return forecast_response.json()

        # TODO: 处理天气数据

    except httpx.HTTPError as e:
        logger.error(f"HTTP 错误: {e}")
        return None
    except Exception as e:
        logger.error(f"未知错误: {e}")
        return None
