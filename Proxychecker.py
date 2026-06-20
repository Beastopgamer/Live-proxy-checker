import telebot
import requests
from concurrent.futures import ThreadPoolExecutor

BOT_TOKEN = "8170261460:AAGanU42MoI94NwsYerTrmkF2f9iHNxCq-4"

bot = telebot.TeleBot(BOT_TOKEN)

def check_proxy(proxy):
    proxy = proxy.strip()

    try:
        proxies = {
            "http": f"http://{proxy}",
            "https": f"http://{proxy}"
        }

        r = requests.get(
            "http://httpbin.org/ip",
            proxies=proxies,
            timeout=8
        )

        if r.status_code == 200:
            return proxy

    except:
        pass

    return None

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(
        message,
        "📁 Proxy TXT file bhejo.\nFormat:\nIP:PORT"
    )

@bot.message_handler(content_types=['document'])
def handle_file(message):
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)

        with open("proxies.txt", "wb") as f:
            f.write(downloaded)

        with open("proxies.txt", "r", encoding="utf-8", errors="ignore") as f:
            proxies = [x.strip() for x in f if ":" in x]

        msg = bot.reply_to(
            message,
            f"🔍 Checking {len(proxies)} proxies..."
        )

        live = []

        with ThreadPoolExecutor(max_workers=100) as executor:
            results = executor.map(check_proxy, proxies)

            for result in results:
                if result:
                    live.append(result)

        with open("live.txt", "w") as f:
            f.write("\n".join(live))

        with open("live.txt", "rb") as f:
            bot.send_document(
                message.chat.id,
                f,
                caption=f"✅ Live: {len(live)}\n❌ Dead: {len(proxies)-len(live)}"
            )

        bot.delete_message(message.chat.id, msg.message_id)

    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

print("Bot Running...")
bot.infinity_polling()