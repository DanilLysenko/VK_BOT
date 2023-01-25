import requests
import re
import datetime
import timezonefinder
import pytz
from geopy import Nominatim
from models import db_session
from settings import WEATHER_API_KEY

re_name = re.compile("[А-я]{3,40}")
re_email = re.compile("(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")


def name_handler(s, context):
    if re.match(re_name, s):
        context['name'] = s.capitalize()
        return True
    return False


def email_handler(s, context):
    res = re.match(re_email, s)
    if res:
        context['email'] = res[0]
        return True
    return False


def weather_handler(text, context):
    if weather_api(text, context):
        return True
    return False


def date_handler(s, context):
    coordinates = get_coord(s)
    if coordinates is None:
        return False
    tf = timezonefinder.TimezoneFinder()
    timezone_str = tf.certain_timezone_at(**coordinates)

    if timezone_str is None:
        return False
    else:
        timezone = pytz.timezone(timezone_str)
        dt = datetime.datetime.utcnow()
        raw_data = dt + timezone.utcoffset(dt)
        date = raw_data.strftime("%A %d %B %Y")
        context['place'] = s
        context['time'] = raw_data.strftime("%H:%M")
        date_converter(date, context)
        return True


def get_coord(s):
    try:
        res = Nominatim(user_agent='tutorial').geocode(s)
        return {'lat': res.latitude, 'lng': res.longitude}
    except Exception as exc:
        return None


def weather_api(s, context):
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


def date_converter(date, context):
    days_ru = {'Monday': 'Понедельник', 'Tuesday': 'Вторник', 'Wednesday': 'Среда',
               'Thursday': 'Четверг', 'Friday': 'Пятница', 'Saturday': 'Суббота', 'Sunday': 'Воскресенье'}

    months_ru = {'January': 'Января', 'February': 'Февраля', 'March': 'Марта', 'April': 'Апреля',
                 'May': 'Мая', 'June': 'Июня', 'July': 'Июля', 'August': 'Августа', 'September': 'Сентября',
                 'October': 'Октября', 'November': 'Ноября', 'December': 'Декабря'}
    list_raw = str(date).split()
    context["weekday"] = days_ru[list_raw[0]]
    context["month"] = months_ru[list_raw[2]]
    context["day"] = list_raw[1]
    context["year"] = list_raw[3]


