from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_GET
import requests
import os
from datetime import datetime
import xml.etree.ElementTree as ET

@require_GET
def get_weather(request):
    city = request.GET.get('city', 'New York')
    api_key = os.getenv('WEATHER_API_KEY')

    if not api_key:
        return JsonResponse({"error": "API key not configured"}, status=500)

    try:
        # Fetch weather forecast data (includes current and forecast)
        forecast_url = f"http://api.weatherapi.com/v1/forecast.xml?key={api_key}&q={city}&days=5&aqi=yes&alerts=no"
        response = requests.get(forecast_url)

        if response.status_code != 200:
            return JsonResponse({"error": "City not found or API error"}, status=response.status_code)

        root = ET.fromstring(response.content)

        # Extract current weather data
        location = root.find('location')
        current = root.find('current')
        forecast = root.find('forecast')

        if None in [location, current, forecast]:
            return JsonResponse({"error": "Invalid XML structure"}, status=500)

        # Current weather data
        current_data = {
            "location": f"{location.find('name').text}, {location.find('country').text}",
            "temp": current.find('temp_c').text,
            "feels_like": current.find('feelslike_c').text,
            "humidity": current.find('humidity').text,
            "wind_speed": current.find('wind_kph').text,
            "description": current.find('condition').find('text').text,
            "icon": current.find('condition').find('icon').text,
            "is_day": current.find('is_day').text == '1',
            "uv": current.find('uv').text,
            "visibility": f"{float(current.find('vis_km').text) / 1.60934:.1f}",
            "pressure": current.find('pressure_mb').text
        }

        # Process hourly forecast (next 24 hours)
        hourly_data = []
        today_forecast = forecast.find('forecastday')
        if today_forecast is not None:
            for hour in today_forecast.findall('hour'):
                hour_time_str = hour.get('time')
                if hour_time_str:  # Check if hour_time_str is not None
                    hour_time = datetime.strptime(hour_time_str, "%Y-%m-%d %H:%M")
                    if hour_time.date() == datetime.now().date():
                        hourly_data.append({
                            "time": hour_time.strftime("%I %p"),
                            "temp": hour.find('temp_c').text,
                            "icon": hour.find('condition').find('icon').text,
                            "condition": hour.find('condition').find('text').text
                        })

        # Process 5-day forecast
        daily_data = []
        for day in forecast.findall('forecastday'):
            date_str = day.get('date')
            if date_str:  # Check if date_str is not None
                date = datetime.strptime(date_str, "%Y-%m-%d")
                daily_data.append({
                    "day": date.strftime("%a"),
                    "high": day.find('day').find('maxtemp_c').text,
                    "low": day.find('day').find('mintemp_c').text,
                    "icon": day.find('day').find('condition').find('icon').text,
                    "condition": day.find('day').find('condition').find('text').text
                })

        # Prepare final response
        weather_data = {
            "location": current_data['location'],
            "current": {
                "temp": current_data['temp'],
                "feels_like": current_data['feels_like'],
                "humidity": current_data['humidity'],
                "wind_speed": current_data['wind_speed'],
                "description": current_data['description'],
                "icon": current_data['icon'],
                "iconClass": get_icon_class(current_data['description']),
                "uvIndex": current_data['uv'],
                "visibility": current_data['visibility'],
                "pressure": current_data['pressure'],
                "isDay": current_data['is_day']
            },
            "hourly": hourly_data,
            "daily": daily_data
        }

        return JsonResponse(weather_data)
    
    except requests.exceptions.RequestException as e:
        return JsonResponse({"error": f"Network error: {str(e)}"}, status=503)
    except Exception as e:
        return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)

def get_icon_class(condition_text):
    condition = condition_text.lower()
    if 'rain' in condition:
        return 'rain-animation text-blue-400'
    elif 'cloud' in condition:
        return 'cloud-animation text-gray-400'
    elif 'sun' in condition or 'clear' in condition:
        return 'sun-animation text-yellow-400'
    elif 'snow' in condition or 'sleet' in condition:
        return 'snow-animation text-blue-200'
    elif 'storm' in condition or 'thunder' in condition:
        return 'text-purple-500'
    elif 'fog' in condition or 'mist' in condition or 'haze' in condition:
        return 'text-gray-500'
    else:
        return 'text-gray-500'

def index(request):
    return render(request, 'weather.html')
