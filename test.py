import unittest
from unittest.mock import Mock, patch
from copy import deepcopy
from services import Person
from settings import INTENTS, SCENARIOS, DEFAULT_ANSWER
from Bot import Bot
from vk_api.bot_longpoll import VkBotMessageEvent
from pony.orm import rollback, db_session

CONTEXT = {'city': 'Владивосток', 'temp': -22.99, 'feels_like': -29.99, 'wind': 8.02, 'rain': 'Дождя нет',
           'snow': 'Снега нет', 'place': 'торонто', 'time': '05:03', 'weekday': 'Вторник',
           'month': 'Января', 'day': '24', 'year': '2023'}
INPUTS = ['Привте !',
          'как дела ?',
          'а что ты умеешь?',
          'что такое гиря?',
          'Владивосток',
          'торонто',
          'хочу попасть на конференцию',
          'Михаил',
          'asdfasdf.ru',
          'misha@gmail.com']

EXPECTED_OUTPUTS = [INTENTS[0]['answer'],
                    INTENTS[1]['answer'],
                    INTENTS[2]['answer'],
                    DEFAULT_ANSWER,
                    SCENARIOS['weather']['steps']['step_2']['text'].format(**CONTEXT),
                    SCENARIOS['date']['steps']['step_2']['text'].format(**CONTEXT),
                    SCENARIOS['registration']['steps']['step_1']['text'],
                    SCENARIOS['registration']['steps']['step_2']['text'],
                    SCENARIOS['registration']['steps']['step_2']['failure_text'],
                    SCENARIOS['registration']['steps']['step_3']['text'].format(**{'name': 'Михаил',
                                                                                   'email': 'misha@gmail.com'}),
                    ]

RAW_EVENT_TYPING = {'group_id': 12345, 'type': 'message_typing_state',
                    'event_id': '5b71506a9a37410d9876bab0c6e91c00f7ca017d',
                    'v': '5.131', 'object': {'state': 'typing', 'from_id': 123, 'to_id': 345346}}

RAW_EVENT_MESSAGE_NEW = {'group_id': 12312445, 'type': 'message_new',
                         'event_id': '94a305614f6bac0e0f9379ce99c0349eb716d824', 'v': '5.131',
                         'object': {'message': {'date': 1674124555712, 'from_id': 12124345, 'id': 1163, 'out': 0,
                                                'attachments': [],
                                                'conversation_message_id': 1068, 'fwd_messages': [], 'important': False,
                                                'is_hidden': False, 'peer_id': 12312445,
                                                'random_id': 0, 'text': 'привет'}, 'client_info': {
                             'button_actions': ['text', 'vkpay', 'open_app', 'location', 'open_link', 'callback',
                                                'intent_subscribe', 'intent_unsubscribe'], 'keyboard': True,
                             'inline_keyboard': True, 'carousel': True, 'lang_id': 0}}}


def db_isolate(func):
    def wrapper(*args, **kwargs):
        with db_session:
            func(*args, **kwargs)
            rollback()

    return wrapper


class TestBot(unittest.TestCase):
    def setUp(self):
        self.api_mock = Mock()
        self.send_mock = Mock()
        self.api_mock.messages.send = self.send_mock
        self.long_poller_mock = Mock()

    @db_isolate
    def test_intents(self):
        event_list_mock = []
        for inp in INPUTS[:4]:
            event = deepcopy(RAW_EVENT_MESSAGE_NEW)
            event['object']['message']['text'] = inp
            event_list_mock.append(VkBotMessageEvent(event))
        self.long_poller_mock.listen = Mock(return_value=event_list_mock)

        with patch('Bot.VkBotLongPoll', return_value=self.long_poller_mock):
            bot = Bot('', '')
            bot.vk_api = self.api_mock
            bot.run()

        real_output = []
        for arg, kwarg in self.send_mock.call_args_list:
            real_output.append(kwarg['message'])

        assert EXPECTED_OUTPUTS[:4] == real_output

    @db_isolate
    def test_weather(self):
        event_list_mock = []

        event = deepcopy(RAW_EVENT_MESSAGE_NEW)
        event['object']['message']['text'] = INPUTS[4]
        event_list_mock.append(VkBotMessageEvent(event))

        self.long_poller_mock.listen = Mock(return_value=event_list_mock)

        test_person = Person(user_id=12312445, scenario_name='weather', step_name='step_1', context=CONTEXT)
        with patch('Bot.Person.get', return_value=test_person):
            with patch('services.handlers.weather_handler', return_value=True):
                with patch('Bot.VkBotLongPoll', return_value=self.long_poller_mock):
                    bot = Bot('', '')
                    bot.vk_api = self.api_mock
                    bot.run()

        for arg, kwarg in self.send_mock.call_args_list:
            real_output = kwarg['message']
        assert EXPECTED_OUTPUTS[4] == real_output

    @db_isolate
    def test_date(self):
        event_list_mock = []

        event = deepcopy(RAW_EVENT_MESSAGE_NEW)
        event['object']['message']['text'] = INPUTS[5]
        event_list_mock.append(VkBotMessageEvent(event))

        self.long_poller_mock.listen = Mock(return_value=event_list_mock)

        test_person = Person(user_id=12312445, scenario_name='date', step_name='step_1', context=CONTEXT)
        with patch('Bot.Person.get', return_value=test_person):
            with patch('services.handlers.date_handler', return_value=True):
                with patch('Bot.VkBotLongPoll', return_value=self.long_poller_mock):
                    bot = Bot('', '')
                    bot.vk_api = self.api_mock
                    bot.run()

        for arg, kwarg in self.send_mock.call_args_list:
            real_output = kwarg['message']
        assert EXPECTED_OUTPUTS[5] == real_output

    @db_isolate
    def test_registration(self):
        event_list_mock = []
        for inp in INPUTS[6:10]:
            event = deepcopy(RAW_EVENT_MESSAGE_NEW)
            event['object']['message']['text'] = inp
            event_list_mock.append(VkBotMessageEvent(event))
        self.long_poller_mock.listen = Mock(return_value=event_list_mock)

        with patch('Bot.VkBotLongPoll', return_value=self.long_poller_mock):
            bot = Bot('', '')
            bot.vk_api = self.api_mock
            bot.run()

        real_outputs = []
        for arg, kwarg in self.send_mock.call_args_list:
            real_outputs.append(kwarg['message'])

        assert EXPECTED_OUTPUTS[6:10] == real_outputs


if __name__ == '__main__':
    unittest.main()
