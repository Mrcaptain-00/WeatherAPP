"""
    URL configuration for weather project.
    """
from django.contrib import admin
from django.urls import path
    # Import your views directly from the weatherapp
from weatherapp.views import index, get_weather # <--- CORRECTED IMPORT

urlpatterns = [
        path('admin/', admin.site.urls),
        path('api/weather/', get_weather, name='get_weather_api'), # <--- API ENDPOINT
        path('', index, name='weather_frontend'), # <--- FRONTEND AT ROOT URL
    ]
    