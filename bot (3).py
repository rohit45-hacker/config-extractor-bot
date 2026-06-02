#!/usr/bin/env python3
"""
Config Extractor Bot - Render Compatible
"""

import os
import sys
import base64
import json
import re
import time
import threading
import logging
from datetime import datetime

from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters
)

# Flask app
flask_app = Flask(__name__)

# Config
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
OWNER_NAME = os.environ.get("OWNER_NAME", "DʌʀᴋSᴘᴇᴄɪᴀʟ")
CHANNEL_LINK = os.environ.get("CHANNEL_LINK", "https://t.me/YourChannel")
DEV_USERNAME = os.environ.get("DEV_USERNAME", "@YourDev")
ADMIN_ID = os.environ.get("ADMIN_ID", "8217006573")
PORT = int(os.environ.get("PORT", "10000"))

RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL", "")
RENDER_EXTERNAL_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "")

if RENDER_EXTERNAL_URL:
    WEBHOOK_URL = RENDER_EXTERNAL_URL
elif RENDER_EXTERNAL_HOSTNAME:
    WEBHOOK_URL = f"https://{RENDER_EXTERNAL_HOSTNAME}"
else:
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")

USER_COOLDOWN = {}
COOLDOWN_SECONDS = 15

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class ConfigExtractor:
    def __init__(self):
        self.version = "3.2"

    def detect_format(self, content):
        content_str = content.decode('utf-8', errors='ignore') if isinstance(content, bytes) else content
        content_lower = content_str.lower()
        if 'darktunnel' in content_lower or 'dark' in content_str[:100].lower():
            return 'DARK'
        elif any(x in content_lower for x in ['ehi', 'ssh', 'payload', 'injector']):
            return 'EHI'
        elif 'openvpn' in content_lower or 'ovpn' in content_lower:
            return 'OVPN'
        else:
            return 'UNKNOWN'

    def decode_base64_content(self, content):
        try:
            if isinstance(content, bytes):
                try:
                    return content.decode('utf-8')
                except:
                    try:
                        decoded = base64.b64decode(content)
                        return decoded.decode('utf-8', errors='ignore')
                    except:
                        return content.decode('utf-8', errors='ignore')
            else:
                try:
                    decoded = base64.b64decode(content)
                    return decoded.decode('utf-8', errors='ignore')
                except:
                    return content
        except:
            return content if isinstance(content, str) else content.decode('utf-8', errors='ignore')

    def extract_server_details(self, content):
        content_str = content if isinstance(content, str) else content.decode('utf-8', errors='ignore')
        details = {
            'host': 'Not Found',
            'port': '80',
            'user': 'Not Found',
            'pass': 'Not Found',
            'sni': '',
            'mode': 'NORMAL',
            'payload': '',
            'ssl': False,
            'expiration': '',
            'dns': ''
        }

        # Host extraction
        host_match = re.search(r'Host[:\s]+([a-zA-Z0-9][a-zA-Z0-9.-]*\.[a-zA-Z]{2,})', content_str, re.IGNORECASE)
        if not host_match:
            host_match = re.search(r'Server[:\s]+([a-zA-Z0-9][a-zA-Z0-9.-]*\.[a-zA-Z]{2,})', content_str, re.IGNORECASE)
        if not host_match:
            host_match = re.search(r'host[:\s]+([a-zA-Z0-9][a-zA-Z0-9.-]+)', content_str, re.IGNORECASE)
        if not host_match:
            host_match = re.search(r'remote\s+([a-zA-Z0-9][a-zA-Z0-9.-]*\.[a-zA-Z]{2,})', content_str, re.IGNORECASE)
        if not host_match:
            host_match = re.search(r'([a-zA-Z0-9][a-zA-Z0-9.-]*\.netbill\.site)', content_str, re.IGNORECASE)
        if not host_match:
            host_match = re.search(r'([a-zA-Z0-9][a-zA-Z0-9.-]*\.kamatera\.com)', content_str, re.IGNORECASE)
        if not host_match:
            host_match = re.search(r'([a-zA-Z0-9][a-zA-Z0-9.-]*\.vultr\.com)', content_str, re.IGNORECASE)
        if not host_match:
            host_match = re.search(r'([a-zA-Z0-9][a-zA-Z0-9.-]*\.digitalocean\.com)', content_str, re.IGNORECASE)

        if host_match:
            host = host_match.group(1).strip()
            if len(host) > 3 and '.' in host:
                details['host'] = host

        # Port extraction
        port_match = re.search(r'Port[:\s]+(\d{2,5})', content_str, re.IGNORECASE)
        if not port_match:
            port_match = re.search(r'port[:\s]+(\d{2,5})', content_str, re.IGNORECASE)
        if not port_match:
            port_match = re.search(r'remote\s+\S+\s+(\d{2,5})', content_str, re.IGNORECASE)

        if port_match:
            port = port_match.group(1)
            if 1 <= int(port) <= 65535:
                details['port'] = port

        if 'ssl' in content_str.lower() or 'tls' in content_str.lower() or details['port'] == '443':
            if details['port'] == '80':
                details['port'] = '443'
            details['ssl'] = True

        # User
        user_match = re.search(r'User(?:name)?[:\s]+(\S+)', content_str, re.IGNORECASE)
        if not user_match:
            user_match = re.search(r'user[:\s]+(\S+)', content_str, re.IGNORECASE)
        if user_match:
            user = user_match.group(1).strip()
            if user.lower() not in ['not', 'found', 'none', 'null']:
                details['user'] = user

        # Pass
        pass_match = re.search(r'Pass(?:word)?[:\s]+(\S+)', content_str, re.IGNORECASE)
        if not pass_match:
            pass_match = re.search(r'pass[:\s]+(\S+)', content_str, re.IGNORECASE)
        if pass_match:
            password = pass_match.group(1).strip()
            if password.lower() not in ['not', 'found', 'none', 'null']:
                details['pass'] = password

        # SNI
        sni_match = re.search(r'SNI[:\s]+([a-zA-Z0-9][a-zA-Z0-9.-]*\.[a-zA-Z]{2,})', content_str, re.IGNORECASE)
        if not sni_match:
            sni_match = re.search(r'sni[:\s]+([a-zA-Z0-9][a-zA-Z0-9.-]*\.[a-zA-Z]{2,})', content_str, re.IGNORECASE)
        if sni_match:
            details['sni'] = sni_match.group(1).strip()
            details['ssl'] = True

        if details['port'] in ['443', '8443', '9443']:
            details['ssl'] = True

        # Mode
        if '[crlf]' in content_str or 'Host:' in content_str or 'User-Agent:' in content_str:
            details['mode'] = 'HC (Header Custom)'
        elif 'normal' in content_str.lower() or 'direct' in content_str.lower():
            details['mode'] = 'NM (Normal Mode)'
        elif 'ws' in content_str.lower() or 'websocket' in content_str.lower():
            details['mode'] = 'WS (WebSocket)'
        else:
            details['mode'] = 'UNKNOWN'

        # Payload
        payload_section = re.search(r'\[PAYLOAD\](.*?)(?:\[|\Z)', content_str, re.DOTALL | re.IGNORECASE)
        if payload_section:
            details['payload'] = payload_section.group(1).strip()
        else:
            get_match = re.search(r'(GET\s+\S+\s+HTTP/[\d.]+.*?(?:\n\n|\r\n\r\n|$))', content_str, re.DOTALL | re.IGNORECASE)
            if get_match:
                payload = get_match.group(1).strip()
                if len(payload) > 20:
                    details['payload'] = payload
            else:
                post_match = re.search(r'(POST\s+\S+\s+HTTP/[\d.]+.*?(?:\n\n|\r\n\r\n|$))', content_str, re.DOTALL | re.IGNORECASE)
                if post_match:
                    payload = post_match.group(1).strip()
                    if len(payload) > 20:
                        details['payload'] = payload

        # Expiration
        exp_match = re.search(r'Expir(?:y|ation|es)[:\s]+(\S+)', content_str, re.IGNORECASE)
        if exp_match:
            details['expiration'] = exp_match.group(1)

        return details

    def generate_import_link(self, details, format_type='DARK'):
        config_data = {
            'v': self.version,
            'host': details['host'],
            'port': details['port'],
            'user': details['user'],
            'pass': details['pass'],
            'sni': details['sni'],
            'mode': details['mode'],
            'ssl': details['ssl'],
            'payload': details['payload'],
            'timestamp': datetime.now().isoformat()
        }
        json_str = json.dumps(config_data, separators=(',', ':'))
        encoded = base64.b64encode(json_str.encode()).decode()

        if format_type == 'DARK':
            return f"darktunnel://{encoded}"
        elif format_type == 'EHI':
            return f"httpinjector://{encoded}"
        else:
            return f"config://{encoded}"

    def format_payload_display(self, payload, max_lines=8):
        if not payload:
            return "No payload detected"
        display = payload.replace('\\r\\n', '[crlf]').replace('\\n', '[crlf]').replace('\\r', '[crlf]')
        display = display.replace('\r\n', '[crlf]').replace('\n', '[crlf]').replace('\r', '[crlf]')
        lines = display.split('[crlf]')
        lines = [l.strip() for l in lines if l.strip()]
        if len(lines) > max_lines:
            lines = lines[:max_lines]
            lines.append('...')
        return '[crlf]'.join(lines)

    def process_content(self, content, filename="config.txt"):
        try:
            decoded = self.decode_base64_content(content)
            format_type = self.detect_format(decoded)
            details = self.extract_server_details(decoded)
            import_link = self.generate_import_link(details, format_type)
            return {
                'success': True,
                'details': details,
                'import_link': import_link,
                'format': format_type,
                'filename': filename
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

extractor = ConfigExtractor()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = f"""
🔷 <b>Welcome to Premium Config Extractor Bot!</b> 🔷

👤 <b>User:</b> {user.first_name}
🆔 <b>ID:</b> <code>{user.id}</code>

📋 <b>How to use:</b>
1️⃣ Send me a config file (.ehi, .dark, .txt)
2️⃣ I'll extract server details automatically
3️⃣ Get styled output + import link

📁 <b>Supported Formats:</b>
• EHI (HTTP Injector)
• DARK (DarkTunnel)
• OVPN (OpenVPN)

⚡ <b>Features:</b>
✅ Auto format detection
✅ NM / HC / WS mode detection
✅ SSL/SNI extraction
✅ Payload parsing
✅ Import link generation

👑 <b>Owner:</b> {OWNER_NAME}
📢 <b>Channel:</b> {CHANNEL_LINK}
👨‍💻 <b>Dev:</b> {DEV_USERNAME}
    """
    keyboard = [
        [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)],
        [InlineKeyboardButton("💬 Support", url=f"https://t.me/{DEV_USERNAME[1:]}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_text, parse_mode='HTML', reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = f"""
📖 <b>Bot Commands:</b>

/start - Start the bot
/help - Show this help message
/about - About the bot
/status - Check bot status

📁 <b>Send me any config file:</b>
• .ehi files (HTTP Injector)
• .dark files (DarkTunnel)
• .txt files (Any text config)

⚙️ <b>What I extract:</b>
🎯 Server Host | 🔌 Port | 👤 Username | 🔑 Password
🔒 SSL/SNI status | 🚀 Payload details | 📥 Import link

⏱️ <b>Rate Limit:</b> {COOLDOWN_SECONDS}s between requests
    """
    await update.message.reply_text(help_text, parse_mode='HTML')

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    about_text = f"""
🔷 <b>About Premium Extractor Bot</b> 🔷

🤖 <b>Bot Name:</b> Config Extractor
📊 <b>Version:</b> 3.2
🛠️ <b>Status:</b> Active ✅

👑 <b>Owner:</b> {OWNER_NAME}
📢 <b>Channel:</b> {CHANNEL_LINK}
👨‍💻 <b>Developer:</b> {DEV_USERNAME}
🆔 <b>Admin ID:</b> <code>{ADMIN_ID}</code>

⚡ <b>Powered by Python & Flask</b>
    """
    await update.message.reply_text(about_text, parse_mode='HTML')

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    is_admin = str(user.id) == ADMIN_ID
    admin_badge = "👑 ADMIN" if is_admin else "👤 USER"
    status_text = f"""
📊 <b>Bot Status</b> 📊

👤 <b>Your Status:</b> {admin_badge}
🆔 <b>Your ID:</b> <code>{user.id}</code>

🤖 <b>Bot:</b> Active ✅
⚡ <b>Version:</b> 3.2

📁 <b>Supported:</b> EHI | DARK | OVPN
🚀 <b>Modes:</b> NM | HC | WS

⏱️ <b>Cooldown:</b> {COOLDOWN_SECONDS} seconds
    """
    await update.message.reply_text(status_text, parse_mode='HTML')

def check_cooldown(user_id):
    current_time = time.time()
    if str(user_id) == ADMIN_ID:
        return False, 0
    if user_id in USER_COOLDOWN:
        elapsed = current_time - USER_COOLDOWN[user_id]
        if elapsed < COOLDOWN_SECONDS:
            return True, COOLDOWN_SECONDS - int(elapsed)
    USER_COOLDOWN[user_id] = current_time
    return False, 0

async def process_config_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message
    on_cooldown, remaining = check_cooldown(user.id)
    if on_cooldown:
        await message.reply_text(f"⏱️ <b>Please wait {remaining}s before next request!</b>", parse_mode='HTML')
        return
    if not message.document:
        await message.reply_text("❌ Please send a file!")
        return
    doc = message.document
    filename = doc.file_name or "unknown.txt"
    allowed_ext = ['.ehi', '.dark', '.txt', '.ovpn', '.conf']
    if not any(filename.lower().endswith(ext) for ext in allowed_ext):
        await message.reply_text(f"❌ <b>Unsupported file format!</b>\n\n📁 <b>Supported:</b> .ehi, .dark, .txt, .ovpn, .conf", parse_mode='HTML')
        return
    processing_msg = await message.reply_text(f"🔍 <b>Processing:</b> <code>{filename}</code>\n⏳ Please wait...", parse_mode='HTML')
    try:
        file = await context.bot.get_file(doc.file_id)
        file_bytes = await file.download_as_bytearray()
        result = extractor.process_content(bytes(file_bytes), filename)
        if not result['success']:
            await processing_msg.edit_text(f"❌ <b>Error processing file!</b>\n\n<code>{result['error']}</code>", parse_mode='HTML')
            return
        details = result['details']
        format_type = result['format']
        import_link = result['import_link']
        timestamp = datetime.now().strftime("%I:%M %p")
        ssl_status = f"✅ {details['sni']}" if details['ssl'] and details['sni'] else ("✅ Enabled" if details['ssl'] else "❌ Disabled")
        is_admin = str(user.id) == ADMIN_ID
        admin_tag = "👑 ADMIN" if is_admin else "👤 USER"
        response = f"""
🔷 <b>════[ PREMIUM EXTRACTOR ]════</b> 🔷

📁 <b>Name:</b> <code>{filename[:40]}</code>

🌐 <b>SERVER DETAILS</b> ]—✧
├─ 🎯 <b>Host:</b> <code>{details['host']}</code>
├─ 🔌 <b>Port:</b> <code>{details['port']}</code>
├─ 👤 <b>User:</b> <code>{details['user']}</code>
└─ 🔑 <b>Pass:</b> <code>{details['pass']}</code>

🚀 <b>INJECT DETAILS</b> ]—✧
├─ ⚙️ <b>Mode:</b> <code>{details['mode']}</code>
├─ 🔒 <b>SSL/SNI:</b> {ssl_status}
└─ 📦 <b>Payload:</b>
<pre>{extractor.format_payload_display(details['payload'])[:400]}</pre>

📥 <b>IMPORT LINK</b> (Copy Below)
Format: <code>{format_type}</code>
<code>{import_link[:400]}</code>
{"..." if len(import_link) > 400 else ""}

👤 <b>Requested by:</b> {admin_tag}
├─ 🆔 <code>{user.id}</code>
├─ 👑 {OWNER_NAME}
└─ 📢 {CHANNEL_LINK}

⏰ <code>{timestamp}</code> ✅ <b>Decrypted Successfully</b>
        """
        keyboard = [
            [InlineKeyboardButton("📢 Channel", url=CHANNEL_LINK), InlineKeyboardButton("👨‍💻 Dev", url=f"https://t.me/{DEV_USERNAME[1:]}")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await processing_msg.delete()
        await message.reply_text(response, parse_mode='HTML', reply_markup=reply_markup)
        await message.reply_text(f"📥 <b>Quick Copy Link:</b>\n\n<code>{import_link}</code>", parse_mode='HTML')
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        await processing_msg.edit_text(f"❌ <b>Error:</b> <code>{str(e)}</code>", parse_mode='HTML')

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message
    if not message.text or len(message.text) < 50:
        return
    on_cooldown, remaining = check_cooldown(user.id)
    if on_cooldown:
        await message.reply_text(f"⏱️ <b>Please wait {remaining}s!</b>", parse_mode='HTML')
        return
    processing_msg = await message.reply_text("🔍 <b>Processing pasted config...</b>\n⏳ Please wait...", parse_mode='HTML')
    try:
        result = extractor.process_content(message.text, "pasted_config.txt")
        if not result['success']:
            await processing_msg.delete()
            return
        details = result['details']
        format_type = result['format']
        import_link = result['import_link']
        ssl_status = f"✅ {details['sni']}" if details['ssl'] and details['sni'] else ("✅ Enabled" if details['ssl'] else "❌ Disabled")
        is_admin = str(user.id) == ADMIN_ID
        admin_tag = "👑 ADMIN" if is_admin else "👤 USER"
        timestamp = datetime.now().strftime("%I:%M %p")
        response = f"""
🔷 <b>════[ PREMIUM EXTRACTOR ]════</b> 🔷

📁 <b>Name:</b> <code>Pasted Config</code>

🌐 <b>SERVER DETAILS</b> ]—✧
├─ 🎯 <b>Host:</b> <code>{details['host']}</code>
├─ 🔌 <b>Port:</b> <code>{details['port']}</code>
├─ 👤 <b>User:</b> <code>{details['user']}</code>
└─ 🔑 <b>Pass:</b> <code>{details['pass']}</code>

