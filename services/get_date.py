import datetime
import timezonefinder
import pytz
from geopy import Nominatim


def get_date(s, context):
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
