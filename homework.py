import logging
import os
import time
from logging.handlers import RotatingFileHandler

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()


PRAKTIKUM_TOKEN = os.getenv("PRAKTIKUM_TOKEN")
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

BOT_CREATE_SUCCES = 'Бот был успешно создан'


URL_API_PRAKTIKUM = (
    'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
)
URL_API_TELEGRAM = 'https://api.telegram.org/bot'

logger = logging.getLogger('__name__')
handler = RotatingFileHandler(
    filename=__file__ + '.log',
    maxBytes=50000000,
    backupCount=5
)
logger.addHandler(handler)


BAD_VERDICT = 'К сожалению в работе нашлись ошибки.'
GOOD_VERDICT = 'Ревьюеру всё понравилось, можно приступать к следующему уроку.'
REVIEW_IN_PROGRESS = 'Задание находится на проверке'
ANSWER = 'У вас проверили работу "{name}"!\n\n{verdict}'
KEY_ERROR = 'По ключам не получилось получить данные'
PARSE_PROBLEM = 'Проблемы с ключами'
NONAME_STATUS = 'Неизвестный статус работы'

statuses = {
    'rejected': BAD_VERDICT,
    'approved': GOOD_VERDICT,
    'reviewing': REVIEW_IN_PROGRESS
}


def parse_homework_status(homework):
    homework_status = homework['status']
    for status, verdict in statuses.items():
        if homework_status == status:
            return ANSWER.format(
                name=homework['homework_name'],
                verdict=verdict,
            )
    raise KeyError('Ниодин из возможных статусов не обнаружен')


CONNECTON_ERROR = (
    'Отправлен запрос на {URL_API_PRAKTIKUM}\n'
    'с текущим временем {current_timestamp}\n'
    'от имени(токен): {PRAKTIKUM_TOKEN}\n'
    'получена ошибка: {error}\n'
)
ERROR_IN_RESPONSE = 'Запрос домашней работы провалился'


def get_homework_statuses(current_timestamp):
    current_timestamp = current_timestamp or int(time.time())
    PARAMS = {
        'from_date': current_timestamp
    }
    HEADERS = {
        'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'
    }
    ARGUMENTS = {
        'URL_API_PRAKTIKUM': URL_API_PRAKTIKUM,
        'current_timestamp': PARAMS['from_date'],
        'PRAKTIKUM_TOKEN': PRAKTIKUM_TOKEN,
    }
    try:
        response = requests.get(
            URL_API_PRAKTIKUM,
            params=PARAMS,
            headers=HEADERS
        )
    except requests.exceptions.RequestException as error:
        raise ConnectionError(CONNECTON_ERROR.format(
            ARGUMENTS,
            error=error.__doc__
        ))

    homeworks = response.json()
    for error_key in ['error', 'code']:
        if error_key in homeworks.keys():
            raise ValueError(ERROR_IN_RESPONSE.format(
                ARGUMENTS,
                error=homeworks[error_key]
            )
            )
    return homeworks


"""
Внесение изменений в функцию send_message не позволяет пройти pytest
(бот-клиент как необязательный параметр)
"""


def send_message(message, bot_client):
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


MAIN_ERROR_TEXT = 'Бот столкнулся с ошибкой: {error_text}'
MAIN_PROCCESS_TEXT = 'Отправлен запрос для проверки домашки'


def main():
    bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
    logging.info(BOT_CREATE_SUCCES)
    current_timestamp = int(time.time())
    while True:
        try:
            logging.info(MAIN_PROCCESS_TEXT)
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(
                    parse_homework_status(
                        new_homework.get('homeworks')[0]),
                        bot_client,
                    )
            current_timestamp = new_homework.get(
                'current_date',
                current_timestamp
            )
            time.sleep(1200)
        except Exception as error:
            logging.error(MAIN_ERROR_TEXT.format(error_text=error))
            time.sleep(300)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        filename=__file__ + '.log',
        filemode='a',
        format='%(asctime)s, %(levelname)s, %(name)s, %(message)s',
    )
    main()
