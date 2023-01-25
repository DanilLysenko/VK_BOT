# -*- coding: utf-8 -*-

import logging
from random import randint
from vk_api import VkApi
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType, VkBotMessageEvent
from models import *
import handlers

try:
    from settings import *
except ImportError:
    print('Нужно переименовать setting.py.default -> settings.py')

logger = logging.getLogger('vk_bot')


def log_config():
    handler = logging.FileHandler(filename='vk_bot.log', mode='a', encoding='utf8')
    s_handler = logging.StreamHandler()

    formatter = logging.Formatter("[%(levelname)s] [%(asctime)s] [%(message)s]", datefmt='%Y-%m-%d %H:%M:%S')
    s_formatter = logging.Formatter("[%(levelname)s] [%(message)s]")

    handler.setFormatter(formatter)
    s_handler.setFormatter(s_formatter)

    logger.addHandler(handler)
    logger.addHandler(s_handler)

    logger.setLevel(logging.DEBUG)


class Bot:
    """
    Сценарный бот для группы VK

    Для имплементации новых сценариев нужно:
    •Добавить сценарное дерево в settings.SCENARIOS
    •Создать новый словарь в setting.INTENTS для поиска токенов в сообщении пользователя для начала сценария
    •Создать handler в handlers.py для каждого шага сценария, где есть проверка

    Готовые сценарии:
    •Регистрация
    •Вывод погоды в русских городах
    •Вывод даты и времени в любой точке мира
    """

    def __init__(self, token, group_id):
        """
        :param token: ключ доступа группы Vk
        :param group_id: ID группы VK
        """
        self.vk = VkApi(token=token)
        self.long_poller = VkBotLongPoll(self.vk, group_id=group_id)
        self.vk_api = self.vk.get_api()

    def run(self):
        """
        Функция запуска бота. Проверяет тип пришедшего события
        """
        logger.debug('Bot started')
        for event in self.long_poller.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                logger.debug(f"Got message - ({event.object['message']['text']})")
                user_id = event.object['message']['from_id']
                text_to_send = self.on_message_new(event)
                self.send_text(user_id=user_id, text_to_send=text_to_send)
            else:
                logger.info(f'Не имплементирована функция обработки - {event.type}')

    @db_session
    def on_message_new(self, event: VkBotMessageEvent):
        """
        Возвращает текст для отправки сообщения и оперирует с таблицей models.Person
        :return: str
        """
        text = event.object['message']['text']
        user_id = event.object['message']['from_id']
        if not Person.get(user_id=user_id):
            for intent in INTENTS:
                if any(token in text.lower() for token in intent['token']):
                    if intent['answer']:
                        return intent['answer']
                    else:
                        return self.start_scenario(intent, user_id)
            else:
                logger.debug(f'Message from user ({user_id}) not recognized - ({text})')
                return DEFAULT_ANSWER
        else:
            state = Person.get(user_id=user_id)
            scenario_name = state.scenario_name
            steps = SCENARIOS[scenario_name]['steps']
            step = steps[state.step_name]
            handler = getattr(handlers, step['handler'])

            if handler(text, state.context):
                next_step_name = step['next_step']
                if next_step_name:
                    state.step_name = next_step_name
                    text_to_send = steps[next_step_name]['text'].format(**state.context)
                    if steps[next_step_name]['next_step'] is None:
                        if scenario_name == 'registration':
                            Registration(user_id=user_id, name=state.context['name'], email=state.context['email'])
                            logger.debug(f'user ({user_id}) registered at conference')
                        state.delete()
                    return text_to_send
            else:
                logger.debug(f"user input - ({text}) did not pass ({handler.__name__})")
                return step['failure_text']

    def start_scenario(self, intent, user_id):
        scenario_name = intent['scenario_name']
        if scenario_name == 'registration':
            reg_state = Registration.get(user_id=user_id)
            if reg_state:
                return f"{reg_state.name}, Вы уже зарегистрированы, проверьте вашу почту - {reg_state.email}"

        steps = SCENARIOS[scenario_name]['steps']
        first_step = SCENARIOS[scenario_name]['first_step']

        Person(user_id=user_id, scenario_name=scenario_name,
               step_name=first_step, context={})

        logger.debug(f"User ({user_id}) started scenario ({scenario_name})")
        return steps[first_step]['text']

    def send_text(self, user_id, text_to_send):
        self.vk_api.messages.send(peer_id=user_id,
                                  random_id=randint(-2_147_483_648, 2_147_483_647),
                                  message=text_to_send)

    def start_dialog(self, user_id):
        self.send_text(user_id, f'Привет!{LIST_OF_POSIBILITIES}')


if __name__ == '__main__':
    log_config()
    vk_bot = Bot(token=TOKEN, group_id=GROUP_ID)
    try:
        vk_bot.run()
    except Exception as exc:
        logger.error('Process crashed', exc)
