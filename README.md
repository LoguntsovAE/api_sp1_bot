# api_sp1_bot
### Telegram - бот
Телеграмм бот, который регулярно с помощью API опрашивает сервис Я.Практикума и если обнаруживается изменение состояния проверки проекта ревьюером то происходит отправка уведомления владельцу сервиса в Telegram.

# Настройка проекта под себя
1. В коде используется скрытие секретной информации с помощью пакета dotenv: токены (на практикуме и telegram-бота), id пользователя в telegram
2. В директори с проектом локально необходимо создать файл .env и  заполнить в нём секретную информацию.
