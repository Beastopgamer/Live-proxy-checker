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
        "📁 Send a TXT file containing proxies.\n\nFormat:\nIP:PORT"
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

        total_count = len(proxies)
        live_count = len(live)
        dead_count = total_count - live_count

        try:
            bot.delete_message(message.chat.id, msg.message_id)
        except:
            pass

        user_name = (
            f"@{message.from_user.username}"
            if message.from_user.username
            else message.from_user.first_name
        )

        if live_count == 0:
            bot.send_message(
                message.chat.id,
                f"""
╔═══ ⚡ 𝐋𝐈𝐕𝐄 𝐏𝐑𝐎𝐗𝐘 𝐂𝐇𝐄𝐂𝐊𝐄𝐑 ⚡ ═══╗

👤 𝐂𝐡𝐞𝐜𝐤𝐞𝐝 𝐁𝐲 : {user_name}
🤖 𝐁𝐨𝐭 𝐁𝐲     : 𝐁𝐄𝐀𝐒𝐓

📊 𝐓𝐨𝐭𝐚𝐥      : {total_count}
✅ 𝐋𝐢𝐯𝐞       : 0
❌ 𝐃𝐞𝐚𝐝       : {dead_count}

🚫 𝐍𝐨 𝐥𝐢𝐯𝐞 𝐩𝐫𝐨𝐱𝐢𝐞𝐬 𝐟𝐨𝐮𝐧𝐝.

╚════════════════════════════╝
"""
            )
            return

        with open("live.txt", "w") as f:
            f.write("\n".join(live))

        caption = f"""
╔═══ ⚡ 𝐋𝐈𝐕𝐄 𝐏𝐑𝐎𝐗𝐘 𝐂𝐇𝐄𝐂𝐊𝐄𝐑 ⚡ ═══╗

👤 𝐂𝐡𝐞𝐜𝐤𝐞𝐝 𝐁𝐲 : {user_name}
🤖 𝐁𝐨𝐭 𝐁𝐲     : 𝐁𝐄𝐀𝐒𝐓

📁 𝐅𝐢𝐥𝐞       : {message.document.file_name}

📊 𝐓𝐨𝐭𝐚𝐥      : {total_count}
✅ 𝐋𝐢𝐯𝐞       : {live_count}
❌ 𝐃𝐞𝐚𝐝       : {dead_count}

🔥 𝐏𝐨𝐰𝐞𝐫𝐞𝐝 𝐁𝐲 𝐁𝐄𝐀𝐒𝐓

╚════════════════════════════╝
"""

        with open("live.txt", "rb") as f:
            bot.send_document(
                message.chat.id,
                f,
                caption=caption
            )

    except Exception as e:
        bot.reply_to(message, f"Error: {e}")


print("Bot Running...")
bot.infinity_polling()
