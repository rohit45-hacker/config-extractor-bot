#!/usr/bin/env python3
"""
DarkTunnel Config Extractor Bot
Simple Polling Mode - Render Compatible
"""

import os
import base64
import json
import re
import time
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters
)

# Config
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
OWNER_NAME = os.environ.get("OWNER_NAME", "DʌʀᴋSᴘᴇᴄɪᴀʟ")
CHANNEL_LINK = os.environ.get("CHANNEL_LINK", "https://t.me/YourChannel")
DEV_USERNAME = os.environ.get("DEV_USERNAME", "@YourDev")
ADMIN_ID = os.environ.get("ADMIN_ID", "8217006573")

USER_COOLDOWN = {}
COOLDOWN_SECONDS = 15

class DarkTunnelExtractor:
    def __init__(self):
        self.version = "1.0"

    def extract(self, content, filename="config.txt"):
        try:
            content_str = content.decode('utf-8', errors='ignore') if isinstance(content, bytes) else content

            details = {
                'host': 'Not Found',
                'port': '443',
                'user': 'Not Found',
                'pass': 'Not Found',
                'sni': '',
                'mode': 'NORMAL',
                'payload': '',
                'ssl': True
            }

            # Host
            host_match = re.search(r'(?:Host|Server|host)[:\s]+([a-zA-Z0-9][a-zA-Z0-9.-]*\.[a-zA-Z]{2,})', content_str, re.IGNORECASE)
            if not host_match:
                host_match = re.search(r'([a-zA-Z0-9][a-zA-Z0-9.-]*\.netbill\.site)', content_str, re.IGNORECASE)
            if not host_match:
                host_match = re.search(r'([a-zA-Z0-9][a-zA-Z0-9.-]*\.kamatera\.com)', content_str, re.IGNORECASE)
            if not host_match:
                host_match = re.search(r'([a-zA-Z0-9][a-zA-Z0-9.-]*\.darktunnel\.[a-z]+)', content_str, re.IGNORECASE)

            if host_match:
                details['host'] = host_match.group(1).strip()

            # Port
            port_match = re.search(r'Port[:\s]+(\d{2,5})', content_str, re.IGNORECASE)
            if port_match:
                port = port_match.group(1)
                if 1 <= int(port) <= 65535:
                    details['port'] = port

            # User
            user_match = re.search(r'User(?:name)?[:\s]+(\S+)', content_str, re.IGNORECASE)
            if user_match:
                user = user_match.group(1).strip()
                if user.lower() not in ['not', 'found', 'none', 'null']:
                    details['user'] = user

            # Pass
            pass_match = re.search(r'Pass(?:word)?[:\s]+(\S+)', content_str, re.IGNORECASE)
            if pass_match:
                password = pass_match.group(1).strip()
                if password.lower() not in ['not', 'found', 'none', 'null']:
                    details['pass'] = password

            # SNI
            sni_match = re.search(r'SNI[:\s]+([a-zA-Z0-9][a-zA-Z0-9.-]*\.[a-zA-Z]{2,})', content_str, re.IGNORECASE)
            if sni_match:
                details['sni'] = sni_match.group(1).strip()

            # Mode
            if '[crlf]' in content_str or 'Host:' in content_str:
                details['mode'] = 'HC (Header Custom)'
            elif 'normal' in content_str.lower():
                details['mode'] = 'NM (Normal Mode)'
            elif 'ws' in content_str.lower() or 'websocket' in content_str.lower():
                details['mode'] = 'WS (WebSocket)'

            # Payload
            payload_section = re.search(r'\[PAYLOAD\](.*?)(?:\[|\Z)', content_str, re.DOTALL | re.IGNORECASE)
            if payload_section:
                details['payload'] = payload_section.group(1).strip()
            else:
                get_match = re.search(r'(GET\s+\S+\s+HTTP/[\d.]+.*?(?:

|

|$))', content_str, re.DOTALL | re.IGNORECASE)
                if get_match:
                    payload = get_match.group(1).strip()
                    if len(payload) > 20:
                        details['payload'] = payload

            # Generate import link
            config_data = {
                'v': self.version,
                'host': details['host'],
                'port': details['port'],
                'user': details['user'],
                'pass': details['pass'],
                'sni': details['sni'],
                'mode': details['mode'],
                'ssl': details['ssl'],
                'payload': details['payload']
            }
            json_str = json.dumps(config_data, separators=(',', ':'))
            encoded = base64.b64encode(json_str.encode()).decode()
            import_link = f"darktunnel://{encoded}"

            return {
                'success': True,
                'details': details,
                'import_link': import_link,
                'filename': filename
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def format_payload(self, payload):
        if not payload:
            return "No payload detected"
        display = payload.replace('\r\n', '[crlf]').replace('\n', '[crlf]').replace('\r', '[crlf]')
        display = display.replace('
', '[crlf]').replace('
', '[crlf]').replace('', '[crlf]')
        lines = display.split('[crlf]')
        lines = [l.strip() for l in lines if l.strip()]
        if len(lines) > 8:
            lines = lines[:8]
            lines.append('...')
        return '[crlf]'.join(lines)

extractor = DarkTunnelExtractor()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = f"""
🔷 <b>DarkTunnel Config Extractor</b> 🔷

👤 <b>User:</b> {user.first_name}
🆔 <b>ID:</b> <code>{user.id}</code>

📁 <b>Send me:</b>
• .dark files (DarkTunnel)
• .txt files (Any config)

⚡ <b>I will extract:</b>
🎯 Host | 🔌 Port | 👤 User | 🔑 Pass
🔒 SNI | 🚀 Payload | 📥 Import Link

👑 <b>Owner:</b> {OWNER_NAME}
📢 <b>Channel:</b> {CHANNEL_LINK}
    """
    keyboard = [[InlineKeyboardButton("📢 Channel", url=CHANNEL_LINK)]]
    await update.message.reply_text(text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"""
📖 <b>Commands:</b>
/start - Start bot
/help - This message

📁 <b>Supported:</b> .dark, .txt
⏱️ <b>Cooldown:</b> {COOLDOWN_SECONDS}s
    """
    await update.message.reply_text(text, parse_mode='HTML')

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

async def process_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message

    on_cooldown, remaining = check_cooldown(user.id)
    if on_cooldown:
        await message.reply_text(f"⏱️ <b>Wait {remaining}s!</b>", parse_mode='HTML')
        return

    if not message.document:
        await message.reply_text("❌ Send a file!")
        return

    doc = message.document
    filename = doc.file_name or "unknown.txt"

    if not any(filename.lower().endswith(ext) for ext in ['.dark', '.txt', '.ehi', '.conf']):
        await message.reply_text("❌ <b>Only .dark, .txt, .ehi files!</b>", parse_mode='HTML')
        return

    processing = await message.reply_text(f"🔍 <b>Extracting:</b> <code>{filename}</code>
⏳ Wait...", parse_mode='HTML')

    try:
        file = await context.bot.get_file(doc.file_id)
        file_bytes = await file.download_as_bytearray()
        result = extractor.extract(bytes(file_bytes), filename)

        if not result['success']:
            await processing.edit_text(f"❌ <b>Error:</b> <code>{result['error']}</code>", parse_mode='HTML')
            return

        d = result['details']
        link = result['import_link']
        timestamp = datetime.now().strftime("%I:%M %p")
        ssl_status = f"✅ {d['sni']}" if d['sni'] else "✅ Enabled" if d['ssl'] else "❌ Disabled"
        is_admin = str(user.id) == ADMIN_ID
        admin_tag = "👑 ADMIN" if is_admin else "👤 USER"

        response = f"""
🔷 <b>════[ DARKTUNNEL EXTRACTOR ]════</b> 🔷

📁 <b>Name:</b> <code>{filename[:40]}</code>

🌐 <b>SERVER DETAILS</b>
├─ 🎯 <b>Host:</b> <code>{d['host']}</code>
├─ 🔌 <b>Port:</b> <code>{d['port']}</code>
├─ 👤 <b>User:</b> <code>{d['user']}</code>
└─ 🔑 <b>Pass:</b> <code>{d['pass']}</code>

🚀 <b>INJECT DETAILS</b>
├─ ⚙️ <b>Mode:</b> <code>{d['mode']}</code>
├─ 🔒 <b>SSL/SNI:</b> {ssl_status}
└─ 📦 <b>Payload:</b>
<pre>{extractor.format_payload(d['payload'])[:400]}</pre>

📥 <b>IMPORT LINK</b>
<code>{link[:400]}</code>
{"..." if len(link) > 400 else ""}

👤 <b>By:</b> {admin_tag} | 🆔 <code>{user.id}</code>
👑 {OWNER_NAME} | 📢 {CHANNEL_LINK}

⏰ <code>{timestamp}</code> ✅ <b>Done!</b>
        """

        keyboard = [[InlineKeyboardButton("📢 Channel", url=CHANNEL_LINK)]]
        await processing.delete()
        await message.reply_text(response, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
        await message.reply_text(f"📥 <b>Copy:</b>
<code>{link}</code>", parse_mode='HTML')

    except Exception as e:
        await processing.edit_text(f"❌ <b>Error:</b> <code>{str(e)}</code>", parse_mode='HTML')

async def process_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message

    if not message.text or len(message.text) < 50:
        return

    on_cooldown, remaining = check_cooldown(user.id)
    if on_cooldown:
        await message.reply_text(f"⏱️ <b>Wait {remaining}s!</b>", parse_mode='HTML')
        return

    processing = await message.reply_text("🔍 <b>Extracting text...</b>
⏳ Wait...", parse_mode='HTML')

    try:
        result = extractor.extract(message.text, "pasted_config.txt")

        if not result['success']:
            await processing.delete()
            return

        d = result['details']
        link = result['import_link']
        timestamp = datetime.now().strftime("%I:%M %p")
        ssl_status = f"✅ {d['sni']}" if d['sni'] else "✅ Enabled" if d['ssl'] else "❌ Disabled"
        is_admin = str(user.id) == ADMIN_ID
        admin_tag = "👑 ADMIN" if is_admin else "👤 USER"

        response = f"""
🔷 <b>════[ DARKTUNNEL EXTRACTOR ]════</b> 🔷

📁 <b>Name:</b> <code>Pasted Config</code>

🌐 <b>SERVER DETAILS</b>
├─ 🎯 <b>Host:</b> <code>{d['host']}</code>
├─ 🔌 <b>Port:</b> <code>{d['port']}</code>
├─ 👤 <b>User:</b> <code>{d['user']}</code>
└─ 🔑 <b>Pass:</b> <code>{d['pass']}</code>

🚀 <b>INJECT DETAILS</b>
├─ ⚙️ <b>Mode:</b> <code>{d['mode']}</code>
├─ 🔒 <b>SSL/SNI:</b> {ssl_status}
└─ 📦 <b>Payload:</b>
<pre>{extractor.format_payload(d['payload'])[:300]}</pre>

📥 <b>IMPORT LINK</b>
<code>{link[:300]}</code>
{"..." if len(link) > 300 else ""}

👤 <b>By:</b> {admin_tag} | 🆔 <code>{user.id}</code>
👑 {OWNER_NAME}

⏰ <code>{timestamp}</code> ✅ <b>Done!</b>
        """

        keyboard = [[InlineKeyboardButton("📢 Channel", url=CHANNEL_LINK)]]
        await processing.delete()
        await message.reply_text(response, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
        await message.reply_text(f"📥 <b>Copy:</b>
<code>{link}</code>", parse_mode='HTML')

    except Exception as e:
        await processing.delete()

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update and update.effective_message:
        await update.effective_message.reply_text("❌ <b>Error!</b> Try again.", parse_mode='HTML')

def main():
    if not BOT_TOKEN:
        print("ERROR: Set BOT_TOKEN!")
        return

    print("🔥 DarkTunnel Extractor Bot Starting...")
    print(f"👑 Owner: {OWNER_NAME}")
    print("=" * 50)

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.Document.ALL, process_file))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_text))
    app.add_error_handler(error_handler)

    print("✅ Bot running! Press Ctrl+C to stop.")
    app.run_polling()

if __name__ == "__main__":
    main()
