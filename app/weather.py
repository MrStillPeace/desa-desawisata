from typing import Any, Dict
import requests

# Koordinat lokasi Desa Wisata Lembah Asri
LATITUDE: float = -6.83
LONGITUDE: float = 107.62
TIMEZONE: str = "Asia/Jakarta"
OPEN_METEO_BASE_URL: str = "https://api.open-meteo.com/v1/forecast"


def get_weather_forecast(days: int = 1) -> Dict[str, Any]:
    """
    Mengambil prakiraan cuaca dari Open-Meteo API untuk koordinat Desa Wisata Lembah Asri.
    
    Args:
        days: Jumlah hari prakiraan yang ingin diambil (default: 1).
        
    Returns:
        Dictionary data cuaca berupa suhu, cuaca terkini, dan parameter relevan.
    """
    # Parameter dasar API Open-Meteo
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "timezone": TIMEZONE,
        "current_weather": True,
        "hourly": "temperature_2m,precipitation_probability,weathercode",
        "forecast_days": days,
    }
    
    # TODO: Diimplementasikan lengkap dengan penanganan error atau fallback oleh tim
    try:
        response = requests.get(OPEN_METEO_BASE_URL, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                "status": "success",
                "location": "Desa Wisata Lembah Asri",
                "coordinates": {"latitude": LATITUDE, "longitude": LONGITUDE},
                "current": data.get("current_weather", {}),
            }
    except Exception as err:
        return {
            "status": "error",
            "message": f"Gagal mengambil data cuaca: {err}",
            "fallback": "Cuaca cerah berawan (estimasi)"
        }

    return {
        "status": "stub",
        "location": "Desa Wisata Lembah Asri",
        "coordinates": {"latitude": LATITUDE, "longitude": LONGITUDE},
        "forecast": f"Prakiraan cuaca {days} hari ke depan (stub)"
    }
