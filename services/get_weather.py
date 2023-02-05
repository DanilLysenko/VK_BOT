import requests
from .models import db_session
from settings import WEATHER_API_KEY


def get_weather(s, context):
    response = requests.get("http://api.openweathermap.org/data/2.5/find",
                            params={'q': s + ',Ru', 'type': 'like', 'units': 'metric', 'APPID': WEATHER_API_KEY})
    res = response.json()
    if len(res['list']) > 0:
        with db_session():
            temp_obj = res['list'][0]['main']
            context['city'] = s
            context['temp'] = temp_obj['temp']
            context['feels_like'] = temp_obj['feels_like']
            context['wind'] = res['list'][0]['wind']['speed']

            rain = res['list'][0]['rain']
            if rain:
                context['rain'] = 'Идёт дождь'
            else:
                context['rain'] = 'Дождя нет'

            snow = res['list'][0]['rain']
            if snow:
                context['snow'] = 'Идёт снег'
            else:
                context['snow'] = 'Снега нет'

            return True
    return False
