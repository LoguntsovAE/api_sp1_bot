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


ANSWER = 'У вас проверили работу "{name}"!\n\n{verdict}'
STATUSES = {
    'rejected': 'К сожалению в работе нашлись ошибки.',
    'approved': ('Ревьюеру всё понравилось, '
                 'можно приступать к следующему уроку.'
                 ),
    'reviewing': 'Задание находится на проверке.'
}
STATUS_ERROR_TEXT = (
    'Ни один из возможных статусов домашки не обнаружен! '
    'Полученный статус: "{status}"'
)


def parse_homework_status(homework):
    homework_status = homework['status']
    if homework_status not in STATUSES.keys():
        raise ValueError(STATUS_ERROR_TEXT.format(status=homework_status))
    return ANSWER.format(
                name=homework['homework_name'],
                verdict=STATUSES[homework_status],
            )


CONNECTION_ERROR = 'Получена ошибка соединения: {error}'
HEADERS = {
        'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'
    }
ERROR_IN_RESPONSE = 'Запрос домашней работы провалился из-за ошибки: {error}'


def get_homework_statuses(current_timestamp):
    current_timestamp = current_timestamp or int(time.time())
    ARGUMENTS = dict(
        url=URL_API_PRAKTIKUM,
        params={'from_date': current_timestamp},
        headers=HEADERS,
    )
    try:
        response = requests.get(**ARGUMENTS)
    except requests.exceptions.RequestException as error:
        raise ConnectionError(CONNECTION_ERROR.format(
            **ARGUMENTS,
            error=str(error)
        ))
    homeworks = response.json()
    for error_key in ['error', 'code']:
        if error_key in homeworks.keys():
            raise KeyError(ERROR_IN_RESPONSE.format(
                error=homeworks[error_key]
            )
            )
    return homeworks


BOT_SEND_MESSAGE = 'Ботом отправленно сообщение о статусе домашки'


def send_message(message, bot_client):
    logging.info(BOT_SEND_MESSAGE)
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


MAIN_ERROR_TEXT = 'Бот столкнулся с ошибкой: {error_text}'
MAIN_PROCCESS_TEXT = 'Отправлен запрос для проверки домашки'


def main():
    bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
    logging.debug(BOT_CREATE_SUCCES)
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
            error_message = MAIN_ERROR_TEXT.format(error_text=error)
            logging.error(error_message)
            send_message(error_message, bot_client)
            time.sleep(300)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        filename=__file__ + '.log',
        filemode='a',
        format='%(asctime)s, %(levelname)s, %(name)s, %(message)s',
    )
    main()
