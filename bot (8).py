#!/usr/bin/env python3
"""
DarkTunnel Config Extractor Bot v3.0
Fixed patterns for .dark files
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
        self.version = "3.0"

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

            # === HOST PATTERNS (More comprehensive) ===
            host_patterns = [
                r'Host[:\s]+([a-zA-Z0-9][a-zA-Z0-9.-]*\.[a-zA-Z]{2,})',
                r'Server[:\s]+([a-zA-Z0-9][a-zA-Z0-9.-]*\.[a-zA-Z]{2,})',
                r'host[:\s]+([a-zA-Z0-9][a-zA-Z0-9.-]+)',
                r'HOST[:\s]+([a-zA-Z0-9][a-zA-Z0-9.-]+)',
                r'remote\s+([a-zA-Z0-9][a-zA-Z0-9.-]*\.[a-zA-Z]{2,})',
                r'([a-zA-Z0-9][a-zA-Z0-9.-]*\.netbill\.site)',
                r'([a-zA-Z0-9][a-zA-Z0-9.-]*\.kamatera\.com)',
                r'([a-zA-Z0-9][a-zA-Z0-9.-]*\.vultr\.com)',
                r'([a-zA-Z0-9][a-zA-Z0-9.-]*\.digitalocean\.com)',
                r'([a-zA-Z0-9][a-zA-Z0-9.-]*\.darktunnel\.[a-z]+)',
                r'([a-zA-Z0-9][a-zA-Z0-9.-]*\.aws\.[a-z]+)',
                r'([a-zA-Z0-9][a-zA-Z0-9.-]*\.azure\.[a-z]+)',
                r'([a-zA-Z0-9][a-zA-Z0-9.-]*\.cloud\.[a-z]+)',
                r'([a-zA-Z0-9][a-zA-Z0-9.-]*\.linode\.[a-z]+)',
                r'([a-zA-Z0-9][a-zA-Z0-9.-]*\.contabo\.[a-z]+)',
                r'([a-zA-Z0-9][a-zA-Z0-9.-]*\.hetzner\.[a-z]+)',
                r'([a-zA-Z0-9][a-zA-Z0-9.-]*\.ovh\.[a-z]+)',
                r'([a-zA-Z0-9][a-zA-Z0-9.-]*\.rackspace\.[a-z]+)',
            ]

            for pattern in host_patterns:
                match = re.search(pattern, content_str, re.IGNORECASE)
                if match:
                    host = match.group(1).strip()
                    if len(host) > 3 and '.' in host:
                        details['host'] = host
                        break

            # === PORT PATTERNS ===
            port_patterns = [
                r'Port[:\s]+(\d{2,5})',
                r'port[:\s]+(\d{2,5})',
                r'PORT[:\s]+(\d{2,5})',
                r'remote\s+\S+\s+(\d{2,5})',
            ]

            for pattern in port_patterns:
                match = re.search(pattern, content_str, re.IGNORECASE)
                if match:
                    port = match.group(1)
                    if 1 <= int(port) <= 65535:
                        details['port'] = port
                        break

            # === USER PATTERNS ===
            user_patterns = [
                r'User(?:name)?[:\s]+(\S+)',
                r'user[:\s]+(\S+)',
                r'USER(?:NAME)?[:\s]+(\S+)',
                r'Username[:\s]+(\S+)',
                r'username[:\s]+(\S+)',
            ]

            for pattern in user_patterns:
                match = re.search(pattern, content_str, re.IGNORECASE)
                if match:
                    user = match.group(1).strip()
                    if user.lower() not in ['not', 'found', 'none', 'null', '']:
                        details['user'] = user
                        break

            # === PASS PATTERNS ===
            pass_patterns = [
                r'Pass(?:word)?[:\s]+(\S+)',
                r'pass(?:word)?[:\s]+(\S+)',
                r'PASSWORD[:\s]+(\S+)',
                r'Password[:\s]+(\S+)',
                r'password[:\s]+(\S+)',
                r'PASS[:\s]+(\S+)',
            ]

            for pattern in pass_patterns:
                match = re.search(pattern, content_str, re.IGNORECASE)
                if match:
                    password = match.group(1).strip()
                    if password.lower() not in ['not', 'found', 'none', 'null', '']:
                        details['pass'] = password
                        break

            # === SNI PATTERNS ===
            sni_patterns = [
                r'SNI[:\s]+([a-zA-Z0-9][a-zA-Z0-9.-]*\.[a-zA-Z]{2,})',
                r'sni[:\s]+([a-zA-Z0-9][a-zA-Z0-9.-]*\.[a-zA-Z]{2,})',
                r'Sni[:\s]+([a-zA-Z0-9][a-zA-Z0-9.-]*\.[a-zA-Z]{2,})',
            ]

            for pattern in sni_patterns:
                match = re.search(pattern, content_str, re.IGNORECASE)
                if match:
                    details['sni'] = match.group(1).strip()
                    details['ssl'] = True
                    break

            # === MODE DETECTION ===
            if '[crlf]' in content_str or 'Host:' in content_str or 'User-Agent:' in content_str:
                details['mode'] = 'HC (Header Custom)'
            elif 'ws' in content_str.lower() or 'websocket' in content_str.lower():
                details['mode'] = 'WS (WebSocket)'
            elif 'normal' in content_str.lower() or 'direct' in content_str.lower():
                details['mode'] = 'NM (Normal Mode)'
            elif 'ssh' in content_str.lower():
                details['mode'] = 'SSH'
            elif 'ssl' in content_str.lower() or 'tls' in content_str.lower():
                details['mode'] = 'SSL/TLS'

            # === PAYLOAD EXTRACTION ===
            payload = ""

            # Method 1: Find [PAYLOAD] section
            payload_start = content_str.find('[PAYLOAD]')
            if payload_start != -1:
                payload_section = content_str[payload_start + 9:]
                next_section = payload_section.find('[')
                if next_section != -1:
                    payload = payload_section[:next_section].strip()
                else:
                    payload = payload_section.strip()

            # Method 2: Find GET request
            if not payload:
                get_start = content_str.find('GET ')
                if get_start != -1:
                    get_end = content_str.find('HTTP/1.1', get_start)
                    if get_end != -1:
                        payload = content_str[get_start:get_end + 8].strip()

            # Method 3: Find POST request
            if not payload:
                post_start = content_str.find('POST ')
                if post_start != -1:
                    post_end = content_str.find('HTTP/1.1', post_start)
                    if post_end != -1:
                        payload = content_str[post_start:post_end + 8].strip()

            # Method 4: Find CONNECT request
            if not payload:
                conn_start = content_str.find('CONNECT ')
                if conn_start != -1:
                    conn_end = content_str.find('HTTP/1.1', conn_start)
                    if conn_end != -1:
                        payload = content_str[conn_start:conn_end + 8].strip()

            details['payload'] = payload

            # === SSL CHECK ===
            if 'ssl' in content_str.lower() or 'tls' in content_str.lower() or details['port'] == '443':
                details['ssl'] = True

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

    processing = await message.reply_text(f"🔍 <b>Extracting:</b> <code>{filename}</code>\n⏳ Wait...", parse_mode='HTML')

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
        await message.reply_text(f"📥 <b>Copy:</b>\n<code>{link}</code>", parse_mode='HTML')

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

    processing = await message.reply_text("🔍 <b>Extracting text...</b>\n⏳ Wait...", parse_mode='HTML')

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
        await message.reply_text(f"📥 <b>Copy:</b>\n<code>{link}</code>", parse_mode='HTML')

    except Exception as e:
        await processing.delete()

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update and update.effective_message:
        await update.effective_message.reply_text("❌ <b>Error!</b> Try again.", parse_mode='HTML')

def main():
    if not BOT_TOKEN:
        print("ERROR: Set BOT_TOKEN!")
        return

    print("🔥 DarkTunnel Extractor Bot v3.0 Starting...")
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
