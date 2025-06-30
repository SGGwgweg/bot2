import os
import time
import requests
from bs4 import BeautifulSoup

AUTHORS = {
    'blobcg': 'https://rule34.xyz/blobcg',
    'croove': 'https://rule34.xyz/croove',
    'giddora': 'https://rule34.xyz/giddora',
    'anna_anon': 'https://rule34.xyz/anna_anon',
}

CHECK_INTERVAL = 300
BOT_TOKEN = '8118312308:AAFB79HimMN01tCPTLQ2nnOHpJfZzg1lv5s'
CHAT_ID = '1812059915'

def get_latest_post_url(model_url):
    resp = requests.get(model_url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    container = soup.find('div', class_='box-grid')
    if not container:
        return None
    first_link = container.find('a', class_='box')
    if not first_link or not first_link.get('href'):
        return None
    return requests.compat.urljoin(model_url, first_link['href'])

def load_last_seen(path):
    if os.path.exists(path):
        with open(path, 'r') as f:
            return f.read().strip()
    return None

def save_last_seen(path, url):
    if os.path.exists(path):
        with open(path, 'w') as f:
            f.write(url)
    else:
        print(f"[INFO] Not saving '{path}' — file does not exist yet.")

def send_telegram_message(text):
    if not text or not text.strip():
        return
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    payload = {'chat_id': CHAT_ID, 'text': text, 'disable_web_page_preview': True}
    try:
        resp = requests.post(url, data=payload)
        data = resp.json()
        if not data.get('ok'):
            print('Telegram error:', data.get('description'))
    except Exception as e:
        print('Failed to send Telegram message:', e)

if __name__ == '__main__':
    last_seen = {}
    all_files_exist = True

    # Проверка: существуют ли все необходимые файлы
    for author in AUTHORS:
        path = f'last_seen_{author}.txt'
        if not os.path.exists(path):
            print(f"[ERROR] Missing file: {path}")
            all_files_exist = False

    if not all_files_exist:
        send_telegram_message("Bot error: not all required .txt files found. Exiting.")
        print("[FATAL] Required files missing. Bot is exiting.")
        exit(1)

    # Загрузка предыдущих ссылок
    for author in AUTHORS:
        path = f'last_seen_{author}.txt'
        last_seen[author] = load_last_seen(path)

    send_telegram_message('Bot re-activated and monitoring started.')

    while True:
        for author, url in AUTHORS.items():
            try:
                latest = get_latest_post_url(url)
                if not latest:
                    continue
                if last_seen.get(author) != latest:
                    message = f'New post by {author}: {latest}'
                    send_telegram_message(message)
                    save_last_seen(f'last_seen_{author}.txt', latest)
                    last_seen[author] = latest
            except Exception as e:
                err_msg = f'Error checking {author}: {e}'
                print(err_msg)
                send_telegram_message(err_msg)
        time.sleep(CHECK_INTERVAL)