🚀 <b>INJECT DETAILS</b> ]—✧
├─ ⚙️ <b>Mode:</b> <code>{details['mode']}</code>
├─ 🔒 <b>SSL/SNI:</b> {ssl_status}
└─ 📦 <b>Payload:</b>
<pre>{extractor.format_payload_display(details['payload'])[:300]}</pre>

📥 <b>IMPORT LINK</b>
Format: <code>{format_type}</code>
<code>{import_link[:300]}</code>
{"..." if len(import_link) > 300 else ""}

👤 <b>Requested by:</b> {admin_tag}
├─ 🆔 <code>{user.id}</code>
└─ 👑 {OWNER_NAME}

⏰ <code>{timestamp}</code> ✅ <b>Decrypted</b>
        """
        keyboard = [
            [InlineKeyboardButton("📢 Channel", url=CHANNEL_LINK)],
            [InlineKeyboardButton("👨‍💻 Dev", url=f"https://t.me/{DEV_USERNAME[1:]}")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await processing_msg.delete()
        await message.reply_text(response, parse_mode='HTML', reply_markup=reply_markup)
        await message.reply_text(f"📥 <b>Quick Copy:</b>\n<code>{import_link}</code>", parse_mode='HTML')
    except Exception as e:
        await processing_msg.delete()
        logger.error(f"Error processing text: {e}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text("❌ <b>An error occurred!</b>\nPlease try again or contact the developer.", parse_mode='HTML')

@flask_app.route('/')
def home():
    return jsonify({"status": "Bot is running!", "version": "3.2", "owner": OWNER_NAME, "channel": CHANNEL_LINK, "dev": DEV_USERNAME})

@flask_app.route('/health')
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@flask_app.route(f'/webhook/<token>', methods=['POST'])
def webhook(token):
    if token != BOT_TOKEN.split(':')[1]:
        return jsonify({"error": "Invalid token"}), 403
    update = Update.de_json(request.get_json(force=True), bot_app.bot)
    bot_app.update_queue.put_nowait(update)
    return jsonify({"status": "ok"})

bot_app = None

def setup_bot():
    global bot_app
    if not BOT_TOKEN:
        print("ERROR: BOT_TOKEN not set!")
        sys.exit(1)
    print("Starting Config Extractor Bot...")
    print(f"Owner: {OWNER_NAME}")
    print(f"Channel: {CHANNEL_LINK}")
    print(f"Dev: {DEV_USERNAME}")
    print("=" * 50)
    bot_app = Application.builder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("help", help_command))
    bot_app.add_handler(CommandHandler("about", about_command))
    bot_app.add_handler(CommandHandler("status", status_command))
    bot_app.add_handler(MessageHandler(filters.Document.ALL, process_config_file))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    bot_app.add_error_handler(error_handler)
    print("Bot handlers registered!")
    return bot_app

def run_webhook():
    global bot_app
    bot_app = setup_bot()
    webhook_path = f"/webhook/{BOT_TOKEN.split(':')[1]}"
    full_webhook_url = f"{WEBHOOK_URL.rstrip('/')}{webhook_path}"
    print(f"Starting WEBHOOK mode...")
    print(f"Webhook URL: {full_webhook_url}")
    print(f"Port: {PORT}")
    def start_bot():
        bot_app.run_polling()
    bot_thread = threading.Thread(target=start_bot)
    bot_thread.daemon = True
    bot_thread.start()
    print(f"Starting Flask server on port {PORT}...")
    flask_app.run(host='0.0.0.0', port=PORT)

def run_polling():
    global bot_app
    bot_app = setup_bot()
    print("Starting POLLING mode...")
    bot_app.run_polling()

if __name__ == "__main__":
    if WEBHOOK_URL:
        run_webhook()
    else:
        run_polling()
