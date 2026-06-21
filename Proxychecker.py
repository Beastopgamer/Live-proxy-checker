import os
import threading
import time
import logging
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get tokens from environment variables
BOT_TOKEN = "8170261460:AAGanU42MoI94NwsYerTrmkF2f9iHNxCq-4"
RENDER_PORT = int(os.environ.get("PORT", 8080))

# Initialize Flask app
app = Flask(__name__)

# Rate limiter to prevent abuse
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)

# Initialize bot
bot = TeleBot(BOT_TOKEN)

# Global variables for tracking checking state
checking_state = {
    "active": False,
    "count": 0,
    "live": 0,
    "dead": 0,
    "last_update": time.time()
}

@app.route("/")
@limiter.limit("10 per minute")
def home():
    return jsonify({
        "status": "running",
        "version": "1.0",
        "uptime": time.time() - os.path.getmtime(__file__)
    })

@app.route("/health")
@limiter.limit("5 per minute")
def health():
    return jsonify({"status": "healthy"})

@app.route("/status")
@limiter.limit("20 per minute")
def status():
    return jsonify({
        "active": checking_state["active"],
        "count": checking_state["count"],
        "live": checking_state["live"],
        "dead": checking_state["dead"]
    })

def run_bot():
    """Run bot polling in background thread."""
    global checking_state
    
    @bot.message_handler(commands=["start"])
    def start(message):
        if checking_state["active"]:
            bot.reply_to(message, "Checking in progress, please wait.")
            return
            
        bot.reply_to(
            message,
            "📁 Send a TXT file or paste proxies.\n\nFormat:\nIP:PORT:TYPE[:AUTH]"
        )

    @bot.message_handler(content_types=["document"])
    def handle_document(message):
        if checking_state["active"]:
            bot.reply_to(message, "Checking in progress, please wait.")
            return

        try:
            file_info = bot.get_file(message.document.file_id)
            downloaded = bot.download_file(file_info.file_path)
            
            with open("proxies.txt", "wb") as f:
                f.write(downloaded)

            with open("proxies.txt", "r", encoding="utf-8", errors="ignore") as f:
                proxies = [x.strip() for x in f if ":" in x]

            # Start checking in background
            threading.Thread(target=check_proxies, args=(message, proxies)).start()
        except Exception as e:
            bot.reply_to(message, f"Error: {e}")

    @bot.message_handler(content_types=["text"])
    def handle_text(message):
        if checking_state["active"]:
            bot.reply_to(message, "Checking in progress, please wait.")
            return

        try:
            if ":" not in message.text:
                return

            proxies = [x.strip() for x in message.text.splitlines() if ":" in x]
            if not proxies:
                return

            # Start checking in background
            threading.Thread(target=check_proxies, args=(message, proxies)).start()
        except Exception as e:
            bot.reply_to(message, f"Error: {e}")

    bot.infinity_polling()

def check_proxies(message, proxies):
    """Check proxies and update state."""
    global checking_state
    
    # Initialize state
    checking_state["active"] = True
    checking_state["count"] = len(proxies)
    checking_state["live"] = 0
    checking_state["dead"] = 0
    
    try:
        # Send initial status update
        update_status(message)
        
        # Process proxies
        for i, proxy in enumerate(proxies):
            try:
                # Parse proxy string
                parts = proxy.split(":")
                if len(parts) < 2:
                    checking_state["dead"] += 1
                    continue
                    
                host, port = parts[0], int(parts[1])
                proxy_type = parts[2].lower() if len(parts) > 2 else "http"
                
                # Try proxy based on type
                success = False
                
                # Try HTTP/HTTPS
                if proxy_type in ["http", "https"]:
                    import requests
                    proxies_dict = {
                        "http": f"{proxy_type}://{host}:{port}",
                        "https": f"{proxy_type}://{host}:{port}"
                    }
                    try:
                        r = requests.get(
                            "http://httpbin.org/ip",
                            proxies=proxies_dict,
                            timeout=5
                        )
                        if r.status_code == 200:
                            success = True
                    except:
                        pass
                        
                # Try SOCKS proxies
                elif proxy_type.startswith("socks"):
                    import socks
                    import socket
                    try:
                        protocol = proxy_type.replace("socks", "")
                        sock_type = socks.SOCKS5 if protocol == "5" else socks.SOCKS4
                        
                        sock = socks.socksocket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.set_proxy(sock_type, host, port)
                        
                        sock.connect(("httpbin.org", 80))
                        success = True
                    except:
                        pass
                
                # Update counters
                if success:
                    checking_state["live"] += 1
                else:
                    checking_state["dead"] += 1
                    
                # Update status every 20 proxies
                if i % 20 == 0 or i == len(proxies) - 1:
                    update_status(message)
                    
            except Exception as e:
                checking_state["dead"] += 1
                
    finally:
        checking_state["active"] = False
        
        # Final results
        total_count = len(proxies)
        live_count = checking_state["live"]
        dead_count = checking_state["dead"]
        
        # Generate results file
        with open("live.txt", "w") as f:
            # In real implementation, write actual live proxies here
            f.write("Live proxies would be written here")
        
        # Send final results
        bot.reply_to(
            message,
            f"""
╔═══ ⚡ [𝐁𝐄𝐀𝐒𝐓 𝐂𝐇𝐄𝐂𝐊𝐄𝐑] ⚡ ═══╗
📊 Checked: {total_count}
✅ Live: {live_count}
❌ Dead: {dead_count}
⏱️ Time: {time.time() - checking_state['last_update']:.1f}s
╚════════════════════════════╝
"""
        )

def update_status(message):
    """Update status message."""
    global checking_state
    
    current_time = time.time()
    elapsed = current_time - checking_state["last_update"]
    
    # Only update if enough time has passed
    if elapsed > 1 or checking_state["count"] == checking_state["live"] + checking_state["dead"]:
        try:
            bot.edit_message_text(
                f"⚡️ [𝐁𝐄𝐀𝐒𝐓 𝐂𝐇𝐄𝐂𝐊𝐄𝐑] ⚡️\n\n🔄 Checking proxies...\n\n📊 Checked: {checking_state['live'] + checking_state['dead']}/{checking_state['count']}\n✅ Live: {checking_state['live']}\n❌ Dead: {checking_state['dead']}\n⏱️ Time: {elapsed:.1f}s\n━━━━━━━━━━━━━━━━━━━━━━",
                message.chat.id,
                message.message_id
            )
            checking_state["last_update"] = current_time
        except:
            pass

def main():
    """Start Flask server in main thread and bot in background."""
    # Start bot in background thread
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Start Flask server in main thread
    app.run(
        host="0.0.0.0",
        port=RENDER_PORT,
        debug=False
    )

if __name__ == "__main__":
    main()
