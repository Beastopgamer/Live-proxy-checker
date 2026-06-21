import telebot
import requests
import socks
import socket
import time
from concurrent.futures import ThreadPoolExecutor
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Configuration
BOT_TOKEN = "8170261460:AAGanU42MoI94NwsYerTrmkF2f9iHNxCq-4"
CHANNELS = [-1002319804649, -1002148143676]
TIMEOUT = 15

bot = telebot.TeleBot(BOT_TOKEN)

def is_joined(user_id):
    """Check if user has joined required channels."""
    try:
        for channel in CHANNELS:
            member = bot.get_chat_member(channel, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        return True
    except:
        return False

def check_proxy(proxy_str, message, index, total, live_list, dead_list, start_time, last_update):
    """Check individual proxy with progress updates."""
    try:
        parts = proxy_str.strip().split(":")
        if len(parts) < 2:
            dead_list.append(None)
            return
            
        host, port = parts[0], int(parts[1])
        proxy_type = parts[2].lower() if len(parts) > 2 else "http"
        auth = f"{parts[3]}:{parts[4]}@" if len(parts) > 4 else ""
        
        # Calculate elapsed time
        elapsed = time.time() - start_time
        time_per_proxy = elapsed / max(index, 1)
        
        # Update progress every 20 proxies or at completion
        if index % 20 == 0 or index == total - 1:
            try:
                bot.edit_message_text(
                    f"⚡️ [𝐁𝐄𝐀𝐒𝐓 𝐂𝐇𝐄𝐂𝐊𝐄𝐑] ⚡️\n\n🔄 Checking proxies...\n\n📊 Checked: {index+1}/{total}\n✅ Live: {len(live_list)}\n❌ Dead: {len(dead_list)}\n⏱️ Time: {elapsed:.1f}s\n⏰ ETA: {(total-index)*time_per_proxy:.1f}s\n━━━━━━━━━━━━━━━━━━━━━━",
                    message.chat.id,
                    message.message_id
                )
                last_update[0] = time.time()
            except:
                pass
        
        # Try HTTP/HTTPS
        if proxy_type in ["http", "https"]:
            proxies = {
                "http": f"{proxy_type}://{auth}{host}:{port}",
                "https": f"{proxy_type}://{auth}{host}:{port}"
            }
            r = requests.get(
                "http://httpbin.org/ip",
                proxies=proxies,
                timeout=TIMEOUT
            )
            if r.status_code == 200:
                live_list.append(f"{host}:{port}")
                return
                
        # Try SOCKS proxies
        elif proxy_type.startswith("socks"):
            protocol = proxy_type.replace("socks", "")
            sock_type = socks.SOCKS5 if protocol == "5" else socks.SOCKS4
            
            sock = socks.socksocket(socket.AF_INET, socket.SOCK_STREAM)
            sock.set_proxy(sock_type, host, port)
            
            if protocol == "5" and len(parts) > 4:
                sock.set_auth(parts[3], parts[4])
                
            sock.connect(("httpbin.org", 80))
            live_list.append(f"{host}:{port}")
            return
            
    except Exception as e:
        pass
    dead_list.append(None)

def send_results(message, proxies):
    """Check all proxies and send results."""
    # Send initial message
    start_time = time.time()
    msg = bot.reply_to(
        message,
        "⚡️ [𝐁𝐄𝐀𝐒𝐓 𝐂𝐇𝐄𝐂𝐊𝐄𝐑] ⚡️\n\n🔄 Checking proxies...\n\n📊 Checked: 0/0\n✅ Live: 0\n❌ Dead: 0\n⏱️ Time: 0.0s\n⏰ ETA: 0.0s\n━━━━━━━━━━━━━━━━━━━━━━"
    )
    
    live = []
    dead = []
    last_update = [time.time()]
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = []
        for i, proxy in enumerate(proxies):
            future = executor.submit(
                check_proxy, 
                proxy, 
                message, 
                i, 
                len(proxies),
                live,
                dead,
                start_time,
                last_update
            )
            futures.append(future)
            
        for future in futures:
            future.result()
    
    # Remove progress message
    try:
        bot.delete_message(message.chat.id, msg.message_id)
    except:
        pass
    
    total_count = len(proxies)
    live_count = len(live)
    dead_count = len(dead)
    elapsed = time.time() - start_time
    
    user_name = (
        f"@{message.from_user.username}"
        if message.from_user.username
        else message.from_user.first_name
    )
    
    if live_count == 0:
        bot.send_message(
            message.chat.id,
            f"""
╔═══ ⚡ [𝐁𝐄𝐀𝐒𝐓 𝐂𝐇𝐄𝐂𝐊𝐄𝐑] ⚡ ═══╗
👤 [𝐂𝐡𝐞𝐜𝐤𝐞𝐝 𝐁𝐲] : {user_name}
🤖 [𝐁𝐨𝐭 𝐁𝐲]     : [𝐁𝐄𝐀𝐒𝐓]
📊 [𝐓𝐨𝐭𝐚𝐥]      : {total_count}
✅ [𝐋𝐢𝐯𝐞]       : 0
❌ [𝐃𝐞𝐚𝐝]       : {dead_count}
⏱️ [𝐓𝐢𝐦𝐞]       : {elapsed:.1f}s
🚫 [𝐍𝐨 𝐋𝐢𝐯𝐞 𝐏𝐫𝐨𝐱𝐢𝐞𝐬 𝐅𝐨𝐮𝐧𝐝]
╚════════════════════════════╝
"""
        )
        return
    
    with open("live.txt", "w") as f:
        f.write("\n".join(live))
    
    caption = f"""
╔═══ ⚡ [𝐁𝐄𝐀𝐒𝐓 𝐂𝐇𝐄𝐂𝐊𝐄𝐑] ⚡ ═══╗
👤 [𝐂𝐡𝐞𝐜𝐤𝐞𝐝 𝐁𝐲] : {user_name}
🤖 [𝐁𝐨𝐭 𝐁𝐲]     : [𝐁𝐄𝐀𝐒𝐓]
📁 [𝐅𝐢𝐥𝐞]       : live.txt
📊 [𝐓𝐨𝐭𝐚𝐥]      : {total_count}
✅ [𝐋𝐢𝐯𝐞]       : {live_count}
❌ [𝐃𝐞𝐚𝐝]       : {dead_count}
⏱️ [𝐓𝐢𝐦𝐞]       : {elapsed:.1f}s
🔥 [𝐏𝐨𝐰𝐞𝐫𝐞𝐝 𝐁𝐲 𝐁𝐄𝐀𝐒𝐓]
╚════════════════════════════╝
"""
    
    with open("live.txt", "rb") as f:
        bot.send_document(
            message.chat.id,
            f,
            caption=caption
        )

@bot.message_handler(commands=["start"])
def start(message):
    if is_joined(message.from_user.id):
        bot.reply_to(
            message,
            "📁 Send a TXT file or paste proxies.\n\nFormat:\nIP:PORT:TYPE[:AUTH]"
        )
        return

    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("📢 Join Channel 1", url="https://t.me/+nhk1ZA4YEqAzZThl"))
    markup.add(InlineKeyboardButton("📢 Join Channel 2", url="https://t.me/+0lmUYBlpF-NlZjg9"))
    markup.add(InlineKeyboardButton("✅ Verify", callback_data="verify_join"))
    
    bot.send_message(
        message.chat.id,
        "⚠️ You must join both channels before using this bot.",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "verify_join")
def verify_join(call):
    if is_joined(call.from_user.id):
        bot.edit_message_text(
            "✅ Verification Successful!\n\n📁 Send a TXT file or paste proxies.\n\nFormat:\nIP:PORT:TYPE[:AUTH]",
            call.message.chat.id,
            call.message.message_id
        )
    else:
        bot.answer_callback_query(call.id, "❌ Please join both channels first.")

@bot.message_handler(content_types=["document"])
def handle_document(message):
    if not is_joined(message.from_user.id):
        start(message)
        return

    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        
        with open("proxies.txt", "wb") as f:
            f.write(downloaded)

        with open("proxies.txt", "r", encoding="utf-8", errors="ignore") as f:
            proxies = [x.strip() for x in f if ":" in x]

        send_results(message, proxies)
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

@bot.message_handler(content_types=["text"])
def handle_text(message):
    if not is_joined(message.from_user.id):
        start(message)
        return

    try:
        if ":" not in message.text:
            return

        proxies = [x.strip() for x in message.text.splitlines() if ":" in x]
        if not proxies:
            return

        send_results(message, proxies)
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

print("Bot Running...")
bot.infinity_polling()
