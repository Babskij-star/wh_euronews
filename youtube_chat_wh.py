import requests
import time
import random
import logging

# Конфигурация
API_KEY = 'AIzaSyAcaItM4vmsh2HE6pF7gMJpQm62MmxjY5E'  # Вставь свой API-ключ
VIDEO_ID = 'lwYzwdBiaho'  # ID видео
TARGET_USER =  'White'  # Имя пользователя, за которым будем следить
TELEGRAM_TOKEN = '7458010578:AAFn2QR5x7cVQcXduUbObqjId3zgUL-S_ms'  # Токен вашего Telegram бота
CHAT_ID = '486253984'  # Ваш chat_id для отправки сообщений

# Переменные для отслеживания
last_message_time = None  # Храним время последнего обработанного сообщения
last_success_time = time.time()  # Время последнего успешного получения сообщений
last_check_time = time.time()  # Время последней проверки работоспособности

# Настройка логирования
logging.basicConfig(level=logging.INFO, filename="chat_monitor_target_user.log", filemode="a",
                    format="%(asctime)s - %(levelname)s - %(message)s")

def send_telegram_message(message):
    """Отправить сообщение в Telegram с логированием"""
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    data = {'chat_id': CHAT_ID, 'text': message}
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        logging.info("Сообщение отправлено в Telegram: %s", message)
    except Exception as e:
        logging.error("Ошибка при отправке сообщения в Telegram: %s", str(e))

def get_live_chat_id(video_id):
    """Получить ID чата для активной трансляции"""
    video_url = f'https://www.googleapis.com/youtube/v3/videos?id={video_id}&key={API_KEY}&part=liveStreamingDetails'
    try:
        video_response = requests.get(video_url)
        video_response.raise_for_status()
        video_data = video_response.json()
        if 'items' in video_data and 'liveStreamingDetails' in video_data['items'][0]:
            return video_data['items'][0]['liveStreamingDetails']['activeLiveChatId']
        else:
            logging.info("Чат недоступен.")
            return None
    except Exception as e:
        logging.error(f"Ошибка при получении ID чата: {e}")
        send_telegram_message("Ошибка скрипта при получении ID чата")
        return None

def get_chat_messages(chat_id):
    """Получить сообщения из чата с обработкой ошибок"""
    chat_url = f'https://www.googleapis.com/youtube/v3/liveChat/messages?liveChatId={chat_id}&part=snippet,authorDetails&key={API_KEY}'
    try:
        chat_response = requests.get(chat_url)
        chat_response.raise_for_status()
        return chat_response.json()
    except Exception as e:
        logging.error(f"Ошибка при получении сообщений из чата: {e}")
        send_telegram_message("Ошибка скрипта при получении сообщений из чата")
        return {}

def get_new_messages(chat_id):
    """Получить только новые сообщения, появившиеся после последнего обработанного времени"""
    global last_message_time, last_success_time
    new_messages = []
    try:
        messages = get_chat_messages(chat_id)
        if 'items' in messages:
            if messages['items']:  # Проверка на наличие новых сообщений
                last_success_time = time.time()  # Обновляем время последнего успешного получения сообщений
            for item in messages['items']:
                message_time = item['snippet']['publishedAt']
                if last_message_time is None or message_time > last_message_time:
                    author = item['authorDetails']['displayName']
                    message = item['snippet']['displayMessage']

 					# Добавляем отладочный вывод перед отправкой сообщения
                    print(f"Обрабатываем сообщение: {message} от {author} в {message_time}")

                    # Проверка на TARGET_USER
                    if TARGET_USER in author:
                        send_telegram_message(f"{TARGET_USER} оставила сообщение: {message}")
                    last_message_time = message_time

    except Exception as e:
        logging.error(f"Ошибка при обработке новых сообщений: {e}")
        send_telegram_message("Ошибка скрипта при обработке новых сообщений")
    return new_messages

def check_script_health():
    """Проверить работоспособность скрипта и перезапустить, если он не работает"""
    global last_success_time
    if time.time() - last_success_time > 2800:  # 63 минут
        send_telegram_message("Скрипт не работал более 63 минуты. Перезапуск...")
        logging.info("Перезапуск скрипта из-за отсутствия новых сообщений.")
        raise Exception("Перезапуск скрипта из-за отсутствия новых сообщений")

def main():
    while True:
        try:
            chat_id = get_live_chat_id(VIDEO_ID)
            if chat_id:
                while True:
                    get_new_messages(chat_id)
                    check_script_health()  # Проверка работоспособности
                    time.sleep(random.uniform(50, 80))
            else:
                logging.error("Не удалось получить ID чата.")
            time.sleep(300)  # Повторная проверка трансляции каждые 5 минут
        except Exception as e:
            logging.error(f"Общая ошибка в скрипте: {e}")
            send_telegram_message("Ошибка скрипта")
            time.sleep(600)  # Подождать 10 минут перед повторным запуском

if __name__ == "__main__":
    main()
