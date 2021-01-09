import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()


PRAKTIKUM_TOKEN = os.getenv("PRAKTIKUM_TOKEN")
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

URL_API_PRAKTIKUM = (
    'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
)
URL_API_TELEGRAM = 'https://api.telegram.org/bot'
HEADERS = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
BOT_CREATE_SUCCES = 'Бот был успешно создан'
ANSWER = 'У вас проверили работу "{name}"!\n\n{verdict}'
STATUSES = {
    'rejected': 'К сожалению в работе нашлись ошибки.',
    'approved': 'Ревьюеру всё понравилось, '
                'можно приступать к следующему уроку.',
    'reviewing': 'Задание находится на проверке.'
}
STATUS_ERROR_TEXT = (
    'Ни один из ожидаемых статусов домашки не обнаружен! '
    'Полученный статус: "{status}"'
)
ERROR = ('По запросу: {url}, {params}, {headers} '
         'получена ошибка: {error}'
         )
BOT_SEND_MESSAGE = ('Ботом отправленно сообщение о статусе домашки. '
                    'Текст сообщения:"{message}"'
                    )
SEND_MESSAGE_ERROR = 'Бот не смог отправить сообщение из-за ошибки: {error}'
MAIN_ERROR_TEXT = 'Бот столкнулся с ошибкой: {error}'
MAIN_PROCCESS_TEXT = 'Отправлен запрос для проверки домашки'


def parse_homework_status(homework):
    status = homework['status']
    if status not in STATUSES:
        raise ValueError(STATUS_ERROR_TEXT.format(status=status))
    return ANSWER.format(
        name=homework['homework_name'],
        verdict=STATUSES[status],
    )


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
        raise ConnectionError(ERROR.format(
            **ARGUMENTS,
            error=error
        ))
    homeworks = response.json()
    for error_key in ['error', 'code']:
        if error_key in homeworks:
            raise ValueError(ERROR.format(
                **ARGUMENTS,
                error=homeworks[error_key]
            ))
    return homeworks


def send_message(message, bot_client):
    try:
        sending = bot_client.send_message(chat_id=CHAT_ID, text=message)
        logging.info(BOT_SEND_MESSAGE.format(message=message))
        return sending
    except Exception as error:
        logging.error(SEND_MESSAGE_ERROR.format(error=error))


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
            error_message = MAIN_ERROR_TEXT.format(error=error)
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
