import re
from .get_date import get_date
from .get_weather import get_weather


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
    if get_weather(text, context):
        return True
    return False


def date_handler(s, context):
    if get_date(s, context):
        return True
    else:
        return False


