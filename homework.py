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

URL_API_PRAKTIKUM = (
    'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
)
URL_API_TELEGRAM = 'https://api.telegram.org/bot'

logging.basicConfig(
    level=logging.DEBUG,
    filename='homework.log',
    filemode='a',
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s',
)
logger = logging.getLogger('__name__')
handler = RotatingFileHandler(
    filename='homework.log',
    maxBytes=50000000,
    backupCount=5
)
logger.addHandler(handler)


BAD_VERDICT = 'К сожалению в работе нашлись ошибки.'
GOOD_VERDICT = 'Ревьюеру всё понравилось, можно приступать к следующему уроку.'
REVIEW_IN_PROGRESS = 'Задание находится на проверке'
ANSWER = 'У вас проверили работу "{homework_name}"!\n\n{verdict}'
KEY_ERROR = 'По ключам не получилось получить данные'
PARSE_PROBLEM = 'Проблемы с ключами'
NONAME_STATUS = 'Неизвестный статус работы'


def parse_homework_status(homework):
    if homework.get('homework_name') is None or homework.get('status') is None:
        return PARSE_PROBLEM
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status == 'rejected':
        verdict = BAD_VERDICT
    elif homework_status == 'approved':
        verdict = GOOD_VERDICT
    elif homework_status == 'reviewing':
        verdict = REVIEW_IN_PROGRESS
    else:
        return NONAME_STATUS
    result = ANSWER.format(
        homework_name=homework_name,
        verdict=verdict,
    )
    return result


CODE_RESPONSE_PRAKTIKUM = (
    'Отправлен запрос на сайт Практикума.'
    'Код ответа с сайта Практикума: '
    '{response_status_code}'
)
ERROR_WTH_SERVER = 'Ошибка получения ответа от сервера'


def get_homework_statuses(current_timestamp):
    current_timestamp = current_timestamp or int(time.time())
    PARAMS = {
        'from_date': current_timestamp
    }
    HEADERS = {
        'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'
    }
    try:
        homework_statuses = requests.get(
            URL_API_PRAKTIKUM,
            params=PARAMS,
            headers=HEADERS
        )
        return homework_statuses.json() 
    except (requests.exceptions.RequestException, ValueError):
        logging.error(ERROR_WTH_SERVER)


def send_message(message, bot_client):
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


BOT_CREATE_SUCCES = 'Бот был успешно создан'
BOT_CREATE_ERROR = 'Чё то ботик не создался'
MAIN_ERROR_TEXT = 'Бот столкнулся с ошибкой: {error_text}'


def main():
    try:
        bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
        logging.info(BOT_CREATE_SUCCES)
    except:
        logging.error(BOT_CREATE_ERROR)
    current_timestamp = int(time.time())
    while True:
        try:
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
        except Exception as e:
            logging.error(MAIN_ERROR_TEXT.format(error_text=e))
            time.sleep(300)


if __name__ == '__main__':
    main()
